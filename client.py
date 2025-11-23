import json
import socket
import os

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    Default = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def clear_screen():
    os.system('cls')

def send_command(comando_json, host='127.0.0.1', port=5000, timeout=5):
    dados_formatados = json.dumps(comando_json) + '\n'

    with socket.create_connection((host, port), timeout=timeout) as conexao_socket:
        conexao_socket.sendall(dados_formatados.encode('utf-8'))
        
        buffer_resposta = b'' # b'' significa que é uma string de bytes
        while True:
            pedaco_recebido = conexao_socket.recv(4096)
            if not pedaco_recebido:
                break
            buffer_resposta += pedaco_recebido
            if b'\n' in pedaco_recebido: # Linha completa recebida
                break
        
        linha_resposta = buffer_resposta.split(b'\n', 1)[0] # Pega até o primeiro \n
        try:
            return json.loads(linha_resposta.decode('utf-8'))
        except Exception:
            return {
                'ok': False, 
                'error': 'resposta_invalida', 
            }

def print_header(title: str):
    print(f"{Colors.HEADER}{title}{Colors.Default}")

def print_success(message: str):
    print(f"{Colors.GREEN}Correto - {message}{Colors.Default}")

def print_error(message: str):
    print(f"{Colors.RED}Errado - {message}{Colors.Default}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}Aviso - {message}{Colors.Default}")

def print_info(message: str):
    print(f"{Colors.CYAN}info - {message}{Colors.Default}")

def print_menu_option(number: str, description: str):
    print(f"  {number}) {description}")

def input_prompt(prompt: str) -> str:
    return input(f"{Colors.BLUE}{prompt}{Colors.Default}").strip()

def input_prompt_seguro(prompt: str):
    import getpass
    return getpass.getpass(f"{Colors.BLUE}{prompt}{Colors.Default}").strip()

class Session:
    def __init__(self):
        self.username = ''
        self.password = ''
        self.cargo = ''

    def is_logged_in(self) -> bool:
        return self.username == '' and self.password == ''

    def get_status(self) -> str:
        if self.is_logged_in():
            return f"Conectado como: {Colors.BOLD}{self.username}{Colors.Default} ({self.cargo or 'Cliente'})"
        return "Não conectado"

    def logout(self):
        self.username = None
        self.password = None
        self.cargo = None
        print_success("Sessão encerrada")

class MenuManager:
    def __init__(self, host='127.0.0.1', port=5000):
        self.host = host
        self.port = port
        self.session = Session()
        self.available_commands = {}  # Armazena comandos disponíveis

    def verificar_conexao(self):
        try:
            res = send_command({'action': 'ping'}, host=self.host, port=self.port, timeout=3)
            if res.get('ok'):
                return True
        except:
            pass
        return False

    def obter_comandos_disponiveis(self):
        try:
            # Se está logado, enviar credenciais para obter comandos autenticados
            if self.session.is_logged_in():
                resultado = send_command({
                    'action': 'help',
                    'params': {
                        'username': self.session.username,
                        'password': self.session.password
                    }
                }, host=self.host, port=self.port)
            else:
                # Se não está logado, obter comandos públicos
                res = send_command({'action': 'help'}, host=self.host, port=self.port)
            
            if res.get('ok'):
                self.available_commands = res.get('result', {}).get('categorias', {})
                return True
        except:
            pass
        return False

    def pode_acessar_menu(self, categoria):
        return categoria in self.available_commands

    def print_session_status(self):
        print(f"\n{Colors.YELLOW}Estado: {self.session.get_status()}{Colors.Default}")

    def mostrar_menu(self, titulo, opcoes, texto_sair="Sair"):
        clear_screen()
        print_header(titulo)
        self.print_session_status()
            
        for i, opcao in enumerate(opcoes):
            print_menu_option(str(i + 1), opcao)

        print_menu_option("0", texto_sair)

        opcao = input_prompt("\nEscolha uma opção: ")
        return opcao

    def menu_principal(self):
        # Verificar conexão ao iniciar
        while True:
            clear_screen()
            print_header("Sistema de Vendas")
            print_info("A verificar conexão com o servidor...")
            
            if self.verificar_conexao():
                break
            
            print_error("Erro: Tente novamente, o servidor não está a responder")
            input("Pressione ENTER para tentar de novo...")
        
        print_success("Conectado ao servidor!")
        print_info("A obter comandos disponíveis...")
        
        if not self.obter_comandos_disponiveis():
            print_warning("Aviso: Não foi possível obter lista de comandos")
        
        print_info("Bem-vindo!")
        input("Pressione ENTER...")
        
        while True:
            # Montar menu dinâmico baseado em permissões
            opcoes = []
            opcao_map = {}
            opcao_num = 1
            
            if self.pode_acessar_menu('autenticacao'):
                opcoes.append("Autenticação")
                opcao_map[str(opcao_num)] = 'autenticacao'
                opcao_num += 1
            
            if self.pode_acessar_menu('compras'):
                opcoes.append("Compras")
                opcao_map[str(opcao_num)] = 'compras'
                opcao_num += 1
            
            if self.pode_acessar_menu('administracao') or self.pode_acessar_menu('produtos'):
                opcoes.append("Administração")
                opcao_map[str(opcao_num)] = 'administracao'
                opcao_num += 1
            
            if self.pode_acessar_menu('utilitarios'):
                opcoes.append("Utilitários")
                opcao_map[str(opcao_num)] = 'utilitarios'
                opcao_num += 1
            
            opcao = self.mostrar_menu("Menu do Sistema de Vendas", opcoes, "Sair")
            
            menu_escolhido = opcao_map.get(opcao)
            
            if opcao == "0":
                print_info("Encerrando aplicação...")
                break
            elif menu_escolhido == 'autenticacao':
                self.menu_autenticacao()
            elif menu_escolhido == 'compras':
                if not self.session.is_logged_in():
                    print_error("Deve fazer login primeiro!")
                    input("Pressione ENTER...")
                else:
                    self.menu_compras()
            elif menu_escolhido == 'administracao':
                self.menu_administracao()
            elif menu_escolhido == 'utilitarios':
                self.menu_utilitarios()
            else:
                print_error("Opção inválida!")
                input("Pressione ENTER...")
    
    def menu_autenticacao(self):
        """Menu de autenticação"""
        while True:
            opcoes = []
            opcao_map = {}
            opcao_num = 1
            
            if not self.session.is_logged_in():
                # Mostrar apenas Login e Registar se NÃO estiver logado
                opcoes.append("Fazer Login")
                opcao_map[str(opcao_num)] = 'login'
                opcao_num += 1
                
                opcoes.append("Registar Conta")
                opcao_map[str(opcao_num)] = 'registar'
                opcao_num += 1
            else:
                # Mostrar opções do utilizador logado
                # Alterar Senha (sempre disponível se logado)
                opcoes.append("Alterar Senha")
                opcao_map[str(opcao_num)] = 'alterar_senha'
                opcao_num += 1
                
                # Mudar para Admin (se disponível no servidor)
                if any('promover_para_admin' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                    opcoes.append("Mudar para Admin")
                    opcao_map[str(opcao_num)] = 'promover_para_admin'
                    opcao_num += 1
                
                # Logout
                opcoes.append("Logout")
                opcao_map[str(opcao_num)] = 'logout'
                opcao_num += 1
            
            opcao = self.mostrar_menu("Menu de Autenticação", opcoes, "Voltar ao Menu Principal")
                        
            if opcao == "0":
                break

            match opcao_map.get(opcao):
                case 'login':
                    self.fazer_login()
                case'registar':
                    self.registar_cliente()
                case 'alterar_senha':
                    self.alterar_senha()
                case 'promover_para_admin':
                    self.promover_para_admin()
                case 'logout':
                    self.session.logout()
                    # Atualizar comandos disponíveis após logout
                    self.obter_comandos_disponiveis()
                case _:
                    print_error("Opção inválida!")
                    input("Pressione ENTER...")

    def menu_compras(self):
        """Menu de compras"""
        while True:
            opcoes = []
            opcao_map = {}
            opcao_num = 1
            
            # Verificar o que o servidor realmente devolve no help
            if any('list_products' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Listar Produtos")
                opcao_map[str(opcao_num)] = 'listar_produtos'
                opcao_num += 1
            
            if any('realizar_venda' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Comprar Produto")
                opcao_map[str(opcao_num)] = 'comprar_produto'
                opcao_num += 1
            
            if any('ver_meu_historico' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Ver Meu Histórico")
                opcao_map[str(opcao_num)] = 'ver_historico'
                opcao_num += 1
            
            if not opcoes:
                print_error("Sem permissões para acessar compras!")
                input("Pressione ENTER...")
                break
            
            opcao = self.mostrar_menu("Menu de Compras", opcoes, "Voltar ao Menu Principal")
                        
            if opcao == "0":
                break
            match opcao_map.get(opcao):
                case 'listar_produtos':
                    self.listar_produtos()
                case 'comprar_produto':
                    self.comprar_produto()
                case 'ver_historico':
                    self.ver_historico()
                case _:
                    print_error("Opção inválida!")
                    input("Pressione ENTER...")

    def menu_administracao(self):
        """Menu de administração"""
        if not self.session.is_logged_in():
            print_error("Deve fazer login primeiro!")
            input("Pressione ENTER...")
            return
        
        while True:
            opcoes = []
            opcao_map = {}
            opcao_num = 1
            
            # Verificar o que o servidor realmente devolve no help
            # Procurar em todas as categorias por 'criar_funcionario'
            if any('criar_funcionario' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Criar Funcionário")
                opcao_map[str(opcao_num)] = 'criar_funcionario'
                opcao_num += 1
            
            # Procurar por 'add_product' (criar produto)
            if any('add_product' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Adicionar Produto")
                opcao_map[str(opcao_num)] = 'add_product'
                opcao_num += 1
            
            # Procurar por 'editar_produto'
            if any('editar_produto' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Editar Produto")
                opcao_map[str(opcao_num)] = 'editar_produto'
                opcao_num += 1
            
            # Procurar por 'concluir_pedido'
            if any('concluir_pedido' in self.available_commands.get(categoria, []) for categoria in self.available_commands):
                opcoes.append("Concluir Pedido")
                opcao_map[str(opcao_num)] = 'concluir_pedido'
                opcao_num += 1

            if not opcoes:
                print_error("Sem permissões para acessar administração!")
                input("Pressione ENTER...")
                break
            
            opcao = self.mostrar_menu("Menu de Administração", opcoes, "Voltar ao Menu Principal")
            
            if opcao == "0":
                break
            match opcao_map.get(opcao):
                case 'criar_funcionario':
                    self.criar_funcionario()
                case 'add_product':
                    self.adicionar_produto()
                case 'editar_produto':
                    self.editar_produto()
                case 'concluir_pedido':
                    self.concluir_pedido()
                case _:
                    print_error("Opção inválida!")
                    input("Pressione ENTER...")

    def menu_utilitarios(self):
        """Menu de utilitários"""
        while True:
            opcoes = []
            opcao_map = {}
            opcao_num = 1
            
            # Sempre mostrar teste de conexão (ping é sempre disponível)
            if any('ping' in self.available_commands.get(cat, []) for cat in self.available_commands):
                opcoes.append("Teste de Conexão (Ping)")
                opcao_map[str(opcao_num)] = 'ping'
                opcao_num += 1
            
            # Adicionar opção para limpar tela
            opcoes.append("Limpar Tela")
            opcao_map[str(opcao_num)] = 'limpar_tela'
            opcao_num += 1
            
            opcao = self.mostrar_menu("Menu de Utilitários", opcoes, "Voltar ao Menu Principal")
            
            acao = opcao_map.get(opcao)
            
            if opcao == "0":
                break
            elif acao == 'ping':
                self.fazer_ping()
            elif acao == 'limpar_tela':
                clear_screen()
                continue
            else:
                print_error("Opção inválida!")
                input("Pressione ENTER...")


    # Funções de Autenticação 
    def fazer_login(self):
        """Login do utilizador"""
        clear_screen()
        print_header("Login:")
        
        try:
            username = input_prompt("Username: ")
            password = input_prompt_seguro("Password: ")
            
            if not username or not password:
                print_error("Username e password são obrigatórios!")
                input("Pressione ENTER...")
                return
            
            print_info("A processar...")
            
            res = send_command({
                'action': 'autenticar',
                'params': {'username': username, 'password': password}
            }, host=self.host, port=self.port)
            
            if res.get('ok'):
                self.session.username = username
                self.session.password = password
                self.session.cargo = res.get('result', {}).get('cargo', 'cliente')
                print_success(f"Login realizado com sucesso como: {username}")
                print_info(f"Cargo: {self.session.cargo}")
                
                # Atualizar comandos disponíveis após login
                print_info("A obter novos comandos disponíveis...")
                self.obter_comandos_disponiveis()
            else:
                print_error(f"Login inválido!")
        except Exception as e:
            print_error(f"Erro ao fazer login: {str(e)}")
        
        input("Pressione ENTER...")

    def registar_cliente(self):
        clear_screen()
        print_header("Registar Conta")
        
        try:
            username = input_prompt("Username: ")
            password = input_prompt_seguro("Password: ")
            password_conf = input_prompt_seguro("Confirmar Password: ")
            
            if not username or not password or not password_conf:
                print_error("Todos os campos são obrigatórios!")
                input("Pressione ENTER...")
                return
            
            if password != password_conf:
                print_error("As passwords não correspondem!")
                input("Pressione ENTER...")
                return
            
            print_info("A registar conta...")
            
            res = send_command({
                'action': 'registar_cliente',
                'params': {'username': username, 'password': password}
            }, host=self.host, port=self.port)
            
            if res.get('ok'):
                print_success(f"Conta criada com sucesso! Username: {username}")
                print_info("Pode agora fazer login com estas credenciais")
            else:
                print_error(f"Erro ao registar: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao registar: {str(e)}")
        
        input("Pressione ENTER...")

    def alterar_senha(self):
        clear_screen()
        print_header("Alterar Senha")
        
        try:
            senha_atual = input_prompt_seguro("Senha atual: ")
            senha_nova = input_prompt_seguro("Nova senha: ")
            senha_conf = input_prompt_seguro("Confirmar nova senha: ")
            
            if not senha_atual or not senha_nova or not senha_conf:
                print_error("Todos os campos são obrigatórios!")
                input("Pressione ENTER...")
                return
            
            if senha_nova != senha_conf:
                print_error("As novas senhas não correspondem!")
                input("Pressione ENTER...")
                return
            
            # Validar senha atual
            if senha_atual != self.session.password:
                print_error("Senha atual incorreta!")
                input("Pressione ENTER...")
                return
            
            print_info("A alterar senha...")
            
            res = send_command({
                'action': 'editar_senha',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password,
                    'nova_senha': senha_nova
                }
            }, host=self.host, port=self.port)
            
            if res.get('ok'):
                # Atualizar a senha na sessão
                self.session.password = senha_nova
                print_success("Senha alterada com sucesso!")
            else:
                print_error(f"Erro ao alterar senha: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao alterar senha: {str(e)}")
        
        input("Pressione ENTER...")

    def promover_para_admin(self):
        clear_screen()
        print_header("Mudar para Admin")
        
        try:
            if not self.session.is_logged_in():
                print_error("Deve fazer login primeiro!")
                input("Pressione ENTER...")
                return
            
            chave = input_prompt_seguro("Código de promoção: ")
            
            if not chave:
                print_error("Código de promoção é obrigatório!")
                return
            
            print_info("A processar promoção...")
            
            res = send_command({
                'action': 'promover_para_admin',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password,
                    'chave': chave
                }
            }, host=self.host, port=self.port)
            
            if res.get('ok'):
                self.session.cargo = 'admin'
                print_success(f"Parabéns! Promovido para admin com sucesso!")
                print_info("Os seus novos privilégios estão agora ativos")
                
                # Atualizar comandos disponíveis após promoção
                print_info("A obter novos comandos disponíveis...")
                self.obter_comandos_disponiveis()
            else:
                print_error(f"Erro: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao promover para admin: {str(e)}")
        
        input("Pressione ENTER...")

    # Funções de Compras
    def listar_produtos(self):
        clear_screen()
        print_header("LISTA DE PRODUTOS")
        
        try:
            resultado = send_command({'action': 'list_products'}, host=self.host, port=self.port)
            if resultado.get('ok'):
                products = resultado.get('result', [])
                if products:
                    for product in products:
                        self._print_product(product)
                else:
                    print_info("Nenhum produto disponível")
            else:
                print_error(f"Erro: {resultado.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao listar produtos: {str(e)}")
        
        input("Pressione ENTER...")

    def _print_product(self, product):
        print(f"\n{Colors.BOLD}ID: {Colors.Default}{product['id']}")
        print(f"{Colors.BOLD}Nome:{Colors.Default} {product['nome']}")
        print(f"{Colors.BOLD}Categoria:{Colors.Default} {product['categoria']}")
        print(f"{Colors.BOLD}Descrição:{Colors.Default} {product['descricao']}")
        print(f"{Colors.BOLD}Preço:{Colors.Default} €{product['preco']:.2f}")
        print(f"{Colors.BOLD}Stock:{Colors.Default} {product['stock']}")
        print(f"{Colors.BOLD}Loja:{Colors.Default} {product['loja']}")
        print("\n")

    def comprar_produto(self):
        clear_screen()
        print_header("Produtos")
        
        try:
            self.listar_produtos()

            print_header("Comprar Produto")

            try:
                pid = int(input_prompt("ID do produto: "))
                qty = int(input_prompt("Quantidade: "))
            except ValueError:
                print_error("ID e quantidade devem ser números!")
                return
            
            cmd = {
                'action': 'realizar_venda',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password,
                    'itens': {str(pid): qty}
                }
            }
            resultado = send_command(cmd, host=self.host, port=self.port)

            if resultado.get('ok'):
                res = resultado.get('result')
                # Tratar caso especial: lista com [status_name, dados]
                if isinstance(res, list) and len(res) == 2:
                    status_name, dados = res
                    print_success(f"Compra realizada com sucesso!")
                    print_info(f"ID do Pedido: {Colors.BOLD}{dados.get('order_id')}{Colors.Default}")
                    print_info(f"Valor Total: €{dados.get('total_price'):.2f}")
                    print_warning(f"Status: {status_name} - Aguardando confirmação do vendedor")
                else:
                    print_success(f"Compra realizada com sucesso! Status: {res}")
            else:
                print_error(f"Erro: {resultado.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao comprar produto: {str(e)}")
        
        input("Pressione ENTER...")

    def ver_historico(self):
        """Ver histórico de compras"""
        clear_screen()
        print_header("Histórico de Compras")
        
        try:
            cmd = {
                'action': 'ver_meu_historico',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password
                }
            }
            resultado = send_command(cmd, host=self.host, port=self.port)

            if resultado.get('ok'):
                historico = resultado.get('result', [])
                if historico:
                    for idx, item in enumerate(historico, 1):
                        self._print_order(idx, item)
                else:
                    print_info("Nenhuma compra registada")
            else:
                print_error(f"Erro: {resultado.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao obter histórico: {str(e)}")
        
        input("Pressione ENTER...")

    def _print_order(self, idx, order):
        """Formata e imprime uma encomenda"""
        print(f"\n{Colors.BOLD}Encomenda #{idx}{Colors.Default}")
        print(f"  Data: {order.get('order_date', 'N/A')}")
        print(f"  Produto: {order.get('produto', 'N/A')} (ID: {order.get('product_id')})")
        print(f"  Quantidade: {order.get('quantity')}")
        print(f"  Preço unitário: €{order.get('unit_price', 0):.2f}")
        print(f"  Total: €{order.get('quantity', 0) * order.get('unit_price', 0):.2f}")
        print(f"  Loja: {order.get('loja', 'N/A')}")
        print(f"  Status: {Colors.YELLOW}{order.get('status', 'N/A').upper()}{Colors.Default}")
        print("\n")

    # Funções de Administração
    def criar_funcionario(self):
        """Cria um novo funcionário (vendedor ou admin)"""
        clear_screen()
        print_header("Criar Funcionário")
        
        try:
            if not self.session.is_logged_in():
                print_error("Deve fazer login como admin primeiro!")
                input("Pressione ENTER...")
                return
            
            username = input_prompt("Username: ")
            password = input_prompt_seguro("Password: ")
            
            # Pergunta o tipo de funcionário
            print_menu_option("1", "Vendedor (com loja)")
            print_menu_option("2", "Admin")
            tipo_choice = input_prompt("Escolha o tipo: ")
            
            loja_id = None
            if tipo_choice == "1":
                tipo = "vendedor"
                try:
                    loja_id = int(input_prompt("ID da loja: "))
                except ValueError:
                    print_error("ID da loja deve ser um número!")
                    return
            elif tipo_choice == "2":
                tipo = "admin"
            else:
                print_error("Opção inválida!")
                return
            
            if not username or not password:
                print_error("Username e password são obrigatórios!")
                return
            
            params = {
                'username': self.session.username,
                'password': self.session.password,
                'username_func': username,
                'password_func': password,
                'tipo': tipo
            }
            
            if tipo == 'vendedor':
                params['loja_id'] = loja_id
            
            res = send_command({
                'action': 'criar_funcionario',
                'params': params
            }, host=self.host, port=self.port)
            
            if res.get('ok'):
                resultado = res.get('result', {})
                print_success(f"Funcionário criado com sucesso!")
                print_info(f"Username: {resultado.get('created')}")
                print_info(f"Tipo: {resultado.get('cargo')}")
                if resultado.get('loja'):
                    print_info(f"Loja: {resultado.get('loja')}")
            else:
                print_error(f"Erro: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao criar funcionário: {str(e)}")
        
        input("Pressione ENTER...")

    def concluir_pedido(self):
        """Conclui um pedido"""
        clear_screen()
        print_header("CONCLUIR PEDIDO")
        
        try:
            if not self.session.is_logged_in():
                print_error("Deve fazer login primeiro!")
                input("Pressione ENTER...")
                return
            
            try:
                oid = int(input_prompt("Order ID a concluir: "))
            except ValueError:
                print_error("ID deve ser um número!")
                return
            
            cmd = {
                'action': 'concluir_pedido',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password,
                    'order_id': oid
                }
            }
            res = send_command(cmd, host=self.host, port=self.port)
            
            if res.get('ok'):
                print_success(f"Pedido concluído! Status: {res.get('result')}")
            else:
                print_error(f"Erro: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao concluir pedido: {str(e)}")
        
        input("Pressione ENTER...")

    def editar_produto(self):
        """Edita um produto (Admin/Vendedor)"""
        clear_screen()
        print_header("EDITAR PRODUTO")
        
        try:
            if not self.session.is_logged_in():
                print_error("Deve fazer login primeiro!")
                input("Pressione ENTER...")
                return
            
            # Listar produtos primeiro
            self.listar_produtos()
            
            clear_screen()
            print_header("EDITAR PRODUTO")
            
            try:
                pid = int(input_prompt("ID do produto a editar: "))
            except ValueError:
                print_error("ID deve ser um número!")
                return
            
            # Solicitar dados a editar (opcional)
            novo_preco_str = input_prompt("Novo preço (deixar em branco para manter): ")
            novo_stock_str = input_prompt("Novo stock (deixar em branco para manter): ")
            nova_descricao = input_prompt("Nova descrição (deixar em branco para manter): ")
            
            cmd = {
                'action': 'editar_produto',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password,
                    'product_id': pid,
                    'novo_preco': float(novo_preco_str) if novo_preco_str else None,
                    'novo_stock': int(novo_stock_str) if novo_stock_str else None,
                    'nova_descricao': nova_descricao if nova_descricao else None
                }
            }
            res = send_command(cmd, host=self.host, port=self.port)
            
            if res.get('ok'):
                print_success(f"Produto editado com sucesso! Status: {res.get('result')}")
            else:
                print_error(f"Erro: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao editar produto: {str(e)}")
        
        input("Pressione ENTER...")

    def adicionar_produto(self):
        """Adiciona um novo produto (Admin only)"""
        clear_screen()
        print_header("ADICIONAR PRODUTO")
        
        try:
            if not self.session.is_logged_in():
                print_error("Deve fazer login primeiro!")
                input("Pressione ENTER...")
                return
            
            nome = input_prompt("Nome do produto: ")
            categoria = input_prompt("Categoria: ")
            descricao = input_prompt("Descrição: ")
            
            try:
                preco = float(input_prompt("Preço: "))
                stock = int(input_prompt("Stock: "))
                store_id = int(input_prompt("ID da loja: "))
            except ValueError:
                print_error("Preço deve ser número, stock e loja devem ser inteiros!")
                return
            
            if not nome or not categoria or not descricao:
                print_error("Todos os campos são obrigatórios!")
                return
            
            cmd = {
                'action': 'add_product',
                'params': {
                    'username': self.session.username,
                    'password': self.session.password,
                    'nome': nome,
                    'categoria': categoria,
                    'descricao': descricao,
                    'preco': preco,
                    'stock': stock,
                    'store_id': store_id
                }
            }
            res = send_command(cmd, host=self.host, port=self.port)
            
            if res.get('ok'):
                print_success(f"Produto adicionado com sucesso! Status: {res.get('result')}")
            else:
                print_error(f"Erro: {res.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro ao adicionar produto: {str(e)}")
        
        input("Pressione ENTER...")

    def fazer_ping(self):
        clear_screen()
        
        try:
            print_info("A testar conexão...")
            resultado = send_command({'action': 'ping'}, host=self.host, port=self.port)
            if resultado.get('ok'):
                print_success(f"Servidor respondeu: {resultado.get('result')}")
            else:
                print_error(f"Erro: {resultado.get('error', 'Desconhecido')}")
        except Exception as e:
            print_error(f"Erro de conexão: {str(e)}")
        
        input("Pressione ENTER...")

def interactive_menu(host='127.0.0.1', port=5000):
    manager = MenuManager(host=host, port=port)
    manager.menu_principal()

if __name__ == '__main__':
    try:
        interactive_menu()
    except KeyboardInterrupt:
        print('\n' * 100)
        print(f'A fechar o Cliente.')
    except Exception as e:
        print(f"\n{Colors.RED}Erro fatal: {str(e)}{Colors.Default}")
