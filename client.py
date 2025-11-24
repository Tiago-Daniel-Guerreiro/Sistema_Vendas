import json
import socket
import os
import getpass
import time

class Cores:
    CABECALHO = '\033[95m'
    AZUL = '\033[94m'
    CIANO = '\033[96m'
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    NORMAL = '\033[0m'
    NEGRITO = '\033[1m'

class ClienteRede:
    def __init__(self, host='127.0.0.1', porta=5000):
        self.host = host
        self.porta = porta

    def enviar(self, acao, parametros=None):
        if parametros is None:
            parametros = {}
        
        dados_json = json.dumps({'acao': acao, 'parametros': parametros}) + '\n'
        
        try:
            with socket.create_connection((self.host, self.porta), timeout=5) as conexao:
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
                
                return json.loads(resposta_str)
        except ConnectionRefusedError:
            return {'ok': False, 'erro': 'Não foi possível conectar ao servidor.'}
        except Exception as e:
            return {'ok': False, 'erro': f'Erro de comunicação: {str(e)}'}

class ClienteVendas:
    def __init__(self):
        self.rede = ClienteRede()
        self.utilizador = None
        self.cargo = None
        self.comandos_disponiveis = {}

    def limpar_tela(self):
        os.system('cls')

    def imprimir_cabecalho(self, texto):
        print(f"\n{Cores.CABECALHO}{Cores.NEGRITO} {texto} {Cores.NORMAL}")

    def imprimir_sucesso(self, texto):
        print(f"{Cores.VERDE}Sucesso - {texto}{Cores.NORMAL}")

    def imprimir_erro(self, texto):
        print(f"{Cores.VERMELHO}Erro - {texto}{Cores.NORMAL}")

    def imprimir_info(self, texto):
        print(f"{Cores.CIANO}Info - {texto}{Cores.NORMAL}")

    def imprimir_aviso(self, texto):
        print(f"{Cores.AMARELO}Aviso - {texto}{Cores.NORMAL}")

    def ler_texto(self, prompt):
        return input(f"{Cores.AZUL}{prompt}{Cores.NORMAL} ").strip()

    def ler_segredo(self, prompt):
        return getpass.getpass(f"{Cores.AZUL}{prompt}{Cores.NORMAL} ").strip()

    def pausar(self):
        input(f"\n{Cores.NEGRITO}Pressione ENTER para continuar...{Cores.NORMAL}")

    def executar_menu(self, titulo, opcoes, condicao_de_saida_lambda = None):
        while True:
            if condicao_de_saida_lambda is not None and condicao_de_saida_lambda() == True:
                return

            self.imprimir_cabecalho(titulo)
            
            for indice, (descricao, _) in enumerate(opcoes, 1):
                print(f"{indice}. {descricao}")
            print("0. Voltar/Sair")
            
            texto_opcao = self.ler_texto("Opção:")

            if texto_opcao == '0':
                return
            try:
                indice_selecionado = int(texto_opcao) - 1
                if 0 <= indice_selecionado < len(opcoes):
                    # Executa a ação associada à opção
                    opcoes[indice_selecionado][1]()
                else:
                    self.imprimir_erro("Opção inválida")
                    input("Pressione qualquer tecla para continuar...")
            except ValueError:
                self.imprimir_erro("Opção inválida")
                input("Pressione qualquer tecla para continuar...")

    def iniciar(self):
        while True:
            self.limpar_tela()
            self.imprimir_cabecalho("Sistema de Vendas")

            ping = self.rede.enviar('ping')
            if not ping.get('ok'):
                self.imprimir_erro("Servidor indisponível.")
                self.imprimir_info("Tentando reconectar em 5 segundos...")
                time.sleep(5)
                continue

            self._atualizar_comandos()
            
            if not self.utilizador:
                self._menu_inicial()
            else:
                self._menu_principal()

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
        # Sai do menu se o usuário logar
        self.executar_menu("Bem-vindo", opcoes, condicao_de_saida_lambda=lambda: self.utilizador is not None)
        
        # Se saiu do menu e não logou, encerra o app (usuário escolheu 0)
        if not self.utilizador:
            self.imprimir_info("A sair...")
            exit(0)

    def _menu_principal(self):
        if not self.utilizador: 
            return
        
        opcoes = []
        
        if 'compras' in self.comandos_disponiveis:
            opcoes.append(('Compras (Listar, Comprar, Histórico)', self._menu_compras))
            
        if 'pedidos' in self.comandos_disponiveis:
            opcoes.append(('Gestão de Loja (Pedidos, Stock)', self._menu_loja))
            
        if 'administracao' in self.comandos_disponiveis or 'produtos' in self.comandos_disponiveis:
            opcoes.append(('Administração (Produtos, Funcionários)', self._menu_administracao))
            
        opcoes.append(('Minha Conta (Senha, Promoção, Logout)', self._menu_conta))
        
        # Sai do menu se o usuário deslogar
        self.executar_menu(f"Menu Principal - {self.utilizador['username']} [{self.cargo}]", opcoes, condicao_de_saida_lambda=lambda: self.utilizador is None)
        
        # Se saiu do menu e ainda está logado, significa que escolheu 0 (Sair do App)
        if self.utilizador:
            self.imprimir_info("A sair...")
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
        
        if 'add_product' in todos_comandos:
            opcoes.append(("Adicionar Produto", self._adicionar_produto))
        if 'editar_produto' in todos_comandos:
            opcoes.append(("Editar Produto", self._editar_produto))
        if 'deletar_produto' in todos_comandos:
            opcoes.append(("Remover Produto", self._remover_produto))
        if 'criar_funcionario' in todos_comandos:
            opcoes.append(("Criar Funcionário", self._criar_funcionario))
            
        self.executar_menu("Administração", opcoes)

    def _menu_conta(self):
        opcoes = [ ("Alterar Senha", self._alterar_senha) ]
        
        if 'promover_para_admin' in self.comandos_disponiveis.get('autenticacao', []):
            opcoes.append(("Promover a Admin", self._promover_admin))
            
        opcoes.append(("Logout", self._fazer_logout))
        
        # Sai do menu se deslogar
        self.executar_menu("Minha Conta", opcoes, condicao_de_saida_lambda=lambda: self.utilizador is None)


    def _fazer_login(self):
        self.imprimir_cabecalho("Login")
        utilizador = self.ler_texto("Username:")
        senha = self.ler_segredo("Password:")
        
        resposta = self.rede.enviar('autenticar', {'username': utilizador, 'password': senha})
        if resposta.get('ok'):
            self.utilizador = {'username': utilizador, 'password': senha}
            self.cargo = resposta['resultado'].get('cargo')
            self.imprimir_sucesso(f"Bem-vindo, {utilizador} ({self.cargo})")
            time.sleep(1)
        else:
            self.imprimir_erro(resposta.get('erro', 'Erro no login'))
            self.pausar()

    def _registar_cliente(self):
        self.imprimir_cabecalho("Registo")
        utilizador = self.ler_texto("Username:")
        senha = self.ler_segredo("Password:")
        confirmacao = self.ler_segredo("Confirmar Password:")
        
        if senha != confirmacao:
            self.imprimir_erro("As passwords não coincidem.")
            self.pausar()
            return

        resposta = self.rede.enviar('registar_cliente', {'username': utilizador, 'password': senha})
        if resposta.get('ok'):
            self.imprimir_sucesso("Conta criada com sucesso! Faça login para continuar.")
        else:
            self.imprimir_erro(resposta.get('erro', 'Erro ao criar conta'))
        self.pausar()

    def _fazer_logout(self):
        self.utilizador = None
        self.cargo = None
        self.imprimir_sucesso("Logout efetuado.")
        time.sleep(1)

    def _listar_produtos(self):
        if not self.utilizador: return
        self.imprimir_cabecalho("Filtros (Enter para ignorar)")
        categoria = self.ler_texto("Categoria:")
        preco_maximo = self.ler_texto("Preço Máximo:")
        
        parametros = {}
        if categoria: parametros['categoria'] = categoria
        if preco_maximo: 
            try: parametros['preco_max'] = float(preco_maximo)
            except: pass
            
        resposta = self.rede.enviar('list_products', {**self.utilizador, **parametros})
        if resposta.get('ok'):
            produtos = resposta.get('resultado', [])
            if not produtos:
                self.imprimir_aviso("Nenhum produto encontrado.")
            else:
                print(f"\n{Cores.NEGRITO}{'ID':<5} {'Nome':<20} {'Categoria':<15} {'Preço':<10} {'Stock':<8} {'Loja':<15}{Cores.NORMAL}")
                print("-" * 80)
                for produto in produtos:
                    print(f"{produto['id']:<5} {produto['nome']:<20} {produto['categoria']:<15} {produto['preco']:<10.2f} {produto['stock']:<8} {produto['loja']:<15}")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _realizar_compra(self):
        if not self.utilizador: 
            return
        
        produto_id = self.ler_texto("ID do Produto:")
        quantidade = self.ler_texto("Quantidade:")
        
        try:
            itens = {produto_id: int(quantidade)}
            resposta = self.rede.enviar('realizar_venda', {**self.utilizador, 'itens': itens})
            
            if resposta.get('ok'):
                resultado = resposta.get('resultado')
                if isinstance(resultado, list):
                    status, dados = resultado
                    self.imprimir_sucesso(f"Pedido realizado! Status: {status}")
                    self.imprimir_info(f"Total: {dados.get('total_price')}€ | ID Pedido: {dados.get('order_id')}")
                else:
                    self.imprimir_sucesso(f"Pedido realizado: {resultado}")
            else:
                self.imprimir_erro(resposta.get('erro'))
        except ValueError:
            self.imprimir_erro("Quantidade inválida.")
        self.pausar()

    def _ver_historico(self):
        resposta = self.rede.enviar('ver_meu_historico', self.utilizador)
        if resposta.get('ok'):
            historico = resposta.get('resultado', [])
            if not historico:
                self.imprimir_info("Histórico vazio.")
            else:
                for h in historico:
                    print(f"Data: {h['order_date']} | Produto: {h['produto']} | Qtd: {h['quantity']} | Total: {h['quantity']*h['unit_price']:.2f}€ | Status: {h['status']}")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _listar_pedidos_loja(self):
        if not self.utilizador: 
            return
        self.imprimir_cabecalho("Pedidos da Loja")
        filtro = self.ler_texto("Filtrar Status (pendente/concluida/vazio):")
        parametros = {**self.utilizador}
        if filtro: parametros['filtro_status'] = filtro
        
        resposta = self.rede.enviar('listar_pedidos', parametros)
        if resposta.get('ok'):
            pedidos = resposta.get('resultado', [])
            for produto in pedidos:
                print(f"ID: {produto['id']} | Data: {produto['order_date']} | Cliente: {produto['cliente']} | Total: {produto['total_price']:.2f}€ | Status: {produto['status']}")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _concluir_pedido(self):
        if not self.utilizador: 
            return
        pedido_id = self.ler_texto("ID do Pedido a concluir:")
        resposta = self.rede.enviar('concluir_pedido', {**self.utilizador, 'order_id': pedido_id})
        if resposta.get('ok'):
            self.imprimir_sucesso("Pedido concluído com sucesso!")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _verificar_stock(self):
        if not self.utilizador: 
            return
        resposta = self.rede.enviar('verificar_stock_baixo', self.utilizador)
        if resposta.get('ok'):
            resultado = resposta.get('resultado')
            if isinstance(resultado, list) and len(resultado) == 2:
                mensagem, produtos = resultado
                self.imprimir_aviso(f"ALERTA: {mensagem}")
                for produto in produtos:
                    print(f" - Produto: {produto['nome']} (ID: {produto['id']}) | Stock: {produto['stock']} | Loja: {produto['loja']}")
            elif resultado == "SUCESSO":
                self.imprimir_sucesso("Stock está normal (nenhum produto abaixo de 5 unidades).")
            else:
                self.imprimir_info(f"Resultado: {resultado}")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _adicionar_produto(self):
        if not self.utilizador: return
        self.imprimir_cabecalho("Novo Pedido")
        nome = self.ler_texto("Nome:")
        categoria = self.ler_texto("Categoria:")
        descricao = self.ler_texto("Descrição:")
        preco = self.ler_texto("Preço:")
        stock = self.ler_texto("Stock:")
        loja_id = self.ler_texto("ID Loja:")
        
        try:
            parametros = {
                **self.utilizador,
                'nome': nome, 'categoria': categoria, 'descricao': descricao,
                'preco': float(preco), 'stock': int(stock), 'store_id': int(loja_id)
            }
            resposta = self.rede.enviar('add_product', parametros)
            if resposta.get('ok'):
                self.imprimir_sucesso("Produto adicionado!")
            else:
                self.imprimir_erro(resposta.get('erro'))
        except ValueError:
            self.imprimir_erro("Valores numéricos inválidos.")
        self.pausar()

    def _editar_produto(self):
        if not self.utilizador: 
            return
        produto_id = self.ler_texto("ID Produto:")
        self.imprimir_info("Deixe em branco para não alterar")
        
        novo_nome = self.ler_texto("Novo Nome:")
        nova_categoria = self.ler_texto("Nova Categoria:")
        novo_preco = self.ler_texto("Novo Preço:")
        novo_stock = self.ler_texto("Novo Stock:")
        nova_descricao = self.ler_texto("Nova Descrição:")
        
        parametros = {**self.utilizador, 'product_id': produto_id}
        if novo_nome: parametros['novo_nome'] = novo_nome
        if nova_categoria: parametros['nova_categoria'] = nova_categoria
        if novo_preco: parametros['novo_preco'] = novo_preco
        if novo_stock: parametros['novo_stock'] = novo_stock
        if nova_descricao: parametros['nova_descricao'] = nova_descricao
        
        if self.cargo == 'admin':
            novo_id_da_loja = self.ler_texto("Novo ID Loja:")
            if novo_id_da_loja: parametros['novo_id_da_loja'] = novo_id_da_loja
        
        resposta = self.rede.enviar('editar_produto', parametros)
        if resposta.get('ok'):
            self.imprimir_sucesso("Produto atualizado!")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _remover_produto(self):
        if not self.utilizador: return
        produto_id = self.ler_texto("ID Produto a remover:")
        confirmacao = self.ler_texto("Tem a certeza? (s/n):")
        if confirmacao.lower() != 's': return
        
        resposta = self.rede.enviar('deletar_produto', {**self.utilizador, 'product_id': produto_id})
        if resposta.get('ok'):
            self.imprimir_sucesso("Produto removido!")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _criar_funcionario(self):
        if not self.utilizador: 
            return
        self.imprimir_cabecalho("Criar Funcionario")
        utilizador = self.ler_texto("Username:")
        senha = self.ler_segredo("Password:")
        tipo = self.ler_texto("Tipo (admin/vendedor):")
        loja_id = ""
        if tipo == 'vendedor':
            loja_id = self.ler_texto("ID Loja:")
            
        parametros = {
            **self.utilizador,
            'username_func': utilizador, 'password_func': senha,
            'tipo': tipo, 'loja_id': loja_id
        }
        
        resposta = self.rede.enviar('criar_funcionario', parametros)
        if resposta.get('ok'):
            self.imprimir_sucesso("Funcionário criado!")
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _alterar_senha(self):
        if not self.utilizador: 
            return
        nova_senha = self.ler_segredo("Nova Senha:")
        confirmacao = self.ler_segredo("Confirmar:")
        if nova_senha != confirmacao:
            self.imprimir_erro("Não coincidem.")
            self.pausar()
            return
            
        resposta = self.rede.enviar('editar_senha', {**self.utilizador, 'nova_senha': nova_senha})
        if resposta.get('ok'):
            self.imprimir_sucesso("Senha alterada!")
            self.utilizador['password'] = nova_senha
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

    def _promover_admin(self):
        if not self.utilizador: 
            return
        chave = self.ler_segredo("Chave de Admin:")
        resposta = self.rede.enviar('promover_para_admin', {**self.utilizador, 'chave': chave})
        if resposta.get('ok'):
            self.imprimir_sucesso("Promovido a Admin! Faça login novamente para atualizar permissões.")
            self.utilizador = None # Forçar logout
        else:
            self.imprimir_erro(resposta.get('erro'))
        self.pausar()

if __name__ == '__main__':
    try:
        app = ClienteVendas()
        app.iniciar()
    except KeyboardInterrupt:
        print("\nEncerrando...")
    except Exception as e:
        print(f"Erro fatal: {e}")
