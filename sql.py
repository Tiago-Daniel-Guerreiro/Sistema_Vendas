from Sql_Utilitarios.Base import TipoSQL, RestricaoColuna, DirecaoOrdenacao, OperadorComparacao, OperadorLogico, TipoJunta, Conjunto_De_Dados_Para_Inserir, Script_SQL, ExpressaoSQL, ExcecaoSegurancaSQL,VerificadorDeSeguranca, FormatadorSQL, Condicao, AcaoReferencial, ChaveEstrangeira, ChavePrimaria,Coluna,Tabela,BaseDeDados, ClausulaWhere, ClausulaJoin,ClausulaOrderBy, ClausulaLimit, ClausulaSet,ConstrutorSelect,ConstrutorUpdate,ConstrutorDelete, ExecutorSQL

# adiciona o que for necessário em cima

executor = ExecutorSQL(
    host="localhost",
    user="root",
    password="",
    port=3306
)
"""
    executor.preparar_base_limpa(bd_teste.nome)
    
    # Assumindo que BaseDeDados tem um método para gerar o script de criação completo
    script_criar = bd_teste.construir_sql_criar_tabelas() 
    executor.executar_script(str(script_criar))

                
sql_base.ConstrutorSelect # Para consultas

Exemplo:
                script_select = (
                    ConstrutorSelect(tabela_clientes)
                    .juntar(tabela_pedidos)
                    .selecionar("clientes.nome", "pedidos.valor_total", "pedidos.data_pedido")
                    .ordenar_por("clientes.nome")
                ).gerar_script()
                
                resultados_finais = executor.consultar(script_select)
                self.exibir_resultados("Consulta Final: Clientes e Pedidos", script_select, resultados_finais)

"""

"""
BASE DE DADOS:
utilizador
- Recebe credenciais do cliente (utilizador/senha).
- Verifica se o utilizador é admin, vendedor, cliente.

produto
id, nome, preço, stock, descrição

categoria, 
id
nome 

vendas
pedidos

Exemplo:
        bd_teste = BaseDeDados(self.BD_Nome_Teste)
        tabela_clientes = Tabela(
            "clientes",
            [
                Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
                Coluna("nome", TipoSQL.varchar(tamanho=50), [RestricaoColuna.Nao_Nulo]),
                Coluna("email", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo, RestricaoColuna.Unico])
            ],
            chave_primaria=ChavePrimaria.Simples("id")
        )

        tabela_pedidos = Tabela(
            "pedidos",
            [
                Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
                Coluna("cliente_id", TipoSQL.inteiro(), [RestricaoColuna.Nao_Nulo]),
                Coluna("data_pedido", TipoSQL.timestamp(), [RestricaoColuna.Nao_Nulo, RestricaoColuna.Padrao], valor_padrao=ExpressaoSQL("CURRENT_TIMESTAMP")),
                Coluna("valor_total", TipoSQL.decimal(precisao=10, escala=2), [RestricaoColuna.Nao_Nulo])
            ],
            chaves_estrangeiras=[ChaveEstrangeira.Simples("cliente_id", "clientes", "id")],
            chave_primaria=ChavePrimaria.Simples("id")
        )
"""




bd_Lojas = BaseDeDados("Loja")
tabela_clientes = Tabela(
    "clientes",
    [
        Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
        Coluna("username", TipoSQL.varchar(tamanho=50), [RestricaoColuna.Nao_Nulo,RestricaoColuna.Unico]),
        Coluna("senha", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo]),
        Coluna("id_permissao", TipoSQL.inteiro()),
    ],
    chave_primaria=ChavePrimaria.Simples("id")
)

tabela_produto = Tabela(
    "produtos",
    [
        Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
        Coluna("nome", TipoSQL.varchar(tamanho=50), [RestricaoColuna.Nao_Nulo,RestricaoColuna.Unico]),
        Coluna("senha", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo]),
        Coluna("stock", TipoSQL.inteiro(), [RestricaoColuna.Nao_Nulo]),
        Coluna("descrição", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo])
    ],
    chave_primaria=ChavePrimaria.Simples("id")
)

tabela_permissao = Tabela(
    "permissoes",
    [
        Coluna("id",TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
        Coluna("Admin",TipoSQL.Booleano()),
        Coluna("Limitado_loja",TipoSQL.inteiro())
    ],
)

"""
BASE DE DADOS:
utilizador
- Recebe credenciais do cliente (utilizador/senha).
- Verifica se o utilizador é admin, vendedor, cliente.

produto
id, nome, preço, stock, descrição

categoria, 
id
nome 

vendas
pedidos = 
grupo_produtos
status (concluido, pendente...)

conjunto_produtos=
produto
id_grupo
"""



