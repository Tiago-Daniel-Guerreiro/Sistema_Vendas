import json
import socket
import os
import getpass
import time
import subprocess
from enums import Cores
from console import sucesso, erro, aviso, info, limpar, pausar

# Mapeamento de respostas de sucesso esperadas por comando do servidor.
# Cada entrada é uma lista de formas esperadas de sucesso (string sem prefixo 'Mensagem.' ou com).
COMMAND_SUCCESS = {
    'ping': ['pong'],
    'help': [],
    'registrar': ['UTILIZADOR_CRIADO'],
    'criar_loja': ['ADICIONADO'],
    'add_product': ['SUCESSO', 'ADICIONADO'],
    'editar_produto': ['SUCESSO'],
    'deletar_produto': ['SUCESSO'],
    'criar_funcionario': ['SUCESSO'],
    'editar_senha': ['SUCESSO'],
    'editar_username': ['SUCESSO'],
    'apagar_utilizador': ['SUCESSO', 'REMOVIDO'],
    'promover_para_admin': ['SUCESSO'],
    'criar_loja': ['ADICIONADO'],
    'realizar_venda': [],  # retorna lista com detalhes do pedido
    'list_products': [],
    'listar_lojas': [],
    'ver_meu_historico': [],
    'listar_pedidos': [],
}

class InterfaceUtilizador:
    @staticmethod
    def limpar():
        limpar()

    @staticmethod
    def mostrar_cabecalho(texto):
        info(f"\n{Cores.ROXO}{Cores.NEGRITO}{texto}{Cores.NORMAL}")

    @staticmethod
    def mostrar_sucesso(mensagem):
        sucesso(f"Sucesso: {mensagem}")

    @staticmethod
    def mostrar_erro(mensagem):
        erro(f"Erro: {mensagem}")

    @staticmethod
    def mostrar_aviso(mensagem):
        aviso(f"Aviso: {mensagem}")

    @staticmethod
    def mostrar_info(mensagem):
        info(mensagem)

    @staticmethod
    def eh_sucesso_resposta(resposta, aceitos=None, comando=None, sessao=None):
        if resposta is None:
            return False
        if isinstance(resposta, dict):
            resultado = resposta.get('resultado')
        else:
            resultado = None
        # Se aceitos não for passado, tenta buscar da sessão
        if aceitos is None and comando and sessao and sessao.comandos_disponiveis:
            aceitos = sessao.comandos_disponiveis.get(comando, {}).get('mensagens_sucesso', [])
        if not aceitos:
            aceitos = []
        if isinstance(resultado, str):
            res_clean = resultado.strip()
            res_no_prefix = res_clean.replace('Mensagem.', '')
            variants = {res_clean, res_clean.upper(), res_no_prefix, res_no_prefix.upper()}
            for a in aceitos:
                if a in variants or a.upper() in variants:
                    return True
            if 'SUCESSO' in res_clean.upper() or res_no_prefix.upper() == 'ADICIONADO' or 'REMOVIDO' in res_clean.upper():
                return True
        if isinstance(resultado, (dict, list)):
            return True
        if resposta.get('ok') and not aceitos:
            return True
        return False

    @staticmethod
    def ler_texto(mensagem, obrigatorio=True):
        while True:
            valor = input(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip()
            
            if obrigatorio and (valor == None or valor == ""):
                print(f"{Cores.VERMELHO}Este campo não pode estar vazio.{Cores.NORMAL}")
                continue
            
            return valor

    @staticmethod
    def ler_senha(mensagem, obrigatorio=True):
        # Se obrigatório, permite até 3 tentativas vazias e depois retorna None
        tentativas = 0
        while True:
            valor = getpass.getpass(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip()

            if obrigatorio:
                if valor == "":
                    tentativas += 1
                    if tentativas >= 3:
                        # sinaliza cancelamento/aborto
                        return None
                    print(f"{Cores.VERMELHO}A senha não pode estar vazia. Tentativa {tentativas}/3.{Cores.NORMAL}")
                    continue
                return valor

            # Se não obrigatório, permite retornar string vazia
            return valor

    @staticmethod
    def pausar():
        try:
            pausar()
        except (KeyboardInterrupt, EOFError):
            erro("Saindo...")
            exit(0)

    @staticmethod
    def mostrar_tabela(lista_dados, configuracao_colunas):
        if not lista_dados:
            InterfaceUtilizador.mostrar_aviso("Nenhum registro encontrado.")
            return False

        # Se o servidor retornar um dict (por exemplo {id: {..}}), converte para lista
        if isinstance(lista_dados, dict):
            lista_dados = list(lista_dados.values())

        # Preparar o Cabeçalho e o Separador
        titulos_formatados = []
        tracos_separadores = []
        
        #ljust exemplo: "Ola".ljust(10) = "Ola       "
        for coluna in configuracao_colunas:
            tracos_separadores.append("-" * coluna['largura'])
            titulos_formatados.append(coluna['titulo'].ljust(coluna['largura']))

        # Juntar tudo com um espaço entre colunas
        linha_cabecalho = " ".join(titulos_formatados)
        linha_separador = " ".join(tracos_separadores)

        # Mostra o Cabeçalho
        info(f"\n{Cores.NEGRITO}{linha_cabecalho}{Cores.NORMAL}")
        info(f"{Cores.CINZA}{linha_separador}{Cores.NORMAL}")

        # Monta todas as linhas antes de imprimir para poder avaliar conteúdo
        linhas = []
        for item in lista_dados:
            colunas_linha = []
            tem_valor_real = False

            for coluna in configuracao_colunas:
                chave = coluna['chave']
                tamanho = coluna['largura']

                # Garante que item suporta .get
                if not hasattr(item, 'get'):
                    # item é provavelmente uma string ou outro tipo; embalamos num dict
                    item = {'valor': item}

                valor = item.get(chave, "N/A")

                # Formatação simples de preço
                if isinstance(valor, float):
                    texto_valor = f"{valor:.2f}"
                else:
                    texto_valor = str(valor)

                if texto_valor.strip() != "N/A":
                    tem_valor_real = True

                colunas_linha.append(texto_valor.ljust(tamanho))

            if tem_valor_real:
                linhas.append(" ".join(colunas_linha))

        # Se não houver linhas com valores reais, considera nenhum registro
        if not linhas:
            InterfaceUtilizador.mostrar_aviso("Nenhum registro encontrado.")
            return False

        # Imprime as linhas válidas
        for linha in linhas:
            info(linha)
        info("")
        return True

    @staticmethod
    def exibir_menu(titulo, opcoes, sair_texto="Sair", ):
        # Exibe um menu simples. Se `opcoes` estiver vazio mostra uma mensagem e volta.
        while True:
            InterfaceUtilizador.pausar()
            InterfaceUtilizador.limpar()
            InterfaceUtilizador.mostrar_cabecalho(titulo)

            if not opcoes:
                return

            for indice, (texto, _) in enumerate(opcoes, 1):
                info(f"{indice}) {texto}")
            info(f"0) {sair_texto}")

            escolha = InterfaceUtilizador.ler_texto("Opção:", obrigatorio=False)

            if escolha == '0':
                return
            if escolha == '' or not escolha.isdigit():
                InterfaceUtilizador.mostrar_aviso("Por favor, selecione uma opção válida.")
                continue

            try:
                indice_escolhido = int(escolha) - 1
                if 0 <= indice_escolhido < len(opcoes):
                    funcao = opcoes[indice_escolhido][1]
                    fechar = funcao()
                    if fechar is True:
                        return
                else:
                    InterfaceUtilizador.mostrar_erro("Opção inválida.")
                    continue
            except ValueError:
                InterfaceUtilizador.mostrar_erro("Introduza apenas números.")

class ClienteRede:
    def __init__(self, host, porta, debug=False, sessao=None):
        self.host = host
        self.porta = porta
        self.debug = debug
        self.timeout = 5
        self.sessao = sessao
        self.tokens = self._carregar_tokens()

    def _carregar_tokens(self):
        caminho = 'tokens.txt'
        tokens = {}
        if os.path.exists(caminho):
            try:
                with open(caminho, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if ':' in linha:
                            username, token = linha.split(':', 1)
                            tokens[username] = token
            except Exception:
                pass
        return tokens

    def _salvar_token(self, username, token):
        caminho = 'tokens.txt'
        self.tokens[username] = token
        try:
            with open(caminho, 'w', encoding='utf-8') as f:
                for user, tkn in self.tokens.items():
                    f.write(f'{user}:{tkn}\n')
        except Exception:
            pass

    def _remover_token(self, username):
        caminho = 'tokens.txt'
        if username in self.tokens:
            del self.tokens[username]
            try:
                with open(caminho, 'w', encoding='utf-8') as f:
                    for user, tkn in self.tokens.items():
                        f.write(f'{user}:{tkn}\n')
            except Exception:
                pass

    def testar_ping(self):
        try:
            resposta = self.enviar_comando('ping')
            if resposta.get('ok'):
                resultado = resposta.get('resultado')
                if resultado == 'pong' or (isinstance(resultado, dict) and resultado.get('cargo')):
                    return True
            return False
        except Exception:
            return False

    def enviar_comando(self, acao, parametros=None):
        if parametros is None:
            parametros = {}
        # Adiciona token de sessão se existir
        if self.sessao is not None and hasattr(self.sessao, 'token_sessao') and self.sessao.token_sessao:
            parametros['token_sessao'] = self.sessao.token_sessao
        pacote = {'acao': acao, 'parametros': parametros}
        dados_json = json.dumps(pacote) + '\n'
        try:
            # Conexão socket
            with socket.create_connection((self.host, self.porta), timeout=self.timeout) as conexao:
                conexao.sendall(dados_json.encode('utf-8'))
                resposta_bytes = b''
                while True:
                    parte = conexao.recv(4096)
                    if not parte:
                        break
                    resposta_bytes += parte
                    if b'\n' in parte:
                        break
                resposta_texto = resposta_bytes.decode('utf-8').strip()
                if not resposta_texto:
                    if self.sessao is not None:
                        self.sessao.encerrar_sessao()
                    InterfaceUtilizador.mostrar_aviso("Desconectado do servidor. Sessão encerrada.")
                    return {'ok': False, 'erro': 'Resposta vazia do servidor'}
                if self.debug:
                    print(f"{Cores.CINZA}{resposta_texto}{Cores.NORMAL}")
                return json.loads(resposta_texto)
        except ConnectionRefusedError:
            if self.sessao is not None:
                self.sessao.encerrar_sessao()
            InterfaceUtilizador.mostrar_aviso("Servidor desconectado. Sessão encerrada.")
            return {'ok': False, 'erro': 'Conexão recusada. Verifique se o servidor está ligado.'}
        except Exception as erro:
            if self.sessao is not None:
                self.sessao.encerrar_sessao()
            InterfaceUtilizador.mostrar_aviso("Erro de comunicação. Sessão encerrada.")
            return {'ok': False, 'erro': f'Erro de comunicação: {str(erro)}'}
                
class SessaoCliente:
    def __init__(self):
        self.utilizador_atual = None
        self.cargo = None
        self.comandos_disponiveis = {}
        self.token_sessao = None

    def iniciar_sessao(self, dados_login, cargo, token_sessao=None):
        self.utilizador_atual = dados_login
        self.cargo = cargo
        self.token_sessao = token_sessao

    def encerrar_sessao(self):
        self.utilizador_atual = None
        self.cargo = None
        self.comandos_disponiveis = {}
        self.token_sessao = None

    def esta_logado(self):
        if self.utilizador_atual is not None:
            return True
        return False

    def obter_credenciais(self):
        cred = {}
        if self.token_sessao:
            cred['token_sessao'] = self.token_sessao
        return cred

class ControladorAutenticacao:
    def __init__(self, rede, sessao):
        self.rede = rede
        self.sessao = sessao

    def fazer_login(self):
        InterfaceUtilizador.limpar()
        InterfaceUtilizador.mostrar_cabecalho("Login")
        contas = self.rede.tokens
        usernames = list(contas.keys())
        print("Sessões salvas:")
        for i, username in enumerate(usernames, 1):
            print(f"{i}) {username}")
        print(f"{len(usernames)+1}) Outra conta")
        escolha = InterfaceUtilizador.ler_texto("Selecione o número da conta ou crie nova:")
        if escolha.isdigit() and 1 <= int(escolha) <= len(usernames):
            username = usernames[int(escolha)-1]
            token = contas[username]
            resposta = self.rede.enviar_comando('autenticar', {'username': username, 'token_sessao': token})
            if resposta.get('ok') and isinstance(resposta.get('resultado'), dict):
                self.sessao.iniciar_sessao({'username': username}, resposta['resultado'].get('cargo'), token_sessao=token)
                InterfaceUtilizador.mostrar_sucesso(f"Bem-vindo, {username} ({self.sessao.cargo})")
                return True
            else:
                InterfaceUtilizador.mostrar_aviso("Token inválido ou expirado. Será necessário informar a senha.")
                senha = InterfaceUtilizador.ler_senha(f"Senha para {username}:")
                resposta = self.rede.enviar_comando('autenticar', {'username': username, 'password': senha})
                if resposta.get('ok') and isinstance(resposta.get('resultado'), dict):
                    novo_token = resposta['resultado'].get('token_sessao')
                    if novo_token:
                        self.rede._salvar_token(username, novo_token)
                        self.sessao.iniciar_sessao({'username': username}, resposta['resultado'].get('cargo'), token_sessao=novo_token)
                        InterfaceUtilizador.mostrar_sucesso(f"Bem-vindo, {username} ({self.sessao.cargo})")
                        return True
                    else:
                        InterfaceUtilizador.mostrar_erro("Token não recebido do servidor.")
                else:
                    InterfaceUtilizador.mostrar_erro(resposta.get('erro', 'Erro no login'))
                InterfaceUtilizador.pausar()
        elif escolha == str(len(usernames)+1):
            utilizador = InterfaceUtilizador.ler_texto("Utilizador:")
            if not utilizador:
                InterfaceUtilizador.mostrar_erro("Username não pode estar vazio.")
                InterfaceUtilizador.pausar()
                return
            senha = InterfaceUtilizador.ler_senha("Senha:")
            if not senha:
                InterfaceUtilizador.mostrar_erro("Senha não pode estar vazia.")
                InterfaceUtilizador.pausar()
                return
            resposta = self.rede.enviar_comando('autenticar', {'username': utilizador, 'password': senha})
            if resposta.get('ok') and isinstance(resposta.get('resultado'), dict):
                novo_token = resposta['resultado'].get('token_sessao')
                if novo_token:
                    self.rede._salvar_token(utilizador, novo_token)
                    self.sessao.iniciar_sessao({'username': utilizador}, resposta['resultado'].get('cargo'), token_sessao=novo_token)
                    InterfaceUtilizador.mostrar_sucesso(f"Bem-vindo, {utilizador} ({self.sessao.cargo})")
                    return True
                else:
                    InterfaceUtilizador.mostrar_erro("Token não recebido do servidor.")
            else:
                InterfaceUtilizador.mostrar_erro(resposta.get('erro', 'Erro no login'))
            InterfaceUtilizador.pausar()
        else:
            InterfaceUtilizador.mostrar_erro("Opção inválida.")
            InterfaceUtilizador.pausar()

    def registrar_conta(self):
        InterfaceUtilizador.limpar()
        InterfaceUtilizador.mostrar_cabecalho("Criar Conta")

        utilizador = InterfaceUtilizador.ler_texto("Novo Utilizador:")
        senha = InterfaceUtilizador.ler_senha("Senha:")
        confirmacao = InterfaceUtilizador.ler_senha("Confirmar Senha:")

        if senha != confirmacao:
            InterfaceUtilizador.mostrar_erro("As senhas não coincidem.")
            return

        resposta = self.rede.enviar_comando('registrar', {'username': utilizador, 'password': senha})

        if resposta.get('ok'):
            resultado = resposta.get('resultado')
            # Se resultado for dict e tiver token, faz login automático
            if isinstance(resultado, dict) and resultado.get('token_sessao'):
                token = resultado.get('token_sessao')
                cargo = resultado.get('cargo')
                self.sessao.iniciar_sessao({'username': utilizador, 'password': senha}, cargo, token_sessao=token)
                InterfaceUtilizador.mostrar_sucesso(f"Conta criada e login automático realizado! Bem-vindo, {utilizador}!")
                return True
            elif resultado == 'UTILIZADOR_CRIADO':
                InterfaceUtilizador.mostrar_sucesso("Conta criada com sucesso!")
            else:
                InterfaceUtilizador.mostrar_erro(str(resultado))
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def terminar_sessao(self):
        # Remove token do arquivo ao fazer logout
        if self.sessao.utilizador_atual and 'username' in self.sessao.utilizador_atual:
            username = self.sessao.utilizador_atual['username']
            self.rede._remover_token(username)
        self.sessao.encerrar_sessao()
        InterfaceUtilizador.mostrar_sucesso("Sessão terminada.")
        return True

    def alterar_senha(self):
        # Permitir que o utilizador cancele pressionando Enter (senha vazia)
        nova_senha = InterfaceUtilizador.ler_senha("Nova Senha:", obrigatorio=False)
        if not nova_senha:
            InterfaceUtilizador.mostrar_aviso("Atualização de senha cancelada.")
            return

        confirmacao = InterfaceUtilizador.ler_senha("Confirmar:", obrigatorio=False)
        if nova_senha != confirmacao:
            InterfaceUtilizador.mostrar_erro("Senhas não coincidem.")
            return

        credenciais = self.sessao.obter_credenciais().copy()
        credenciais['nova_senha'] = nova_senha

        resposta = self.rede.enviar_comando('editar_senha', credenciais)

        if resposta.get('ok'):
            InterfaceUtilizador.mostrar_sucesso("Senha alterada com sucesso. Faça login novamente.")
            self.sessao.encerrar_sessao()
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def editar_username(self):
        InterfaceUtilizador.mostrar_cabecalho("Editar Username")

        novo_username = InterfaceUtilizador.ler_texto("Novo Username:")
        credenciais = self.sessao.obter_credenciais().copy()
        credenciais['novo_username'] = novo_username

        resposta = self.rede.enviar_comando('editar_username', credenciais)

        if resposta.get('ok'):
            self.sessao.utilizador_atual['username'] = novo_username
            InterfaceUtilizador.mostrar_sucesso("Username alterado com sucesso. Faça login novamente.")
            self.sessao.encerrar_sessao()
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def apagar_utilizador(self):
        InterfaceUtilizador.mostrar_cabecalho("Apagar Utilizador")

        confirmacao = InterfaceUtilizador.ler_texto("Tem certeza que deseja apagar sua conta? (s/n):")
        if confirmacao.lower() != 's':
            InterfaceUtilizador.mostrar_aviso("Operação cancelada.")
            return

        credenciais = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando('apagar_utilizador', credenciais)
        aceitos = COMMAND_SUCCESS.get('apagar_utilizador', [])
        if InterfaceUtilizador.eh_sucesso_resposta(resposta, aceitos=aceitos):
            InterfaceUtilizador.mostrar_sucesso("Conta apagada com sucesso.")
            self.sessao.encerrar_sessao()
            return True
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro') or str(resposta.get('resultado')))

    def promover_para_admin(self):
        InterfaceUtilizador.mostrar_cabecalho("Promover para Admin")
        chave = InterfaceUtilizador.ler_texto("Chave de promoção:")
        parametros = self.sessao.obter_credenciais().copy()
        parametros['chave'] = chave
        resposta = self.rede.enviar_comando('promover_para_admin', parametros)
        if InterfaceUtilizador.eh_sucesso_resposta(resposta, aceitos=COMMAND_SUCCESS.get('promover_para_admin', [])):
            InterfaceUtilizador.mostrar_sucesso("Promovido a admin com sucesso. Faça login novamente.")
            self.sessao.encerrar_sessao()
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro') or str(resposta.get('resultado')))
            self.sessao.encerrar_sessao()

class ControladorLoja:
    # Métodos de aviso para comandos referenciados mas não implementados
    def deletar_pedido(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade deletar_pedido ainda não implementada no cliente.")

    def editar_produto_admin(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade editar_produto (admin) ainda não implementada no cliente.")

    def listar_categorias(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade listar_categorias ainda não implementada no cliente.")

    def listar_nomes_produtos(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade listar_nomes_produtos ainda não implementada no cliente.")

    def listar_descricoes(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade listar_descricoes ainda não implementada no cliente.")

    def criar_loja(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade criar_loja ainda não implementada no cliente.")

    def editar_loja(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade editar_loja ainda não implementada no cliente.")

    def apagar_loja(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade apagar_loja ainda não implementada no cliente.")

    def criar_funcionario(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade criar_funcionario ainda não implementada no cliente.")
    def __init__(self, rede, sessao):
        self.rede = rede
        self.sessao = sessao

    def _escolher_loja(self):
        # Lista lojas para o utilizador escolher
        parametros = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando('listar_lojas', parametros)
        
        if not resposta.get('ok'):
            InterfaceUtilizador.mostrar_erro("Erro ao listar lojas.")
            return None

        lojas = resposta.get('resultado', [])
        
        colunas = [
            {'titulo': 'ID', 'chave': 'id', 'largura': 5},
            {'titulo': 'Nome', 'chave': 'nome', 'largura': 20},
            {'titulo': 'Localização', 'chave': 'localizacao', 'largura': 20}
        ]
        
        print("\nLojas Disponíveis:")
        tem = InterfaceUtilizador.mostrar_tabela(lojas, colunas)

        # Se não há lojas (ou se a tabela não imprimiu linhas), não permitir continuar
        if not lojas or not tem:
            return None

        id_loja = InterfaceUtilizador.ler_texto("Digite o ID da Loja (Enter para todas):", obrigatorio=False)
        return id_loja

    def listar_produtos(self):
        InterfaceUtilizador.mostrar_cabecalho("Produtos")
        id_loja = self._escolher_loja()

        parametros = self.sessao.obter_credenciais().copy()
        if id_loja:
            parametros['store_id'] = id_loja

        resposta = self.rede.enviar_comando('list_products', parametros)

        if resposta.get('ok'):
            produtos = resposta.get('resultado', [])

            colunas = [
                {'titulo': 'ID', 'chave': 'id', 'largura': 5},
                {'titulo': 'Produto', 'chave': 'nome', 'largura': 20},
                {'titulo': 'Categoria', 'chave': 'categoria', 'largura': 15},
                {'titulo': 'Preço', 'chave': 'preco', 'largura': 10},
                {'titulo': 'Stock', 'chave': 'stock', 'largura': 8},
                {'titulo': 'Loja', 'chave': 'loja', 'largura': 15}
            ]
            tem = InterfaceUtilizador.mostrar_tabela(produtos, colunas)
            if not tem:
                return
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def realizar_compra(self):
        InterfaceUtilizador.mostrar_cabecalho("Nova Compra")
        # Primeiro escolhe loja
        id_loja = self._escolher_loja()
        if not id_loja:
            InterfaceUtilizador.mostrar_aviso("Selecione uma loja específica para comprar.")
            return

        # Lista produtos da loja escolhida
        parametros = self.sessao.obter_credenciais().copy()
        parametros['store_id'] = id_loja
        resposta_produtos = self.rede.enviar_comando('list_products', parametros)

        if not resposta_produtos.get('ok'):
            InterfaceUtilizador.mostrar_erro(resposta_produtos.get('erro'))
            return

        produtos = resposta_produtos.get('resultado', [])
        colunas = [
            {'titulo': 'ID', 'chave': 'id', 'largura': 5},
            {'titulo': 'Produto', 'chave': 'nome', 'largura': 20},
            {'titulo': 'Categoria', 'chave': 'categoria', 'largura': 15},
            {'titulo': 'Preço', 'chave': 'preco', 'largura': 10},
            {'titulo': 'Stock', 'chave': 'stock', 'largura': 8}
        ]

        tem = InterfaceUtilizador.mostrar_tabela(produtos, colunas)
        if not produtos or not tem:
            InterfaceUtilizador.mostrar_aviso('Nenhum produto disponível nesta loja.')
            return

        id_produto = InterfaceUtilizador.ler_texto('ID do Produto:')
        if not id_produto.isdigit():
            InterfaceUtilizador.mostrar_erro('ID inválido.')
            return

        # Encontrar produto pelo id
        produto_encontrado = None
        for p in produtos:
            try:
                if int(p.get('id')) == int(id_produto):
                    produto_encontrado = p
                    break
            except Exception:
                continue

        if produto_encontrado is None:
            InterfaceUtilizador.mostrar_erro('Produto não encontrado.')
            return

        InterfaceUtilizador.mostrar_info(f"Produto: {produto_encontrado.get('nome')} | Preço: {produto_encontrado.get('preco')}€ | Stock: {produto_encontrado.get('stock')}")

        quantidade_str = InterfaceUtilizador.ler_texto('Quantidade:')
        if not quantidade_str.isdigit():
            InterfaceUtilizador.mostrar_erro('Quantidade inválida.')
            return

        quantidade = int(quantidade_str)

        parametros_venda = self.sessao.obter_credenciais().copy()
        parametros_venda['itens'] = {str(produto_encontrado.get('id')): quantidade}

        resposta_venda = self.rede.enviar_comando('realizar_venda', parametros_venda)
        if resposta_venda.get('ok'):
            resultado = resposta_venda.get('resultado')
            if isinstance(resultado, list):
                dados_pedido = resultado[1]
                InterfaceUtilizador.mostrar_sucesso(f"Pedido realizado! ID: {dados_pedido.get('order_id')}")
                InterfaceUtilizador.mostrar_sucesso(f"Total Pago: {dados_pedido.get('total_price'):.2f}€")
            else:
                InterfaceUtilizador.mostrar_aviso(str(resultado))
        else:
            InterfaceUtilizador.mostrar_erro(resposta_venda.get('erro'))

    def ver_meu_historico(self):
        InterfaceUtilizador.mostrar_cabecalho("Meu Histórico de Compras")

        parametros = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando('ver_meu_historico', parametros)

        if resposta.get('ok'):
            historico = resposta.get('resultado', [])

            colunas = [
                {'titulo': 'ID Pedido', 'chave': 'id_pedido', 'largura': 10},
                {'titulo': 'Data', 'chave': 'data', 'largura': 15},
                {'titulo': 'Total', 'chave': 'total', 'largura': 10},
                {'titulo': 'Status', 'chave': 'status', 'largura': 15}
            ]

            tem = InterfaceUtilizador.mostrar_tabela(historico, colunas)
            if not tem:
                return
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def listar_lojas(self):
        InterfaceUtilizador.mostrar_cabecalho("Lojas")
        resposta = self.rede.enviar_comando('listar_lojas', self.sessao.obter_credenciais().copy())
        if not resposta.get('ok'):
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))
            return

        lojas = resposta.get('resultado', [])
        colunas = [
            {'titulo': 'ID', 'chave': 'id', 'largura': 5},
            {'titulo': 'Nome', 'chave': 'nome', 'largura': 20},
            {'titulo': 'Localização', 'chave': 'localizacao', 'largura': 20}
        ]
        InterfaceUtilizador.mostrar_tabela(lojas, colunas)

    def buscar_produto_por_nome(self):
        InterfaceUtilizador.mostrar_cabecalho("Buscar Produto por Nome")
        # Escolhe loja primeiro
        id_loja = self._escolher_loja()
        if not id_loja:
            InterfaceUtilizador.mostrar_aviso("Seleção de loja cancelada ou sem lojas disponíveis.")
            return

        # Lista produtos da loja para auxiliar a pesquisa
        parametros = self.sessao.obter_credenciais().copy()
        parametros['store_id'] = id_loja
        resposta = self.rede.enviar_comando('list_products', parametros)
        if not resposta.get('ok'):
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))
            return

        produtos = resposta.get('resultado', [])
        colunas = [
            {'titulo': 'ID', 'chave': 'id', 'largura': 5},
            {'titulo': 'Produto', 'chave': 'nome', 'largura': 20},
            {'titulo': 'Categoria', 'chave': 'categoria', 'largura': 15},
            {'titulo': 'Preço', 'chave': 'preco', 'largura': 10},
            {'titulo': 'Stock', 'chave': 'stock', 'largura': 8}
        ]
        tem = InterfaceUtilizador.mostrar_tabela(produtos, colunas)
        if not tem:
            InterfaceUtilizador.mostrar_aviso('Nenhum produto disponível nesta loja.')
            return

        nome = InterfaceUtilizador.ler_texto('Nome do Produto:')
        parametros = self.sessao.obter_credenciais().copy()
        parametros['store_id'] = id_loja
        parametros['nome_produto'] = nome

        resposta_busca = self.rede.enviar_comando('buscar_produto_por_nome', parametros)
        if resposta_busca.get('ok'):
            resultado = resposta_busca.get('resultado')
            InterfaceUtilizador.mostrar_info(str(resultado))
        else:
            InterfaceUtilizador.mostrar_erro(resposta_busca.get('erro') or str(resposta_busca.get('resultado')))

class ControladorAdministracao:
    def deletar_pedido(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade deletar_pedido ainda não implementada no cliente.")

    def listar_categorias(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade listar_categorias ainda não implementada no cliente.")

    def listar_nomes_produtos(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade listar_nomes_produtos ainda não implementada no cliente.")

    def listar_descricoes(self):
        InterfaceUtilizador.mostrar_aviso("Funcionalidade listar_descricoes ainda não implementada no cliente.")
    def __init__(self, rede, sessao):
        self.rede = rede
        self.sessao = sessao

    def menu_admin(self):
        opcoes = [
            ("Listar Utilizadores", self.listar_utilizadores),
            ("Criar Loja", self.criar_loja),
            ("Editar Loja", self.editar_loja),
            ("Apagar Loja", self.apagar_loja),
            ("Adicionar Produto", self.adicionar_produto),
            ("Editar Produto", self.editar_produto),
            ("Deletar Produto", self.deletar_produto),
            ("Criar Funcionário", self.criar_funcionario)
        ]

        InterfaceUtilizador.exibir_menu("Painel de Administração", opcoes, sair_texto="Voltar")

    def listar_utilizadores(self):
        InterfaceUtilizador.mostrar_cabecalho("Utilizadores do Sistema")

        parametros = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando('listar_utilizadores', parametros)

        if resposta.get('ok'):
            utilizadores = resposta.get('resultado', [])

            colunas = [
                {'titulo': 'ID', 'chave': 'id', 'largura': 5},
                {'titulo': 'Username', 'chave': 'username', 'largura': 20},
                {'titulo': 'Cargo', 'chave': 'cargo', 'largura': 10},
                {'titulo': 'Loja', 'chave': 'loja', 'largura': 20}
            ]

            tem = InterfaceUtilizador.mostrar_tabela(utilizadores, colunas)
            if not tem:
                return
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))


    def criar_loja(self):
        InterfaceUtilizador.mostrar_cabecalho("Nova Loja")

        nome = InterfaceUtilizador.ler_texto("Nome da Loja:")
        localizacao = InterfaceUtilizador.ler_texto("Localização:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros['nome'] = nome
        parametros['localizacao'] = localizacao

        resposta = self.rede.enviar_comando('criar_loja', parametros)
        if InterfaceUtilizador.eh_sucesso_resposta(resposta, aceitos=['ADICIONADO']):
            InterfaceUtilizador.mostrar_sucesso("Loja criada com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(str(resposta.get('resultado') or resposta.get('erro')))


    def editar_loja(self):
        InterfaceUtilizador.mostrar_cabecalho("Editar Loja")

        id_loja = InterfaceUtilizador.ler_texto("ID da Loja:")
        novo_nome = InterfaceUtilizador.ler_texto("Novo Nome:")
        nova_localizacao = InterfaceUtilizador.ler_texto("Nova Localização:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros.update({'id_loja': id_loja, 'nome': novo_nome, 'localizacao': nova_localizacao})

        resposta = self.rede.enviar_comando('editar_loja', parametros)

        if resposta.get('ok'):
            InterfaceUtilizador.mostrar_sucesso("Loja editada com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))


    def apagar_loja(self):
        InterfaceUtilizador.mostrar_cabecalho("Apagar Loja")

        id_loja = InterfaceUtilizador.ler_texto("ID da Loja:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros['id_loja'] = id_loja

        resposta = self.rede.enviar_comando('apagar_loja', parametros)

        if resposta.get('ok'):
            InterfaceUtilizador.mostrar_sucesso("Loja apagada com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))


    def adicionar_produto(self):
        InterfaceUtilizador.mostrar_cabecalho("Novo Produto")

        nome = InterfaceUtilizador.ler_texto("Nome:")
        categoria = InterfaceUtilizador.ler_texto("Categoria:")
        descricao = InterfaceUtilizador.ler_texto("Descrição:")
        preco = InterfaceUtilizador.ler_texto("Preço:")
        stock = InterfaceUtilizador.ler_texto("Stock:")
        id_loja = InterfaceUtilizador.ler_texto("ID da Loja:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros.update({
            'nome': nome, 'categoria': categoria, 'descricao': descricao,
            'preco': preco, 'stock': stock, 'store_id': id_loja
        })

        resposta = self.rede.enviar_comando('add_product', parametros)
        if InterfaceUtilizador.eh_sucesso_resposta(resposta):
            InterfaceUtilizador.mostrar_sucesso("Produto adicionado!")
        else:
            InterfaceUtilizador.mostrar_erro(str(resposta.get('resultado') or resposta.get('erro')))


    def editar_produto(self):
        InterfaceUtilizador.mostrar_cabecalho("Editar Produto")

        id_produto = InterfaceUtilizador.ler_texto("ID do Produto:")
        nome = InterfaceUtilizador.ler_texto("Novo Nome:")
        categoria = InterfaceUtilizador.ler_texto("Nova Categoria:")
        descricao = InterfaceUtilizador.ler_texto("Nova Descrição:")
        preco = InterfaceUtilizador.ler_texto("Novo Preço:")
        stock = InterfaceUtilizador.ler_texto("Novo Stock:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros.update({
            'id_produto': id_produto,
            'nome': nome,
            'categoria': categoria,
            'descricao': descricao,
            'preco': preco,
            'stock': stock
        })

        resposta = self.rede.enviar_comando('editar_produto', parametros)
        if InterfaceUtilizador.eh_sucesso_resposta(resposta):
            InterfaceUtilizador.mostrar_sucesso("Produto editado com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(str(resposta.get('resultado') or resposta.get('erro')))


    def deletar_produto(self):
        InterfaceUtilizador.mostrar_cabecalho("Deletar Produto")

        id_produto = InterfaceUtilizador.ler_texto("ID do Produto:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros['id_produto'] = id_produto

        resposta = self.rede.enviar_comando('deletar_produto', parametros)
        if InterfaceUtilizador.eh_sucesso_resposta(resposta):
            InterfaceUtilizador.mostrar_sucesso("Produto deletado com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(str(resposta.get('resultado') or resposta.get('erro')))


    def criar_funcionario(self):
        InterfaceUtilizador.mostrar_cabecalho("Criar Funcionário")

        username = InterfaceUtilizador.ler_texto("Username:")
        senha = InterfaceUtilizador.ler_senha("Senha:")
        cargo = InterfaceUtilizador.ler_texto("Cargo:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros.update({'username': username, 'password': senha, 'cargo': cargo})

        resposta = self.rede.enviar_comando('criar_funcionario', parametros)
        if InterfaceUtilizador.eh_sucesso_resposta(resposta):
            InterfaceUtilizador.mostrar_sucesso("Funcionário criado com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(str(resposta.get('resultado') or resposta.get('erro')))

class ControladorVendedor:
    def __init__(self, rede, sessao):
        self.rede = rede
        self.sessao = sessao

    def listar_pedidos(self):
        InterfaceUtilizador.mostrar_cabecalho("Pedidos")

        parametros = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando('listar_pedidos', parametros)

        if resposta.get('ok'):
            pedidos = resposta.get('resultado', [])

            colunas = [
                {'titulo': 'ID', 'chave': 'id', 'largura': 5},
                {'titulo': 'Cliente', 'chave': 'cliente', 'largura': 20},
                {'titulo': 'Total', 'chave': 'total', 'largura': 10},
                {'titulo': 'Status', 'chave': 'status', 'largura': 15}
            ]

            tem = InterfaceUtilizador.mostrar_tabela(pedidos, colunas)
            if not tem:
                return
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def concluir_pedido(self):
        InterfaceUtilizador.mostrar_cabecalho("Concluir Pedido")

        id_pedido = InterfaceUtilizador.ler_texto("ID do Pedido:")
        parametros = self.sessao.obter_credenciais().copy()
        parametros['id_pedido'] = id_pedido

        resposta = self.rede.enviar_comando('concluir_pedido', parametros)

        if resposta.get('ok'):
            InterfaceUtilizador.mostrar_sucesso("Pedido concluído com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def verificar_stock_baixo(self):
        InterfaceUtilizador.mostrar_cabecalho("Produtos com Stock Baixo")

        parametros = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando('verificar_stock_baixo', parametros)

        if resposta.get('ok'):
            produtos = resposta.get('resultado', [])

            colunas = [
                {'titulo': 'ID', 'chave': 'id', 'largura': 5},
                {'titulo': 'Produto', 'chave': 'nome', 'largura': 20},
                {'titulo': 'Stock', 'chave': 'stock', 'largura': 10}
            ]

            tem = InterfaceUtilizador.mostrar_tabela(produtos, colunas)
            if not tem:
                return
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def editar_produto(self):
        InterfaceUtilizador.mostrar_cabecalho("Editar Produto")

        id_produto = InterfaceUtilizador.ler_texto("ID do Produto:")
        nome = InterfaceUtilizador.ler_texto("Novo Nome:")
        categoria = InterfaceUtilizador.ler_texto("Nova Categoria:")
        descricao = InterfaceUtilizador.ler_texto("Nova Descrição:")
        preco = InterfaceUtilizador.ler_texto("Novo Preço:")
        stock = InterfaceUtilizador.ler_texto("Novo Stock:")

        parametros = self.sessao.obter_credenciais().copy()
        parametros.update({
            'id_produto': id_produto,
            'nome': nome,
            'categoria': categoria,
            'descricao': descricao,
            'preco': preco,
            'stock': stock
        })

        resposta = self.rede.enviar_comando('editar_produto', parametros)

        if resposta.get('ok'):
            InterfaceUtilizador.mostrar_sucesso("Produto editado com sucesso!")
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

class AplicacaoCliente:
    def __init__(self, host, porta, debug=False):
        self.sessao = SessaoCliente()
        self.rede = ClienteRede(host, porta, debug, sessao=self.sessao)
        self.auth = ControladorAutenticacao(self.rede, self.sessao)
        self.loja = ControladorLoja(self.rede, self.sessao)
        self.admin = ControladorAdministracao(self.rede, self.sessao)
        self.vendedor = ControladorVendedor(self.rede, self.sessao)

    def verificar_conexao_inicial(self):
        if not self.rede.testar_ping():
            InterfaceUtilizador.mostrar_erro("O servidor não responde ao ping. Verifique o IP e a rede.")
            return False
        
        resposta = self.rede.enviar_comando('ping')
        if not resposta.get('ok'):
            InterfaceUtilizador.mostrar_erro("O servidor recusou a conexão da aplicação.")
            return False
            
        return True

    def atualizar_permissoes(self):
        credenciais = self.sessao.obter_credenciais()
        cargo = None
        if credenciais.get('username') and credenciais.get('password'):
            resposta_auth = self.rede.enviar_comando('autenticar', credenciais)
            if resposta_auth.get('ok'):
                resultado = resposta_auth.get('resultado', {})
                if isinstance(resultado, dict):
                    cargo = resultado.get('cargo')
                    self.sessao.cargo = cargo
        resposta = self.rede.enviar_comando('help', credenciais)
        if resposta.get('ok') and 'comandos' in resposta.get('resultado', {}):
            comandos_agrupados = resposta['resultado']['comandos']
            comandos_disponiveis = {}
            for categoria, lista_cmds in comandos_agrupados.items():
                for cmd in lista_cmds:
                    nome = cmd.get('nome')
                    mensagens_sucesso = cmd.get('mensagens_sucesso', [])
                    comandos_disponiveis[nome] = {
                        'categoria': categoria,
                        'mensagens_sucesso': mensagens_sucesso
                    }
            self.sessao.comandos_disponiveis = comandos_disponiveis
        else:
            self.sessao.comandos_disponiveis = {}

    def _executar_comando_generico(self, comando):
        """Executa um comando simples no servidor passando as credenciais atuais."""
        parametros = self.sessao.obter_credenciais().copy()
        resposta = self.rede.enviar_comando(comando, parametros)
        if resposta.get('ok'):
            resultado = resposta.get('resultado')
            # valida resposta usando mapeamento de sucessos esperados
            aceitos = COMMAND_SUCCESS.get(comando)
            # Se o resultado for um payload (lista/dict) mostra como info para o utilizador
            if isinstance(resultado, (dict, list)):
                InterfaceUtilizador.mostrar_info(str(resultado))
            else:
                if InterfaceUtilizador.eh_sucesso_resposta(resposta, aceitos=aceitos):
                    InterfaceUtilizador.mostrar_sucesso(str(resultado))
                else:
                    InterfaceUtilizador.mostrar_aviso(str(resultado))
        else:
            InterfaceUtilizador.mostrar_erro(resposta.get('erro'))

    def menu_inicial(self):
        opcoes = [
            ("Login", self.auth.fazer_login),
            ("registrar Conta", self.auth.registrar_conta)
        ]
        InterfaceUtilizador.exibir_menu("Sistema de Vendas", opcoes, sair_texto="Sair")

    def menu_principal(self):
        if not self.sessao.esta_logado():
            return

        if self.sessao.utilizador_atual is not None:
            utilizador = self.sessao.utilizador_atual.get('username', 'Desconhecido')
        else:
            utilizador = 'Desconhecido'

        if self.sessao.cargo is not None:
            cargo = self.sessao.cargo
        else:
            cargo = 'Desconhecido'

        titulo = f"Menu Principal - {utilizador} [{cargo}]"
        # Construir menu por categorias (sub-menus) com comandos disponíveis
        opcoes_menu = []
        comandos = self.sessao.comandos_disponiveis or {}

        # Mapeamento de comandos conhecidos para funções locais
        mapa_comandos = {
            'ping': (lambda: self._executar_comando_generico('ping')),
            'help': (lambda: self._executar_comando_generico('help')),
            'autenticar': self.auth.fazer_login,
            'registrar': self.auth.registrar_conta,
            'list_products': self.loja.listar_produtos,
            'realizar_venda': self.loja.realizar_compra,
            'ver_meu_historico': self.loja.ver_meu_historico,
            'buscar_produto_por_nome': self.loja.buscar_produto_por_nome,
            'listar_lojas': self.loja.listar_lojas,
            'editar_senha': self.auth.alterar_senha,
            'editar_username': self.auth.editar_username,
            'apagar_utilizador': self.auth.apagar_utilizador,
            'promover_para_admin': self.auth.promover_para_admin,
            # vendedor/admin mappings
            'listar_pedidos': self.vendedor.listar_pedidos,
            'concluir_pedido': self.vendedor.concluir_pedido,
            'verificar_stock_baixo': self.vendedor.verificar_stock_baixo,
            'criar_loja': self.admin.criar_loja,
            'editar_loja': self.admin.editar_loja,
            'apagar_loja': self.admin.apagar_loja,
            'criar_funcionario': self.admin.criar_funcionario,
            'listar_utilizadores': self.admin.listar_utilizadores,
            'add_product': self.admin.adicionar_produto,
            'editar_produto': self.admin.editar_produto,
            'deletar_produto': self.admin.deletar_produto,
            'listar_categorias': (lambda: self._executar_comando_generico('listar_categorias')),
            'listar_nomes_produtos': (lambda: self._executar_comando_generico('listar_nomes_produtos')),
            'listar_descricoes': (lambda: self._executar_comando_generico('listar_descricoes')),
            # fallback: outros comandos serão executados genericamente
        }

        # Para cada categoria, criar submenu (exceto autenticação)
        for categoria, lista_cmds in comandos.items():
            if categoria.lower() == 'autenticacao':
                continue

            nome_categoria = categoria.capitalize()
            opcoes_da_categoria = []
            for cmd in lista_cmds:
                func_local = mapa_comandos.get(cmd)
                if func_local:
                    opcoes_da_categoria.append((cmd, func_local))
                else:
                    opcoes_da_categoria.append((cmd, (lambda c=cmd: self._executar_comando_generico(c))))

            if opcoes_da_categoria:
                def criar_submenu(opcoes, title):
                    def abrir_submenu():
                        InterfaceUtilizador.exibir_menu(title, opcoes, sair_texto="Voltar")
                    return abrir_submenu
                opcoes_menu.append((nome_categoria, criar_submenu(opcoes_da_categoria, nome_categoria)))

        # Sempre adicionar utilitários locais essenciais
        def abrir_utilitarios():
            InterfaceUtilizador.exibir_menu('Utilitários', [
                ('Alterar Senha', self.auth.alterar_senha),
                ('Editar Username', self.auth.editar_username),
                ('Apagar Conta', self.auth.apagar_utilizador)
            ], sair_texto='Voltar')
        
        opcoes_menu.append(('Utilitários', abrir_utilitarios))

        # Terminar Sessão como opção final
        opcoes_menu.append(('Terminar Sessão', self.auth.terminar_sessao))
        
        InterfaceUtilizador.exibir_menu(titulo, opcoes_menu, sair_texto="Sair da Aplicação")


    def iniciar(self):
        InterfaceUtilizador.limpar()
        InterfaceUtilizador.mostrar_info("A conectar ao servidor...")
        
        # Tentativa de reconexão simples
        tentativas = 0
        conectado = False
        while tentativas < 2:
            if self.verificar_conexao_inicial():
                conectado = True
                break
            
            InterfaceUtilizador.mostrar_aviso("A tentar reconectar em 3 segundos...")
            time.sleep(3)
            tentativas += 1
        
        if not conectado:
            InterfaceUtilizador.mostrar_erro("Falha crítica de conexão. O programa será encerrado.")
            return

        # Loop principal da aplicação
        while True:
            self.atualizar_permissoes()
            
            if not self.sessao.esta_logado():
                self.menu_inicial()
            else:
                self.menu_principal()

def run(host='127.0.0.1', port=5000, debug=False):
    app = AplicacaoCliente(host, port, debug)
    try:
        app.iniciar()
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as erro:
        print(f"\n{Cores.VERMELHO}Erro fatal no cliente: {erro}{Cores.NORMAL}")

if __name__ == '__main__':
    run()