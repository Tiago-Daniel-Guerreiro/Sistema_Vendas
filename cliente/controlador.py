import consola
from enums import Cores
from cliente.interface_cliente import Interface

class ControladorGenerico:
    def __init__(self, rede, sessao, processador_respostas):
        self.rede = rede
        self.sessao = sessao
        self.processador_respostas = processador_respostas

    def executar_comando(self, nome_comando, parametros_predefinidos=None):
        info_comando = self.sessao.comandos_por_nome.get(nome_comando)

        if info_comando is None:
            consola.erro(
                f"Comando '{nome_comando}' não reconhecido ou não permitido."
            )
            return

        parametros_para_servidor = self.sessao.obter_credenciais()

        if parametros_predefinidos is not None:
            parametros_para_servidor.update(parametros_predefinidos)

        parametros_definidos_no_comando = info_comando.get('parametros', {})

        # Pede ao utilizador os parâmetros obrigatórios que ainda não foram fornecidos.
        for nome_parametro, configuracao_parametro in parametros_definidos_no_comando.items():
            parametro_obrigatorio = configuracao_parametro.get('obrigatorio')
            parametro_ja_definido = nome_parametro in parametros_para_servidor

            if parametro_obrigatorio is True and parametro_ja_definido is False:
                valor_parametro = consola.ler_texto(
                    f"Parâmetro '{nome_parametro}':"
                )
                parametros_para_servidor[nome_parametro] = valor_parametro

        resposta = self.rede.enviar_comando(
            nome_comando,
            parametros_para_servidor
        )
        self.processador_respostas(resposta, info_comando)

class ControladorAutenticacao:
    def __init__(self, rede, sessao):
        self.rede = rede
        self.sessao = sessao

    def _carregar_comandos_disponiveis(self, token_sessao):
        # Após autenticação, pede ao servidor a lista de comandos disponíveis
        # para o utilizador autenticado e guarda-os na sessão.
        resposta_help = self.rede.enviar_comando(
            'help',
            {'token_sessao': token_sessao}
        )

        if resposta_help is None:
            consola.aviso("Não foi possível carregar comandos do servidor.")
            return
        
        if resposta_help.get('ok') is False:
            consola.aviso(f"Erro ao carregar comandos: {resposta_help.get('erro', 'desconhecido')}")
            return

        resultado = resposta_help.get('resultado', {})
        comandos_agrupados = resultado.get('comandos', {})

        comandos_por_nome = {}

        for lista_comandos in comandos_agrupados.values():
            for informacao_comando in lista_comandos:
                nome_comando = informacao_comando.get('comando')

                if nome_comando is not None and len(nome_comando) > 0:
                    comandos_por_nome[nome_comando] = informacao_comando

        self.sessao.definir_comandos_disponiveis(comandos_por_nome)
        consola.info_adicional(f"Carregados {len(comandos_por_nome)} comandos disponíveis.")

    def iniciar_sessao_guardada(self):
        contas_guardadas = self.sessao.tokens_locais

        if contas_guardadas is None or len(contas_guardadas) == 0:
            consola.aviso(
                "Nenhuma sessão guardada. A avançar para login manual."
            )
            return self.iniciar_sessao_manual()

        utilizadores = list(contas_guardadas.keys())
        
        # Criar opções para o menu - cada opção é um utilizador
        opcoes = []
        for utilizador in utilizadores:
            # Criar uma função lambda que captura o utilizador
            def tentar_login(username=utilizador):
                return self._login_com_token(username, contas_guardadas[username])
            
            opcoes.append((utilizador, tentar_login))
        
        # Opção para fazer login com outra conta
        opcoes.append(("Iniciar sessão com outra conta", self.iniciar_sessao_manual))
        
        # Exibir menu e capturar resultado (True se login bem-sucedido)
        resultado = Interface.exibir_menu("Iniciar Sessão", opcoes, "Voltar")
        return resultado

    def _login_com_token(self, utilizador_escolhido, token_guardado):
        resposta = self.rede.enviar_comando(
            'autenticar',
            {
                'token_sessao': token_guardado,
                'username': utilizador_escolhido
            }
        )

        if resposta is None:
            consola.erro("Falha na comunicação com o servidor.")
            return self.iniciar_sessao_manual(
                utilizador_preenchido=utilizador_escolhido
            )

        if resposta.get('ok') is True:
            resultado = resposta.get('resultado', {})

            self.sessao.iniciar_sessao(
                utilizador_escolhido,
                resultado.get('cargo'),
                token_guardado
            )

            self._carregar_comandos_disponiveis(token_guardado)

            consola.sucesso(
                f"Sessão iniciada como {utilizador_escolhido} "
                f"({self.sessao.cargo})."
            )
            return True

        erro = resposta.get('erro', 'Token inválido ou expirado')
        consola.erro(f"{erro}")
        return self.iniciar_sessao_manual(
            utilizador_preenchido=utilizador_escolhido
        )

    def iniciar_sessao_manual(self, utilizador_preenchido=None):
        if utilizador_preenchido is None or len(utilizador_preenchido) == 0:
            Interface.mostrar_cabecalho("Login Manual")
            utilizador = consola.ler_texto("Utilizador:")
        else:
            utilizador = utilizador_preenchido

        senha = consola.ler_senha("Palavra-passe:")

        if senha is None:
            return False

        resposta = self.rede.enviar_comando(
            'autenticar',
            {
                'username': utilizador,
                'password': senha
            }
        )

        if resposta is None:
            consola.erro("Falha na comunicação com o servidor.")
            return False

        if resposta.get('ok') is True:
            resultado = resposta.get('resultado', {})
            token_novo = resultado.get('token')

            self.sessao.iniciar_sessao(
                utilizador,
                resultado.get('cargo'),
                token_novo
            )

            self.rede.guardar_token_local(utilizador, token_novo)
            self._carregar_comandos_disponiveis(token_novo)

            consola.sucesso(
                f"Sessão iniciada como {utilizador} ({self.sessao.cargo})."
            )
            return True

        erro = resposta.get('erro', 'Erro desconhecido')
        
        # Traduzir códigos de erro comuns
        if erro == 'CREDENCIAIS_INVALIDAS':
            consola.erro("Utilizador ou senha incorretos.")
        elif erro == 'LOGIN_INVALIDO':
            consola.erro("Credenciais inválidas.")
        elif erro == 'ERRO_GENERICO':
            consola.erro("Credenciais inválidas. Verifique o utilizador e senha.")
        else:
            consola.erro(f"Falha no login: {erro}")
        
        return False
        return False

    def registar_conta(self):
        Interface.mostrar_cabecalho("Criar Nova Conta de Cliente")

        utilizador = consola.ler_texto("Nome de utilizador:")
        senha_primeira = consola.ler_senha("Palavra-passe:")

        if senha_primeira is None:
            return

        senha_confirmacao = consola.ler_senha("Confirme a palavra-passe:")

        if senha_confirmacao is None:
            return

        if senha_primeira != senha_confirmacao:
            consola.erro("As palavras-passe não coincidem.")
            return

        resposta = self.rede.enviar_comando(
            'registar',
            {
                'username': utilizador,
                'password': senha_primeira
            }
        )

        if resposta is None:
            consola.erro("Falha na comunicação com o servidor.")
            return

        if resposta.get('ok') is True:
            consola.sucesso(
                "Conta criada com sucesso! Pode agora iniciar sessão."
            )
        else:
            erro = resposta.get('erro', 'Erro desconhecido')
            
            # Traduzir códigos de erro comuns
            if erro == 'UTILIZADOR_JA_EXISTE':
                consola.erro("Esse nome de utilizador já está em uso.")
            else:
                consola.erro(f"Falha no registo: {erro}")

    def encerrar_sessao(self):
        self.rede.remover_token_local(self.sessao.nome_utilizador)
        self.sessao.encerrar_sessao()
        consola.sucesso("Sessão encerrada com sucesso.")
        return False  # Retorna False para voltar ao menu de autenticação

    def editar_username(self):
        Interface.mostrar_cabecalho("Editar Username")
        
        consola.info(f"Username atual: {self.sessao.nome_utilizador}\n")
        
        novo_username = consola.ler_texto("Novo Username:")
        
        if not novo_username:
            consola.erro("Username não pode estar vazio.")
            return
        
        # Confirmação
        confirmacao = consola.ler_texto(
            f"Alterar username para '{novo_username}'? (s/n):"
        )
        
        if confirmacao.lower() != 's':
            consola.info("Operação cancelada.")
            return
        
        resposta = self.rede.enviar_comando(
            'editar_nome_utilizador',
            {
                'token_sessao': self.sessao.token_sessao,
                'novo_username': novo_username
            }
        )
        
        if resposta is not None and resposta.get('ok') is True:
            resultado = resposta.get('resultado', '')
            
            if resultado == 'ATUALIZADO':
                consola.sucesso("Username atualizado com sucesso!")
                consola.info(
                    "A encerrar sessão. Faça login com o novo username."
                )
                # Forçar logout e voltar ao menu de autenticação
                self.rede.remover_token_local(self.sessao.nome_utilizador)
                self.sessao.encerrar_sessao()
                return False  # Volta ao menu de autenticação
            else:
                if resultado == 'UTILIZADOR_JA_EXISTE':
                    consola.erro("Username já está em uso por outro utilizador.")
                else:
                    consola.erro(f"{resultado}")
        else:
            consola.erro(
                f"Erro ao editar username: {resposta.get('erro')}"
            )

    def alterar_senha(self):
        Interface.mostrar_cabecalho("Alterar Senha")
        
        nova_senha = consola.ler_senha("Nova Senha:")
        
        if nova_senha is None:
            return
        
        confirmacao = consola.ler_senha("Confirmar Nova Senha:")
        
        if confirmacao is None:
            return
        
        if nova_senha != confirmacao:
            consola.erro("As senhas não coincidem.")
            return
        
        resposta = self.rede.enviar_comando(
            'editar_senha',
            {
                'token_sessao': self.sessao.token_sessao,
                'nova_senha': nova_senha
            }
        )
        
        if resposta is not None and resposta.get('ok') is True:
            consola.sucesso("Senha alterada com sucesso!")
            consola.info("A encerrar sessão por segurança. Faça login com a nova senha.")
            # Forçar logout e voltar ao menu de autenticação
            self.rede.remover_token_local(self.sessao.nome_utilizador)
            self.sessao.encerrar_sessao()
            return False  # Volta ao menu de autenticação
        else:
            consola.erro(
                f"Erro ao alterar senha: {resposta.get('erro')}"
            )

    def promover_para_admin(self):
        Interface.mostrar_cabecalho("Promover para Admin")
        
        chave = consola.ler_senha("Chave de Admin:")
        
        if chave is None:
            return
        
        resposta = self.rede.enviar_comando(
            'promover_para_admin',
            {
                'token_sessao': self.sessao.token_sessao,
                'chave': chave
            }
        )
        
        if resposta is not None and resposta.get('ok') is True:
            resultado = resposta.get('resultado', '')
            
            if resultado == 'SUCESSO':
                consola.sucesso(
                    "Promovido a Admin! "
                    "A encerrar sessão para atualizar permissões..."
                )
                # Forçar logout e voltar ao menu de autenticação
                self.rede.remover_token_local(self.sessao.nome_utilizador)
                self.sessao.encerrar_sessao()
                return False  # Volta ao menu de autenticação
            else:
                consola.erro(f"{resultado}")
        else:
            consola.erro(
                f"Erro ao promover: {resposta.get('erro')}"
            )

    def apagar_conta(self):
        Interface.mostrar_cabecalho("Apagar Conta")
        
        username = self.sessao.nome_utilizador
        
        consola.aviso(
            f"ATENÇÃO: Esta ação é IRREVERSÍVEL! "
            f"Todos os seus dados serão permanentemente apagados."
        )
        
        frase_correta = (
            f"Tenho a certeza {username} que pretendo apagar "
            f"a conta juntamente com todos os meus dados"
        )
        
        confirmacao = consola.ler_texto(
            f"\nPara confirmar, digite exatamente:\n'{frase_correta}'\n\n"
        )
        
        if confirmacao != frase_correta:
            consola.aviso("Confirmação incorreta. Operação cancelada.")
            return
        
        resposta = self.rede.enviar_comando(
            'apagar_utilizador',
            {'token_sessao': self.sessao.token_sessao}
        )
        
        if resposta is not None and resposta.get('ok') is True:
            resultado = resposta.get('resultado')
            
            if resultado == 'REMOVIDO':
                consola.sucesso("Conta apagada com sucesso!")
                self.rede.remover_token_local(self.sessao.nome_utilizador)
                self.sessao.encerrar_sessao()
                return True  # Fecha o menu
            elif resultado == 'NAO_PERMITIDO':
                consola.erro(
                    "Por motivos de segurança essa ação não pode ser "
                    "efetuada agora. Solicite a um administrador para "
                    "limpar todos os seus dados."
                )
            else:
                consola.erro(f"{resultado}")
        else:
            consola.erro(
                f"Erro ao apagar conta: {resposta.get('erro')}"
            )

    def esquecer_conta(self):
        Interface.mostrar_cabecalho("Esquecer Conta")
        
        username = self.sessao.nome_utilizador
        
        confirmacao = consola.sim_ou_nao(
            f"Tem a certeza que deseja remover '{username}' do cache local?\n"
            f"Terá que fazer login manualmente na próxima vez."
        )
        
        if confirmacao is False:
            consola.aviso("Operação cancelada.")
            return
        
        # Remove o token local
        self.rede.remover_token_local(username)
        consola.sucesso(f"Conta '{username}' removida do cache local com sucesso!")
        
        # Encerra a sessão para voltar ao menu de login
        self.sessao.encerrar_sessao()
        return True  # Fecha o menu


class ControladorLoja:
    def __init__(self, controlador_generico):
        self.controlador_generico = controlador_generico

    def listar_produtos_com_filtros(self):
        Interface.mostrar_cabecalho("Listar Produtos")
        
        # Listar lojas disponíveis
        resposta_lojas = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_lojas is None or resposta_lojas.get('ok') is False:
            consola.erro("Erro ao carregar lojas.")
            return
        
        lojas = resposta_lojas.get('resultado', [])
        
        if len(lojas) == 0:
            consola.aviso("Nenhuma loja disponível.")
            return
        
        consola.info("\nLojas disponíveis:")
        for loja in lojas:
            consola.normal(f"  {Cores.AZUL}{loja['id']}.{Cores.NORMAL} {loja['nome']} - {loja['localizacao']}")
        
        loja_id = consola.ler_texto("\nID da Loja (Enter para ver todas):", obrigatorio=False)
        categoria = consola.ler_texto("Categoria (Enter para ignorar):", obrigatorio=False)
        preco_maximo = consola.ler_texto("Preço Máximo (Enter para ignorar):", obrigatorio=False)
        
        parametros = {}
        
        if loja_id and loja_id.isdigit():
            parametros['store_id'] = loja_id
        
        if categoria:
            parametros['categoria'] = categoria
        
        if preco_maximo:
            try:
                float(preco_maximo)
                parametros['preco_max'] = preco_maximo
            except ValueError:
                consola.aviso("Preço máximo inválido, será ignorado.")
        
        self.controlador_generico.executar_comando('list_products', parametros)

    def pesquisar_produtos_por_nome(self):
        Interface.mostrar_cabecalho("Procurar Produto por Nome")
        
        # PASSO 1: Listar e selecionar loja
        resposta_lojas = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_lojas is None or resposta_lojas.get('ok') is False:
            consola.erro("Erro ao carregar lojas.")
            return
        
        lojas = resposta_lojas.get('resultado', {})
        if not lojas:
            consola.erro("Nenhuma loja disponível.")
            return
        
        # Criar opções de loja
        opcoes_lojas = []
        for loja_id, info_loja in lojas.items():
            nome_loja = info_loja.get('nome', f'Loja {loja_id}')
            opcoes_lojas.append((nome_loja, loja_id))
        
        # Mostrar menu de seleção de loja
        consola.info("Selecione uma loja:")
        for idx, (nome_loja, loja_id) in enumerate(opcoes_lojas, 1):
            print(f"{idx}. {nome_loja}")
        
        try:
            escolha = consola.ler_texto("Escolha (número):", obrigatorio=False)
            if not escolha or not escolha.isdigit():
                consola.aviso("Operação cancelada.")
                return
            
            idx_escolha = int(escolha) - 1
            if idx_escolha < 0 or idx_escolha >= len(opcoes_lojas):
                consola.erro("Opção inválida.")
                return
            
            loja_selecionada = opcoes_lojas[idx_escolha][1]
        except ValueError:
            consola.erro("Entrada inválida.")
            return
        
        # PASSO 2: Procurar por nome na loja selecionada
        nome_produto = consola.ler_texto("Nome do Produto a procurar:")
        if not nome_produto:
            consola.aviso("Nome inválido.")
            return
        
        parametros = {
            'nome': nome_produto,
            'loja_id': loja_selecionada
        }
        
        self.controlador_generico.executar_comando('pesquisar_produtos', parametros)

    def realizar_encomenda(self):
        Interface.mostrar_cabecalho("Realizar Encomenda")

        # 1. Listar lojas disponíveis
        resposta_lojas = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )

        if resposta_lojas is None or resposta_lojas.get('ok') is False:
            consola.erro("Erro ao carregar lojas.")
            return

        lojas = resposta_lojas.get('resultado', [])

        if len(lojas) == 0:
            consola.aviso("Nenhuma loja disponível.")
            return

        # 2. Mostrar lojas e pedir seleção
        consola.info("\nLojas disponíveis:")
        for loja in lojas:
            consola.info(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")

        loja_id = consola.ler_texto("\nID da Loja para comprar:")
        
        if not loja_id.isdigit():
            consola.erro("ID da loja inválido.")
            return

        # 3. Listar produtos da loja
        parametros_produtos = {
            'token_sessao': self.controlador_generico.sessao.token_sessao,
            'store_id': loja_id
        }

        resposta_produtos = self.controlador_generico.rede.enviar_comando(
            'listar_produtos',
            parametros_produtos
        )

        if resposta_produtos is None or resposta_produtos.get('ok') is False:
            consola.erro("Erro ao carregar produtos da loja.")
            return

        produtos = resposta_produtos.get('resultado', [])

        if len(produtos) == 0:
            consola.aviso("Nenhum produto disponível nesta loja.")
            return

        consola.info("\nProdutos disponíveis:")
        for produto in produtos:
            consola.info(
                f"  {produto['id']}. {produto['nome']} - "
                f"€{produto['preco']} (Stock: {produto['stock']})"
            )

        # 4. Permitir adicionar múltiplos itens ao carrinho
        itens = {}
        
        while True:
            id_produto = consola.ler_texto(
                "\nID do produto a adicionar (Enter para finalizar):",
                obrigatorio=False
            )

            if len(id_produto) == 0:
                break

            if not id_produto.isdigit():
                consola.erro("ID inválido.")
                continue

            quantidade = consola.ler_texto("Quantidade:")

            if not quantidade.isdigit() or int(quantidade) <= 0:
                consola.erro("Quantidade inválida.")
                continue

            itens[id_produto] = int(quantidade)
            consola.sucesso(f"Produto {id_produto} adicionado com quantidade {quantidade}.")

        if len(itens) == 0:
            consola.aviso("Nenhum produto foi adicionado.")
            return

        # 5. Realizar encomenda
        parametros = {
            'itens': itens
        }

        self.controlador_generico.executar_comando(
            'realizar_encomenda',
            parametros
        )


class ControladorVendedor:
    def __init__(self, controlador_generico):
        self.controlador_generico = controlador_generico

    def listar_pedidos_loja(self):
        Interface.mostrar_cabecalho("Pedidos da Loja")
        
        filtro = consola.ler_texto(
            "Filtrar Status (pendente/concluida/vazio):",
            obrigatorio=False
        )
        
        parametros = {}
        if filtro:
            parametros['filtro_estado'] = filtro
        
        self.controlador_generico.executar_comando('listar_encomendas', parametros)

    def concluir_pedido(self):
        Interface.mostrar_cabecalho("Concluir Pedido")
        
        # Primeiro listar os pedidos disponíveis
        resposta_pedidos = self.controlador_generico.rede.enviar_comando(
            'listar_encomendas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_pedidos is None or resposta_pedidos.get('ok') is False:
            consola.erro("Erro ao listar pedidos.")
            return
        
        pedidos = resposta_pedidos.get('resultado', [])
        
        if len(pedidos) == 0:
            consola.aviso("Nenhum pedido disponível para concluir.")
            return
        
        consola.info("\nPedidos disponíveis:")
        for pedido in pedidos:
            consola.info(
                f"  {pedido['id']}. Cliente: {pedido.get('cliente', 'Desconhecido')} | "
                f"Total: {pedido.get('total_price', 0):.2f}€ | Status: {pedido.get('status', 'desconhecido')}"
            )
        
        pedido_id = consola.ler_texto("\nID do Pedido a concluir:")
        
        self.controlador_generico.executar_comando(
            'concluir_encomenda',
            {'id_encomenda': pedido_id}
        )

    def verificar_stock_baixo(self):
        self.controlador_generico.executar_comando('verificar_stock_baixo')

    def menu_vendedor(self):
        opcoes = [
            ("Listar Pedidos da Loja", self.listar_pedidos_loja),
            ("Concluir Pedido", self.concluir_pedido),
            ("Verificar Stock Baixo", self.verificar_stock_baixo),
            (
                "Concluir Encomenda Pendente",
                lambda: self.controlador_generico.executar_comando(
                    'concluir_encomenda'
                )
            ),
            (
                "Listar Encomendas da Loja",
                lambda: self.controlador_generico.executar_comando(
                    'listar_encomendas'
                )
            ),
            (
                "Ver Histórico de Vendas da Loja",
                lambda: self.controlador_generico.executar_comando(
                    'ver_historico_vendas'
                )
            ),
            (
                "Editar Produto",
                lambda: self.controlador_generico.executar_comando(
                    'editar_produto'
                )
            )
        ]

        Interface.exibir_menu("Painel do Vendedor", opcoes, "Voltar")


class ControladorAdministracao:
    def __init__(self, controlador_generico):
        self.controlador_generico = controlador_generico

    def adicionar_produto(self):
        Interface.mostrar_cabecalho("Novo Produto")
        
        # Nome do produto com sugestões
        nome = Interface.ler_com_sugestoes(
            self.controlador_generico.rede,
            "Nome do Produto",
            "listar_nomes_produtos",
            permitir_vazio=False
        )
        
        if not nome:
            consola.erro("Nome não pode estar vazio.")
            return
        
        # Categoria com sugestões
        categoria = Interface.ler_com_sugestoes(
            self.controlador_generico.rede,
            "Categoria",
            "listar_categorias",
            permitir_vazio=False
        )
        
        if not categoria:
            consola.erro("Categoria não pode estar vazia.")
            return
        
        # Descrição com sugestões
        descricao = Interface.ler_com_sugestoes(
            self.controlador_generico.rede,
            "Descrição",
            "listar_descricoes",
            permitir_vazio=False
        )
        
        if not descricao:
            consola.erro("Descrição não pode estar vazia.")
            return
        
        preco = consola.ler_texto("Preço:")
        stock = consola.ler_texto("Stock:")
        
        # Listar lojas para escolher
        resposta_lojas = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_lojas is None or resposta_lojas.get('ok') is False:
            consola.erro("Erro ao carregar lojas.")
            return
        
        lojas = resposta_lojas.get('resultado', [])
        
        if len(lojas) == 0:
            consola.erro("Nenhuma loja disponível. Crie uma loja primeiro.")
            return
        
        consola.info("\nLojas disponíveis:")
        for loja in lojas:
            consola.info(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        
        loja_id = consola.ler_texto("\nID da Loja:")
        
        try:
            parametros = {
                'nome': nome,
                'categoria': categoria,
                'descricao': descricao,
                'preco': preco,
                'stock': stock,
                'store_id': loja_id
            }
            
            self.controlador_generico.executar_comando('add_product', parametros)
        except Exception as e:
            consola.erro(f"Valores inválidos: {e}")

    def editar_produto(self):
        Interface.mostrar_cabecalho("Editar Produto")
        
        # Listar produtos antes de pedir o ID
        resposta_produtos = self.controlador_generico.rede.enviar_comando(
            'list_products',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_produtos is None or resposta_produtos.get('ok') is False:
            consola.erro("Erro ao listar produtos.")
            return
        
        produtos = resposta_produtos.get('resultado', [])
        
        if len(produtos) == 0:
            consola.aviso("Nenhum produto disponível para editar.")
            return
        
        consola.info("\nProdutos disponíveis:")
        for produto in produtos:
            consola.info(
                f"  {produto['id']}. {produto['nome']} | "
                f"Categoria: {produto['categoria']} | Stock: {produto['stock']} | "
                f"Loja: {produto['loja']}"
            )
        
        produto_id = consola.ler_texto("\nID Produto:")
        
        if not produto_id or not produto_id.isdigit():
            consola.erro("ID inválido.")
            return
        
        consola.info("Deixe em branco para não alterar ou escolha da lista de sugestões")
        
        # Nome com sugestões
        consola.info("\nNovo Nome")
        novo_nome = Interface.ler_com_sugestoes(
            self.controlador_generico.rede,
            "Nome do Produto",
            "listar_nomes_produtos",
            permitir_vazio=True
        )
        
        # Categoria com sugestões
        consola.info("\nNova Categoria")
        nova_categoria = Interface.ler_com_sugestoes(
            self.controlador_generico.rede,
            "Categoria",
            "listar_categorias",
            permitir_vazio=True
        )
        
        # Descrição com sugestões
        consola.info("\nNova Descrição")
        nova_descricao = Interface.ler_com_sugestoes(
            self.controlador_generico.rede,
            "Descrição",
            "listar_descricoes",
            permitir_vazio=True
        )
        
        novo_preco = consola.ler_texto("\nNovo Preço:", obrigatorio=False)
        novo_stock = consola.ler_texto("Novo Stock:", obrigatorio=False)
        
        parametros = {'product_id': produto_id}
        
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
        
        if self.controlador_generico.sessao.cargo == 'admin':
            # Listar lojas
            resposta_lojas = self.controlador_generico.rede.enviar_comando('listar_lojas')
            
            if resposta_lojas is not None and resposta_lojas.get('ok') is True:
                lojas = resposta_lojas.get('resultado', [])
                if len(lojas) > 0:
                    consola.info("\nLojas disponíveis:")
                    for loja in lojas:
                        consola.info(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
            
            novo_id_da_loja = consola.ler_texto("\nNovo ID Loja:", obrigatorio=False)
            if novo_id_da_loja:
                parametros['novo_id_da_loja'] = novo_id_da_loja
        
        self.controlador_generico.executar_comando('editar_produto', parametros)

    def remover_produto(self):
        Interface.mostrar_cabecalho("Remover Produto")
        
        # Listar produtos antes de pedir o ID
        resposta_produtos = self.controlador_generico.rede.enviar_comando(
            'list_products',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_produtos is None or resposta_produtos.get('ok') is False:
            consola.erro("Erro ao listar produtos.")
            return
        
        produtos = resposta_produtos.get('resultado', [])
        
        if len(produtos) == 0:
            consola.aviso("Nenhum produto disponível para remover.")
            return
        
        consola.info("\nProdutos disponíveis:")
        for produto in produtos:
            consola.info(
                f"  {produto['id']}. {produto['nome']} | "
                f"Categoria: {produto['categoria']} | Stock: {produto['stock']} | "
                f"Loja: {produto['loja']}"
            )
        
        produto_id = consola.ler_texto("\nID Produto a remover:")
        confirmacao = consola.ler_texto("Tem a certeza? (s/n):")
        
        if confirmacao.lower() != 's':
            consola.info("Operação cancelada.")
            return
        
        self.controlador_generico.executar_comando(
            'deletar_produto',
            {'product_id': produto_id}
        )

    def menu_administracao(self):
        opcoes = [
            ("Gestão de Utilizadores", self.menu_utilizadores),
            ("Gestão de Lojas", self.menu_lojas),
            ("Gestão de Produtos (Global)", self.menu_produtos),
            ("Gestão de Encomendas (Global)", self.menu_encomendas),
        ]

        Interface.exibir_menu("Painel de Administração", opcoes, "Voltar")

    def criar_loja(self):
        Interface.mostrar_cabecalho("Criar Nova Loja")
        
        nome = consola.ler_texto("Nome da Loja:")
        if not nome:
            consola.erro("Nome não pode estar vazio.")
            return
        
        localizacao = consola.ler_texto("Localização:")
        if not localizacao:
            consola.erro("Localização não pode estar vazia.")
            return
        
        parametros = {
            'nome': nome,
            'localizacao': localizacao
        }
        
        self.controlador_generico.executar_comando('criar_loja', parametros)

    def editar_loja(self):
        Interface.mostrar_cabecalho("Editar Loja")
        
        # Listar lojas antes de pedir o ID
        resposta_lojas = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_lojas is None or resposta_lojas.get('ok') is False:
            consola.erro("Erro ao listar lojas.")
            return
        
        lojas = resposta_lojas.get('resultado', [])
        
        if len(lojas) == 0:
            consola.erro("Nenhuma loja disponível.")
            return
        
        consola.info("\nLojas disponíveis:")
        for loja in lojas:
            consola.info(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        
        store_id = consola.ler_texto("\nID da Loja a editar:")
        
        if not store_id or not store_id.isdigit():
            consola.erro("ID inválido.")
            return
        
        consola.info("Deixe em branco para não alterar")
        
        novo_nome = consola.ler_texto("Novo Nome:", obrigatorio=False)
        nova_localizacao = consola.ler_texto("Nova Localização:", obrigatorio=False)
        
        if not novo_nome and not nova_localizacao:
            consola.aviso("Nenhuma alteração foi feita.")
            return
        
        parametros = {'store_id': store_id}
        
        if novo_nome:
            parametros['novo_nome'] = novo_nome
        if nova_localizacao:
            parametros['nova_localizacao'] = nova_localizacao
        
        self.controlador_generico.executar_comando('editar_loja', parametros)

    def remover_loja(self):
        Interface.mostrar_cabecalho("Remover Loja")
        
        # Listar lojas antes de pedir o ID
        resposta_lojas = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta_lojas is None or resposta_lojas.get('ok') is False:
            consola.erro("Erro ao listar lojas.")
            return
        
        lojas = resposta_lojas.get('resultado', [])
        
        if len(lojas) == 0:
            consola.erro("Nenhuma loja disponível.")
            return
        
        consola.info("\nLojas disponíveis:")
        for loja in lojas:
            consola.info(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
        
        store_id = consola.ler_texto("\nID da Loja a remover:")
        
        if not store_id or not store_id.isdigit():
            consola.erro("ID inválido.")
            return
        
        confirmacao = consola.ler_texto(
            "Tem certeza? Esta ação não pode ser desfeita. (s/n):"
        )
        
        if confirmacao.lower() != 's':
            consola.info("Operação cancelada.")
            return
        
        self.controlador_generico.executar_comando(
            'apagar_loja',
            {'store_id': store_id}
        )

    def listar_utilizadores_com_filtros(self):
        # Criar funções para cada opção de filtro
        def listar_todos():
            self.controlador_generico.executar_comando('listar_utilizadores', {})
        
        def listar_clientes():
            self.controlador_generico.executar_comando('listar_utilizadores', {'filtro_cargo': 'cliente'})
        
        def listar_vendedores():
            self.controlador_generico.executar_comando('listar_utilizadores', {'filtro_cargo': 'vendedor'})
        
        def listar_admins():
            self.controlador_generico.executar_comando('listar_utilizadores', {'filtro_cargo': 'admin'})
        
        def listar_por_loja():
            # Listar lojas primeiro
            resposta_lojas = self.controlador_generico.rede.enviar_comando(
                'listar_lojas',
                self.controlador_generico.sessao.obter_credenciais()
            )
            
            if resposta_lojas is None or resposta_lojas.get('ok') is False:
                consola.erro("Erro ao carregar lojas.")
                return
            
            lojas = resposta_lojas.get('resultado', [])
            
            if len(lojas) == 0:
                consola.erro("Nenhuma loja disponível.")
                return
            
            # Criar menu de lojas
            opcoes_lojas = []
            for loja in lojas:
                loja_id = loja['id']
                loja_nome = loja['nome']
                
                def selecionar_loja(id_loja=loja_id):
                    self.controlador_generico.executar_comando('listar_utilizadores', {'filtro_loja': str(id_loja)})
                
                opcoes_lojas.append((loja_nome, selecionar_loja))
            
            Interface.exibir_menu("Selecionar Loja", opcoes_lojas, "Voltar")
        
        opcoes = [
            ("Todos os utilizadores", listar_todos),
            ("Apenas Clientes", listar_clientes),
            ("Apenas Vendedores", listar_vendedores),
            ("Apenas Admins", listar_admins),
            ("Por Loja específica", listar_por_loja),
        ]
        
        Interface.exibir_menu("Listar Utilizadores - Filtros", opcoes, "Voltar")


    def criar_funcionario(self):
        Interface.mostrar_cabecalho("Criar Funcionário")
        
        tipo = consola.ler_texto("Tipo (admin/vendedor):")
        
        loja_id = ""
        
        if tipo == 'vendedor':
            resposta_lojas = self.controlador_generico.rede.enviar_comando(
                'listar_lojas',
                self.controlador_generico.sessao.obter_credenciais()
            )
            
            if resposta_lojas is None or resposta_lojas.get('ok') is False:
                consola.erro("Erro ao carregar lojas.")
                return
            
            lojas = resposta_lojas.get('resultado', [])
            
            if len(lojas) == 0:
                consola.erro("Nenhuma loja disponível para associar ao vendedor.")
                return
            
            consola.info("\nLojas disponíveis:")
            for loja in lojas:
                consola.info(f"  {loja['id']}. {loja['nome']} - {loja['localizacao']}")
            
            loja_id = consola.ler_texto("\nID Loja:")
        
        utilizador = consola.ler_texto("Username:")
        senha = consola.ler_senha("Password:")
        
        if senha is None:
            return
        
        parametros = {
            'nome_utilizador_novo': utilizador,
            'palavra_passe_nova': senha,
            'cargo': tipo
        }
        
        if tipo == 'vendedor' and loja_id:
            parametros['id_loja'] = loja_id
        
        self.controlador_generico.executar_comando('criar_funcionario', parametros)

    def menu_utilizadores(self):
        opcoes = [
            ("Listar Utilizadores com Filtros", self.listar_utilizadores_com_filtros),
            (
                "Listar todos os Utilizadores",
                lambda: self.controlador_generico.executar_comando(
                    'listar_utilizadores'
                )
            ),
            ("Criar novo Funcionário", self.criar_funcionario)
        ]

        Interface.exibir_menu("Gestão de Utilizadores", opcoes, "Voltar")

    def listar_lojas(self):
        resposta = self.controlador_generico.rede.enviar_comando(
            'listar_lojas',
            self.controlador_generico.sessao.obter_credenciais()
        )
        
        if resposta is None or resposta.get('ok') is False:
            consola.erro("Erro ao carregar lojas.")
            return
        
        lojas = resposta.get('resultado', [])
        
        if not lojas or len(lojas) == 0:
            consola.aviso("Nenhuma loja disponível.")
            return
        
        # Exibir lojas
        Interface.mostrar_cabecalho("Lojas Disponíveis")
        for loja in lojas:
            consola.info(f"ID: {loja['id']} | Nome: {loja['nome']} | Localização: {loja['localizacao']}")

    def menu_lojas(self):
        opcoes = [
            ("Listar todas as Lojas", self.listar_lojas),
            ("Criar nova Loja", self.criar_loja),
            ("Editar Loja", self.editar_loja),
            ("Apagar Loja", self.remover_loja),
        ]

        Interface.exibir_menu("Gestão de Lojas", opcoes, "Voltar")

    def menu_produtos(self):
        opcoes = [
            (
                "Listar todos os Produtos",
                lambda: self.controlador_generico.executar_comando(
                    'listar_produtos'
                )
            ),
            ("Adicionar novo Produto", self.adicionar_produto),
            ("Editar um Produto", self.editar_produto),
            ("Apagar um Produto", self.remover_produto),
        ]

        Interface.exibir_menu("Gestão de Produtos", opcoes, "Voltar")

    def menu_encomendas(self):
        opcoes = [
            (
                "Ver Histórico de Vendas (Global)",
                lambda: self.controlador_generico.executar_comando(
                    'ver_historico_vendas'
                )
            ),
            (
                "Apagar uma Encomenda",
                lambda: self.controlador_generico.executar_comando(
                    'apagar_encomenda'
                )
            ),
        ]

        Interface.exibir_menu("Gestão de Encomendas", opcoes, "Voltar")