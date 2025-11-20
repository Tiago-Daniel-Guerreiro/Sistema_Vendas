import mysql.connector
from mysql.connector import errorcode
import os
import platform

class MySQLAdminConsole:
    """
    Uma classe para visualizar uma base de dados MySQL em modo de apenas leitura
    através de uma consola interativa baseada em menus.
    """

    def __init__(self, config_mysql: dict):
        """
        Inicializa a consola e tenta conectar-se à base de dados.
        """
        self.config = config_mysql
        self.connection = None
        self.cursor = None
        self.current_Database = None
        
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor(dictionary=True) # Usar dicionários facilita o acesso
            print("Conexão com o MySQL estabelecida com sucesso!")
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                print("Erro: Nome de utilizador ou password incorretos.")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                print(f"Erro: A base de dados '{self.config.get('Database')}' não existe.")
            else:
                print(f"Erro ao conectar ao MySQL: {err}")
            self.connection = None

    def _clear_screen(self):
        """Limpa o ecrã do terminal."""
        os.system('cls' if platform.system() == 'Windows' else 'clear')

    def _execute_query(self, query: str, params: tuple = None) -> list | None:
        """Método auxiliar para executar queries e tratar erros."""
        try:
            self.cursor.execute(query, params or ())
            # Para SELECT, SHOW, DESCRIBE, que retornam linhas
            if self.cursor.description:
                return self.cursor.fetchall()
            # Para USE, etc., que não retornam linhas
            return []
        except mysql.connector.Error as err:
            print(f"Erro na query: {err}")
            input("Pressione Enter para continuar...")
            return None

    def _print_table(self, rows: list):
        """Formata e imprime os resultados em formato de tabela."""
        if not rows:
            print("(0 linhas retornadas)\n")
            return

        headers = list(rows[0].keys())
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, header in enumerate(headers):
                cell_len = len(str(row[header]))
                if cell_len > col_widths[i]:
                    col_widths[i] = cell_len

        header_line = " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers))
        print(header_line)
        
        separator_line = "-+-".join("-" * w for w in col_widths)
        print(separator_line)

        for row in rows:
            row_line = " | ".join(f"{str(row[h]):<{col_widths[i]}}" for i, h in enumerate(headers))
            print(row_line)
        
        print(f"\n({len(rows)} linhas retornadas)\n")

    def run(self):
        """Inicia o loop principal da consola de menus."""
        if not self.connection:
            print("Não foi possível iniciar a consola. Verifique os erros de conexão.")
            return

        try:
            self._show_main_menu()
        except (KeyboardInterrupt, EOFError):
            # Garante que o fecho da conexão é chamado ao sair com Ctrl+C
            pass
        finally:
            self.close()
    
    def _show_main_menu(self):
        """Mostra o menu principal para seleção da base de dados."""
        while True:
            self._clear_screen()
            print("--- PAINEL DE ADMINISTRAÇÃO MySQL (Leitura) ---")
            print("Selecione uma Base de Dados para explorar:\n")

            Databases = self._execute_query("SHOW DataBASES")
            if Databases is None:
                return # Sai se houver um erro de query

            db_names = [db['Database'] for db in Databases]
            for i, db_name in enumerate(db_names, 1):
                print(f"  [{i}] {db_name}")

            print("\n  [0] Sair")
            
            choice = input("\nEscolha uma opção: ").strip().lower()

            if choice == '0':
                break
            
            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(db_names):
                    self.current_Database = db_names[choice_index]
                    self._show_Database_menu()
                else:
                    print("Opção inválida.")
                    input("Pressione Enter para continuar...")
            except ValueError:
                print("Opção inválida. Por favor, insira um número ou '0'.")
                input("Pressione Enter para continuar...")

    def _show_Database_menu(self):
        """Mostra o menu de tabelas para a base de dados selecionada."""
        while True:
            self._clear_screen()
            print(f"--- Base de Dados: {self.current_Database} ---")
            print("Selecione uma Tabela:\n")

            # Executa 'USE' para garantir que o conTexto está correto
            self._execute_query(f"USE `{self.current_Database}`")
            tables = self._execute_query("SHOW TABLES")
            if tables is None:
                return # Retorna ao menu anterior se houver erro

            # O nome da coluna é dinâmico, ex: 'Tables_in_test'
            header_name = list(tables[0].keys())[0] if tables else None
            table_names = [table[header_name] for table in tables]

            if not table_names:
                print("Nenhuma tabela encontrada nesta base de dados.")
            else:
                for i, table_name in enumerate(table_names, 1):
                    print(f"  [{i}] {table_name}")

            print("\n  [0] Voltar ao menu principal")
            
            choice = input("\nEscolha uma opção: ").strip().lower()

            if choice == '0':
                break

            try:
                choice_index = int(choice) - 1
                if 0 <= choice_index < len(table_names):
                    self._show_table_menu(table_names[choice_index])
                else:
                    print("Opção inválida.")
                    input("Pressione Enter para continuar...")
            except ValueError:
                print("Opção inválida. Por favor, insira um número ou '0'.")
                input("Pressione Enter para continuar...")

    def _show_table_menu(self, table_name):
        """Mostra o menu de ações para a tabela selecionada."""
        while True:
            self._clear_screen()
            print(f"--- Tabela: {table_name} (em {self.current_Database}) ---")
            print("Selecione uma Ação:\n")
            print("  [1] Ver conteúdo (primeiras 100 linhas)")
            print("  [2] Ver estrutura (colunas)")
            print("\n  [0] Voltar à lista de tabelas")
            
            choice = input("\nEscolha uma opção: ").strip().lower()

            if choice == '0':
                break
            
            if choice == '1':
                self._clear_screen()
                print(f"Conteúdo da tabela '{table_name}':\n")
                rows = self._execute_query(f"SELECT * FROM `{table_name}` LIMIT 100")
                if rows is not None:
                    self._print_table(rows)
                input("Pressione Enter para voltar...")
            
            elif choice == '2':
                self._clear_screen()
                print(f"Estrutura da tabela '{table_name}':\n")
                rows = self._execute_query(f"DESCRIBE `{table_name}`")
                if rows is not None:
                    # Renomeia as colunas de DESCRIBE para serem mais amigáveis
                    friendly_rows = [
                        {'Coluna': r['Field'], 'Tipo': r['Type'], 'Nulo': r['Null'], 'Chave': r['Key'], 'Padrão': r['Default'], 'Extra': r['Extra']}
                        for r in rows
                    ]
                    self._print_table(friendly_rows)
                input("Pressione Enter para voltar...")

            else:
                print("Opção inválida.")
                input("Pressione Enter para continuar...")

    def close(self):
        """Fecha a conexão com a base de dados de forma segura."""
        if self.connection and self.connection.is_connected():
            print("\nConexão com o MySQL fechada. Adeus!")
            self.cursor.close()
            self.connection.close()
        else:
            print("\nAdeus!")

if __name__ == "__main__":
    configuracao_mysql = {
        "host": "127.0.0.1",
        "user": "root",
        "password": "",
        "port": 3306
    }

    admin_console = MySQLAdminConsole(configuracao_mysql)
    admin_console.run()