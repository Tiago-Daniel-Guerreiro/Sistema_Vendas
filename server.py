import json
import socketserver
import threading
import socket
import os
from database import DatabaseManager
from entities import User, Admin, Vendedor, Cliente, Produto
from enums import Mensagem, Cores

DEBUG = False
# DEBUG também ativa o atalho Ctrl+Alt+P para limpar base de dados
Chave_De_Criacao_de_Admin = "ESTA_SENHA_É_USADA_NA_CRIAÇÃO_DE_NOVOS_ADMIN_PROVAVELMENTE_SERÁ_REMOVIDA_DEPOIS_ESTA_SENHA_É_MUITO_GRANDE!"

class GestorComandos(socketserver.StreamRequestHandler):
    def _enviar_resposta(self, ok, resultado=None, erro=None):
        resposta = {'ok': ok}
        
        # Tratar caso especial: tupla (status_enum, dados)
        # Pedido pedente, {id_pedido, preço total}
        if isinstance(resultado, tuple) and len(resultado) == 2:
            status_enum, dados = resultado
            # Se o primeiro elemento for um Enum, converte para string
            if hasattr(status_enum, 'name'):
                resposta['resultado'] = [status_enum, dados]
            else:
                resposta['resultado'] = [status_enum, dados]
        elif resultado is not None:
            resposta['resultado'] = resultado
        
        if erro is not None:
            resposta['erro'] = erro
        
        try:
            Mensagem_json = json.dumps(resposta, ensure_ascii=False, default=str) + '\n'
            self.wfile.write(Mensagem_json.encode('utf-8'))
            self.wfile.flush()  # Garante que os dados são enviados imediatamente
        except Exception as e:
            print(f"Erro ao enviar resposta: {e}")
    
    def _receber_comando(self):
        bytes = self.rfile.readline() # Lê a linha da requesição
        if not bytes:
            return None
        try:
            parametos = json.loads(bytes.decode('utf-8')) # json loads convete os bytes para um dicionário
            if not isinstance(parametos, dict):
                return None
            
            global DEBUG
            if DEBUG:
                print(f"{Cores.CINZA}{parametos}{Cores.NORMAL}")

            return parametos
        except Exception as erro:
            self._enviar_resposta(False, erro=f'JSON inválido: {erro}')
            return None

    def handle(self): # nome padrão do socketserver para tratar requisições, que estamos a sobrescrever
        entrada = self._receber_comando()
        if entrada is None:
            return

        acao = entrada.get('acao')
        parametros = entrada.get('parametros', {}) # {} serve como valor padrão se não existir

        bd = DatabaseManager()
        if not bd.connect():
            self._enviar_resposta(False, erro='Falha ao conectar ao banco de dados')
            return

        try:
            resultado = Aplicar_Acao(bd, acao, parametros)
            self._enviar_resposta(True, resultado=resultado)
        except Exception as erro:
            self._enviar_resposta(False, erro=str(erro))
        finally: # Só termina o comando atual, não afetando outros comandos
            try:
                if bd.conn:
                    bd.conn.close()
            except:
                pass     

def get_help_commands(user):    
    # Comandos disponíveis sem autenticação
    public_commands = {
        'autenticacao': ['ping', 'help', 'registar_cliente', 'autenticar']
    }
    
    # Comandos apenas para clientes autenticados
    cliente_commands = {
        'compras': ['list_products', 'realizar_venda', 'ver_meu_historico'],
        'autenticacao': ['promover_para_admin'],
        'utilitarios': ['editar_senha']
    }
    
    # Comandos apenas para vendedores autenticados
    vendedor_commands = {
        'compras': ['list_products', 'realizar_venda', 'ver_meu_historico'],
        'pedidos': ['concluir_pedido', 'listar_pedidos', 'verificar_stock_baixo'],
        'administracao': ['editar_produto'],
        'autenticacao': ['promover_para_admin'],
        'utilitarios': ['editar_senha']
    }
    
    # Comandos apenas para admins autenticados
    admin_commands = {
        'autenticacao': ['criar_funcionario'],
        'compras': ['list_products', 'realizar_venda', 'ver_meu_historico'],
        'produtos': ['add_product', 'editar_produto', 'deletar_produto'],
        'pedidos': ['concluir_pedido'],
        'utilitarios': ['editar_senha']
    }
    
    # Retornar comandos baseado no tipo de utilizador
    if user is None:
        return {'categorias': public_commands}
    
    elif isinstance(user, Admin):
        all_commands = {**public_commands}
        for categoria, comandos in admin_commands.items():
            all_commands[categoria] = comandos
        return {'categorias': all_commands, 'cargo': 'admin'}
    
    elif isinstance(user, Vendedor):
        all_commands = {**public_commands}
        for categoria, comandos in vendedor_commands.items():
            all_commands[categoria] = comandos
        return {'categorias': all_commands, 'cargo': 'vendedor'}
    
    else:  # Cliente
        all_commands = {**public_commands}
        for categoria, comandos in cliente_commands.items():
            all_commands[categoria] = comandos
        return {'categorias': all_commands, 'cargo': 'cliente'}

def Aplicar_Acao(bd, acao, parametros):
    user = None
    username = parametros.get('username')
    password = parametros.get('password')
    if username and password:
        user = User.login(bd, username, password)

    match acao:
        case 'ping':
            return 'pong'
        case 'help':
            return get_help_commands(user)
        case 'list_products':
            id_loja = parametros.get('store_id')
            if id_loja is not None:
                try:
                    id_loja = int(id_loja)
                except (ValueError, TypeError):
                    id_loja = None
            filtros = {}
            if 'categoria' in parametros:
                filtros['categoria'] = parametros['categoria']
            if 'preco_max' in parametros:
                try:
                    filtros['preco_max'] = float(parametros['preco_max'])
                except (ValueError, TypeError):
                    pass
            return listar_produtos(user, id_loja, filtros)
        case 'listar_lojas':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            return user.listar_lojas()
        case 'registar_cliente':
            username = parametros.get('username')
            password = parametros.get('password')
            if user is not None:
                return Mensagem.REGISTRO_INDISPONIVEL
            if not username or not password:
                return Mensagem.CREDENCIAIS_INVALIDAS
            return Cliente.registar(bd, username, password)
        case 'autenticar':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            return {'utilizador': username, 'cargo': user.cargo}
        case 'promover_para_admin':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            chave = parametros.get('chave')
            if not chave or chave != Chave_De_Criacao_de_Admin:
                return Mensagem.PERMISSAO_NEGADA
            return user.promover_a_admin()
        case 'editar_senha':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            nova_senha = parametros.get('nova_senha')
            if not nova_senha:
                return Mensagem.CREDENCIAIS_INVALIDAS
            try:
                bd.cursor.execute("UPDATE users SET password = %s WHERE id = %s", (nova_senha, user.id))
                bd.conn.commit()
                return Mensagem.SUCESSO
            except Exception:
                bd.conn.rollback()
                return Mensagem.ERRO_GENERICO
        case 'criar_funcionario':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            username_func = parametros.get('username_func')
            password_func = parametros.get('password_func')
            tipo = parametros.get('tipo')
            loja_id = parametros.get('loja_id')
            if not username_func or not password_func or not tipo:
                return Mensagem.CREDENCIAIS_INVALIDAS
            if tipo == 'vendedor':
                if not loja_id:
                    return Mensagem.O_VENDEDOR_TEM_QUE_SER_ASSOCIADO_A_LOJA
                try:
                    loja_id = int(loja_id)
                except (ValueError, TypeError):
                    return Mensagem.CREDENCIAIS_INVALIDAS
            if tipo not in ['vendedor', 'admin']:
                return Mensagem.CARGO_INVALIDO
            try:
                if tipo == 'admin':
                    return Admin.registar(bd, username_func, password_func, store_id=None)
                else:
                    return Vendedor.registar(bd, username_func, password_func, loja_id)
            except Exception:
                bd.conn.rollback()
                return Mensagem.UTILIZADOR_JA_EXISTE
        case 'add_product':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            nome = parametros.get('nome')
            categoria = parametros.get('categoria')
            descricao = parametros.get('descricao')
            preco = parametros.get('preco')
            stock = parametros.get('stock')
            loja = parametros.get('store_id')
            try:
                if preco is not None:
                    preco = float(preco)
                if stock is not None:
                    stock = int(stock)
                if loja is not None:
                    loja = int(loja)
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS
            return user.adicionar_produto(nome, categoria, descricao, preco, stock, loja)
        case 'realizar_venda':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            itens = parametros.get('itens')
            if not itens or not isinstance(itens, dict):
                return Mensagem.ERRO_PROCESSAMENTO
            try:
                itens_validados = {}
                for product_id, quantidade in itens.items():
                    pid = int(product_id)
                    qtd = int(quantidade)
                    if qtd <= 0:
                        return Mensagem.CREDENCIAIS_INVALIDAS
                    itens_validados[str(pid)] = qtd
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS
            return user.realizar_venda(itens_validados)
        case 'ver_meu_historico':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            return user.ver_meu_historico()
        case 'editar_produto':
            product_id = parametros.get('product_id')
            novo_preco = parametros.get('novo_preco')
            novo_stock = parametros.get('novo_stock')
            nova_descricao = parametros.get('nova_descricao')
            novo_nome = parametros.get('novo_nome')
            nova_categoria = parametros.get('nova_categoria')
            novo_id_da_loja = parametros.get('novo_id_da_loja')
            if not product_id:
                return Mensagem.NAO_ENCONTRADO
            if isinstance(user, Admin):
                return user.atualizar_produto(product_id, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome, novo_id_da_loja)
            elif isinstance(user, Vendedor):
                return user.atualizar_produto(product_id, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome)
            else:
                return Mensagem.ERRO_PERMISSAO
        case 'deletar_produto':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            product_id = parametros.get('product_id')
            if not product_id:
                return Mensagem.NAO_ENCONTRADO
            return Produto.remover_produto(bd,product_id)
        case 'concluir_pedido':
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA
            order_id = parametros.get('order_id')
            if not order_id:
                return Mensagem.ERRO_PROCESSAMENTO
            return user.concluir_pedido(order_id)
        case 'listar_pedidos':
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA
            filtro_status = parametros.get('filtro_status')
            return user.listar_pedidos(filtro_status)
        case 'verificar_stock_baixo':
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA
            return Vendedor.verificar_stock_baixo(bd)
        case 'criar_loja':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            nome = parametros.get('nome')
            localizacao = parametros.get('localizacao')
            return user.criar_loja(nome, localizacao)
        case 'editar_loja':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            store_id = parametros.get('store_id')
            novo_nome = parametros.get('novo_nome')
            nova_localizacao = parametros.get('nova_localizacao')
            if not store_id:
                return Mensagem.NAO_ENCONTRADO
            try:
                store_id = int(store_id)
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS
            return user.editar_loja(store_id, novo_nome, nova_localizacao)
        case 'apagar_loja':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            store_id = parametros.get('store_id')
            if not store_id:
                return Mensagem.NAO_ENCONTRADO
            try:
                store_id = int(store_id)
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS
            return user.apagar_loja(store_id)

        case 'listar_utilizadores':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            filtro_cargo = parametros.get('filtro_cargo')
            filtro_loja = parametros.get('filtro_loja')
            if filtro_loja:
                try:
                    filtro_loja = int(filtro_loja)
                except (ValueError, TypeError):
                    filtro_loja = None
            return user.listar_utilizadores(filtro_cargo, filtro_loja)
        case 'editar_username':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            novo_username = parametros.get('novo_username')
            if not novo_username:
                return Mensagem.CREDENCIAIS_INVALIDAS
            resultado = user.editar_username(novo_username)
            if isinstance(resultado, Mensagem):
                return resultado
            return resultado
        case 'listar_categorias':
            return Produto.listar_categorias(bd)
        case 'listar_nomes_produtos':
            return Produto.listar_nomes_produtos(bd)
        case 'listar_descricoes':
            return Produto.listar_descricoes(bd)
        case 'apagar_utilizador':
            username = parametros.get('username')
            password = parametros.get('password')
            user = User.login(bd, username, password)
            if user is None:
                return 'NAO_ENCONTRADO'
            # Só permite apagar se for Cliente
            if isinstance(user, Cliente) and hasattr(user, 'remover_seguranca'):
                resultado = user.remover_seguranca()
                return resultado
            else:
                return Mensagem.ERRO_GENERICO
        case 'deletar_pedido':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            order_id = parametros.get('order_id')
            return user.deletar_pedido(order_id)
        case _:
            return Mensagem.COMANDO_DESCONHECIDO
            
def listar_produtos(user = None, id_loja = None, filtros_extras = None):
    try:
        bd = DatabaseManager()
        if not bd.connect() and bd.conn is None:
            print('Erro ao conectar BD')
            return []
        
        if id_loja is None and user is not None:
            if isinstance(user, Vendedor):
                id_loja = user.store_id

        produtos = Produto.listar_todos(bd, store_id=id_loja, filtros_extras=filtros_extras)
        if bd.conn is not None:
            bd.conn.close()
        return produtos
    except Exception as e:
        print(f'Erro ao listar produtos: {str(e)}')
        return []
    
def limpar_base_dados_servidor():
    try:
        # Só funciona quando o sistema está rodar em localhost por segurança (usado para testes)
        bd = DatabaseManager(limpar_base_de_dados=True) 
        # Cria uma nova conexão para limpar a base de dados
        if not bd.connect() and bd.conn is None:
            print('Erro ao conectar BD para limpar')
            return

        print('Base de dados limpa com sucesso!')
    except Exception as e:
        print(f'Erro ao limpar BD: {str(e)}')

def ativar_atalho_servidor():
    global DEBUG
    if not DEBUG:
        return

    print('Pressione Ctrl+Alt+P para limpar base de dados...')

    try:
        import win32api
        import win32con
        
        while True:
            try:
                # Verifica Ctrl+Alt+P
                if (win32api.GetKeyState(win32con.VK_CONTROL) < 0 and
                    win32api.GetKeyState(win32con.VK_MENU) < 0 and
                    win32api.GetKeyState(ord('P')) < 0):

                    print('Atalho Ctrl+Alt+P detectado!')
                    limpar_base_dados_servidor()
                    os._exit(0) # Finaliza o servidor após limpar a base de dados
            except ImportError: # se passou pela prima verifica só por garantia
                print("A função de limpar base de dados não está disponivel.")
                break
            except: 
                pass

    except ImportError:
        print("A função de limpar base de dados não está disponivel.")
    except Exception as e:
        print(f'Erro: {str(e)}')

def limpar_saida_servidor(mensagem):
    os.system('cls')
    print('\n' * 100) # Coloca 100 linhas em branco para simular uma Limpeza de ecrã
    print(f'{mensagem}')
    
def verificar_port_em_uso(ip, port):
    try:
        conexao_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        resultado = conexao_socket.connect_ex((ip, port))
        conexao_socket.close()
        return resultado == 0  # 0 significa que conseguiu conectar (port em uso)
    except:
        return False

def run_server(host, port, debug = False):
    global DEBUG
    DEBUG = debug
    # Verificar se servidor já está ativo
    if verificar_port_em_uso(host, port):
        print('A port já está a ser usada, tente novamente mais tarde ou feche a aplicação que a está a usar.')
        return
    
    if DEBUG:
        hotkey_thread = threading.Thread(target=ativar_atalho_servidor, daemon=True)
        hotkey_thread.start()

    try:
        server = socketserver.ThreadingTCPServer((host, port), GestorComandos)
        print(f'À espera de pedidos em {host}:{port}')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            limpar_saida_servidor(f"\n\n{Cores.ROXO}A aplicação foi interrompida pelo utilizador.{Cores.NORMAL}")
        except Exception as e:
            limpar_saida_servidor(f"{Cores.VERMELHO}{Cores.NEGRITO}Erro fatal: {e}{Cores.NORMAL}")
        finally:
            server.shutdown()
            server.server_close()
    except Exception as e:
        limpar_saida_servidor(f"{Cores.VERMELHO}{Cores.NEGRITO}Erro fatal ao iniciar o servidor: {e}{Cores.NORMAL}")

def run(host='127.0.0.1', port=5000, debug = False):
    run_server(host, port,debug)

if __name__ == '__main__': # Quando executado diretamente
    run_server(host='127.0.0.1', port=5000)

