import time
import consola
from cliente.rede_cliente import ClienteRede
from cliente.sessao_cliente import Sessao
from cliente.controlador import (
    ControladorAutenticacao,
    ControladorGenerico,
    ControladorLoja,
    ControladorVendedor,
    ControladorAdministracao
)

from cliente.interface_cliente import Interface

class AplicacaoCliente:
    def __init__(self, endereco, porta, depuracao=False):
        self.sessao = Sessao()
        self.rede = ClienteRede(endereco, porta, depuracao, sessao=self.sessao)

        # O Controlador Genérico precisa de uma referência à função de processamento de respostas.
        self.controlador_generico = ControladorGenerico(
            self.rede,
            self.sessao,
            self._processar_resposta_servidor
        )

        # Os outros controladores recebem o genérico para reutilizar a sua funcionalidade.
        self.controlador_autenticacao = ControladorAutenticacao(self.rede, self.sessao)
        self.controlador_loja = ControladorLoja(self.controlador_generico)
        self.controlador_vendedor = ControladorVendedor(self.controlador_generico)
        self.controlador_administracao = ControladorAdministracao(self.controlador_generico)

    def verificar_conexao_servidor(self):
        tentativas_maximas = 3
        consola.info("A verificar ligação com o servidor...")

        for tentativa in range(tentativas_maximas):
            resposta = self.rede.enviar_comando('ping')

            if resposta is not None and resposta.get('ok') is True:
                consola.sucesso("Ligação com o servidor estabelecida.")
                return True

            consola.aviso(
                f"Falha ao ligar ao servidor. Tentando novamente... "
                f"({tentativa + 1}/{tentativas_maximas})"
            )
            time.sleep(3)

        consola.erro("Não foi possível estabelecer ligação com o servidor.")
        return False

    def _processar_resposta_servidor(self, resposta, info_comando):
        # Centraliza a lógica de validação de sucesso e exibição de resultados.
        if resposta is None:
            consola.erro("Resposta nula do servidor.")
            return

        if resposta.get('ok') is False:
            consola.erro(
                f"O servidor retornou um erro: "
                f"{resposta.get('erro', 'Desconhecido')}"
            )
            return

        resultado = resposta.get('resultado')

        mensagens_sucesso_esperadas = []
        if info_comando is not None:
            mensagens_sucesso_esperadas = info_comando.get(
                'mensagens_sucesso',
                []
            )

        match resultado:
            case str():
                if resultado in mensagens_sucesso_esperadas:
                    consola.sucesso(resultado)
                else:
                    consola.sucesso("Operação concluída com sucesso.")
            case list():
                if len(resultado) > 0 and isinstance(resultado[0], dict):
                    colunas = []

                    for chave in resultado[0].keys():
                        coluna = {
                            'titulo': chave.replace('_', ' ').upper(),
                            'chave': chave,
                            'largura': 20
                        }
                        colunas.append(coluna)

                    Interface.mostrar_tabela(resultado, colunas)
                else:
                    for item in resultado:
                        consola.info(str(item))
            case dict():
                for chave, valor in resultado.items():
                    consola.info(
                        f"{chave.replace('_', ' ').title()}: {valor}"
                    )
            case _:
                consola.sucesso("Operação concluída com sucesso.")

    def menu_nao_autenticado(self):
        opcoes = [
            ("Iniciar Sessão", self.controlador_autenticacao.iniciar_sessao_guardada),
            ("Registar Nova Conta", self.controlador_autenticacao.registar_conta)
        ]
        
        # Define função para sair da aplicação
        def sair_sem_autenticacao():
            return True
        
        Interface.exibir_menu(
            "Sistema de Vendas - Bem-vindo",
            opcoes,
            "Sair da Aplicação",
            sair_sem_autenticacao
        )

    def menu_compras(self):
        opcoes = [
            (
                "Listar Todos os Produtos",
                lambda: self.controlador_generico.executar_comando(
                    'listar_produtos'
                )
            ),
            (
                "Listar Produtos com Filtros",
                self.controlador_loja.listar_produtos_com_filtros
            ),
            (
                "Pesquisar Produtos por Nome",
                self.controlador_loja.pesquisar_produtos_por_nome
            ),
            ("Realizar Compra", self.controlador_loja.realizar_encomenda),
            (
                "Ver Meu Histórico de Compras",
                lambda: self.controlador_generico.executar_comando(
                    'ver_historico_compras'
                )
            ),
        ]
        
        Interface.exibir_menu("Menu de Compras", opcoes, "Voltar")

    def menu_principal(self):
        titulo = (
            f"Menu Principal - {self.sessao.nome_utilizador} "
            f"[{self.sessao.cargo}]"
        )

        opcoes_comuns = [
            ("Compras", self.menu_compras),
        ]
        opcoes_vendedor = []
        opcoes_administracao = []

        if self.sessao.cargo == 'vendedor':
            opcoes_vendedor.append(
                ("Painel do Vendedor", self.controlador_vendedor.menu_vendedor)
            )

        if self.sessao.cargo == 'admin':
            opcoes_administracao.append(
                (
                    "Painel de Administração",
                    self.controlador_administracao.menu_administracao
                )
            )

        opcoes_finais = opcoes_comuns + opcoes_vendedor + opcoes_administracao
        opcoes_finais.append(("Minha Conta", self._menu_conta_none))
        opcoes_finais.append(("Terminar Sessão", self._encerrar_sessao_none))

        resultado = Interface.exibir_menu(titulo, opcoes_finais, "Sair da Aplicação", self.sair_aplicacao)
        return resultado

    def sair_aplicacao(self):
        self.controlador_autenticacao.encerrar_sessao()
        return True

    def _menu_conta_none(self):
        self.menu_conta()

    def _encerrar_sessao_none(self):
        self.controlador_autenticacao.encerrar_sessao()

    def menu_conta(self):
        while self.sessao.esta_logado():
            titulo = f"Minha Conta - {self.sessao.nome_utilizador}"
            
            opcoes = [
                ("Alterar Senha", self.controlador_autenticacao.alterar_senha),
                ("Editar Username", self.controlador_autenticacao.editar_username),
                ("Promover a Admin", self.controlador_autenticacao.promover_para_admin),
                ("Esquecer Conta (Cache Local)", self.controlador_autenticacao.esquecer_conta),
                ("Apagar Conta", self.controlador_autenticacao.apagar_conta),
            ]
            
            # Usa a mesma Interface.exibir_menu para garantir formatação consistente
            resultado = Interface.exibir_menu(titulo, opcoes, "Voltar")
            
            # Se sessão foi encerrada (editar username, alterar senha, promover, etc)
            if not self.sessao.esta_logado():
                return False  # Propaga para fechar menu principal e voltar ao login
            
            # Se resultado é True ou False, propaga
            if resultado is True or resultado is False:
                return resultado
            
            # Senão, volta ao menu (opção Voltar foi selecionada)
            break

    def iniciar(self):
        consola.limpar()
        consola.info("A iniciar cliente...")

        if self.verificar_conexao_servidor() is False:
            return

        while True:
            if self.sessao.esta_logado() is False:
                self.menu_nao_autenticado()

                if self.sessao.esta_logado() is False:
                    break
            else:
                resultado = self.menu_principal()
                if resultado is True:
                    break

        consola.sucesso("Obrigado por usar o sistema!")

def iniciar(endereco, porta, depuracao=False):
    aplicacao_cliente = AplicacaoCliente(endereco, porta, depuracao)

    try:
        aplicacao_cliente.iniciar()
    except (KeyboardInterrupt, SystemExit):
        consola.aviso("\nCliente encerrado.")
    except Exception as erro:
        consola.erro(f"\nErro fatal no cliente: {erro}")