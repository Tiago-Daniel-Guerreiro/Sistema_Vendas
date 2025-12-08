from servidor.entidades import Admin, Vendedor, Cliente, Produto, Utilizador, Sessao
from enums import Mensagem
from servidor.configuracao import ConfiguracaoServidor

class Acoes:
    @staticmethod
    def ping():
        return Mensagem.PONG

    @staticmethod
    def help(gestor_comandos, utilizador_atual=None):
        comandos_agrupados = {}
        for comando_atual in gestor_comandos.comandos.values():
            pode_executar = comando_atual.validar_permissao(utilizador_atual)
            
            if pode_executar:
                categoria = comando_atual.categoria or 'outros'
                if categoria not in comandos_agrupados:
                    comandos_agrupados[categoria] = []
                
                # Adiciona apenas se não existe comando com mesmo nome na categoria
                existe = False
                for comando_existente in comandos_agrupados[categoria]:
                    if comando_existente.get('nome') == comando_atual.nome:
                        existe = True
                        break
                if existe is False:
                    comandos_agrupados[categoria].append(comando_atual.para_json())
        return {'comandos': comandos_agrupados}
    
    @staticmethod
    def autenticar(base_de_dados=None, parametros=None, **kwargs):        
        if parametros is None:
            parametros = {}
        
        if base_de_dados is None:
            return Mensagem.ERRO_GENERICO

        username = parametros.get('username')
        password = parametros.get('password')
        token_sessao = parametros.get('token_sessao')

        # Autenticação por token (sessão existente)
        if token_sessao is not None:
            if not Sessao.validar_token(base_de_dados, token_sessao):
                return Mensagem.CREDENCIAIS_INVALIDAS
            
            # Busca o utilizador associado ao token
            base_de_dados.cursor.execute("SELECT nome_utilizador FROM sessoes WHERE token = %s", (token_sessao,))
            resultado_sessao = base_de_dados.cursor.fetchone()
            
            if resultado_sessao is None:
                return Mensagem.CREDENCIAIS_INVALIDAS
            
            nome_utilizador_token = resultado_sessao['nome_utilizador']
            
            # Busca o utilizador completo
            base_de_dados.cursor.execute("SELECT id, cargo FROM utilizadores WHERE nome_utilizador = %s", (nome_utilizador_token,))
            dados_utilizador = base_de_dados.cursor.fetchone()
            
            if dados_utilizador is None:
                return Mensagem.CREDENCIAIS_INVALIDAS
            
            # Retorna informações da sessão válida
            return {
                'cargo': dados_utilizador['cargo'],
                'token': token_sessao,
                'username': nome_utilizador_token
            }

        # Autenticação por username e password (novo login)
        if username is not None and password is not None:
            resultado = Utilizador.autenticar(base_de_dados, username, password)

            # Se retornou uma Mensagem, há erro
            if isinstance(resultado, Mensagem):
                return resultado

            # resultado é um objeto Usuario
            utilizador = resultado

            # Cria sessão
            try:
                token = Sessao.criar_token()
                bd = base_de_dados
                nome_utilizador = utilizador.nome_utilizador
                if bd is not None and hasattr(bd, 'cursor') and hasattr(bd, 'conexao'):
                    bd.cursor.execute("INSERT INTO sessoes (token, nome_utilizador, data_criacao) VALUES (%s, %s, NOW())", (token, nome_utilizador))
                    bd.conexao.commit()
                    return {'cargo': utilizador.cargo, 'token': token}
                else:
                    return {'cargo': utilizador.cargo}
            except Exception:
                return {'cargo': utilizador.cargo}

        return Mensagem.PARAMETROS_INVALIDOS

    @staticmethod
    def registar(base_de_dados, parametros):
        nome = parametros.get('username')
        senha = parametros.get('password')
        return Cliente.registar(base_de_dados, nome, senha)

    @staticmethod
    def editar_senha(utilizador_atual, parametros):
        senha_atual = parametros.get('senha_atual')
        nova_senha = parametros.get('nova_senha')
        
        # Verifica se a senha atual foi fornecida e está correta
        if senha_atual is None:
            return Mensagem.PARAMETROS_INVALIDOS
        
        if not utilizador_atual.verificar_senha(senha_atual):
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        return utilizador_atual.editar_senha(nova_senha)
    
    @staticmethod
    def editar_nome_utilizador(utilizador_atual, parametros):
        novo_nome = parametros.get('novo_username')
        return utilizador_atual.editar_nome_utilizador(novo_nome)
    
    @staticmethod
    def apagar_utilizador(utilizador_atual):
        # Apenas permite a auto-remoção de um cliente.
        if isinstance(utilizador_atual, Cliente):
            return utilizador_atual.remover_utilizador_com_verificacao()
        return Mensagem.PERMISSAO_NEGADA

    @staticmethod
    def promover_para_admin(utilizador_atual, parametros):
        chave = parametros.get('chave')
        if chave != ConfiguracaoServidor.CHAVE_SECRETA_ADMIN:
            return Mensagem.PERMISSAO_NEGADA
        return utilizador_atual.promover_a_admin()

    @staticmethod
    def criar_funcionario(base_de_dados, parametros):
        nome_novo = parametros.get('nome_utilizador_novo')
        senha_nova = parametros.get('palavra_passe_nova')
        cargo = parametros.get('cargo')
        id_loja = parametros.get('id_loja')
        
        match cargo:
            case 'admin':
                return Admin.registar(base_de_dados, nome_novo, senha_nova)
            case 'vendedor':
                if id_loja is None:
                    return Mensagem.O_VENDEDOR_TEM_QUE_SER_ASSOCIADO_A_LOJA
                return Vendedor.registar(base_de_dados, nome_novo, senha_nova, id_loja)
            case _:
                return Mensagem.CARGO_INVALIDO
        
    @staticmethod
    def listar_utilizadores(utilizador_atual, parametros):
        filtro_cargo = parametros.get('filtro_cargo')
        filtro_loja = parametros.get('filtro_loja')
        return utilizador_atual.listar_utilizadores(filtro_cargo, filtro_loja)

    @staticmethod
    def listar_produtos(base_de_dados, parametros):
        id_loja = parametros.get('id_loja')
        filtros = {}
        if 'categoria' in parametros: 
            filtros['categoria'] = parametros['categoria']
        if 'preco_max' in parametros: 
            filtros['preco_max'] = parametros.get('preco_max')
        
        return Produto.listar_todos(base_de_dados, id_loja=id_loja, filtros=filtros)

    @staticmethod
    def adicionar_produto(utilizador_atual, parametros):
        nome = parametros.get('nome')
        categoria = parametros.get('categoria')
        descricao = parametros.get('descricao')
        preco = parametros.get('preco')
        stock = parametros.get('stock')
        id_loja = parametros.get('id_loja')
        return utilizador_atual.adicionar_produto(nome, categoria, descricao, preco, stock, id_loja)
    
    @staticmethod
    def realizar_encomenda(utilizador_atual, parametros):
        itens = parametros.get('itens')
        return utilizador_atual.realizar_encomenda(itens)
    
    @staticmethod
    def ver_historico_compras(utilizador_atual):
        return utilizador_atual.ver_historico_compras()
    
    @staticmethod
    def ver_historico_vendas(utilizador_atual):
        return utilizador_atual.ver_historico_vendas()
    
    @staticmethod
    def editar_produto(utilizador_atual, parametros):
        id_produto = parametros.get('id_produto')
        # As chaves no dicionário devem corresponder aos nomes dos parâmetros no método da entidade
        dados_novos = {
            'novo_preco': parametros.get('novo_preco'),
            'novo_stock': parametros.get('novo_stock'),
            'nova_descricao': parametros.get('nova_descricao'),
            'novo_nome': parametros.get('novo_nome'),
            'nova_categoria': parametros.get('nova_categoria'),
            'novo_id_loja': parametros.get('novo_id_loja') # Apenas o Admin usará este
        }
        return utilizador_atual.atualizar_produto(id_produto, **dados_novos)
    
    @staticmethod
    def apagar_produto(utilizador_atual, parametros):
        id_produto = parametros.get('id_produto')
        return utilizador_atual.remover_produto(id_produto)

    @staticmethod
    def concluir_encomenda(utilizador_atual, parametros):
        id_encomenda = parametros.get('id_encomenda')
        return utilizador_atual.concluir_encomenda(id_encomenda)
    
    @staticmethod
    def listar_encomendas(utilizador_atual, parametros):
        filtro = parametros.get('filtro_estado')
        return utilizador_atual.listar_encomendas(filtro)
    
    @staticmethod
    def verificar_stock_baixo(base_de_dados):
        return Vendedor.verificar_stock_baixo(base_de_dados)
    
    @staticmethod
    def apagar_encomenda(utilizador_atual, parametros):
        id_encomenda = parametros.get('id_encomenda')
        return utilizador_atual.apagar_encomenda(id_encomenda)

    @staticmethod
    def listar_lojas(utilizador_atual):
        return utilizador_atual.listar_lojas()

    @staticmethod
    def criar_loja(utilizador_atual, parametros):
        nome = parametros.get('nome')
        local = parametros.get('localizacao')
        return utilizador_atual.criar_loja(nome, local)
    
    @staticmethod
    def editar_loja(utilizador_atual, parametros):
        id_loja = parametros.get('id_loja')
        nome = parametros.get('novo_nome')
        local = parametros.get('nova_localizacao')
        return utilizador_atual.editar_loja(id_loja, nome, local)
    
    @staticmethod
    def apagar_loja(utilizador_atual, parametros):
        id_loja = parametros.get('id_loja')
        return utilizador_atual.apagar_loja(id_loja)

    @staticmethod
    def obter_produto_por_nome_loja(base_de_dados, parametros):
        nome_produto = parametros.get('nome_produto')
        id_loja = parametros.get('id_loja')
        return Produto.obter_id_pelo_nome_e_loja(base_de_dados, nome_produto, id_loja)
    
    @staticmethod
    def listar_categorias(base_de_dados):
        return Produto.listar_categorias(base_de_dados)

    @staticmethod
    def listar_nomes_produtos(base_de_dados):
        return Produto.listar_nomes_produtos(base_de_dados)

    @staticmethod
    def listar_descricoes(base_de_dados):
        return Produto.listar_descricoes(base_de_dados)

    @staticmethod
    def procurar_produto_por_nome(base_de_dados, parametros):
        nome_produto = parametros.get('nome_produto')
        id_loja = parametros.get('store_id')
        
        if nome_produto is None:
            return Mensagem.PARAMETROS_INVALIDOS
        
        # Busca o produto pelo nome e loja (se fornecida)
        resultado = Produto.obter_id_pelo_nome_e_loja(base_de_dados, nome_produto, id_loja)
        return resultado if resultado else Mensagem.NAO_ENCONTRADO

    @staticmethod
    def pesquisar_produtos(base_de_dados, parametros):
        nome_busca = parametros.get('nome', '').strip()
        loja_id = parametros.get('loja_id')
        preco_min = parametros.get('preco_min')
        preco_max = parametros.get('preco_max')
        
        if not nome_busca or len(nome_busca) < 2:
            return Mensagem.PARAMETROS_INVALIDOS
        
        try:
            # Procura na tabela de nomes primeiro
            sql = """
                SELECT DISTINCT p.id, p.preco, p.quantidade, p.loja_id, pn.nome
                FROM produtos p
                JOIN nomes_produtos pn ON p.nome_produto_id = pn.id
                WHERE pn.nome LIKE %s
            """
            params = [f"%{nome_busca}%"]

            # Adicionar filtros conforme necessário
            if loja_id:
                sql += " AND p.loja_id = %s"
                params.append(str(loja_id))

            if preco_min is not None:
                sql += " AND p.preco >= %s"
                params.append(str(preco_min))

            if preco_max is not None:
                sql += " AND p.preco <= %s"
                params.append(str(preco_max))

            sql += " ORDER BY pn.nome ASC"

            base_de_dados.cursor.execute(sql, params)
            resultados = base_de_dados.cursor.fetchall()

            if not resultados:
                return Mensagem.NAO_ENCONTRADO

            # Converte para dicionários com informações relevantes
            produtos_encontrados = []
            for linha in resultados:
                produtos_encontrados.append({
                    'id': linha['id'],
                    'nome': linha['nome'],
                    'preco': float(linha['preco']),
                    'quantidade': linha['quantidade'],
                    'loja_id': linha['loja_id']
                })

            return produtos_encontrados

        except Exception as e:
            return Mensagem.ERRO_GENERICO