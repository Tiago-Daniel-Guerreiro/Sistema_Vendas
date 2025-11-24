import json
import socketserver
import threading
import socket
import os
from database import DatabaseManager
from entities import User, Admin, Vendedor, Cliente, Produto
from enums import Mensagem, Cores

DEBUG = False
Ativar_Atalho_Limpar_BD = True  # Ctrl+Alt+P para limpar base de dados
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
    """Retorna comandos disponíveis por categoria baseado no tipo de utilizador"""
    
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
    # ações que requerem autenticação
    username = parametros.get('username')
    password = parametros.get('password')

    if username and password:
        user = User.login(bd, username, password) # tenta autenticar, mas fica none se falhar

    match acao:
        case 'ping':
            return 'pong'

        case 'help':
            return get_help_commands(user)

        case 'list_products':
            id_loja = parametros.get('store_id') # Pode ser None, se user == vendedor
            
            # Converter store_id para int se fornecido
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
            # Qualquer um pode listar lojas
            try:
                bd.cursor.execute("SELECT id, nome, localizacao FROM stores ORDER BY nome")
                lojas = bd.cursor.fetchall()
                return lojas
            except Exception:
                return []
        
        case 'buscar_produto_por_nome':
            # Busca produto por nome e loja
            nome_produto = parametros.get('nome_produto')
            store_id = parametros.get('store_id')
            
            if not nome_produto or not store_id:
                return Mensagem.CREDENCIAIS_INVALIDAS.name
            
            try:
                store_id = int(store_id)
                sql = """
                    SELECT p.id, pn.nome, c.nome as categoria, p.preco, p.stock, s.nome as loja
                    FROM products p
                    JOIN product_names pn ON p.product_name_id = pn.id
                    JOIN categories c ON p.category_id = c.id
                    JOIN stores s ON p.store_id = s.id
                    WHERE pn.nome = %s AND p.store_id = %s
                """
                bd.cursor.execute(sql, (nome_produto, store_id))
                produto = bd.cursor.fetchone()
                
                if produto:
                    produto['preco'] = float(produto['preco'])
                    return produto
                else:
                    return Mensagem.PRODUTO_NAO_ENCONTRADO.name
            except Exception:
                return Mensagem.ERRO_GENERICO.name

        case 'registar_cliente':
            username = parametros.get('username')
            password = parametros.get('password')

            if user is not None:
                return Mensagem.REGISTRO_INDISPONIVEL.name
            
            if not username or not password:
                return Mensagem.CREDENCIAIS_INVALIDAS.name
            
            resultado = Cliente.registar(bd, username, password)
            return resultado.name if isinstance(resultado, Mensagem) else resultado

        case 'autenticar':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            
            return {'utilizador': username, 'cargo': user.cargo}

        case 'promover_para_admin':
            if user is None:
                return Mensagem.LOGIN_INVALIDO.name

            chave = parametros.get('chave')

            if not chave or chave != Chave_De_Criacao_de_Admin:
                return Mensagem.PERMISSAO_NEGADA.name

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
            # Apenas admin pode criar funcionários
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            
            username_func = parametros.get('username_func')
            password_func = parametros.get('password_func')
            
            tipo = parametros.get('tipo')  # 'vendedor' ou 'admin'
            loja_id = parametros.get('loja_id')  # obrigatório para vendedor
            
            if not username_func or not password_func or not tipo:
                return Mensagem.CREDENCIAIS_INVALIDAS
            
            if tipo == 'vendedor' and not loja_id:
                return Mensagem.O_VENDEDOR_TEM_QUE_SER_ASSOCIADO_A_LOJA
            
            if tipo not in ['vendedor', 'admin']:
                return Mensagem.CARGO_INVALIDO
            
            try:
                if tipo == 'admin':
                     return Admin.registar(bd, username_func, password_func)
                else:
                    return Vendedor.registar(bd, username_func, password_func, loja_id)
            
            except Exception:
                bd.conn.rollback()
                return Mensagem.UTILIZADOR_JA_EXISTE

        case 'add_product':
            # só admin
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA.name
            
            nome = parametros.get('nome')
            categoria = parametros.get('categoria')
            descricao = parametros.get('descricao')
            preco = parametros.get('preco')
            stock = parametros.get('stock')
            loja = parametros.get('store_id')
            
            # Validar inputs numéricos
            try:
                if preco is not None:
                    preco = float(preco)
                if stock is not None:
                    stock = int(stock)
                if loja is not None:
                    loja = int(loja)
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS.name

            resultado = user.adicionar_produto(nome, categoria, descricao, preco, stock, loja)
            return resultado.name if isinstance(resultado, Mensagem) else resultado

        case 'realizar_venda':
            if user is None:
                return Mensagem.LOGIN_INVALIDO.name
            
            # cliente ou vendedor podem realizar venda (vendedor limitado via store_id na sua conta em entities)
            itens = parametros.get('itens')
            if not itens or not isinstance(itens, dict):
                return Mensagem.ERRO_PROCESSAMENTO.name
            
            # Validar que product_id e quantidade são numéricos
            try:
                itens_validados = {}
                for product_id, quantidade in itens.items():
                    pid = int(product_id)
                    qtd = int(quantidade)
                    if qtd <= 0:
                        return Mensagem.CREDENCIAIS_INVALIDAS.name
                    itens_validados[str(pid)] = qtd
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS.name
            
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
            
            # Admin pode editar qualquer produto, Vendedor apenas de sua loja
            if isinstance(user, Admin):
                result = user.atualizar_produto(product_id, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome, novo_id_da_loja)
            elif isinstance(user, Vendedor):
                result = user.atualizar_produto(product_id, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome)
            else:
                return Mensagem.ERRO_PERMISSAO
            
            return result if isinstance(result, Mensagem) else result

        case 'deletar_produto':
            # Só admin pode deletar
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            
            product_id = parametros.get('product_id')
            if not product_id:
                return Mensagem.NAO_ENCONTRADO
            
            resultado = user.remover_produto(product_id)
            return resultado if isinstance(resultado, Mensagem) else resultado

        case 'concluir_pedido':
            # Vendedor ou Admin conclui um pedido
            if not isinstance(user, Vendedor): # Admin herda de Vendedor
                return Mensagem.PERMISSAO_NEGADA
            
            order_id = parametros.get('order_id')
            if not order_id:
                return Mensagem.ERRO_PROCESSAMENTO
            
            resultado = user.concluir_pedido(order_id)
            return resultado if isinstance(resultado, Mensagem) else resultado

        case 'listar_pedidos':
            # Vendedor lista seus pedidos, com filtro opcional
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA
            
            filtro_status = parametros.get('filtro_status')
            return user.listar_pedidos(filtro_status)
        
        case 'verificar_stock_baixo':
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA.name
            return Vendedor.verificar_stock_baixo(bd)
        
        # Gestão de Lojas (Admin)
        case 'criar_loja':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA.name
            
            nome = parametros.get('nome')
            localizacao = parametros.get('localizacao')
            
            resultado = user.criar_loja(nome, localizacao)
            return resultado.name if isinstance(resultado, Mensagem) else resultado
        
        case 'editar_loja':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA.name
            
            store_id = parametros.get('store_id')
            novo_nome = parametros.get('novo_nome')
            nova_localizacao = parametros.get('nova_localizacao')
            
            if not store_id:
                return Mensagem.NAO_ENCONTRADO.name
            
            try:
                store_id = int(store_id)
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS.name
            
            resultado = user.editar_loja(store_id, novo_nome, nova_localizacao)
            return resultado.name if isinstance(resultado, Mensagem) else resultado
        
        case 'apagar_loja':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA.name
            
            store_id = parametros.get('store_id')
            if not store_id:
                return Mensagem.NAO_ENCONTRADO.name
            
            try:
                store_id = int(store_id)
            except (ValueError, TypeError):
                return Mensagem.CREDENCIAIS_INVALIDAS.name
            
            resultado = user.apagar_loja(store_id)
            return resultado.name if isinstance(resultado, Mensagem) else resultado
        
        case 'listar_utilizadores':
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA.name
            
            filtro_cargo = parametros.get('filtro_cargo')
            filtro_loja = parametros.get('filtro_loja')
            
            # Validar filtro_loja se fornecido
            if filtro_loja:
                try:
                    filtro_loja = int(filtro_loja)
                except (ValueError, TypeError):
                    filtro_loja = None
            
            resultado = user.listar_utilizadores(filtro_cargo, filtro_loja)
            return resultado
        
        case 'editar_username':
            if user is None:
                return Mensagem.LOGIN_INVALIDO.name
            
            novo_username = parametros.get('novo_username')
            if not novo_username:
                return Mensagem.CREDENCIAIS_INVALIDAS.name
            
            resultado = user.editar_username(novo_username)

            if isinstance(resultado, Mensagem):
                return resultado.name
            return resultado

        case 'listar_categorias':
            # Listar todas as categorias únicas
            try:
                bd_temp = DatabaseManager()
                if bd_temp.connect() and bd_temp.cursor is not None:
                    bd_temp.cursor.execute("SELECT DISTINCT nome FROM categories ORDER BY nome")
                    categorias = [row['nome'] for row in bd_temp.cursor.fetchall()]  # type: ignore
                    if bd_temp.conn:
                        bd_temp.conn.close()
                    return categorias
                return []
            except:
                return []
        
        case 'listar_nomes_produtos':
            # Listar todos os nomes de produtos únicos
            try:
                bd_temp = DatabaseManager()
                if bd_temp.connect() and bd_temp.cursor is not None:
                    bd_temp.cursor.execute("SELECT DISTINCT nome FROM product_names ORDER BY nome")
                    nomes = [row['nome'] for row in bd_temp.cursor.fetchall()]  # type: ignore
                    if bd_temp.conn:
                        bd_temp.conn.close()
                    return nomes
                return []
            except:
                return []
        
        case 'listar_descricoes':
            # Listar todas as descrições únicas
            try:
                bd_temp = DatabaseManager()
                if bd_temp.connect() and bd_temp.cursor is not None:
                    bd_temp.cursor.execute("SELECT DISTINCT descricao FROM descriptions ORDER BY descricao")
                    descricoes = [row['descricao'] for row in bd_temp.cursor.fetchall()]  # type: ignore
                    if bd_temp.conn:
                        bd_temp.conn.close()
                    return descricoes
                return []
            except:
                return []

        case _:
            return Mensagem.COMANDO_DESCONHECIDO.name

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
    if not Ativar_Atalho_Limpar_BD:
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

    if Ativar_Atalho_Limpar_BD:
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

