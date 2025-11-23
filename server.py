import json
import socketserver
import threading
import socket
from database import DatabaseManager
from entities import User, Admin, Vendedor, Cliente, Produto
from enums import Mensagem

Ativar_Atalho_Limpar_BD = True  # Ctrl+Alt+P para limpar base de dados
Chave_De_Criacao_de_Admin = "ESTA_SENHA_É_USADA_NA_CRIAÇÃO_DE_NOVOS_ADMIN_PROVAVELMENTE_SERÁ_REMOVIDA_DEPOIS_ESTA_SENHA_É_MUITO_GRANDE!"

class GestorComandos(socketserver.StreamRequestHandler):
    def _enviar_resposta(self, ok, resultado=None, erro=None):
        resposta = {'ok': ok}
        
        # Tratar caso especial: tupla (status_enum, dados)
        # Pedido pedente, {id_pedido, preço total}
        if isinstance(resultado, tuple) and len(resultado) == 2:
            status_enum, dados = resultado
            resposta['resultado'] = [status_enum.name, dados]
        elif resultado is not None:
            resposta['resultado'] = resultado
        
        if erro is not None:
            resposta['erro'] = erro
        
        Mensagem = json.dumps(resposta, ensure_ascii=False, default=str) + '\n'
        self.wfile.write(Mensagem.encode()) # Enviar resposta como bytes
    
    def _receber_comando(self):
        bytes = self.rfile.readline() # Lê a linha da requesição
        if not bytes:
            return None
        
        try:
            params = json.loads(bytes.decode('utf-8')) # json loads convete os bytes para um dicionário
            if not isinstance(params, dict):
                return None
            
            return params
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
        'pedidos': ['confirmar_pedido', 'listar_pedidos'],
        'administracao': ['editar_produto'],
        'autenticacao': ['promover_para_admin'],
        'utilitarios': ['editar_senha']
    }
    
    # Comandos apenas para admins autenticados
    admin_commands = {
        'autenticacao': ['criar_funcionario'],
        'compras': ['list_products', 'realizar_venda', 'ver_meu_historico'],
        'produtos': ['add_product', 'editar_produto', 'deletar_produto'],
        'pedidos': ['concluir_pedido_admin'],
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
            return listar_produtos(user, id_loja) # listar produtos com possível filtro por loja, e pela loja do vendedor

        case 'registar_cliente':
            username = parametros.get('username')
            password = parametros.get('password')

            if user is not None:
                return Mensagem.REGISTRO_INDISPONIVEL
            
            if not username or not password:
                return Mensagem.CREDENCIAIS_INVALIDAS
            
            try:
                bd.cursor.execute("INSERT INTO users (username, password, role_type) VALUES (%s, %s, 'cliente')", (username, password))
                bd.conn.commit()
                return Mensagem.UTILIZADOR_CRIADO
            except Exception:
                bd.conn.rollback()
                return Mensagem.UTILIZADOR_JA_EXISTE

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
            
            if isinstance(user, Admin):
                return Mensagem.O_PERFIL_JA_E_ADMIN
            
            try:
                bd.cursor.execute("UPDATE users SET role_type = 'admin' WHERE id = %s", (user.id,)) # "," pois é uma tupla
                bd.conn.commit()
                return Mensagem.SUCESSO
            except Exception:
                bd.conn.rollback()
                return Mensagem.ERRO_GENERICO
            
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
                return Mensagem.PERMISSAO_NEGADA
            
            nome = parametros.get('nome')
            categoria = parametros.get('categoria')
            descricao = parametros.get('descricao')
            preco = parametros.get('preco')
            stock = parametros.get('stock')
            loja = parametros.get('store_id')

            return user.adicionar_produto(nome, categoria, descricao, preco, stock, loja)

        case 'realizar_venda':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
            
            # cliente ou vendedor podem realizar venda (vendedor limitado via store_id na sua conta em entities)
            itens = parametros.get('itens')
            if not itens or not isinstance(itens, dict):
                return Mensagem.ERRO_PROCESSAMENTO
            
            return user.realizar_venda(itens)

        case 'ver_meu_historico':
            if user is None:
                return Mensagem.LOGIN_INVALIDO
        
            return user.ver_meu_historico()

        case 'editar_produto':
            product_id = parametros.get('product_id')
            novo_preco = parametros.get('novo_preco')
            novo_stock = parametros.get('novo_stock')
            nova_descricao = parametros.get('nova_descricao')

            if not product_id:
                return Mensagem.NAO_ENCONTRADO
            
            # Admin pode editar qualquer produto, Vendedor apenas de sua loja
            if isinstance(user, Admin):
                result = user.atualizar_produto(product_id, novo_preco, novo_stock, nova_descricao)
            elif isinstance(user, Vendedor):
                result = user.atualizar_produto(product_id, novo_preco, novo_stock, nova_descricao)
            else:
                return Mensagem.ERRO_PERMISSAO
            
            return result

        case 'deletar_produto':
            # Só admin pode deletar
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            
            product_id = parametros.get('product_id')
            if not product_id:
                return Mensagem.NAO_ENCONTRADO
            
            return user.remover_produto(product_id)

        case 'confirmar_pedido':
            # Vendedor confirma um pedido pendente
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA
            
            order_id = parametros.get('order_id')
            if not order_id:
                return Mensagem.ERRO_PROCESSAMENTO
            
            return user.concluir_pedido(order_id)

        case 'listar_pedidos':
            # Vendedor lista seus pedidos, com filtro opcional
            if not isinstance(user, Vendedor):
                return Mensagem.PERMISSAO_NEGADA
            
            filtro_status = parametros.get('filtro_status')
            return user.listar_pedidos(filtro_status)

        case 'concluir_pedido_admin':
            # Admin conclui um pedido (deve estar confirmado)
            if not isinstance(user, Admin):
                return Mensagem.PERMISSAO_NEGADA
            
            order_id = parametros.get('order_id')
            if not order_id:
                return Mensagem.ERRO_PROCESSAMENTO
            
            return user.concluir_pedido(order_id)
        
        case _:
            return Mensagem.COMANDO_DESCONHECIDO

def listar_produtos(user = None, id_loja = None):
    try:
        bd = DatabaseManager()
        if not bd.connect() is None or bd.conn is None:
            print('Erro ao conectar BD')
            return []
        
        if id_loja is None and user is not None:
            if isinstance(user, Vendedor):
                id_loja = user.store_id

        if id_loja is None:
            produtos = Produto.listar_todos(bd)
        else:
            produtos = Produto.listar_todos(bd, f" WHERE p.store_id = {id_loja}")

        bd.conn.close()
        return produtos
    except Exception as e:
        print(f'Erro ao listar produtos: {str(e)}')
        return []
    
def limpar_base_dados_servidor():
    """Limpa a base de dados (chamado pelo hotkey)"""
    try:
        bd = DatabaseManager()
        if not bd.connect():
            print('Erro ao conectar BD')
            return
        
        if bd.cursor and bd.conn:
            # Obtém todos os nomes de tabelas
            bd.cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tabelas = bd.cursor.fetchall()

            for tabela in tabelas:
                bd.cursor.execute(f'DROP TABLE IF EXISTS "{tabela}" CASCADE')
            bd.conn.commit()
            bd.conn.close()
        
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
                    exit() # Finaliza o servidor após limpar a base de dados
            except:
                pass
    except Exception as e:
        print(f'Erro: {str(e)}')

def limpar_saida_servidor(mensagem):
    """Imprime 100 quebras de linha seguidas de uma mensagem"""
    print('\n' * 100)
    print(f'{mensagem}')
    
def verificar_porta_em_uso(ip, porta):
    try:
        conexao_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        resultado = conexao_socket.connect_ex((ip, porta))
        conexao_socket.close()
        return resultado == 0  # 0 significa que conseguiu conectar (porta em uso)
    except:
        return False

def run_server(host='127.0.0.1', port=5000):
    # Verificar se servidor já está ativo
    if verificar_porta_em_uso(host, port):
        print('A porta já está a ser usada, tente novamente mais tarde ou feche a aplicação que a está a usar.')
        return
    
    if Ativar_Atalho_Limpar_BD: # Serve para testes, para conseguir limpar a base de dados rapidamente
        hotkey_thread = threading.Thread(target=ativar_atalho_servidor, daemon=True)
        hotkey_thread.start()
    
    server = socketserver.ThreadingTCPServer((host, port), GestorComandos) # chama automaticamente o "handle"
    print(f'À espera de pedidos em {host}:{port}')
    try:
        server.serve_forever() # Inicia o loop do servidor
    except KeyboardInterrupt:
        limpar_saida_servidor('Servidor a encerrar.')
    except Exception as e:
        print(f'Erro: {str(e)}\nServidor a encerrar.')
    finally:
        server.shutdown()
        server.server_close()

if __name__ == '__main__':
    run_server()
