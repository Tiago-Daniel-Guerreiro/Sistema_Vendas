import mysql.connector
from mysql.connector import Error

class DatabaseManager:
    def __init__(self, host='localhost', user='root', password='', database='sistema_vendas', limpar_base_de_dados = False):
        self.config = {'host': host, 'user': user, 'password': password}
        self.database = database 
        self.conn = None
        self.cursor = None
        self.__limpar_base_de_dados = limpar_base_de_dados


    def connect(self):
        while True:
            try:
                # Garante que a BD existe antes de tentar ligar a ela
                if not self.Verificar_Conectar_bd():
                    print("Falha ao verificar/criar base de dados. Tentando novamente...")
                    continue # Continua para o proximo loop

                # Adiciona a base de dados à configuração antes de conectar
                self.config['database'] = self.database
                self.conn = mysql.connector.connect(**self.config)
                self.cursor = self.conn.cursor(dictionary=True)
                self.create_tables()
                print(f"Conectado com sucesso a: {self.database}")
                return True
            except Error as e:
                print(f"Erro ao conectar ao MySQL: {e}. Tentando novamente...")
        
    def Verificar_Conectar_bd(self):
        try:
            # Conecta sem BD para garantir que existe
            temp_conn = mysql.connector.connect(**self.config)
            cursor = temp_conn.cursor()

            if self.__limpar_base_de_dados== True:
                cursor.execute(f"DROP DATABASE {self.database}")

            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database}")

            cursor.close()
            temp_conn.close()
            return True
        except Error as e:
            print(f"Erro Crítico: {e}")
            return False

    def create_tables(self):
        queries = [
            # Tabelas Auxiliares 
            "CREATE TABLE IF NOT EXISTS categories (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(50) UNIQUE)",
            "CREATE TABLE IF NOT EXISTS product_names (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(100) UNIQUE)",
            "CREATE TABLE IF NOT EXISTS descriptions (id INT AUTO_INCREMENT PRIMARY KEY, texto TEXT)",
            "CREATE TABLE IF NOT EXISTS stores (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(50), localizacao VARCHAR(100))",
            
            # Utilizadores
            """CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE,
            password VARCHAR(255),
            cargo ENUM('admin', 'vendedor', 'cliente'),
            store_id INT NULL,
            FOREIGN KEY (store_id) REFERENCES stores(id)
            )""",
            
            # Produtos (Não pode haver 2 nomes iguais na mesma loja)
            """CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            store_id INT,
            product_name_id INT,
            category_id INT,
            description_id INT,
            preco DECIMAL(10, 2),
            stock INT,
            FOREIGN KEY (store_id) REFERENCES stores(id),
            FOREIGN KEY (product_name_id) REFERENCES product_names(id),
            FOREIGN KEY (category_id) REFERENCES categories(id),
            FOREIGN KEY (description_id) REFERENCES descriptions(id),
            UNIQUE KEY unique_prod_store (store_id, product_name_id)
            )""",

            # Pedidos / Compras (um pedido contém vários itens e está associado a uma loja)
            """CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            buyer_user_id INT,
            store_id INT,
            seller_user_id INT NULL,
            status ENUM('pendente', 'concluida') DEFAULT 'pendente',
            total_price DECIMAL(10,2) DEFAULT 0,
            order_date DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (buyer_user_id) REFERENCES users(id),
            FOREIGN KEY (store_id) REFERENCES stores(id),
            FOREIGN KEY (seller_user_id) REFERENCES users(id)
            )""",

            # Não pode haver produtos iguais na mesma compra (order_id, product_id) deve ser único
            """CREATE TABLE IF NOT EXISTS order_items (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_id INT,
            product_id INT,
            quantity INT,
            unit_price DECIMAL(10,2),
            FOREIGN KEY (order_id) REFERENCES orders(id) ON DELETE CASCADE,
            FOREIGN KEY (product_id) REFERENCES products(id),
            UNIQUE KEY unique_product_per_order (order_id, product_id)
            )""",
        ]

        if self.cursor is None:
            if self.conn is not None:
                self.cursor = self.conn.cursor(dictionary=True)
            else:
                raise Exception("Database connection is not established.")

        for querie in queries:
            self.cursor.execute(querie)
        if self.conn:
            self.conn.commit()

db = DatabaseManager()
db.connect()