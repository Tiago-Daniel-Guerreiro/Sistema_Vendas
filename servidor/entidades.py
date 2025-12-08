import secrets
import datetime
import mysql.connector
from enums import Mensagem

class Sessao:
    _SEGUNDOS_POR_DIA = 86400  # 24h * 60m * 60s

    def __init__(self, bd, token=None):
        self.bd = bd
        self.token = token
        self.nome_utilizador = None
        self.data_criacao = None

        if self.token is not None:
            self._carregar()

    @staticmethod
    def obter_utilizador(bd, parametros):        
        token_sessao = parametros.get('token_sessao')
        nome_utilizador = parametros.get('username')
        palavra_passe = parametros.get('password')

        cargo_para_classe = {
            'admin': Admin,
            'vendedor': Vendedor,
            'cliente': Cliente
        }

        if token_sessao is not None:
            sql = "SELECT nome_utilizador FROM sessoes WHERE token = %s"
            bd.cursor.execute(sql, (token_sessao,))
            resultado = bd.cursor.fetchone()
            
            if resultado is not None and Sessao.validar_token(bd, token_sessao):
                utilizador_do_token = resultado['nome_utilizador']
                bd.cursor.execute("SELECT id, cargo FROM utilizadores WHERE nome_utilizador = %s", (utilizador_do_token,))
                dados_utilizador = bd.cursor.fetchone()
                
                if dados_utilizador is not None:
                    cargo = dados_utilizador['cargo']
                    id_util = dados_utilizador['id']
                    classe = cargo_para_classe.get(cargo)
                    if classe: # Se a classe correspondente ao cargo existir
                        return classe(id_util, bd) 

        if nome_utilizador is not None and palavra_passe is not None:
            return Utilizador.autenticar(bd, nome_utilizador, palavra_passe)
            
        return None

    @staticmethod
    def criar_token(): # cria um token de 32 bytes (64 caracteres hexadecimais)
        return secrets.token_hex(32) # hexadecimais = maicusculos + minúsculos + números

    @staticmethod
    def criar(bd, nome_utilizador, palavra_passe):
        sql = "SELECT token, data_criacao FROM sessoes WHERE nome_utilizador = %s ORDER BY data_criacao DESC LIMIT 1"
        bd.cursor.execute(sql, (nome_utilizador,))
        resultado = bd.cursor.fetchone() # fetchone retorna o valor do ultimo execute do cursor
        
        if resultado is None:
            novo_token = Sessao.criar_token()
            sql_insert = "INSERT INTO sessoes (token, nome_utilizador, palavra_passe, data_criacao) VALUES (%s, %s, %s, NOW())"
            bd.cursor.execute(sql_insert, (novo_token, nome_utilizador, palavra_passe))
            bd.conexao.commit()
            return Sessao(bd, novo_token)
        
        token_existente = resultado['token']
        data_criacao = resultado['data_criacao']
        data_criacao = datetime.datetime.fromisoformat(data_criacao) # Converte string para datetime
        delta = datetime.datetime.now() - data_criacao 
        segundos_restantes = Sessao._SEGUNDOS_POR_DIA - delta.total_seconds()
        
        if segundos_restantes > (Sessao._SEGUNDOS_POR_DIA / 4): # Se faltar mais de 6 horas para expirar, reutiliza o token
            return Sessao(bd, token_existente)

    def _carregar(self):
        sql = "SELECT nome_utilizador, data_criacao FROM sessoes WHERE token = %s"
        self.bd.cursor.execute(sql, (self.token,))
        resultado = self.bd.cursor.fetchone()
        if resultado is not None:
            self.nome_utilizador = resultado['nome_utilizador']
            self.data_criacao = resultado['data_criacao']

    def obter_credenciais(self):
        return {'token': self.token, 'username': self.nome_utilizador}

    def encerrar(self):
        if self.token is not None:
            self.bd.cursor.execute("DELETE FROM sessoes WHERE token = %s", (self.token,))
            self.bd.conexao.commit()
            
        self.token = None
        self.nome_utilizador = None
        self.data_criacao = None

    @staticmethod
    def validar_token(bd, token):
        sql = "SELECT data_criacao FROM sessoes WHERE token = %s"
        bd.cursor.execute(sql, (token,))
        resultado = bd.cursor.fetchone()
        if resultado is None: 
            return False
        
        data_criacao = resultado['data_criacao']
        if isinstance(data_criacao, str): 
            data_criacao = datetime.datetime.fromisoformat(data_criacao)

        delta = datetime.datetime.now() - data_criacao
        return delta.total_seconds() < Sessao._SEGUNDOS_POR_DIA

    @staticmethod
    def remover_expiradas(bd):
        bd.cursor.execute("DELETE FROM sessoes WHERE data_criacao < (NOW() - INTERVAL 1 DAY)")
        bd.conexao.commit()

class Produto:
    @staticmethod
    def _obter_ou_criar_id(bd, tabela, coluna, valor):
        bd.cursor.execute(f"SELECT id FROM {tabela} WHERE {coluna} = %s", (valor,))
        resultado = bd.cursor.fetchone()
        
        if resultado is not None: 
            return resultado['id']
        
        bd.cursor.execute(f"INSERT INTO {tabela} ({coluna}) VALUES (%s)", (valor,))
        bd.conexao.commit()
        return bd.cursor.lastrowid

    @staticmethod
    def criar(bd, id_loja, nome, categoria, descricao, preco, stock):
        try:
            id_nome = Produto._obter_ou_criar_id(bd, "nomes_produtos", "nome", nome)
            id_categoria = Produto._obter_ou_criar_id(bd, "categorias", "nome", categoria)
            id_descricao = Produto._obter_ou_criar_id(bd, "descricoes", "texto", descricao)

            sql = "INSERT INTO produtos (loja_id, nome_produto_id, categoria_id, descricao_id, preco, stock) VALUES (%s, %s, %s, %s, %s, %s)"
            bd.cursor.execute(sql, (id_loja, id_nome, id_categoria, id_descricao, preco, stock))
            bd.conexao.commit()
            return Mensagem.ADICIONADO
        except mysql.connector.IntegrityError:
            return Mensagem.ERRO_DUPLICADO
        except mysql.connector.Error: 
            return Mensagem.ERRO_GENERICO

    @staticmethod
    def listar_todos(bd, id_loja=None, filtros=None):
        sql = """
            SELECT p.id, pn.nome, c.nome as categoria, d.texto as descricao, p.preco, p.stock, l.nome as loja
            FROM produtos p
            JOIN nomes_produtos pn ON p.nome_produto_id = pn.id
            JOIN categorias c ON p.categoria_id = c.id
            JOIN descricoes d ON p.descricao_id = d.id
            JOIN lojas l ON p.loja_id = l.id
        """
        parametros, clausulas = [], []
        if id_loja is not None: 
            clausulas.append("p.loja_id = %s"); parametros.append(id_loja)
        if filtros is not None:
            if 'categoria' in filtros: 
                clausulas.append("c.nome = %s")
                parametros.append(filtros['categoria'])

            if 'preco_max' in filtros: 
                clausulas.append("p.preco <= %s")
                parametros.append(filtros['preco_max'])
                
        if len(clausulas) > 0: 
            sql += " WHERE " + " AND ".join(clausulas)

        bd.cursor.execute(sql, tuple(parametros))
        resultados = bd.cursor.fetchall()
        
        for linha in resultados: 
            linha['preco'] = float(linha['preco'])
            
        return resultados

    @staticmethod
    def atualizar_produto(bd, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_id_loja=None, novo_nome=None):
        bd.cursor.execute("SELECT loja_id FROM produtos WHERE id = %s", (id_produto,))
        if bd.cursor.fetchone() is None: # fetchone retorna o valor do ultimo execute do cursor
            return Mensagem.NAO_ENCONTRADO

        campos, valores = [], []
        if novo_preco is not None: 
            campos.append("preco=%s")
            valores.append(float(novo_preco))

        if novo_stock is not None: 
            campos.append("stock=%s")
            valores.append(int(novo_stock))
            
        if nova_descricao is not None: 
            campos.append("descricao_id=%s")
            valores.append(Produto._obter_ou_criar_id(bd, "descricoes", "texto", nova_descricao))
            
        if nova_categoria is not None: 
            campos.append("categoria_id=%s")
            valores.append(Produto._obter_ou_criar_id(bd, "categorias", "nome", nova_categoria))
            
        if novo_nome is not None: 
            campos.append("nome_produto_id=%s")
            valores.append(Produto._obter_ou_criar_id(bd, "nomes_produtos", "nome", novo_nome))
            
        if novo_id_loja is not None:
            if Vendedor.verificar_loja_valida(bd, novo_id_loja) is False: 
                return Mensagem.LOJA_NAO_ENCONTRADA
            
            campos.append("loja_id=%s")
            valores.append(novo_id_loja)
        
        if len(campos) == 0: 
            return Mensagem.ATUALIZADO
        
        valores.append(id_produto)
        sql = f"UPDATE produtos SET {', '.join(campos)} WHERE id=%s"
        bd.cursor.execute(sql, tuple(valores))
        bd.conexao.commit()
        
        if bd.cursor.rowcount > 0: # Se alguma linha foi afetada
            return Mensagem.ATUALIZADO

        return Mensagem.ERRO_PROCESSAMENTO

    @staticmethod
    def remover_produto(bd, id_produto):
        try:
            bd.cursor.execute("SELECT id FROM produtos WHERE id=%s", (id_produto,))
            if bd.cursor.fetchone() is None: # fetchone retorna o valor do ultimo execute do cursor
                return Mensagem.NAO_ENCONTRADO
            
            bd.cursor.execute("DELETE FROM produtos WHERE id=%s", (id_produto,))
            bd.conexao.commit()

            if bd.cursor.rowcount > 0: # Se alguma linha foi afetada
                return Mensagem.REMOVIDO 
            
            return Mensagem.ERRO_PROCESSAMENTO
        
        except mysql.connector.Error: 
            bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    @staticmethod
    def listar_categorias(bd):
        bd.cursor.execute("SELECT DISTINCT nome FROM categorias ORDER BY nome")
        categorias = []
        for linha in bd.cursor.fetchall(): 
            categorias.append(linha['nome'])
            
        return categorias

    @staticmethod
    def listar_nomes_produtos(bd):
        bd.cursor.execute("SELECT DISTINCT nome FROM nomes_produtos ORDER BY nome")
        nomes = []
        for linha in bd.cursor.fetchall(): 
            nomes.append(linha['nome'])
        return nomes
    
    @staticmethod
    def listar_descricoes(bd):
        bd.cursor.execute("SELECT DISTINCT texto FROM descricoes ORDER BY texto")
        descricoes = []
        for linha in bd.cursor.fetchall(): 
            descricoes.append(linha['texto'])
            
        return descricoes

    @staticmethod
    def obter_id_pelo_nome_e_loja(bd, nome_produto, id_loja):
        sql = "SELECT p.id FROM produtos p JOIN nomes_produtos pn ON p.nome_produto_id = pn.id WHERE pn.nome = %s AND p.loja_id = %s"
        bd.cursor.execute(sql, (nome_produto, id_loja))
        resultado = bd.cursor.fetchone()
        
        if resultado is not None:
            return resultado['id'] 

        return None

class Utilizador:
    def __init__(self, id, bd):
        self.id = id
        self.bd = bd
        self.nome_utilizador = ""
        self.cargo = None
        self.id_loja = None
        self._carregar()

    def _carregar(self):
        self.bd.cursor.execute("SELECT nome_utilizador, cargo, loja_id FROM utilizadores WHERE id = %s", (self.id,))
        resultado = self.bd.cursor.fetchone() # fetchone retorna o valor do ultimo execute do cursor
        if resultado is not None:
            self.nome_utilizador = resultado['nome_utilizador']
            self.cargo = resultado['cargo']
            self.id_loja = resultado['loja_id']
    
    @staticmethod
    def autenticar(bd, nome_utilizador, palavra_passe):
        # Verifica se o nome de utilizador e senha estão corretos
        sql = "SELECT id, cargo FROM utilizadores WHERE nome_utilizador = %s AND palavra_passe = %s"
        bd.cursor.execute(sql, (nome_utilizador, palavra_passe))
        resultado = bd.cursor.fetchone()
        
        if resultado is None:
            # Credenciais inválidas (utilizador não existe ou senha incorreta)
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        # classe do cargo
        cargo_para_classe = {
            'admin': Admin,
            'vendedor': Vendedor,
            'cliente': Cliente
        }

        classe = cargo_para_classe.get(resultado['cargo'])
        if classe:
            return classe(resultado['id'], bd)
        return Mensagem.ERRO_GENERICO

    @staticmethod
    def verificar_loja_valida(bd, id_loja):
        bd.cursor.execute("SELECT id FROM lojas WHERE id=%s", (id_loja,))
        return bd.cursor.fetchone() is not None

    def remover_utilizador_com_verificacao(self):
        try:
            # Verifica se o utilizador tem encomendas associadas
            self.bd.cursor.execute("SELECT COUNT(*) as total FROM encomendas WHERE comprador_id = %s", (self.id,))
            if self.bd.cursor.fetchone()['total'] > 0: # Se o utilizador tiver encomendas
                return Mensagem.ERRO_PROCESSAMENTO
            
            # Remove o utilizador
            self.bd.cursor.execute("DELETE FROM utilizadores WHERE id = %s", (self.id,))
            self.bd.conexao.commit()
            if self.bd.cursor.rowcount > 0: # Se alguma linha foi afetada
                return Mensagem.REMOVIDO
            
            return Mensagem.NAO_ENCONTRADO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def editar_nome_utilizador(self, novo_nome):
        try:
            novo_nome_limpo = novo_nome.strip()
            if len(novo_nome_limpo) == 0:
                return Mensagem.CREDENCIAIS_INVALIDAS
            
            # Verificar se o novo nome de utilizador já existe
            self.bd.cursor.execute("SELECT id FROM utilizadores WHERE nome_utilizador = %s AND id != %s", (novo_nome_limpo, self.id))
            if self.bd.cursor.fetchone() is not None:
                return Mensagem.UTILIZADOR_JA_EXISTE

            # Atualizar nome de utilizador
            self.bd.cursor.execute("UPDATE utilizadores SET nome_utilizador = %s WHERE id = %s", (novo_nome_limpo, self.id))
            self.bd.conexao.commit()
            if self.bd.cursor.rowcount > 0: # Se alguma linha foi afetada
                self.nome_utilizador = novo_nome_limpo
                return Mensagem.ATUALIZADO
            
            return Mensagem.ERRO_PROCESSAMENTO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def verificar_senha(self, senha):
        try:
            self.bd.cursor.execute("SELECT palavra_passe FROM utilizadores WHERE id = %s", (self.id,))
            resultado = self.bd.cursor.fetchone()
            
            if resultado is None:
                return False
            
            # Compara a senha fornecida com a armazenada na base de dados
            return resultado['palavra_passe'] == senha
            
        except mysql.connector.Error:
            return False

    def editar_senha(self, nova_senha):
        if nova_senha is None or len(nova_senha) == 0:
            return Mensagem.PARAMETROS_INVALIDOS
        
        try:
            # Verificar se o utilizador existe
            self.bd.cursor.execute("SELECT palavra_passe FROM utilizadores WHERE id = %s", (self.id,))
            resultado = self.bd.cursor.fetchone()
            
            if resultado is None:
                return Mensagem.NAO_ENCONTRADO
            
            # Atualizar senha
            self.bd.cursor.execute("UPDATE utilizadores SET palavra_passe = %s WHERE id = %s", (nova_senha, self.id))
            self.bd.conexao.commit()
            
            # Sempre retorna sucesso se não houve erro, mesmo que a senha seja igual
            return Mensagem.ATUALIZADO
            
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def listar_lojas(self):
        try:
            self.bd.cursor.execute("SELECT id, nome, localizacao FROM lojas ORDER BY nome ASC")
            return self.bd.cursor.fetchall()
        except mysql.connector.Error:
            return []

# Cliente herda de Utilizador. Representa um cliente/comprador.	
class Cliente(Utilizador):
    def __init__(self, id, bd):
        super().__init__(id, bd)
    
    @staticmethod
    def registar(bd, nome_utilizador, palavra_passe):
        try:
            sql = "INSERT INTO utilizadores (nome_utilizador, palavra_passe, cargo) VALUES (%s, %s, 'cliente')"
            bd.cursor.execute(sql, (nome_utilizador, palavra_passe))
            bd.conexao.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except mysql.connector.IntegrityError:
            return Mensagem.UTILIZADOR_JA_EXISTE
            
    def promover_a_admin(self):
        if self.cargo == 'admin':
            return Mensagem.O_PERFIL_JA_E_ADMIN
        try:
            self.bd.cursor.execute("UPDATE utilizadores SET cargo = 'admin' WHERE id = %s", (self.id,))
            self.bd.conexao.commit()
            if self.bd.cursor.rowcount > 0: # Se alguma linha foi afetada
                return Mensagem.SUCESSO
            
            return Mensagem.ERRO_PROCESSAMENTO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def realizar_encomenda(self, itens, estado_inicial='pendente'):
        if itens is None or not isinstance(itens, dict) or len(itens) == 0:
            return Mensagem.ERRO_PROCESSAMENTO
        
        id_loja_encomenda = None
        preco_total = 0.0
        produtos_info = []
        try:
            for id_produto, quantidade in itens.items():
                self.bd.cursor.execute("SELECT stock, preco, loja_id FROM produtos WHERE id = %s", (id_produto,))
                produto_bd = self.bd.cursor.fetchone()

                if produto_bd is None:
                    self.bd.conexao.rollback()
                    return Mensagem.PRODUTO_NAO_ENCONTRADO
                
                if produto_bd['stock'] < quantidade:
                    self.bd.conexao.rollback()
                    return Mensagem.STOCK_INSUFICIENTE

                # Acontece na primeira iteração para definir a loja da encomenda
                if id_loja_encomenda is None:
                    id_loja_encomenda = produto_bd['loja_id']

                # Garante que todos os produtos no carrinho são da mesma loja
                elif id_loja_encomenda != produto_bd['loja_id']:
                    self.bd.conexao.rollback()
                    return Mensagem.ERRO_PROCESSAMENTO
                
                preco_unitario = float(produto_bd['preco'])
                produtos_info.append((id_produto, quantidade, preco_unitario))
                preco_total += preco_unitario * quantidade

            sql_encomenda = "INSERT INTO encomendas (comprador_id, loja_id, estado, preco_total) VALUES (%s, %s, %s, %s)"
            self.bd.cursor.execute(sql_encomenda, (self.id, id_loja_encomenda, estado_inicial, preco_total))
            id_encomenda = self.bd.cursor.lastrowid # ID da encomenda recém-criada

            for id_prod, quant, preco_un in produtos_info:
                sql_item = "INSERT INTO itens_encomenda (encomenda_id, produto_id, quantidade, preco_unitario) VALUES (%s, %s, %s, %s)"
                self.bd.cursor.execute(sql_item, (id_encomenda, id_prod, quant, preco_un))
                self.bd.cursor.execute("UPDATE produtos SET stock = stock - %s WHERE id = %s", (quant, id_prod))

            self.bd.conexao.commit()
            
            if estado_inicial == 'pendente':
                return (Mensagem.PENDENTE, {'id_encomenda': id_encomenda, 'preco_total': preco_total})

            return Mensagem.CONCLUIDA
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_PROCESSAMENTO

    def ver_historico_compras(self):
        return self.ver_historico_pessoal()

    def ver_historico_pessoal(self):
        sql = """
            SELECT e.data_encomenda, pn.nome as produto, ie.quantidade, ie.preco_unitario, l.nome as loja, e.estado
            FROM encomendas e
            JOIN itens_encomenda ie ON ie.encomenda_id = e.id
            JOIN produtos p ON ie.produto_id = p.id
            JOIN nomes_produtos pn ON p.nome_produto_id = pn.id
            JOIN lojas l ON e.loja_id = l.id
            WHERE e.comprador_id = %s ORDER BY e.data_encomenda DESC
        """
        try:
            self.bd.cursor.execute(sql, (self.id,))
            resultados = self.bd.cursor.fetchall()
            for linha in resultados:
                linha['preco_unitario'] = float(linha['preco_unitario'])
                linha['data_encomenda'] = str(linha['data_encomenda'])
            return resultados
        except mysql.connector.Error:
            return []

# Vendedor herda de Cliente, pois um vendedor também pode ser um cliente.	
class Vendedor(Cliente):
    def __init__(self, id, bd):
        super().__init__(id, bd)
    
    @staticmethod
    def registar(bd, nome_utilizador, palavra_passe, id_loja):
        if Utilizador.verificar_loja_valida(bd, id_loja) is False:
            return Mensagem.LOJA_NAO_ENCONTRADA
        try:
            sql = "INSERT INTO utilizadores (nome_utilizador, palavra_passe, cargo, loja_id) VALUES (%s, %s, 'vendedor', %s)"
            bd.cursor.execute(sql, (nome_utilizador, palavra_passe, id_loja))
            bd.conexao.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except mysql.connector.IntegrityError:
            return Mensagem.UTILIZADOR_JA_EXISTE

    def _verificar_permissao_produto(self, id_produto):
        self.bd.cursor.execute("SELECT loja_id FROM produtos WHERE id=%s", (id_produto,))
        resultado = self.bd.cursor.fetchone()
        if resultado is None:
            return Mensagem.NAO_ENCONTRADO
        if resultado['loja_id'] != self.id_loja:
            return Mensagem.ERRO_PERMISSAO
        return None

    def _verificar_permissao_encomenda(self, id_encomenda):
        self.bd.cursor.execute("SELECT loja_id, estado FROM encomendas WHERE id=%s", (id_encomenda,))
        resultado = self.bd.cursor.fetchone()
        if resultado is None:
            return Mensagem.NAO_ENCONTRADO
        
        if resultado['loja_id'] != self.id_loja:
            return Mensagem.ERRO_PERMISSAO
        
        if resultado['estado'] != 'pendente':
            return Mensagem.ERRO_PROCESSAMENTO
        return None

    def atualizar_produto(self, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_nome=None):
        permissao = self._verificar_permissao_produto(id_produto)
        if permissao is not None:
            return permissao # Retorna a mensagem de erro se a permissão falhar
        return Produto.atualizar_produto(self.bd, id_produto, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome=novo_nome)

    def concluir_encomenda(self, id_encomenda):
        permissao = self._verificar_permissao_encomenda(id_encomenda)
        if permissao is not None:
            return permissao # Retorna a mensagem de erro se a permissão falhar
        try:
            sql = "UPDATE encomendas SET estado=%s, vendedor_id=%s WHERE id=%s"
            self.bd.cursor.execute(sql, ('concluida', self.id, id_encomenda))
            self.bd.conexao.commit()
            if self.bd.cursor.rowcount > 0:
                return Mensagem.CONCLUIDA
            return Mensagem.ERRO_PROCESSAMENTO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO
    
    def listar_encomendas(self, filtro_estado=None):
        try:
            sql = """
                SELECT encomendas.id, encomendas.data_encomenda, utilizadores.nome_utilizador as cliente, encomendas.preco_total, encomendas.estado
                FROM encomendas
                JOIN utilizadores ON encomendas.comprador_id = utilizadores.id
                WHERE encomendas.loja_id = %s
            """
            parametros = [self.id_loja]
            if filtro_estado in ['pendente', 'concluida']:
                sql += " AND encomendas.estado = %s"
                parametros.append(filtro_estado)
            sql += " ORDER BY encomendas.data_encomenda DESC"
            self.bd.cursor.execute(sql, tuple(parametros))
            resultados = self.bd.cursor.fetchall()
            for linha in resultados:
                linha['preco_total'] = float(linha['preco_total'])
                linha['data_encomenda'] = str(linha['data_encomenda'])
            return resultados
        except mysql.connector.Error:
            return []

    @staticmethod
    def verificar_stock_baixo(bd):
        try:
            sql = """
                SELECT produtos.id, nomes_produtos.nome, produtos.stock, lojas.nome as loja
                FROM produtos
                JOIN nomes_produtos ON produtos.nome_produto_id = nomes_produtos.id
                JOIN lojas ON produtos.loja_id = lojas.id
                WHERE produtos.stock < 5
            """
            bd.cursor.execute(sql)
            produtos = bd.cursor.fetchall()
            if len(produtos) > 0:
                return (Mensagem.ALERTA_STOCK_BAIXO, produtos)
            return Mensagem.SUCESSO
        except mysql.connector.Error:
            return Mensagem.ERRO_GENERICO


    def ver_historico_vendas(self):
        sql = """
            SELECT encomendas.data_encomenda, utilizadores_comprador.nome_utilizador as cliente, 
                nomes_produtos.nome as produto, itens_encomenda.quantidade, itens_encomenda.preco_unitario, 
                lojas.nome as loja, encomendas.estado, utilizadores_vendedor.nome_utilizador as vendedor
            FROM encomendas
            JOIN utilizadores AS utilizadores_comprador ON encomendas.comprador_id = utilizadores_comprador.id
            JOIN itens_encomenda ON itens_encomenda.encomenda_id = encomendas.id
            JOIN produtos ON itens_encomenda.produto_id = produtos.id
            JOIN nomes_produtos ON produtos.nome_produto_id = nomes_produtos.id
            JOIN lojas ON encomendas.loja_id = lojas.id
            LEFT JOIN utilizadores AS utilizadores_vendedor ON encomendas.vendedor_id = utilizadores_vendedor.id
            WHERE encomendas.loja_id = %s
            ORDER BY encomendas.data_encomenda DESC
        """
        try:
            self.bd.cursor.execute(sql, (self.id_loja,))
            resultados = self.bd.cursor.fetchall()
            for linha in resultados:
                linha['preco_unitario'] = float(linha['preco_unitario'])
                linha['data_encomenda'] = str(linha['data_encomenda'])
            return resultados
        except mysql.connector.Error:
            return []

# Admin herda de Cliente, pois um admin também pode ser um cliente. 
# Não herda de vendedor, pois um admin não é necessariamente um vendedor.
# Não vende, e a herança complicaria a lógica e não estaria correta do ponto de vista técnico.
class Admin(Cliente):
    def __init__(self, id, bd):
        super().__init__(id, bd)
        self._remover_associacao_loja_bd()

    def _remover_associacao_loja_bd(self):
        # Garante que, na base de dados, este utilizador não tem loja associada.
        if self.id_loja is not None:
            self.bd.cursor.execute("UPDATE utilizadores SET loja_id=NULL WHERE id=%s AND cargo='admin'", (self.id,))
            self.bd.conexao.commit()
            self.id_loja = None

    def ver_historico_vendas(self, id_loja=None, id_vendedor=None):
        sql = """
            SELECT encomendas.data_encomenda, utilizadores_comprador.nome_utilizador as cliente, 
                nomes_produtos.nome as produto, itens_encomenda.quantidade, itens_encomenda.preco_unitario, 
                lojas.nome as loja, encomendas.estado, utilizadores_vendedor.nome_utilizador as vendedor
            FROM encomendas
            JOIN utilizadores AS utilizadores_comprador ON encomendas.comprador_id = utilizadores_comprador.id
            JOIN itens_encomenda ON itens_encomenda.encomenda_id = encomendas.id
            JOIN produtos ON itens_encomenda.produto_id = produtos.id
            JOIN nomes_produtos ON produtos.nome_produto_id = nomes_produtos.id
            JOIN lojas ON encomendas.loja_id = lojas.id
            LEFT JOIN utilizadores AS utilizadores_vendedor ON encomendas.vendedor_id = utilizadores_vendedor.id
        """
        clausulas_where = []
        parametros = []

        if id_loja is not None:
            clausulas_where.append("encomendas.loja_id = %s")
            parametros.append(id_loja)
            
        if id_vendedor is not None:
            clausulas_where.append("encomendas.vendedor_id = %s")
            parametros.append(id_vendedor)
        
        if len(clausulas_where) > 0:
            sql += " WHERE " + " AND ".join(clausulas_where)
        
        sql += " ORDER BY e.data_encomenda DESC"
        
        try:
            self.bd.cursor.execute(sql, tuple(parametros))
            resultados = self.bd.cursor.fetchall()
            for linha in resultados:
                linha['preco_unitario'] = float(linha['preco_unitario'])
                linha['data_encomenda'] = str(linha['data_encomenda'])
            return resultados
        except mysql.connector.Error:
            return []
        
    @staticmethod
    def registar(bd, nome_utilizador, palavra_passe):
        try:
            sql = "INSERT INTO utilizadores (nome_utilizador, palavra_passe, cargo, loja_id) VALUES (%s, %s, 'admin', NULL)"
            bd.cursor.execute(sql, (nome_utilizador, palavra_passe))
            bd.conexao.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except mysql.connector.IntegrityError:
            return Mensagem.UTILIZADOR_JA_EXISTE

    def adicionar_produto(self, nome, categoria, descricao, preco, stock, id_loja):
        if id_loja is None:
            return Mensagem.ERRO_LOJA_OBRIGATORIA
        return Produto.criar(self.bd, id_loja, nome, categoria, descricao, preco, stock)

    def atualizar_produto(self, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_nome=None, novo_id_loja=None):
        return Produto.atualizar_produto(self.bd, id_produto, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome, novo_id_loja)

    def remover_produto(self, id_produto):
        return Produto.remover_produto(self.bd, id_produto)

    def criar_loja(self, nome, localizacao):
        try:
            if len(nome.strip()) == 0 or len(localizacao.strip()) == 0:
                return Mensagem.CREDENCIAIS_INVALIDAS
            self.bd.cursor.execute("INSERT INTO lojas (nome, localizacao) VALUES (%s, %s)", (nome, localizacao))
            self.bd.conexao.commit()
            return Mensagem.ADICIONADO
        except mysql.connector.IntegrityError:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_DUPLICADO

    def editar_loja(self, id_loja, novo_nome=None, nova_localizacao=None):
        try:
            if not self.verificar_loja_valida(self.bd, id_loja):
                return Mensagem.NAO_ENCONTRADO
            
            campos, valores = [], []
            if novo_nome is not None: campos.append("nome=%s"); valores.append(novo_nome)
            if nova_localizacao is not None: campos.append("localizacao=%s"); valores.append(nova_localizacao)

            if len(campos) == 0: # Se não houver campos para atualizar
                return Mensagem.ATUALIZADO
            
            valores.append(id_loja)
            sql = f"UPDATE lojas SET {','.join(campos)} WHERE id=%s"
            self.bd.cursor.execute(sql, tuple(valores))
            self.bd.conexao.commit()

            if self.bd.cursor.rowcount > 0: # Se alguma linha foi afetada
                return Mensagem.ATUALIZADO
            
            return Mensagem.ERRO_PROCESSAMENTO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def apagar_loja(self, id_loja):
        try:
            if not self.verificar_loja_valida(self.bd, id_loja):
                return Mensagem.NAO_ENCONTRADO
            
            # Verifica se existem produtos ou utilizadores associados à loja
            self.bd.cursor.execute("SELECT COUNT(*) as total FROM produtos WHERE loja_id=%s", (id_loja,))
            if self.bd.cursor.fetchone()['total'] > 0:
                return Mensagem.ERRO_PROCESSAMENTO
            
            self.bd.cursor.execute("SELECT COUNT(*) as total FROM utilizadores WHERE loja_id=%s", (id_loja,))
            if self.bd.cursor.fetchone()['total'] > 0:
                return Mensagem.ERRO_PROCESSAMENTO

            self.bd.cursor.execute("DELETE FROM lojas WHERE id=%s", (id_loja,))
            self.bd.conexao.commit()

            if self.bd.cursor.rowcount > 0:
                return Mensagem.REMOVIDO

            return Mensagem.NAO_ENCONTRADO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def apagar_encomenda(self, id_encomenda):
        if id_encomenda is None:
            return Mensagem.NAO_ENCONTRADO
        try:
            self.bd.cursor.execute("DELETE FROM encomendas WHERE id = %s", (id_encomenda,))
            self.bd.conexao.commit()
            if self.bd.cursor.rowcount > 0:
                return Mensagem.SUCESSO
            return Mensagem.NAO_ENCONTRADO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def concluir_encomenda(self, id_encomenda):
        # O Admin pode concluir qualquer encomenda de qualquer loja.
        try:
            sql = "UPDATE encomendas SET estado=%s, vendedor_id=%s WHERE id=%s AND estado='pendente'"
            self.bd.cursor.execute(sql, ('concluida', self.id, id_encomenda))
            self.bd.conexao.commit()
            if self.bd.cursor.rowcount > 0:
                return Mensagem.CONCLUIDA
            return Mensagem.ERRO_PROCESSAMENTO
        except mysql.connector.Error:
            self.bd.conexao.rollback()
            return Mensagem.ERRO_GENERICO

    def ver_historico_global(self):
        sql = """
            SELECT encomendas.data_encomenda, utilizadores.nome_utilizador as cliente, nomes_produtos.nome as produto, itens_encomenda.quantidade, itens_encomenda.preco_unitario, lojas.nome as loja, encomendas.estado
            FROM encomendas
            JOIN utilizadores ON encomendas.comprador_id = utilizadores.id
            JOIN itens_encomenda ON itens_encomenda.encomenda_id = encomendas.id
            JOIN produtos ON itens_encomenda.produto_id = produtos.id
            JOIN nomes_produtos ON produtos.nome_produto_id = nomes_produtos.id
            JOIN lojas ON encomendas.loja_id = lojas.id
            ORDER BY encomendas.data_encomenda DESC
        """
        try:
            self.bd.cursor.execute(sql)
            resultados = self.bd.cursor.fetchall()
            for linha in resultados:
                linha['preco_unitario'] = float(linha['preco_unitario'])
                linha['data_encomenda'] = str(linha['data_encomenda'])
            return resultados
        except mysql.connector.Error:
            return []

    def listar_utilizadores(self, filtro_cargo=None, filtro_loja=None):
        try:
            sql = """
                SELECT utilizadores.id, utilizadores.nome_utilizador, utilizadores.cargo, lojas.nome as loja, lojas.id as id_loja
                FROM utilizadores
                LEFT JOIN lojas ON utilizadores.loja_id = lojas.id
                WHERE 1=1
            """
            parametros = []
            if filtro_cargo is not None:
                sql += " AND utilizadores.cargo = %s"
                parametros.append(filtro_cargo)
            if filtro_loja is not None:
                sql += " AND utilizadores.loja_id = %s"
                parametros.append(filtro_loja)
            sql += " ORDER BY utilizadores.cargo, utilizadores.nome_utilizador"
            self.bd.cursor.execute(sql, tuple(parametros))
            return self.bd.cursor.fetchall()
        except mysql.connector.Error:
            return []
