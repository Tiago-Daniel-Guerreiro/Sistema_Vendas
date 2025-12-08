from enums import Mensagem
from servidor.acoes import Acoes
from servidor.comando import Comando # Utiliza a nova versão de comando.py
from servidor.entidades import Sessao
import inspect

class GestorComandos:
    def __init__(self):
        self.comandos = {}
        self._registar_comandos_predefinidos()

    def _registar_comandos_predefinidos(self):
        
        # Utilidades
        self.registar(Comando('ping', Acoes.ping, 'Retorna pong', None, 'utilidades', [Mensagem.PONG]))
        self.registar(Comando('help', Acoes.help, 'Lista todos os comandos disponíveis', None, 'utilidades', [Mensagem.SUCESSO]))
        
        # Conta e Autenticação
        self.registar(Comando('autenticar', Acoes.autenticar, 'Autentica o utilizador', None, 'minha conta', [Mensagem.SUCESSO]))
        self.registar(Comando('registar', Acoes.registar, 'Regista um novo cliente', None, 'minha conta', [Mensagem.UTILIZADOR_CRIADO], parametros={'username': {'obrigatorio': True}, 'password': {'obrigatorio': True}}))
        self.registar(Comando('editar_senha', Acoes.editar_senha, 'Edita a senha do utilizador', 'cliente', 'minha conta', [Mensagem.ATUALIZADO], {'nova_senha': {'obrigatorio': True}}))
        self.registar(Comando('editar_nome_utilizador', Acoes.editar_nome_utilizador, 'Edita o nome do utilizador', 'cliente', 'minha conta', [Mensagem.ATUALIZADO], {'novo_username': {'obrigatorio': True}}))
        self.registar(Comando('apagar_utilizador', Acoes.apagar_utilizador, 'Remove a conta do cliente logado', 'cliente', 'minha conta', [Mensagem.REMOVIDO]))
        self.registar(Comando('promover_para_admin', Acoes.promover_para_admin, 'Promove o utilizador a admin', 'cliente', 'minha conta', [Mensagem.SUCESSO], {'chave': {'obrigatorio': True}}))
        
        # Compras
        self.registar(Comando('realizar_encomenda', Acoes.realizar_encomenda, 'Realiza uma encomenda', 'cliente', 'compras', [Mensagem.CONCLUIDA, Mensagem.PENDENTE], {'itens': {'obrigatorio': True}}))
        self.registar(Comando('ver_historico_compras', Acoes.ver_historico_compras, 'Exibe o histórico de compras', 'cliente', 'compras', [Mensagem.SUCESSO]))

        # Lojas
        self.registar(Comando('listar_lojas', Acoes.listar_lojas, 'Lista todas as lojas', 'cliente', 'lojas', [Mensagem.SUCESSO]))
        
        # Produtos
        self.registar(Comando('list_products', Acoes.listar_produtos, 'Lista produtos disponíveis', 'cliente', 'produtos', [Mensagem.SUCESSO]))
        self.registar(Comando('listar_produtos', Acoes.listar_produtos, 'Lista produtos disponíveis', 'cliente', 'produtos', [Mensagem.SUCESSO]))
        self.registar(Comando('procurar_produto_por_nome', Acoes.procurar_produto_por_nome, 'Busca um produto pelo nome', 'cliente', 'produtos', [Mensagem.SUCESSO], {'nome_produto': {'obrigatorio': True}}))
        self.registar(Comando('pesquisar_produtos', Acoes.pesquisar_produtos, 'Pesquisa produtos por nome (busca parcial)', 'cliente', 'produtos', [Mensagem.SUCESSO], {'nome': {'obrigatorio': True}}))
        self.registar(Comando('listar_nomes_produtos', Acoes.listar_nomes_produtos, 'Lista nomes de produtos existentes', 'cliente', 'produtos', [Mensagem.SUCESSO]))
        self.registar(Comando('listar_categorias', Acoes.listar_categorias, 'Lista categorias de produtos', 'cliente', 'produtos', [Mensagem.SUCESSO]))
        self.registar(Comando('listar_descricoes', Acoes.listar_descricoes, 'Lista descrições de produtos', 'cliente', 'produtos', [Mensagem.SUCESSO]))
        self.registar(Comando('editar_produto', Acoes.editar_produto, 'Edita um produto', 'vendedor', 'produtos', [Mensagem.ATUALIZADO], {'id_produto': {'obrigatorio': True}}))
        self.registar(Comando('verificar_stock_baixo', Acoes.verificar_stock_baixo, 'Verifica produtos com baixo stock', 'vendedor', 'produtos', [Mensagem.ALERTA_STOCK_BAIXO, Mensagem.SUCESSO]))
        
        # Encomendas (Vendedor)
        self.registar(Comando('concluir_encomenda', Acoes.concluir_encomenda, 'Conclui uma encomenda pendente', 'vendedor', 'encomendas', [Mensagem.CONCLUIDA], {'id_encomenda': {'obrigatorio': True}}))
        self.registar(Comando('listar_encomendas', Acoes.listar_encomendas, 'Lista encomendas da loja', 'vendedor', 'encomendas', [Mensagem.SUCESSO]))
        self.registar(Comando('concluir_pedido', Acoes.concluir_encomenda, 'Conclui um pedido pendente', 'vendedor', 'encomendas', [Mensagem.CONCLUIDA], {'order_id': {'obrigatorio': True}}))
        self.registar(Comando('listar_pedidos', Acoes.listar_encomendas, 'Lista pedidos da loja', 'vendedor', 'encomendas', [Mensagem.SUCESSO]))
        
        # Gestão (Admin)
        self.registar(Comando('criar_funcionario', Acoes.criar_funcionario, 'Cria um novo funcionário', 'admin', 'gestao', [Mensagem.UTILIZADOR_CRIADO], {'nome_utilizador_novo': {'obrigatorio': True}, 'palavra_passe_nova': {'obrigatorio': True}, 'cargo': {'obrigatorio': True}}))
        self.registar(Comando('listar_utilizadores', Acoes.listar_utilizadores, 'Lista todos os utilizadores', 'admin', 'gestao', [Mensagem.SUCESSO]))
        self.registar(Comando('adicionar_produto', Acoes.adicionar_produto, 'Adiciona um novo produto a uma loja', 'admin', 'gestao', [Mensagem.ADICIONADO], {'nome':True, 'categoria':True, 'descricao':True, 'preco':True, 'stock':True, 'id_loja':True}))
        self.registar(Comando('add_product', Acoes.adicionar_produto, 'Adiciona um novo produto a uma loja (alias)', 'admin', 'gestao', [Mensagem.ADICIONADO], {'nome':True, 'categoria':True, 'descricao':True, 'preco':True, 'stock':True, 'store_id':True}))
        self.registar(Comando('apagar_produto', Acoes.apagar_produto, 'Apaga um produto do sistema', 'admin', 'gestao', [Mensagem.REMOVIDO], {'id_produto': {'obrigatorio': True}}))
        self.registar(Comando('deletar_produto', Acoes.apagar_produto, 'Apaga um produto do sistema (alias)', 'admin', 'gestao', [Mensagem.REMOVIDO], {'product_id': {'obrigatorio': True}}))
        self.registar(Comando('apagar_encomenda', Acoes.apagar_encomenda, 'Apaga uma encomenda do sistema', 'admin', 'gestao', [Mensagem.REMOVIDO], {'id_encomenda': {'obrigatorio': True}}))
        self.registar(Comando('criar_loja', Acoes.criar_loja, 'Cria uma nova loja', 'admin', 'gestao', [Mensagem.ADICIONADO], {'nome': {'obrigatorio': True}, 'localizacao': {'obrigatorio': True}}))
        self.registar(Comando('editar_loja', Acoes.editar_loja, 'Edita uma loja existente', 'admin', 'gestao', [Mensagem.ATUALIZADO], {'id_loja': {'obrigatorio': True}}))
        self.registar(Comando('apagar_loja', Acoes.apagar_loja, 'Apaga uma loja do sistema', 'admin', 'gestao', [Mensagem.REMOVIDO], {'id_loja': {'obrigatorio': True}}))
        
    def registar(self, comando):
        self.comandos[comando.nome] = comando

    def obter(self, nome):
        return self.comandos.get(nome)

    def todos_para_json(self):
        lista_comandos = []
        for comando in self.comandos.values():
            lista_comandos.append(comando.para_json())
        return lista_comandos

class ProcessadorComandos:
    @staticmethod
    def processar_pedido(base_de_dados, gestor_comandos, acao, parametros):
        utilizador_atual = Sessao.obter_utilizador(base_de_dados, parametros)
        
        Sessao.remover_expiradas(base_de_dados)

        comando = gestor_comandos.obter(acao)
        if comando is None:
            return Mensagem.COMANDO_NAO_ENCONTRADO

        if comando.validar_permissao(utilizador_atual) is False:
            return Mensagem.PERMISSAO_NEGADA

        if comando.validar_parametros(parametros) is False:
            return Mensagem.PARAMETROS_INVALIDOS

        argumentos_acao = {
            'base_de_dados': base_de_dados,
            'utilizador_atual': utilizador_atual,
            'parametros': parametros,
            'gestor_comandos': gestor_comandos
        }

        # inspect é usado para verificar os parâmetros da função de ação
        # exemplo: se a ação não precisa de base_de_dados, não o passamos

        try:
            assinatura = inspect.signature(comando.acao)
            argumentos_para_passar = {}

            for nome_parametro in assinatura.parameters:
                param = assinatura.parameters[nome_parametro]
                # Se o parâmetro é **kwargs, passa todos os argumentos disponíveis
                if param.kind == inspect.Parameter.VAR_KEYWORD:
                    argumentos_para_passar.update(argumentos_acao)
                # Se o parâmetro está disponível, passa-o
                elif nome_parametro in argumentos_acao:
                    argumentos_para_passar[nome_parametro] = argumentos_acao[nome_parametro]
            
            if len(argumentos_para_passar) == 0:
                return comando.acao()

            return comando.acao(**argumentos_para_passar)

        except Exception:
            return Mensagem.ERRO_GENERICO
        
gestor_comandos_global = GestorComandos()