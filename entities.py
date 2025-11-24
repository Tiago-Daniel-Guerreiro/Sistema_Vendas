from enums import *

class Produto:
    @staticmethod
    def _get_or_create_id(bd, tabela, coluna, valor): 
        # Verifica se o valor existe, senão cria e retorna o id, para as tabelas auxiliares
        bd.cursor.execute(f"SELECT id FROM {tabela} WHERE {coluna} = %s", (valor,))

        resultado = bd.cursor.fetchone()
        if resultado is not None: 
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
            return Mensagem.ERRO_DUPLICADO

    @staticmethod
    def listar_todos(bd, store_id=None, filtros_extras=None):
        # CORREÇÃO SQL INJECTION: Usar parametros bindados
        sql = """
            SELECT products.id, product_names.nome, categories.nome as categoria, descriptions.texto as descricao, products.preco, products.stock, stores.nome as loja
            FROM products
            JOIN product_names ON products.product_name_id = product_names.id
            JOIN categories ON products.category_id = categories.id
            JOIN descriptions ON products.description_id = descriptions.id
            JOIN stores ON products.store_id = stores.id
        """
        
        parametoetos = []
        clauses = []

        if store_id is not None:
            clauses.append("products.store_id = %s")
            parametoetos.append(store_id)
            
        # Exemplo de filtros extras (dicionário)
        if filtros_extras:
            if 'categoria' in filtros_extras:
                clauses.append("categories.nome = %s")
                parametoetos.append(filtros_extras['categoria'])
            if 'preco_max' in filtros_extras:
                clauses.append("products.preco <= %s")
                parametoetos.append(filtros_extras['preco_max'])

        if clauses:
            sql += " WHERE " + " AND ".join(clauses)

        bd.cursor.execute(sql, tuple(parametoetos))
        resultado = bd.cursor.fetchall()

        for res in resultado:
            res['preco'] = float(res['preco'])

        return resultado

    @staticmethod
    def verificar_stock_baixo(bd):
        # Método removido da classe Produto e movido para Vendedor
        pass

    @staticmethod
    def atualizar_produto(bd, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_id_da_loja=None, novo_nome=None):
        bd.cursor.execute("SELECT store_id FROM products WHERE id = %s", (id_produto,))
        resultado = bd.cursor.fetchone()
        if not resultado:
            return Mensagem.NAO_ENCONTRADO

        campos, valores = [], []
        if novo_preco is not None:
            campos.append("preco=%s")
            valores.append(float(novo_preco))

        if novo_stock is not None:
            campos.append("stock=%s")
            valores.append(int(novo_stock))

        if nova_descricao is not None:
            desc_id = Produto._get_or_create_id(bd, "descriptions", "texto", nova_descricao)
            campos.append("description_id=%s")
            valores.append(desc_id)
            
        if nova_categoria is not None:
            categoria_id = Produto._get_or_create_id(bd, "categories", "nome", nova_categoria)
            campos.append("category_id=%s")
            valores.append(categoria_id)

        if novo_nome is not None:
            name_id = Produto._get_or_create_id(bd, "product_names", "nome", novo_nome)
            campos.append("product_name_id=%s")
            valores.append(name_id)

        if novo_id_da_loja is not None:
            if Vendedor.verificar_loja_valida(bd, novo_id_da_loja) is False:
                return Mensagem.LOJA_NAO_ENCONTRADA
            
            campos.append("store_id=%s")
            valores.append(novo_id_da_loja)

        if not campos: 
            return Mensagem.ATUALIZADO
        
        valores.append(id_produto)

        try:
            bd.cursor.execute(f"UPDATE products SET {','.join(campos)} WHERE id=%s", tuple(valores))
            bd.conn.commit()
            
            if bd.cursor.rowcount > 0:
                return Mensagem.ATUALIZADO
        except:
            pass

        return Mensagem.NAO_ENCONTRADO
    
    @staticmethod
    def remover_produto(bd, id_produto):
        try:
            # Verifica se o produto existe
            bd.cursor.execute("SELECT id FROM products WHERE id=%s", (id_produto,))
            if not bd.cursor.fetchone():
                return Mensagem.NAO_ENCONTRADO
            
            # Remove o produto
            bd.cursor.execute("DELETE FROM products WHERE id=%s", (id_produto,))
            bd.conn.commit()
            
            if bd.cursor.rowcount > 0:
                return Mensagem.REMOVIDO

            return Mensagem.NAO_ENCONTRADO
        except Exception:
            bd.conn.rollback()
            return Mensagem.ERRO_GENERICO

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
            self.cargo = resultado['cargo']
            self.store_id = resultado['store_id']

    @staticmethod
    def login(bd, username, password):
        sql = "SELECT id, cargo FROM users WHERE username = %s AND password = %s"
        bd.cursor.execute(sql, (username, password))
        resultado = bd.cursor.fetchone()
        if resultado:
            cargo = resultado['cargo']

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
            # Clientes não têm loja associada, logo store_id é NULL
            sql = "INSERT INTO users (username, password, cargo) VALUES (%s, %s, 'cliente')"
            bd.cursor.execute(sql, (username, password))
            bd.conn.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except:
            return Mensagem.UTILIZADOR_JA_EXISTE

    def promover_a_admin(self):
        if self.cargo == 'admin':
            return Mensagem.O_PERFIL_JA_E_ADMIN
        try:
            self.bd.cursor.execute("UPDATE users SET cargo = 'admin' WHERE id = %s", (self.id,))
            self.bd.conn.commit()
            return Mensagem.SUCESSO
        except:
            self.bd.conn.rollback()
            return Mensagem.ERRO_GENERICO
    def realizar_venda(self, itens, status_inicial='pendente'):
        # Refatorado: Cliente usa sempre o seu ID como comprador
        comprador = self.id

        if not itens or not isinstance(itens, dict):
            return Mensagem.ERRO_PROCESSAMENTO

        loja_pedido = None
        total_price = 0.0
        produtos_info = []

        try:
            for product_id, quantidade in itens.items():
                self.bd.cursor.execute("SELECT stock, preco, store_id FROM products WHERE id = %s", (product_id,))
                product = self.bd.cursor.fetchone()

                if not product or product['stock'] < quantidade:
                    return Mensagem.STOCK_INSUFICIENTE

                if loja_pedido is None: 
                    loja_pedido = product['store_id']
                elif loja_pedido != product['store_id']: 
                    return Mensagem.ERRO_PROCESSAMENTO

                unit_price = float(product['preco'])
                produtos_info.append((product_id, quantidade, unit_price))
                total_price += unit_price * quantidade

            # Cria o pedido com o status definido (pendente para cliente, concluida para vendedor)
            self.bd.cursor.execute(
                "INSERT INTO orders (buyer_user_id, store_id, status, total_price) VALUES (%s, %s, %s, %s)",
                (comprador, loja_pedido, status_inicial, total_price)
            )
            order_id = self.bd.cursor.lastrowid 

            for product_id, quantidade, unit_price in produtos_info:
                self.bd.cursor.execute(
                    "INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES (%s, %s, %s, %s)",
                    (order_id, product_id, quantidade, unit_price)
                )
                self.bd.cursor.execute("UPDATE products SET stock = stock - %s WHERE id = %s", (quantidade, product_id))

            self.bd.conn.commit()
            
            msg_retorno = Mensagem.PENDENTE if status_inicial == 'pendente' else Mensagem.CONCLUIDA
            return (msg_retorno, {'order_id': order_id, 'total_price': total_price})
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
        """ # Desc = Data por ordem Descresente

        self.bd.cursor.execute(sql, (self.id,)) # "," pois é uma tupla
        resultado = self.bd.cursor.fetchall() 

        for resultado in resultado: # Edita dentro do proprio objeto resultado sem criar um novo objeto
            resultado['unit_price'] = float(resultado['unit_price'])
            resultado['order_date'] = str(resultado['order_date'])

        return resultado

class Vendedor(Cliente):
    @staticmethod
    def registar(bd, username, password, store_id):
        if Vendedor.verificar_loja_valida(bd, store_id) is False:
            return Mensagem.LOJA_NAO_ENCONTRADA

        try:
            sql = "INSERT INTO users (username, password, cargo, store_id) VALUES (%s, %s, 'vendedor', %s)"
            bd.cursor.execute(sql, (username, password, store_id))
            bd.conn.commit()
            return Mensagem.UTILIZADOR_CRIADO
        except:
            return Mensagem.UTILIZADOR_JA_EXISTE

    def atualizar_produto(self, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_nome=None):
        # Vendedor só pode atualizar produtos da sua loja
        verificacao = self._verificar_pedido_permissao_vendedor(id_produto, verificar_pedido_status=False)
        if verificacao is not None:
            return verificacao
            
        return Produto.atualizar_produto(self.bd, id_produto, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_nome=novo_nome)

    @staticmethod
    def verificar_stock_baixo(bd):
        try:
            # Verifica produtos com stock < 5
            sql = """
                SELECT p.id, pn.nome, p.stock, s.nome as loja
                FROM products p
                JOIN product_names pn ON p.product_name_id = pn.id
                JOIN stores s ON p.store_id = s.id
                WHERE p.stock < 5
            """
            bd.cursor.execute(sql)
            produtos = bd.cursor.fetchall()
            
            if not produtos:
                return Mensagem.SUCESSO 
            
            return (Mensagem.ALERTA_STOCK_BAIXO, produtos)
        except Exception:
            return Mensagem.ERRO_GENERICO

    def concluir_pedido(self, order_id):
        # Simplificado: Remove verificação de 'confirmada', passa direto para 'concluida'
        resultado_verificacao = self._verificar_pedido_permissao_vendedor(order_id, verificar_pedido_status=True)
        if resultado_verificacao is not None:
            return resultado_verificacao

        try:
            self.bd.cursor.execute(
                "UPDATE orders SET status=%s, seller_user_id=%s WHERE id=%s", 
                ('concluida', self.id, order_id)
            )
            self.bd.conn.commit()
            return Mensagem.CONCLUIDA
        except:
            self.bd.conn.rollback()
            return Mensagem.ERRO_PROCESSAMENTO
    
    def listar_pedidos(self, filtro_status=None):
        try:
            # Correção SQL: Alternar lógica baseada no filtro
            sql = """
                SELECT o.id, o.order_date, u.username as cliente, o.total_price, o.status
                FROM orders o
                JOIN users u ON o.buyer_user_id = u.id
                WHERE o.store_id = %s
            """
            parametoetos = [self.store_id]

            if filtro_status and filtro_status in ['pendente', 'concluida']:
                sql += " AND o.status = %s"
                parametoetos.append(filtro_status)
            
            sql += " ORDER BY o.order_date DESC"
            
            self.bd.cursor.execute(sql, tuple(parametoetos))
            resultado = self.bd.cursor.fetchall()

            for linha in resultado:
                linha['total_price'] = float(linha['total_price']) 
                linha['order_date'] = str(linha['order_date'])

            return resultado
        except Exception:
            return []
        
    def _verificar_pedido_permissao_vendedor(self, id_alvo, verificar_pedido_status=False):
        # Verifica se é produto ou pedido para saber qual tabela consultar
        # Simplificação: assume que id_alvo é order_id se verificar_pedido_status=True
        tabela = "orders" if verificar_pedido_status else "products"
        
        self.bd.cursor.execute(f"SELECT store_id FROM {tabela} WHERE id=%s", (id_alvo,))
        resultado = self.bd.cursor.fetchone()

        if not resultado:
            return Mensagem.NAO_ENCONTRADO
        
        if resultado['store_id'] != self.store_id:
            return Mensagem.ERRO_PERMISSAO

        if verificar_pedido_status and tabela == "orders":
             # Se for pedido, verifica se está pendente antes de concluir
             self.bd.cursor.execute("SELECT status FROM orders WHERE id=%s", (id_alvo,))
             res_status = self.bd.cursor.fetchone()
             if res_status and res_status['status'] != 'pendente':
                 return Mensagem.ERRO_PROCESSAMENTO

        return None

    @staticmethod
    def verificar_loja_valida(bd, store_id):
        bd.cursor.execute("SELECT id FROM stores WHERE id=%s", (store_id,))
        resultado = bd.cursor.fetchone()
        return resultado is not None

class Admin(Vendedor):
    
    @staticmethod
    def registar(bd, username, password):
        try:
            sql = "INSERT INTO users (username, password, cargo) VALUES (%s, %s, 'admin')"
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
        self.bd.cursor.execute("UPDATE users SET store_id=NULL WHERE id=%s AND cargo='admin'", (self.id,))
        self.bd.conn.commit()

    def adicionar_produto(self, nome, categoria, descricao, preco, stock, id_da_loja_do_produto):
        if id_da_loja_do_produto is None:
            return Mensagem.ERRO_LOJA_OBRIGATORIA
        
        return Produto.criar(self.bd, id_da_loja_do_produto, nome, categoria, descricao, preco, stock)

    def atualizar_produto(self, id_produto, novo_preco=None, novo_stock=None, nova_descricao=None, nova_categoria=None, novo_nome=None, novo_id_da_loja=None):
        return Produto.atualizar_produto(self.bd, id_produto, novo_preco, novo_stock, nova_descricao, nova_categoria, novo_id_da_loja, novo_nome)

    def remover_produto(self, id_produto):
        Produto.remover_produto(self.bd,id_produto)

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

        for linha in resultado:
            linha['unit_price'] = float(resultado['unit_price'])
            linha['order_date'] = str(resultado['order_date'])

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