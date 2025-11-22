from enums import *

class Produto:
    @staticmethod
    def _get_or_create_id(bd, tabela, coluna, valor): 
        # Verifica se o valor existe, senão cria e retorna o id, para as tabelas auxiliares
        bd.cursor.execute(f"SELECT id FROM {tabela} WHERE {coluna} = %s", (valor,))

        resultado = bd.cursor.fetchone()
        if resultado: 
            return resultado['id']
        
        bd.cursor.execute(f"INSERT INTO {tabela} ({coluna}) VALUES (%s)", (valor,))
        bd.conn.commit()
        return bd.cursor.lastrowid

    @staticmethod
    def criar(bd, store_id, nome, categoria, descricao, preco, stock):
        try:
            name_id = Produto._get_or_create_id(bd, "product_names", "nome", nome)
            categoria_id = Produto._get_or_create_id(bd, "categories", "nome", categoria)
            desc_id = Produto._get_or_create_id(bd, "descriptions", "texto", descricao)

            sql = """
                INSERT INTO products (store_id, product_name_id, category_id, description_id, preco, stock) 
                VALUES (%s, %s, %s, %s, %s, %s)
            """

            bd.cursor.execute(sql, (store_id, name_id, categoria_id, desc_id, preco, stock))
            bd.conn.commit()
            return Mensagem.ADICIONADO
        except Exception:
            return Mensagem.ERRO_DUPLICADO # Quando o atributo

    @staticmethod
    def listar_todos(bd, filtros=""):
        # O sql pega os valores das várias tabelas para apresentar uma visão completa do produto
        sql = """
            SELECT products.id, product_names.nome, categories.nome as categoria, descriptions.texto as descricao, products.preco, products.stock, stores.nome as loja
            FROM products
            JOIN product_names ON products.product_name_id = product_names.id
            JOIN categories ON products.category_id = categories.id
            JOIN descriptions ON products.description_id = descriptions.id
            JOIN stores ON products.store_id = stores.id
        """ + filtros

        bd.cursor.execute(sql)
        resultado = bd.cursor.fetchall()

        # Converter Decimal para float
        for resultado in resultado: # Edita dentro do proprio objeto resultado sem criar um novo objeto
            resultado['preco'] = float(resultado['preco'])

        return resultado

    @staticmethod
    def verificar_alertas(bd):
        bd.cursor.execute("""
            SELECT p.id, n.nome, p.stock, s.nome as loja
            FROM products p JOIN product_names n ON p.product_name_id = n.id 
            JOIN stores s ON p.store_id = s.id
            WHERE p.stock < 5
        """)
        return bd.cursor.fetchall()

    @staticmethod
    def atualizar_produto(bd, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_id_da_loja=None):
        bd.cursor.execute("SELECT store_id FROM products WHERE id = %s", (id_produto,))
        resultado = bd.cursor.fetchone()
        if not resultado:
            return Mensagem.NAO_ENCONTRADO

        campos, vals = [], []
        if novo_preco:
            campos.append("preco=%s")
            vals.append(float(novo_preco))

        if novo_stock:
            campos.append("stock=%s")
            vals.append(int(novo_stock))

        if nova_descricao:
            desc_id = Produto._get_or_create_id(bd, "descriptions", "texto", nova_descricao)
            campos.append("description_id=%s")
            vals.append(desc_id)
            
        if nova_categoria:
            categoria_id = Produto._get_or_create_id(bd, "categories", "nome", nova_categoria)
            campos.append("category_id=%s")
            vals.append(categoria_id)

        if novo_id_da_loja:
            if Vendedor.verificar_loja_valida(bd, novo_id_da_loja) is False:
                return Mensagem.LOJA_NAO_ENCONTRADA
            
            campos.append("store_id=%s")
            vals.append(novo_id_da_loja)

        if not campos: # Se não há campos para atualizar
            return Mensagem.ATUALIZADO
        
        vals.append(id_produto)
        
        # Atualiza os campos necessários
        try:
            bd.cursor.execute(f"UPDATE products SET {','.join(campos)} WHERE id=%s", tuple(vals))
            bd.conn.commit()
            
            if bd.cursor.rowcount > 0:
                return Mensagem.ATUALIZADO
        except:
            pass

        return Mensagem.NAO_ENCONTRADO

# Utilizadores
class User:
    def __init__(self, id, bd):
        self.id = id
        self.bd = bd
        self.username = ""
        self.password = ""
        self.cargo = None
        self.store_id = None
        self._carregar()

    def _carregar(self):
        self.bd.cursor.execute("SELECT * FROM users WHERE id = %s", (self.id,))
        resultado = self.bd.cursor.fetchone()
        if resultado:
            self.username = resultado['username']
            self.cargo = resultado['cargo_type']
            self.store_id = resultado['store_id']

    @staticmethod
    def login(bd, username, password):
        sql = "SELECT id, cargo_type FROM users WHERE username = %s AND password = %s"
        bd.cursor.execute(sql, (username, password))
        resultado = bd.cursor.fetchone()
        if resultado:
            cargo = resultado['cargo_type']

            match cargo: # match para limitar o cargo ás classes existentes e facilitar a leitura
                case 'admin':
                    return Admin(resultado['id'], bd)
                case 'vendedor':
                    return Vendedor(resultado['id'], bd)
                case 'cliente':
                    return Cliente(resultado['id'], bd)
        return None

class Cliente(User):
    @staticmethod
    def registar(bd, username, password):
        try:
            sql = "INSERT INTO users (username, password, cargo_type) VALUES (%s, %s, 'cliente')"
            bd.cursor.execute(sql, (username, password))
            bd.conn.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except:
            return Mensagem.UTILIZADOR_JA_EXISTE
        
    def realizar_venda(self, itens, id_cliente_alvo=None):
        if id_cliente_alvo is not None:
            comprador = id_cliente_alvo
        else:
            comprador = self.id

        if not itens or not isinstance(itens, dict):
            return Mensagem.ERRO_PROCESSAMENTO

        loja_pedido = None
        total_price = 0.0
        produtos_info = []

        try:
            for product_id, quantidade in itens.items():
                self.bd.cursor.execute("SELECT stock, preco, store_id FROM products WHERE id = %s", (product_id,))
                prod = self.bd.cursor.fetchone()

                if not prod or prod['stock'] < quantidade:
                    return Mensagem.STOCK_INSUFICIENTE

                if loja_pedido is None: # Primeiro produto
                    loja_pedido = prod['store_id']
                elif loja_pedido != prod['store_id']: # Verifica se todos os produtos são da mesma loja
                    return Mensagem.ERRO_PROCESSAMENTO

                unit_price = float(prod['preco'])
                produtos_info.append((product_id, quantidade, unit_price))
                total_price += unit_price * quantidade

            self.bd.cursor.execute(
                "INSERT INTO orders (buyer_user_id, store_id, status, total_price) VALUES (%s, %s, 'pendente', %s)",
                (comprador, loja_pedido, total_price)
            )
            order_id = self.bd.cursor.lastrowid # ID do pedido criado

            for product_id, quantidade, unit_price in produtos_info:
                self.bd.cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                    (order_id, product_id, quantidade, unit_price)
                )
                self.bd.cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (quantidade, product_id))

            self.bd.conn.commit()
            return (Mensagem.PENDENTE, {'order_id': order_id, 'total_price': total_price})
        except Exception:
            self.bd.conn.rollback()
            return Mensagem.ERRO_PROCESSAMENTO

    def ver_meu_historico(self):
        # Obtem o historico de compras, juntando os dados das várias tabelas
        sql = """
            SELECT orders.order_date, order_items.product_id, product_names.nome as produto, order_items.quantity, order_items.unit_price, stores.nome as loja, orders.status
            FROM orders
            JOIN order_items ON order_items.order_id = orders.id
            JOIN products ON order_items.product_id = products.id
            JOIN product_names ON products.product_name_id = product_names.id
            JOIN stores ON orders.store_id = stores.id
            WHERE orders.buyer_user_id = %s
            ORDER BY orders.order_date DESC
        """

        self.bd.cursor.execute(sql, (self.id,)) # "," pois é uma tupla
        resultado = self.bd.cursor.fetchall() 

        for resultado_linha in resultado: # Edita dentro do proprio objeto resultado sem criar um novo objeto
            resultado_linha['unit_price'] = float(resultado_linha['unit_price'])
            resultado_linha['order_date'] = str(resultado_linha['order_date'])

        return resultado

class Vendedor(Cliente):
    @staticmethod
    def registar(bd, username, password, store_id):
        if Vendedor.verificar_loja_valida(bd, store_id) is False:
            return Mensagem.LOJA_NAO_ENCONTRADA

        try:
            sql = "INSERT INTO users (username, password, cargo_type, store_id) VALUES (%s, %s, 'vendedor', %s)"
            bd.cursor.execute(sql, (username, password, store_id))
            bd.conn.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except:
            return Mensagem.UTILIZADOR_JA_EXISTE
        
    def atualizar_produto(self, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None):
        resultado_verificacao = self._verificar_permissao_vendedor(id_produto)
        if resultado_verificacao is not None:
            return resultado_verificacao
        
        # Chamar método estático da classe Produto
        return Produto.atualizar_produto(self.bd, id_produto, novo_preco, novo_stock, nova_descricao, nova_categoria)

    def concluir_pedido(self, order_id):
        resultado_verificacao = self._verificar_permissao_vendedor(order_id, verificar_pedido_status=True)
        if resultado_verificacao is not None:
            return resultado_verificacao

        try:
            # Atualiza o status para 'confirmada' e guarda qual vendedor confirmou
            self.bd.cursor.execute(
                "UPDATE orders SET status=%s, seller_user_id=%s WHERE id=%s", 
                ('confirmada', self.id, order_id)
            )
            self.bd.conn.commit()
            return Mensagem.CONCLUIDA
        except:
            self.bd.conn.rollback()
            return Mensagem.ERRO_PROCESSAMENTO
    
    def listar_pedidos(self, filtro_status=None):
        """Lista todos os pedidos da loja do vendedor com filtro opcional por status"""
        try:
            if filtro_status and filtro_status not in ['pendente', 'confirmada', 'concluida']:
                return []
            
            if filtro_status:
                sql = """
                    SELECT o.id, o.order_date, u.username as cliente, o.total_price, o.status
                    FROM orders o
                    JOIN users u ON o.buyer_user_id = u.id
                    WHERE o.store_id = %s AND o.status = %s
                    ORDER BY o.order_date DESC
                """
                self.bd.cursor.execute(sql, (self.store_id, filtro_status))
            else:
                sql = """
                    SELECT o.id, o.order_date, u.username as cliente, o.total_price, o.status
                    FROM orders o
                    JOIN users u ON o.buyer_user_id = u.id
                    WHERE o.store_id = %s
                    ORDER BY o.order_date DESC
                """
                self.bd.cursor.execute(sql, (self.store_id,))
            
            resultado = self.bd.cursor.fetchall()
            for linha in resultado:
                linha['order_date'] = str(linha['order_date'])
                linha['total_price'] = float(linha['total_price'])
            
            return resultado
        except Exception:
            return []
        
    def _verificar_permissao_vendedor(self, order_id, verificar_pedido_status=False):
        # Vendedor confirma um pedido pendente da sua loja
        self.bd.cursor.execute("SELECT store_id, status FROM orders WHERE id=%s", (order_id,))
        resultado = self.bd.cursor.fetchone()

        if not resultado:
            return Mensagem.NAO_ENCONTRADO
        
        if resultado['store_id'] != self.store_id:
            return Mensagem.ERRO_PERMISSAO

        if verificar_pedido_status and resultado['status'] != 'pendente':
            return Mensagem.ERRO_PROCESSAMENTO

        return None # Quando tem permissão

    @staticmethod
    def verificar_loja_valida(bd, store_id):
        bd.cursor.execute("SELECT id FROM stores WHERE id=%s", (store_id,))
        resultado = bd.cursor.fetchone()
        return resultado is not None

class Admin(Vendedor):
    @staticmethod
    def registar(bd, username, password):
        try:
            sql = "INSERT INTO users (username, password, cargo_type) VALUES (%s, %s, 'admin')"
            bd.cursor.execute(sql, (username, password))
            bd.conn.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except:
            return Mensagem.UTILIZADOR_JA_EXISTE
        
    def __init__(self, id, bd):
        super().__init__(id, bd)
        self.store_id = None
        self.retirar_id_da_loja_do_utilizador()
        
    def retirar_id_da_loja_do_utilizador(self):
        # Limpar store_id para garantir que não há associações indesejadas, 
        # Verifica se é "admin" só para garantir que um vendedor não seja afetado
        self.bd.cursor.execute("UPDATE users SET store_id=NULL WHERE id=%s AND cargo_type='admin'", (self.id,))
        self.bd.conn.commit()

    def adicionar_produto(self, nome, categoria, descricao, preco, stock, id_da_loja_do_produto):
        if id_da_loja_do_produto is None:
            return Mensagem.ERRO_LOJA_OBRIGATORIA
        
        return Produto.criar(self.bd, id_da_loja_do_produto, nome, categoria, descricao, preco, stock)

    def atualizar_produto(self, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None):
        return Produto.atualizar_produto(self.bd, id_produto, novo_preco, novo_stock, nova_descricao, nova_categoria)

    def remover_produto(self, id_produto):
        try:
            # Verifica se o produto existe
            self.bd.cursor.execute("SELECT id FROM products WHERE id=%s", (id_produto,))
            if not self.bd.cursor.fetchone():
                return Mensagem.NAO_ENCONTRADO
            
            # Remove o produto
            self.bd.cursor.execute("DELETE FROM products WHERE id=%s", (id_produto,))
            self.bd.conn.commit()
            
            if self.bd.cursor.rowcount > 0:
                return Mensagem.REMOVIDO

            return Mensagem.NAO_ENCONTRADO
        except Exception:
            self.bd.conn.rollback()
            return Mensagem.ERRO_GENERICO

    def ver_historico_global(self):
        sql = """
            SELECT orders.order_date, users.username as cliente, product_names.nome as produto, order_items.quantity, order_items.unit_price, stores.nome as loja, orders.status
            FROM orders
            JOIN users ON orders.buyer_user_id = users.id
            JOIN order_items ON order_items.order_id = orders.id
            JOIN products ON order_items.product_id = products.id
            JOIN product_names ON products.product_name_id = product_names.id
            JOIN stores ON orders.store_id = stores.id
            ORDER BY orders.order_date DESC
        """
        self.bd.cursor.execute(sql)
        resultado = self.bd.cursor.fetchall()

        for resultado in resultado:
            resultado['unit_price'] = float(resultado['unit_price'])
            resultado['order_date'] = str(resultado['order_date'])

        return resultado

    def concluir_pedido(self, order_id):
        try:
            self.bd.cursor.execute("SELECT id, status FROM orders WHERE id=%s", (order_id,)) # "," pois é uma tupla
            resultado = self.bd.cursor.fetchone()
            if not resultado or resultado['status'] != 'confirmada':
                return Mensagem.ERRO_PROCESSAMENTO
            
            self.bd.cursor.execute("UPDATE orders SET status=%s WHERE id=%s", ('concluida', order_id))
            self.bd.conn.commit()
            return Mensagem.CONCLUIDA
        except:
            self.bd.conn.rollback()
            return Mensagem.ERRO_PROCESSAMENTO