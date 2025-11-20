from Sql_Utilitarios.Base import TipoSQL, RestricaoColuna, DirecaoOrdenacao, OperadorComparacao, OperadorLogico, TipoJunta, Conjunto_De_Dados_Para_Inserir, Script_SQL, ExpressaoSQL, ExcecaoSegurancaSQL,VerificadorDeSeguranca, FormatadorSQL, Condicao, AcaoReferencial, ChaveEstrangeira, ChavePrimaria,Coluna,Tabela,BaseDeDados, ClausulaWhere, ClausulaJoin,ClausulaOrderBy, ClausulaLimit, ClausulaSet,ConstrutorSelect,ConstrutorUpdate,ConstrutorDelete, ExecutorSQL

# adiciona o que for necessário em cima

host="localhost"
user="root"
password=""
port=3306

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
        Coluna("username", TipoSQL.varchar(tamanho=50), [RestricaoColuna.Nao_Nulo,RestricaoColuna.Unico]),
        Coluna("senha", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo])
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
    chave_primaria=ChavePrimaria.Simples("id")
)

tabela_permissao = Tabela(
    "Vendas",
    [
        Coluna("id",TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
        Coluna("pedidos",,
        col
    ],
    chave_primaria=ChavePrimaria.Simples("id")
)


bd_Lojas.adicionar_tabela(tabela_clientes)
bd_Lojas.adicionar_tabela(tabela_produto)
bd_Lojas.adicionar_tabela(tabela_permissao)
bd_Lojas.adicionar_tabela(tabela_vendas)

with ExecutorSQL(host, user, password, port) as executor:
    print(bd_Lojas.construir_sql_criar_tabelas())
    executor.preparar_base_limpa(bd_Lojas.nome)
    executor.executar_script(bd_Lojas.construir_sql_criar_tabelas())
    dados_clientes = [
        {"username": "Ana Guedes", "senha": "ana.guedes@email.com"},
    ]
    conjunto_cli = tabela_clientes.preparar_conjunto_insercao(dados_clientes)
    num_inseridos = executor.inserir_conjunto(conjunto_cli)

    script_construtor = ConstrutorSelect(tabela_clientes).onde("id", OperadorComparacao.Igual, 1).gerar_script()
    #resultados_finais = executor.consultar(script_construtor)

   # print(resultados_finais)
    username = "20"
    script_select_username = (
        ConstrutorSelect(tabela_clientes)
        .selecionar("username")
        .onde("username", OperadorComparacao.Igual, username)
    ).gerar_script()
    
    print(script_select_username)