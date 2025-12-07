import mysql.connector
from mysql.connector import Error
import time
import consola

class GestorBaseDados:
    def __init__(self, host='localhost', utilizador='root', palavra_passe='', nome_banco='sistema_vendas', limpar_base_dados=False):
        # Configuração inicial para conexão (dicionário interno mantendo chaves em inglês exigidas pela biblioteca)
        self.configuracao = {
            'host': host,
            'user': utilizador,
            'password': palavra_passe
        }
        self.nome_banco = nome_banco 
        self.conexao = None
        self.cursor = None
        self.__limpar_base_dados = limpar_base_dados

    def conectar(self):
        while True:
            try:
                # Garante que a Base de Dados existe antes de tentar ligar a ela
                if self.verificar_criar_base_dados() is False:
                    consola.aviso("Falha ao verificar/criar base de dados. Tentando novamente...")
                    time.sleep(2)
                    continue 

                # Adiciona a base de dados à configuração antes de conectar
                self.configuracao['database'] = self.nome_banco
                self.conexao = mysql.connector.connect(**self.configuracao)
                self.cursor = self.conexao.cursor(dictionary=True)
                
                self.criar_tabelas()
                
                consola.sucesso(f"Conectado com sucesso a: {self.nome_banco}")
                return True
            except Error as erro:
                mensagem_erro = str(erro)
                
                # Verifica se é erro de conexão (XAMPP não está ligado)
                if "2003" in mensagem_erro or "refused" in mensagem_erro.lower() or "connect" in mensagem_erro.lower():
                    consola.erro("\nNão foi possível conectar ao MySQL!\n")
                    consola.erro("Certifique-se de que o XAMPP/MySQL está ligado.\n")
                    consola.info("Passos para resolver:")
                    consola.info("  1. Abra o XAMPP Control Panel")
                    consola.info("  2. Clique em 'Start' ao lado de 'MySQL'")
                    consola.info("  3. Aguarde até o status mudar para 'Running'")
                    consola.info("  4. Tente novamente\n")
                    consola.aviso("Tentando reconectar em 5 segundos...")
                else:
                    consola.erro(f"Erro ao conectar ao MySQL: {erro}. Tentando novamente em 5 segundos...")
                
                time.sleep(5)
        
    def verificar_criar_base_dados(self):
        try:
            # Conecta sem especificar BD para poder criar/apagar schemas
            conexao_temporaria = mysql.connector.connect(
                host=self.configuracao['host'], 
                user=self.configuracao['user'], 
                password=self.configuracao['password']
            )
            cursor_temporario = conexao_temporaria.cursor()

            if self.__limpar_base_dados is True:
                cursor_temporario.execute(f"DROP DATABASE IF EXISTS {self.nome_banco}")

            cursor_temporario.execute(f"CREATE DATABASE IF NOT EXISTS {self.nome_banco}")

            cursor_temporario.close()
            conexao_temporaria.close()
            return True
        except Error as erro:
            consola.erro(f"Erro Crítico ao verificar BD: {erro}")
            return False

    def criar_tabelas(self):
        # Lista de comandos SQL para criar a estrutura da base de dados.
        comandos = [
            "CREATE TABLE IF NOT EXISTS categorias (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(50) UNIQUE)",
            "CREATE TABLE IF NOT EXISTS nomes_produtos (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(100) UNIQUE)",
            "CREATE TABLE IF NOT EXISTS descricoes (id INT AUTO_INCREMENT PRIMARY KEY, texto TEXT)",
            "CREATE TABLE IF NOT EXISTS lojas (id INT AUTO_INCREMENT PRIMARY KEY, nome VARCHAR(50) UNIQUE, localizacao VARCHAR(100))",
            
            """CREATE TABLE IF NOT EXISTS utilizadores (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome_utilizador VARCHAR(50) UNIQUE,
                palavra_passe VARCHAR(255),
                cargo ENUM('admin', 'vendedor', 'cliente'),
                loja_id INT NULL,
                FOREIGN KEY (loja_id) REFERENCES lojas(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS sessoes (
                token CHAR(64) PRIMARY KEY,
                nome_utilizador VARCHAR(50),
                palavra_passe VARCHAR(255),
                data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
            )""",
            
            """CREATE TABLE IF NOT EXISTS produtos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                loja_id INT,
                nome_produto_id INT,
                categoria_id INT,
                descricao_id INT,
                preco DECIMAL(10, 2),
                stock INT,
                FOREIGN KEY (loja_id) REFERENCES lojas(id),
                FOREIGN KEY (nome_produto_id) REFERENCES nomes_produtos(id),
                FOREIGN KEY (categoria_id) REFERENCES categorias(id),
                FOREIGN KEY (descricao_id) REFERENCES descricoes(id),
                UNIQUE KEY unique_prod_store (loja_id, nome_produto_id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS encomendas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                comprador_id INT,
                loja_id INT,
                vendedor_id INT NULL,
                estado ENUM('pendente', 'concluida') DEFAULT 'pendente',
                preco_total DECIMAL(10,2) DEFAULT 0,
                data_encomenda DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (comprador_id) REFERENCES utilizadores(id),
                FOREIGN KEY (loja_id) REFERENCES lojas(id),
                FOREIGN KEY (vendedor_id) REFERENCES utilizadores(id)
            )""",
            
            """CREATE TABLE IF NOT EXISTS itens_encomenda (
                id INT AUTO_INCREMENT PRIMARY KEY,
                encomenda_id INT,
                produto_id INT,
                quantidade INT,
                preco_unitario DECIMAL(10,2),
                FOREIGN KEY (encomenda_id) REFERENCES encomendas(id) ON DELETE CASCADE,
                FOREIGN KEY (produto_id) REFERENCES produtos(id),
                UNIQUE KEY unique_product_per_order (encomenda_id, produto_id)
            )""",
        ]
        
        # Garante que o cursor existe antes de executar
        if self.cursor is None:
            if self.conexao is not None:
                self.cursor = self.conexao.cursor(dictionary=True)
            else:
                raise Exception("A conexão com a base de dados não está estabelecida.")
        
        # Executa cada consulta sequencialmente
        for comando in comandos:
            try:
                self.cursor.execute(comando)
            except Error as erro_sql:
                consola.erro(f"Erro ao criar tabela: {erro_sql}")
        
        if self.conexao is not None:
            self.conexao.commit()