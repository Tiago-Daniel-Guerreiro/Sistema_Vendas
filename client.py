import json
import socket
import os
import getpass
import time
from enums import Cores
import subprocess

DEBUG = False

class ClienteRede:
    def __init__(self, host, port):
        self.host = host
        self.port = port

    def testar_ping(self):
        comando = ['ping', '-n', '1', self.host]
        try:
            resultado = subprocess.run(comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=2)
            return resultado.returncode == 0
        except Exception:
            return False

    def enviar(self, acao, parametros=None):
        if parametros is None:
            parametros = {}
        
        dados_json = json.dumps({'acao': acao, 'parametros': parametros}) + '\n'
        
        try:
            with socket.create_connection((self.host, self.port), timeout=5) as conexao:
                conexao.sendall(dados_json.encode('utf-8'))
                
                resposta_bytes = b''
                while True:
                    parte = conexao.recv(4096) # Recebe 4096 bytes por vez
                    if not parte:
                        break
                    
                    resposta_bytes += parte
                    if b'\n' in parte:
                        break
                
                resposta_str = resposta_bytes.decode('utf-8').strip()
                if not resposta_str:
                    return {'ok': False, 'erro': 'Resposta vazia do servidor'}
                
                global DEBUG
                if DEBUG:
                    print(f"{Cores.CINZA}{resposta_str}{Cores.NORMAL}")

                return json.loads(resposta_str)
        except ConnectionRefusedError:
            return {'ok': False, 'erro': 'Não foi possível conectar ao servidor.'}
        except Exception as e:
            return {'ok': False, 'erro': f'Erro de comunicação: {str(e)}'}

class ClienteVendas:
    def __init__(self, host, port):
        self.rede = ClienteRede(host, port)
        self.utilizador = None
        self.cargo = None
        self.comandos_disponiveis = {}

    def limpar_tela(self):
        os.system('cls')

    def mostrar_cabecalho(self, texto):
        print(f"\n{Cores.ROXO}{Cores.NEGRITO}{texto} {Cores.NORMAL}")

    def mostrar_sucesso(self, texto):
        print(f"{Cores.VERDE}Sucesso: {texto}{Cores.NORMAL}")

    def mostrar_erro(self, texto):
        print(f"{Cores.VERMELHO}Erro: {texto}{Cores.NORMAL}")

    def mostrar_info(self, texto):
        print(f"{Cores.CIANO}{texto}{Cores.NORMAL}")

    def mostrar_aviso(self, texto):
        print(f"{Cores.AMARELO}Aviso: {texto}{Cores.NORMAL}")

    def ler_texto(self, prompt):
        return input(f"{Cores.AZUL}{prompt}{Cores.NORMAL}").strip()

    def ler_segredo(self, prompt):
        return getpass.getpass(f"{Cores.AZUL}{prompt}{Cores.NORMAL}").strip()

    def pausar(self): 
        try: # Para Garantir que não aparece um erro ao terminar o programa
            input(f"\n{Cores.NEGRITO}Pressione ENTER para continuar...{Cores.NORMAL}")
        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Cores.ROXO}Programa encerrado pelo utilizador.{Cores.NORMAL}")
            exit(0)

    def executar_menu(self, titulo, opcoes, condicao_de_saida_lambda = None):
        while True:
            if condicao_de_saida_lambda is not None and condicao_de_saida_lambda() == True:
                return # Se houver uma condição especial e ela for comprida retorna

            self.mostrar_cabecalho(titulo)
            
            for indice, (descricao, _) in enumerate(opcoes, 1):
                print(f"{indice}) {descricao}")
                
            print("\n0) Voltar/Sair")
            
            texto_opcao = self.ler_texto("Opção:")

            if texto_opcao == '0':
                return
            
            try:
                indice_selecionado = int(texto_opcao) - 1
                if 0 <= indice_selecionado < len(opcoes):
                    opcoes[indice_selecionado][1]() # Executa a ação associada à opção
                else:
                    self.mostrar_erro("Opção inválida")
            except ValueError:
                self.mostrar_erro("Opção inválida")

            self.pausar()
            self.limpar_tela()

    def iniciar(self):
        self.limpar_tela()
        while True:
            self.mostrar_cabecalho("Sistema de Vendas")
            if not self._verificar_conexao():
                continue

            self._atualizar_comandos()
            if not self.utilizador:
                self._menu_inicial()
            else:
                self._menu_principal()

    def _verificar_conexao(self):
        # Teste de ping antes de tentar conectar
        if not self.rede.testar_ping():
            self._mostrar_erro_rede("Não é possível estabelecer uma ligação com o servidor. Verifique a rede ou a firewall.")
            return False

        # Testa se o servidor está a usar o servidor correto
        pong = self.rede.enviar('ping')
        if not pong.get('ok') or pong.get('resultado') != 'pong':
            self._mostrar_erro_rede("Servidor não está a executar o script ou não está inicializado.")
            return False

        # Verifica se o servidor tem comandos essenciais no 'help'
        help_resp = self.rede.enviar('help')
        if not help_resp.get('ok'):
            self._mostrar_erro_rede("Não é possivel enviar comandos, verifique se o servidor ainda está em execução e se está a usar o script correto")
            return False

        categorias = help_resp.get('resultado', {}).get('categorias', {})
        comandos_essenciais = ['autenticar', 'registar_cliente']

        comandos_servidor = []
        for categoria in categorias.values():
            for comando in categoria:
                comandos_servidor.append(comando)

        todos_presentes = True
        for comando in comandos_essenciais:
            if comando not in comandos_servidor:
                todos_presentes = False
                break
        if not todos_presentes:
            self._mostrar_erro_rede("Servidor não está a executar o script correto ou está desatualizado (comandos essenciais ausentes).")
            return False

        return True

    def _mostrar_erro_rede(self, mensagem):
        self.mostrar_erro(mensagem)
        self.mostrar_info("A tentar novamente em 5 segundos...")
        time.sleep(5)
        self.limpar_tela()

    def _atualizar_comandos(self):
        parametros = {}
        if self.utilizador:
            parametros = {'username': self.utilizador['username'], 'password': self.utilizador['password']}
        
        resposta = self.rede.enviar('help', parametros)
        if resposta.get('ok'):
            self.comandos_disponiveis = resposta.get('resultado', {}).get('categorias', {})
            if 'cargo' in resposta.get('resultado', {}):
                self.cargo = resposta['resultado']['cargo']

    def _menu_inicial(self):
        opcoes = [
            ("Login", self._fazer_login),
            ("Registar Cliente", self._registar_cliente)
        ]
        # Sai do menu se o utilizador iniciar sessão 
        self.executar_menu("Bem-vindo", opcoes, condicao_de_saida_lambda=lambda: self.utilizador is not None)
        
        # Se saiu do menu e não logou, encerra o app (quando o utilizador escolhe 0 sem iniciar sessão)
        if not self.utilizador:
            self.mostrar_info("A sair...")
            exit(0)

    def _menu_principal(self):
        if not self.utilizador: 
            return
        
        opcoes = []
        
        if 'compras' in self.comandos_disponiveis:
            opcoes.append(('Compras', self._menu_compras))
            
        if 'pedidos' in self.comandos_disponiveis:
            opcoes.append(('Gestão de Loja', self._menu_loja))
            
        if 'administracao' in self.comandos_disponiveis or 'produtos' in self.comandos_disponiveis:
            opcoes.append(('Administração', self._menu_administracao))
            
        opcoes.append(('Minha Conta', self._menu_conta))
        
        # Sai do menu se o utilizador deslogar
        self.executar_menu(f"Menu Principal - {self.utilizador['username']} [{self.cargo}]", opcoes, condicao_de_saida_lambda=lambda: self.utilizador is None)
        
        # Se saiu do menu e ainda está logado, significa que escolheu 0 (Sair do App)
        if self.utilizador:
            self.mostrar_info("A sair...")
            exit(0)

    def _menu_compras(self):
        opcoes = [
            ("Listar Produtos", self._listar_produtos),
            ("Realizar Compra", self._realizar_compra),
            ("Meu Histórico", self._ver_historico)
        ]
        self.executar_menu("Compras", opcoes)

    def _menu_loja(self):
        opcoes = [
            ("Listar Pedidos da Loja", self._listar_pedidos_loja),
            ("Concluir Pedido", self._concluir_pedido),
            ("Verificar Stock Baixo", self._verificar_stock)
        ]
        self.executar_menu("Gestão de Loja", opcoes)

    def _menu_administracao(self):
        opcoes = []
        todos_comandos = []
        for categoria in ['administracao', 'produtos', 'autenticacao']:
            if categoria in self.comandos_disponiveis:
                todos_comandos.extend(self.comandos_disponiveis[categoria])
        
        # Gestão de Produtos
        if 'add_product' in todos_comandos:
            opcoes.append(("Adicionar Produto", self._adicionar_produto))
        if 'editar_produto' in todos_comandos:
            opcoes.append(("Editar Produto", self._editar_produto))
        if 'deletar_produto' in todos_comandos:
            opcoes.append(("Remover Produto", self._remover_produto))
        
        # Gestão de Lojas (Admin)
        if self.cargo == 'admin':
            opcoes.append(("Criar Loja", self._criar_loja))
            opcoes.append(("Editar Loja", self._editar_loja))
            opcoes.append(("Remover Loja", self._remover_loja))
            opcoes.append(("Listar Utilizadores", self._listar_utilizadores))
        
        # Gestão de Funcionários
        if 'criar_funcionario' in todos_comandos:
            opcoes.append(("Criar Funcionário", self._criar_funcionario))
            
        self.executar_menu("Administração", opcoes)

    def _menu_conta(self):
        opcoes = [ ("Alterar Senha", self._alterar_senha) ]
        
        if 'promover_para_admin' in self.comandos_disponiveis.get('autenticacao', []):
            opcoes.append(("Promover a Admin", self._promover_admin))
        
        opcoes.append(("Editar Username", self._editar_username))
        opcoes.append(("Logout", self._fazer_logout))
        
        # Sai do menu se deslogar
        self.executar_menu("Minha Conta", opcoes, condicao_de_saida_lambda=lambda: self.utilizador is None)

    def _fazer_login(self):
        self.mostrar_cabecalho("Login")
        utilizador = self.ler_texto("Username:")
        if not utilizador:
            self.mostrar_erro("Username não pode estar vazio.")
            self.pausar()
            return
            
        senha = self.ler_segredo("Password:")
        if not senha:
            self.mostrar_erro("Password não pode estar vazia.")
            self.pausar()
            return
        
        resposta = self.rede.enviar('autenticar', {'username': utilizador, 'password': senha})
        if resposta.get('ok'):
            resultado = resposta.get('resultado')
            # Verifica se resultado é um dicionário
            if isinstance(resultado, dict):
                self.utilizador = {'username': utilizador, 'password': senha}
                self.cargo = resultado.get('cargo', 'desconhecido')
                self.mostrar_sucesso(f"Bem-vindo, {utilizador} ({self.cargo})")
            else:
                self.mostrar_erro(f"{resultado}")
                self.pausar()
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro no login'))
            self.pausar()

    def _registar_cliente(self):
        self.mostrar_cabecalho("Registo")
        utilizador = self.ler_texto("Username:")
        if not utilizador:
            self.mostrar_erro("Username não pode estar vazio.")
            self.pausar()
            return
            
        senha = self.ler_segredo("Password:")
        if not senha:
            self.mostrar_erro("Password não pode estar vazia.")
            self.pausar()
            return
            
        confirmacao = self.ler_segredo("Confirmar Password:")
        
        if senha != confirmacao:
            self.mostrar_erro("As passwords não coincidem.")
            self.pausar()
            return

        resposta = self.rede.enviar('registar_cliente', {'username': utilizador, 'password': senha})
        if resposta.get('ok'):
            resultado = resposta.get('resultado', '')
            # Verificar se é mensagem de sucesso
            if resultado == 'UTILIZADOR_CRIADO':
                self.mostrar_sucesso("Conta criada com sucesso! Faça login para continuar.")
            else:
                # Qualquer outro resultado é erro
                self.mostrar_erro(f"{resultado}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao criar conta'))
        self.pausar()

    def _fazer_logout(self):
        self.utilizador = None
        self.cargo = None
        self.mostrar_sucesso("Logout efetuado.")
    
    def _editar_username(self):
        if not self.utilizador:
            return
        self.mostrar_cabecalho("Editar Username")
        
        print(f"Username atual: {Cores.CIANO}{self.utilizador.get('username', 'N/A')}{Cores.NORMAL}\n")
        
        novo_username = self.ler_texto("Novo Username:")
        if not novo_username:
            self.mostrar_erro("Username não pode estar vazio.")
            self.pausar()
            return
        
        # Confirmação
        confirmacao = self.ler_texto(f"Alterar username para '{novo_username}'? (s/n):")
        if confirmacao.lower() != 's':
            self.mostrar_info("Operação cancelada.")
            self.pausar()
            return
        
        parametros = {**self.utilizador, 'novo_username': novo_username}
        resposta = self.rede.enviar('editar_username', parametros)
        
        if resposta.get('ok'):
            resultado = resposta.get('resultado', '')
            
            # Verificar se é mensagem de sucesso
            if resultado == 'ATUALIZADO':
                self.mostrar_sucesso("Username atualizado com sucesso!")
                self.mostrar_info("Por favor, faça login novamente com o novo username.")
                self.utilizador = None  # Forçar logout
                self.cargo = None
            else:
                # Qualquer outro resultado é erro
                if resultado == 'UTILIZADOR_JA_EXISTE':
                    self.mostrar_erro("Username já está em uso por outro utilizador.")
                else:
                    self.mostrar_erro(f"{resultado}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao editar username'))
        
        self.pausar()

    def _listar_produtos(self):
        if not self.utilizador: 
            return
        self.mostrar_cabecalho("Listar Produtos")
        # Listar lojas antes de pedir o ID
        resposta_lojas = self.rede.enviar('listar_lojas')
        if resposta_lojas.get('ok'):
            lojas = resposta_lojas.get('resultado', [])
            if not lojas:
                self.mostrar_erro("Nenhuma loja disponível.")
                self.pausar()
                return
            print("\nLojas disponíveis:")
            for loja in lojas:
                print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        else:
            self.mostrar_erro("Erro ao carregar lojas.")
            self.pausar()
            return
        loja_id = self.ler_texto("\nID da Loja (Enter para ver todas):")
        # Filtros adicionais
        categoria = self.ler_texto("Categoria (Enter para ignorar):")
        preco_maximo = self.ler_texto("Preço Máximo (Enter para ignorar):")
        parametros = {**self.utilizador}
        if loja_id and loja_id.isdigit():
            parametros['store_id'] = loja_id  # Enviar como string
        if categoria: 
            parametros['categoria'] = categoria
        if preco_maximo:
            try: 
                float(preco_maximo)  # Valida se é número
                parametros['preco_max'] = preco_maximo  # Enviar como string
            except: 
                pass
        resposta = self.rede.enviar('list_products', parametros)
        if resposta.get('ok'):
            produtos = resposta.get('resultado', [])
            if not produtos:
                self.mostrar_aviso("Nenhum produto encontrado.")
            else:
                print(f"\n{Cores.NEGRITO}{'ID':<5} {'Nome':<20} {'Categoria':<15} {'Preço':<10} {'Stock':<8} {'Loja':<15}{Cores.NORMAL}")
                for produto in produtos:
                    print(f"{produto['id']:<5} {produto['nome']:<20} {produto['categoria']:<15} {produto['preco']:<10.2f} {produto['stock']:<8} {produto['loja']:<15}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao listar produtos'))
        self.pausar()

    def _realizar_compra(self):
        if not self.utilizador: 
            return
        
        self.mostrar_cabecalho("Realizar Compra")
        
        resposta_lojas = self.rede.enviar('listar_lojas')
        if not resposta_lojas.get('ok') or not resposta_lojas.get('resultado'):
            self.mostrar_erro("Erro ao carregar lojas.")
            self.pausar()
            return
        
        lojas = resposta_lojas.get('resultado', [])
        print("\nLojas disponíveis:")
        for loja in lojas:
            print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        
        loja_id = self.ler_texto("\nID da Loja:")
        if not loja_id or not loja_id.isdigit():
            self.mostrar_erro("ID da loja inválido.")
            self.pausar()
            return
        
        parametros_lista = {**self.utilizador, 'store_id': loja_id}
        resposta_produtos = self.rede.enviar('list_products', parametros_lista)
        
        if not resposta_produtos.get('ok'):
            self.mostrar_erro("Erro ao carregar produtos.")
            self.pausar()
            return
        
        produtos = resposta_produtos.get('resultado', [])
        if not produtos:
            self.mostrar_aviso("Nenhum produto disponível nesta loja.")
            self.pausar()
            return
        
        print(f"\n{Cores.NEGRITO}Produtos disponíveis:{Cores.NORMAL}")
        print(f"{'Nome':<25} {'Categoria':<15} {'Preço':<10} {'Stock':<8}")
        for produto in produtos:
            print(f"{produto['nome']:<25} {produto['categoria']:<15} {produto['preco']:<10.2f} {produto['stock']:<8}")
        
        nome_produto = self.ler_texto("\nNome do Produto:")
        if not nome_produto:
            self.mostrar_erro("Nome do produto não pode estar vazio.")
            self.pausar()
            return
        
        parametros_busca = {
            **self.utilizador,
            'nome_produto': nome_produto,
            'store_id': loja_id
        }
        resposta_busca = self.rede.enviar('buscar_produto_por_nome', parametros_busca)
        
        if not resposta_busca.get('ok'):
            self.mostrar_erro(resposta_busca.get('erro', 'Erro ao buscar produto'))
            self.pausar()
            return
        
        resultado_busca = resposta_busca.get('resultado')
        if isinstance(resultado_busca, str):
            # É um código de erro
            self.mostrar_erro(f"{resultado_busca}")
            self.pausar()
            return
        
        # Produto encontrado - verificar se é um dicionário válido
        if not isinstance(resultado_busca, dict):
            self.mostrar_erro("Resposta inválida do servidor")
            self.pausar()
            return
            
        produto_info = resultado_busca
        self.mostrar_info(f"Produto: {produto_info['nome']} | Preço: {produto_info['preco']}€ | Stock: {produto_info['stock']}")
        
        quantidade = self.ler_texto("Quantidade:")
        if not quantidade.isdigit() or int(quantidade) <= 0:
            self.mostrar_erro("Quantidade deve ser um número maior que zero.")
            self.pausar()
            return
        
        try:
            itens = {str(produto_info['id']): int(quantidade)}
            resposta = self.rede.enviar('realizar_venda', {**self.utilizador, 'itens': itens})
            
            if resposta.get('ok'):
                resultado = resposta.get('resultado')
                if isinstance(resultado, list) and len(resultado) == 2:
                    status, dados = resultado
                    self.mostrar_sucesso(f"Pedido realizado! Status: {status}")
                    self.mostrar_info(f"Pedido: {dados.get('order_id')} | Total: {dados.get('total_price')}€")
                elif isinstance(resultado, str):
                    self.mostrar_erro(f"{resultado}")
                else:
                    self.mostrar_sucesso(f"Pedido realizado: {resultado}")
            else:
                self.mostrar_erro(resposta.get('erro', 'Erro desconhecido'))
        except Exception as e:
            self.mostrar_erro(f"Erro ao processar compra: {e}")
        self.pausar()

    def _ver_historico(self):
        resposta = self.rede.enviar('ver_meu_historico', self.utilizador)
        if resposta.get('ok'):
            historico = resposta.get('resultado', [])
            if not historico:
                self.mostrar_info("Histórico vazio.")
            else:
                for pedido in historico:
                    print(f"Data: {pedido['order_date']} | Produto: {pedido['produto']} | Qtd: {pedido['quantity']} | Total: {pedido['quantity']*pedido['unit_price']:.2f}€ | Status: {pedido['status']}")
        else:
            self.mostrar_erro(resposta.get('erro'))
        self.pausar()

    def _listar_pedidos_loja(self):
        if not self.utilizador: 
            return
        self.mostrar_cabecalho("Pedidos da Loja")
        filtro = self.ler_texto("Filtrar Status (pendente/concluida/vazio):")
        parametros = {**self.utilizador}
        if filtro: parametros['filtro_status'] = filtro
        
        resposta = self.rede.enviar('listar_pedidos', parametros)
        if resposta.get('ok'):
            pedidos = resposta.get('resultado', [])
            for produto in pedidos:
                print(f"ID: {produto['id']} | Data: {produto['order_date']} | Cliente: {produto['cliente']} | Total: {produto['total_price']:.2f}€ | Status: {produto['status']}")
        else:
            self.mostrar_erro(resposta.get('erro'))
        self.pausar()

    def _concluir_pedido(self):
        if not self.utilizador: 
            return

        self.mostrar_cabecalho("Pedidos da Loja")
        resposta_pedidos = self.rede.enviar('listar_pedidos', self.utilizador)
        if resposta_pedidos.get('ok'):
            pedidos = resposta_pedidos.get('resultado', [])
            if not pedidos:
                self.mostrar_aviso("Nenhum pedido disponível para concluir.")
                self.pausar()
                return
            print("\nPedidos disponíveis:")
            for pedido in pedidos:
                print(f"  {pedido['id']}. Cliente: {pedido['cliente']} | Total: {pedido['total_price']:.2f}€ | Status: {pedido['status']}")
        else:
            self.mostrar_erro("Erro ao listar pedidos.")
            self.pausar()
            return
        pedido_id = self.ler_texto("ID do Pedido a concluir:")
        resposta = self.rede.enviar('concluir_pedido', {**self.utilizador, 'order_id': pedido_id})
        if resposta.get('ok') and resposta.get('resultado') == 'SUCESSO':
            self.mostrar_sucesso("Pedido concluído com sucesso!")
        else:
            if resposta.get('resultado'):
                erro = resposta.get('resultado') 
            else:
                erro = resposta.get('erro', 'Erro ao concluir pedido')
            self.mostrar_erro(erro)
        self.pausar()

    def _verificar_stock(self):
        if not self.utilizador: 
            return
        resposta = self.rede.enviar('verificar_stock_baixo', self.utilizador)
        if resposta.get('ok'):
            resultado = resposta.get('resultado')
            if isinstance(resultado, list) and len(resultado) == 2:
                mensagem, produtos = resultado
                self.mostrar_aviso(f"{mensagem}")
                for produto in produtos:
                    print(f" - Produto: {produto['nome']} (ID: {produto['id']}) | Stock: {produto['stock']} | Loja: {produto['loja']}")
            elif resultado == "SUCESSO":
                self.mostrar_sucesso("Stock está normal (nenhum produto abaixo de 5 unidades).")
            else:
                self.mostrar_info(f"Resultado: {resultado}")
        else:
            self.mostrar_erro(resposta.get('erro'))
        self.pausar()

    def _adicionar_produto(self):
        if not self.utilizador: 
            return
        self.mostrar_cabecalho("Novo Produto")
        # Nome do produto com sugestões obrigatórias
        nome = self._ler_com_sugestoes("Nome do Produto", "listar_nomes_produtos", permitir_vazio=False)
        if not nome:
            self.mostrar_erro("Nome não pode estar vazio.")
            self.pausar()
            return
        # Categoria com sugestões obrigatórias
        categoria = self._ler_com_sugestoes("Categoria", "listar_categorias", permitir_vazio=False)
        if not categoria:
            self.mostrar_erro("Categoria não pode estar vazia.")
            self.pausar()
            return
        # Descrição com sugestões obrigatórias
        descricao = self._ler_com_sugestoes("Descrição", "listar_descricoes", permitir_vazio=False)
        if not descricao:
            self.mostrar_erro("Descrição não pode estar vazia.")
            self.pausar()
            return
        preco = self.ler_texto("Preço:")
        stock = self.ler_texto("Stock:")
        # Listar lojas para escolher
        resposta_lojas = self.rede.enviar('listar_lojas')
        if resposta_lojas.get('ok'):
            lojas = resposta_lojas.get('resultado', [])
            if not lojas:
                self.mostrar_erro("Nenhuma loja disponível. Crie uma loja primeiro.")
                self.pausar()
                return
            print("\nLojas disponíveis:")
            for loja in lojas:
                print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        loja_id = self.ler_texto("\nID da Loja:")
        try:
            parametros = {
                **self.utilizador,
                'nome': nome, 'categoria': categoria, 'descricao': descricao,
                'preco': preco, 'stock': stock, 'store_id': loja_id
            }
            resposta = self.rede.enviar('add_product', parametros)
            if resposta.get('ok'):
                self.mostrar_sucesso("Produto adicionado!")
            else:
                self.mostrar_erro(resposta.get('erro'))
        except Exception:
            self.mostrar_erro("Valores inválidos.")
        self.pausar()
    
    def _ler_com_sugestoes(self, label, acao_listar, permitir_vazio=False):
        # Buscar sugestões do servidor
        resposta = self.rede.enviar(acao_listar)
        sugestoes = []
        
        if resposta.get('ok'):
            sugestoes = resposta.get('resultado', [])
        
        if sugestoes:
            print(f"\n{Cores.CIANO}Valores existentes de {label}:{Cores.NORMAL}")
            for i, sugestao in enumerate(sugestoes, 1):  # Mostrar apenas 10 primeiros
                print(f"  {i}. {sugestao}")
            print(f"\n{Cores.AMARELO}Dica: Digite o número para selecionar ou escreva um novo valor{Cores.NORMAL}")
        
        if not permitir_vazio:
            prompt = f"\n{label}:" 
        else:
            prompt = f"{label} (vazio para manter):"
        entrada = self.ler_texto(prompt)
        
        # Se permitir vazio e entrada for vazia, retorna None
        if permitir_vazio and not entrada:
            return None
        # Se for número, tentar selecionar da lista
        if entrada.isdigit():
            indice = int(entrada) - 1
            if 0 <= indice < len(sugestoes):
                valor_selecionado = sugestoes[indice]
                print(f"{Cores.VERDE}Selecionado: {valor_selecionado}{Cores.NORMAL}")
                return valor_selecionado
        # Caso contrário, retornar o valor digitado
        return entrada

    def _editar_produto(self):
        if not self.utilizador: 
            return
        self.mostrar_cabecalho("Editar Produto")
        # Listar produtos antes de pedir o ID
        resposta_produtos = self.rede.enviar('list_products', self.utilizador)
        if resposta_produtos.get('ok'):
            produtos = resposta_produtos.get('resultado', [])
            if not produtos:
                self.mostrar_aviso("Nenhum produto disponível para editar.")
                self.pausar()
                return
            print("\nProdutos disponíveis:")
            for produto in produtos:
                print(f"  {produto['id']}. {produto['nome']} | Categoria: {produto['categoria']} | Stock: {produto['stock']} | Loja: {produto['loja']}")
        else:
            self.mostrar_erro("Erro ao listar produtos.")
            self.pausar()
            return
        produto_id = self.ler_texto("ID Produto:")
        if not produto_id or not produto_id.isdigit():
            self.mostrar_erro("ID inválido.")
            self.pausar()
            return
        self.mostrar_info("Deixe em branco para não alterar ou escolha da lista de sugestões")
        # Nome com sugestões
        print(f"\n{Cores.AMARELO}Novo Nome{Cores.NORMAL}")
        novo_nome = self._ler_com_sugestoes("Nome do Produto", "listar_nomes_produtos", permitir_vazio=True)
        # Categoria com sugestões
        print(f"\n{Cores.AMARELO}Nova Categoria{Cores.NORMAL}")
        nova_categoria = self._ler_com_sugestoes("Categoria", "listar_categorias", permitir_vazio=True)
        # Descrição com sugestões
        print(f"\n{Cores.AMARELO}Nova Descrição{Cores.NORMAL}")
        nova_descricao = self._ler_com_sugestoes("Descrição", "listar_descricoes", permitir_vazio=True)
        novo_preco = self.ler_texto("\nNovo Preço:")
        novo_stock = self.ler_texto("Novo Stock:")

        parametros = {**self.utilizador, 'product_id': produto_id}

        if novo_nome: 
            parametros['novo_nome'] = novo_nome

        if nova_categoria: 
            parametros['nova_categoria'] = nova_categoria

        if novo_preco: 
            parametros['novo_preco'] = novo_preco

        if novo_stock: 
            parametros['novo_stock'] = novo_stock

        if nova_descricao: 
            parametros['nova_descricao'] = nova_descricao

        if self.cargo == 'admin':
            # Listar lojas
            resposta_lojas = self.rede.enviar('listar_lojas')
            if resposta_lojas.get('ok'):
                lojas = resposta_lojas.get('resultado', [])
                if lojas:
                    print("\nLojas disponíveis:")
                    for loja in lojas:
                        print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
            novo_id_da_loja = self.ler_texto("\nNovo ID Loja:")
            if novo_id_da_loja: 
                parametros['novo_id_da_loja'] = novo_id_da_loja

        resposta = self.rede.enviar('editar_produto', parametros)
        if resposta.get('ok'):
            self.mostrar_sucesso("Produto atualizado!")
        else:
            self.mostrar_erro(resposta.get('erro'))
        self.pausar()
    
    def _remover_produto(self):
        if not self.utilizador:
            return
        # Listar produtos antes de pedir o ID
        self.mostrar_cabecalho("Remover Produto")
        resposta_produtos = self.rede.enviar('list_products', self.utilizador)
        if resposta_produtos.get('ok'):
            produtos = resposta_produtos.get('resultado', [])
            if not produtos:
                self.mostrar_aviso("Nenhum produto disponível para remover.")
                self.pausar()
                return
            print("\nProdutos disponíveis:")
            for produto in produtos:
                print(f"  {produto['id']}. {produto['nome']} | Categoria: {produto['categoria']} | Stock: {produto['stock']} | Loja: {produto['loja']}")
        else:
            self.mostrar_erro("Erro ao listar produtos.")
            self.pausar()
            return
        produto_id = self.ler_texto("ID Produto a remover:")
        confirmacao = self.ler_texto("Tem a certeza? (s/n):")
        if confirmacao.lower() != 's':
            return
        resposta = self.rede.enviar('deletar_produto', {**self.utilizador, 'product_id': produto_id})
        if resposta.get('ok') and resposta.get('resultado') == 'SUCESSO':
            self.mostrar_sucesso("Produto removido!")
        else:
            if resposta.get('resultado'):
                erro = resposta.get('resultado')
            else:
                erro = resposta.get('erro', 'Erro ao remover produto')
            self.mostrar_erro(erro)
        self.pausar()

    def _criar_funcionario(self):
        if not self.utilizador: 
            return
        self.mostrar_cabecalho("Criar Funcionario")
        tipo = self.ler_texto("Tipo (admin/vendedor):")
        loja_id = ""
        if tipo == 'vendedor':
            # Listar lojas antes de pedir o ID
            resposta_lojas = self.rede.enviar('listar_lojas')
            if resposta_lojas.get('ok'):
                lojas = resposta_lojas.get('resultado', [])
                if not lojas:
                    self.mostrar_erro("Nenhuma loja disponível para associar ao vendedor.")
                    self.pausar()
                    return
                print("\nLojas disponíveis:")
                for loja in lojas:
                    print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
            else:
                self.mostrar_erro("Erro ao listar lojas.")
                self.pausar()
                return
            loja_id = self.ler_texto("ID Loja:")
        utilizador = self.ler_texto("Username:")
        senha = self.ler_segredo("Password:")
        parametros = {
            **self.utilizador,
            'username_func': utilizador, 'password_func': senha,
            'tipo': tipo, 'loja_id': loja_id
        }
        resposta = self.rede.enviar('criar_funcionario', parametros)
        resultado = resposta.get('resultado')
        if resposta.get('ok') and resultado == 'UTILIZADOR_CRIADO':
            self.mostrar_sucesso("Funcionário criado!")
        else:
            if resultado is not None:
                erro = resultado 
            else:
                erro = resposta.get('erro', 'Erro ao criar funcionário')
            self.mostrar_erro(erro)
        self.pausar()
    def _apagar_conta(self):
        if not self.utilizador:
            return
        username = self.utilizador.get('username')
        confirmacao = self.ler_texto(f"Para apagar sua conta, digite exatamente: 'Tenho a certeza {username} que pretendo apagar a conta juntamente com todos os meus dados'")
        frase_correta = f"Tenho a certeza {username} que pretendo apagar a conta juntamente com todos os meus dados"
        if confirmacao != frase_correta:
            self.mostrar_aviso("Confirmação incorreta. Operação cancelada.")
            self.pausar()
            return
        resposta = self.rede.enviar('apagar_utilizador', {**self.utilizador})
        resultado = resposta.get('resultado')
        if resposta.get('ok') and resultado == 'REMOVIDO':
            self.mostrar_sucesso("Conta apagada com sucesso!")
            self.utilizador = None
            self.cargo = None
        elif resultado == 'NAO_PERMITIDO':
            self.mostrar_erro("Por motivos de segurança essa ação não pode ser efetuada agora. Solicite a um administrador para limpar todos os seus dados.")
        else:
            if resultado is not None:
                erro = resultado 
            else:
                erro = resposta.get('erro', 'Erro ao apagar conta')
            self.mostrar_erro(erro)

        self.pausar()

    def _alterar_senha(self):
        if not self.utilizador: 
            return
        nova_senha = self.ler_segredo("Nova Senha:")
        confirmacao = self.ler_segredo("Confirmar:")
        if nova_senha != confirmacao:
            self.mostrar_erro("Não coincidem.")
            self.pausar()
            return
            
        resposta = self.rede.enviar('editar_senha', {**self.utilizador, 'nova_senha': nova_senha})
        if resposta.get('ok'):
            self.mostrar_sucesso("Senha alterada!")
            self.utilizador['password'] = nova_senha
        else:
            self.mostrar_erro(resposta.get('erro'))
        self.pausar()

    def _promover_admin(self):
        if not self.utilizador: 
            return
        chave = self.ler_segredo("Chave de Admin:")
        resposta = self.rede.enviar('promover_para_admin', {**self.utilizador, 'chave': chave})
        if resposta.get('ok'):
            resultado = resposta.get('resultado', '')
            # Verificar se é mensagem de sucesso
            if resultado == 'SUCESSO':
                self.mostrar_sucesso("Promovido a Admin! Faça login novamente para atualizar permissões.")
                self.utilizador = None # Forçar logout
            else:
                # Qualquer outro resultado é erro
                self.mostrar_erro(f"{resultado}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao promover'))
        self.pausar()
    
    def _criar_loja(self):
        if not self.utilizador:
            return
        self.mostrar_cabecalho("Criar Nova Loja")
        nome = self.ler_texto("Nome da Loja:")
        if not nome:
            self.mostrar_erro("Nome não pode estar vazio.")
            self.pausar()
            return
        
        localizacao = self.ler_texto("Localização:")
        if not localizacao:
            self.mostrar_erro("Localização não pode estar vazia.")
            self.pausar()
            return
        
        parametros = {**self.utilizador, 'nome': nome, 'localizacao': localizacao}
        resposta = self.rede.enviar('criar_loja', parametros)
        
        if resposta.get('ok'):
            resultado = resposta.get('resultado', '')
            # Verificar se é mensagem de sucesso
            if resultado == 'ADICIONADO':
                self.mostrar_sucesso("Loja criada com sucesso!")
            else:
                # Qualquer outro resultado é erro
                self.mostrar_erro(f"{resultado}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao criar loja'))
        self.pausar()
    
    def _editar_loja(self):
        if not self.utilizador:
            return
        self.mostrar_cabecalho("Editar Loja")
        resposta_lojas = self.rede.enviar('listar_lojas')
        if resposta_lojas.get('ok'):
            lojas = resposta_lojas.get('resultado', [])
            if not lojas:
                self.mostrar_erro("Nenhuma loja disponível.")
                self.pausar()
                return
            print("\nLojas disponíveis:")
            for loja in lojas:
                print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        else:
            self.mostrar_erro("Erro ao listar lojas.")
            self.pausar()
            return
        store_id = self.ler_texto("\nID da Loja a editar:")
        if not store_id or not store_id.isdigit():
            self.mostrar_erro("ID inválido.")
            self.pausar()
            return
        self.mostrar_info("Deixe em branco para não alterar")
        novo_nome = self.ler_texto("Novo Nome:")
        nova_localizacao = self.ler_texto("Nova Localização:")
        if not novo_nome and not nova_localizacao:
            self.mostrar_aviso("Nenhuma alteração foi feita.")
            self.pausar()
            return
        parametros = {**self.utilizador, 'store_id': store_id}
        if novo_nome:
            parametros['novo_nome'] = novo_nome
        if nova_localizacao:
            parametros['nova_localizacao'] = nova_localizacao
        resposta = self.rede.enviar('editar_loja', parametros)
        if resposta.get('ok'):
            resultado = resposta.get('resultado', '')
            if resultado == 'ATUALIZADO':
                self.mostrar_sucesso("Loja atualizada!")
            else:
                self.mostrar_erro(f"{resultado}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao editar loja'))
        self.pausar()
    
    def _remover_loja(self):
        if not self.utilizador:
            return
        self.mostrar_cabecalho("Remover Loja")
        # Listar lojas
        resposta_lojas = self.rede.enviar('listar_lojas')
        if resposta_lojas.get('ok'):
            lojas = resposta_lojas.get('resultado', [])
            if not lojas:
                self.mostrar_erro("Nenhuma loja disponível.")
                self.pausar()
                return
            print("\nLojas disponíveis:")
            for loja in lojas:
                print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        else:
            self.mostrar_erro("Erro ao listar lojas.")
            self.pausar()
            return
        store_id = self.ler_texto("\nID da Loja a remover:")
        if not store_id or not store_id.isdigit():
            self.mostrar_erro("ID inválido.")
            self.pausar()
            return
        confirmacao = self.ler_texto("Tem certeza? Esta ação não pode ser desfeita. (s/n):")
        if confirmacao.lower() != 's':
            self.mostrar_info("Operação cancelada.")
            self.pausar()
            return
        parametros = {**self.utilizador, 'store_id': store_id}
        resposta = self.rede.enviar('apagar_loja', parametros)
        if resposta.get('ok'):
            resultado = resposta.get('resultado', '')
            if resultado == 'REMOVIDO':
                self.mostrar_sucesso("Loja removida com sucesso!")
            else:
                if resultado == 'ERRO_PROCESSAMENTO':
                    self.mostrar_erro("Não é possível remover: loja tem produtos ou vendedores associados")
                else:
                    self.mostrar_erro(f"{resultado}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao remover loja'))
        self.pausar()
    
    def _listar_utilizadores(self):
        if not self.utilizador:
            return
        self.mostrar_cabecalho("Listar Utilizadores")
        
        # Menu de filtros
        print("\nOpções de filtro:")
        print("1. Todos os utilizadores")
        print("2. Apenas Clientes")
        print("3. Apenas Vendedores")
        print("4. Apenas Admins")
        print("5. Por Loja específica")
        
        opcao = self.ler_texto("\nEscolha uma opção (1-5):")
        
        filtro_cargo = None
        filtro_loja = None
        
        if opcao == '2':
            filtro_cargo = 'cliente'
        elif opcao == '3':
            filtro_cargo = 'vendedor'
        elif opcao == '4':
            filtro_cargo = 'admin'
        elif opcao == '5':
            # Listar lojas primeiro
            resposta_lojas = self.rede.enviar('listar_lojas')
            if resposta_lojas.get('ok'):
                lojas = resposta_lojas.get('resultado', [])
                if not lojas:
                    self.mostrar_erro("Nenhuma loja disponível.")
                    self.pausar()
                    return
                
                print("\nLojas disponíveis:")
                for loja in lojas:
                    print(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
                
                loja_id = self.ler_texto("\nID da Loja:")
                if loja_id and loja_id.isdigit():
                    filtro_loja = loja_id
                else:
                    self.mostrar_erro("ID inválido")
                    self.pausar()
                    return
        elif opcao != '1':
            self.mostrar_erro("Opção inválida")
            self.pausar()
            return
        
        # Fazer pedido ao servidor
        parametros = {**self.utilizador}
        if filtro_cargo:
            parametros['filtro_cargo'] = filtro_cargo
        if filtro_loja:
            parametros['filtro_loja'] = filtro_loja
        
        resposta = self.rede.enviar('listar_utilizadores', parametros)
        
        if resposta.get('ok'):
            utilizadores = resposta.get('resultado', [])
            
            if not utilizadores:
                self.mostrar_info("Nenhum utilizador encontrado com os filtros aplicados.")
            else:
                print(f"\n{Cores.CIANO}{'ID':<5} | {'Username':<20} | {'Cargo':<12} | {'Loja':<25}{Cores.NORMAL}")
                
                for user in utilizadores:
                    id_str = str(user['id'])
                    username = user['username']
                    cargo = user['cargo']
                    loja = user.get('loja') or 'N/A'
                    
                    # Colorir por cargo
                    if cargo == 'admin':
                        cor = Cores.VERMELHO
                    elif cargo == 'vendedor':
                        cor = Cores.AMARELO
                    else:
                        cor = Cores.VERDE
                    
                    print(f"{cor}{id_str:<5} | {username:<20} | {cargo:<12} | {loja:<25}{Cores.NORMAL}")
                
                print(f"\n{Cores.CIANO}Total: {len(utilizadores)} utilizador(es){Cores.NORMAL}")
        else:
            self.mostrar_erro(resposta.get('erro', 'Erro ao listar utilizadores'))
        
        self.pausar()

def run_Cliente(host='127.0.0.1', port=5000, debug = False):
    global DEBUG
    DEBUG = debug
    try:
        app = ClienteVendas(host, port)
        app.iniciar()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{Cores.ROXO}Programa encerrado pelo utilizador.{Cores.NORMAL}")
    except Exception as e:
        print(f"{Cores.VERMELHO}{Cores.NEGRITO}Erro fatal: {e}{Cores.NORMAL}")

def run(host='127.0.0.1', port=5000, debug = False):
    run_Cliente(host, port, debug)
    
if __name__ == '__main__': # Quando executado diretamente
    run_Cliente(host='127.0.0.1', port=5000)

