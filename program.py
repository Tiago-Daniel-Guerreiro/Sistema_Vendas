"""
Pessoas:
• Administrador – responsável pela gestão global do sistema e controle de stock.
• Vendedor – responsável por registar vendas e atender clientes.
• Cliente – realiza consultas de produtos e efetua compras

Autenticação:
- Recebe credenciais do cliente (utilizador/senha).
- Verifica se o utilizador é admin, vendedor, cliente.
- Diferenciar permissões (apenas admin pode adicionar produtos).


Gestão de Produtos
- Adicionar produto: Recebe dados (nome, categoria, preço, stock, descrição). (Retorna PRODUTO_ADICIONADO ou ERRO_DUPLICADO)
- Atualizar produto: Permite alterar preço, stock ou descrição. (Retorna ATUALIZACAO_OK ou PRODUTO_NAO_ENCONTRADO)
- Remover produto: Elimina produto do catálogo. (Retorna PRODUTO_REMOVIDO)
- Listar produtos: Recebe o filtro. (retorna a lista completa ou filtrada (por categoria, preço, disponibilidade)

Gestão de Vendas
• Registar venda: Recebe pedido do cliente com ID do produto e quantidade e verifica stock e atualiza base de dados. Retorna VENDA_CONFIRMADA ou STOCK_INSUFICIENTE.
• Consultar histórico de vendas: Envia lista de todas as vendas realizadas, com datas e valores totais.


4. Gestão de Stock
• Monitoriza produtos com stock abaixo de um limite (ex: < 5 unidades).
• Envia alerta ALERTA_STOCK_BAIXO.


Funções do Cliente
1. Login
• Envia utilizador/senha para o servidor.
• Recebe resultado e ajusta o acesso conforme o tipo de utilizador.
• Se o utilizador não possuir credenciais, é necessário fazer o registo na aplicação.
2. Gestão de produtos (para admin ou vendedores)
• Adicionar novo produto (nome, preço, categoria, stock).
• Atualizar ou remover produtos.
3. Realizar vendas (para vendedores (se o cliente estiver presencialmente na loja) ou clientes)
• Selecionar produto e quantidade.
• Enviar pedido de venda ao servidor.
• Receber confirmação e total da compra.
4. Excluir produto (para admin)
• Solicita ao usuário o ID do produto.
• Envia pedido ao servidor e exibe resposta.
5. Atualizar consulta
• Permite alterar data/hora de uma consulta existente.
• Envia pedido UPDATE_CONSULTA.




Gestão de produtos (para admin e vendedores)
	adicionar produto na loja, já existente na base de dados (nome, preço, categoria, stock).
	atualizar (preço descrição).
  	remover visualmente da loja.



Opção Excluir e Adicionar (Na base de dados) Somente ADM
	adicionar na base de dados novo produto.
	excluir da base de dados um produto.



"""

from datetime import datetime
from enum import Enum
from Sql_Utilitarios.Base import TipoSQL, RestricaoColuna, DirecaoOrdenacao, OperadorComparacao, OperadorLogico, TipoJunta, Conjunto_De_Dados_Para_Inserir, Script_SQL, ExpressaoSQL, ExcecaoSegurancaSQL,VerificadorDeSeguranca, FormatadorSQL, Condicao, AcaoReferencial, ChaveEstrangeira, ChavePrimaria,Coluna,Tabela,BaseDeDados, ClausulaWhere, ClausulaJoin,ClausulaOrderBy, ClausulaLimit, ClausulaSet,ConstrutorSelect,ConstrutorUpdate,ConstrutorDelete, ExecutorSQL
from sql import executor, tabela_clientes,tabela_permissao,tabela_produto

"""
CREATE TABLE `clientes` ( `id` INT AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `senha` VARCHAR(255) NOT NULL,
    `id_permissao` INT,
    PRIMARY KEY (`id`) );

CREATE TABLE `produtos` ( `id` INT AUTO_INCREMENT,
    `username` VARCHAR(50) NOT NULL UNIQUE,
    `senha` VARCHAR(255) NOT NULL,
    PRIMARY KEY (`id`) );

CREATE TABLE `permissoes` ( 
    `id` INT AUTO_INCREMENT,
    `Admin` BOOLEAN,
    `Limitado_loja` INT,
    PRIMARY KEY (`id`) );
"""

class TipoUtilizador(Enum):
    ADMINISTRADOR = 1
    VENDEDOR = 2
    CLIENTE = 3

class StatusProduto(Enum):
    PRODUTO_ADICIONADO = 1
    ERRO_DUPLICADO = 2
    ATUALIZACAO_OK = 3
    PRODUTO_NAO_ENCONTRADO = 4
    PRODUTO_REMOVIDO = 5

class StatusVenda(Enum):
    VENDA_CONFIRMADA = 1
    STOCK_INSUFICIENTE = 2

class Alerta(Enum):
    ALERTA_STOCK_BAIXO = 1

class Utilizado: # Classe base para Administrador, Vendedor e Cliente
    def __init__(self, username, senha, tipo):
        self.username = username
        self.senha = senha

    @staticmethod
    def VerificarUtilizadorRepetido(username):
        #
        pass # por fazer

    def Login(self) -> bool:
        """
        Verifica as credenciais do utilizador no sistema.
        
        Returns:
            bool: True se o login for bem-sucedido, False caso contrário
        """
        # Verificar se existe o useername e se tem a mesma senha
        return False
    


"""
1. Login
• Envia utilizador/senha para o servidor.
• Recebe resultado e ajusta o acesso conforme o tipo de utilizador.
• Se o utilizador não possuir credenciais, é necessário fazer o registo na aplicação.

2. Gestão de produtos (para admin ou vendedores)
• Adicionar novo produto (nome, preço, categoria, stock).
• Atualizar ou remover produtos.

3. Realizar vendas (para vendedores (se o cliente estiver presencialmente na loja) ou clientes)
• Selecionar produto e quantidade.
• Enviar pedido de venda ao servidor.
• Receber confirmação e total da compra.

4. Excluir produto (para admin)
• Solicita ao usuário o ID do produto.
• Envia pedido ao servidor e exibe resposta.

"""

class Produto:
    def __init__(self, id):
        self.id = id
        self.nome = None
        self.categoria = None
        self.preco = None
        self.stock = None
        self.descricao = None
        self.data_informacao = None
        self.__atualizar_informacao()

    def __atualizar_informacao(self):
        self.data_informacao = datetime.now()
        # Fazer requesicao á base de dados para atualizar a data de informacao do produto
        pass
