import mysql
import mysql.connector
import mysql.connector.errors
import socket

def conectar():
    coneccao = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="presencas_db"
    )
    cursor = coneccao.cursor()
    return coneccao, cursor

def conectar_sem_bd():
    coneccao = mysql.connector.connect(
        host="localhost",
        user="root",
        password=""
    )
    cursor = coneccao.cursor()
    return coneccao, cursor

def criar_bd_se_nao_existir():
    conexao, cursor = conectar_sem_bd()
    try:
        cursor.execute("CREATE DATABASE IF NOT EXISTS presencas_db")
    except mysql.connector.Error as e:
        print(f"Erro ao criar o banco de dados: {e}")
    finally:
        cursor.close()
        conexao.close()
    criar_tabela_presencas()

def criar_tabela_presencas():
    conexao, cursor = conectar()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS alunos (
                id INT AUTO_INCREMENT PRIMARY KEY,
                nome VARCHAR(255) UNIQUE NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS presencas (
                id INT AUTO_INCREMENT PRIMARY KEY,
                aluno_id INT NOT NULL,
                data_hora TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (aluno_id) REFERENCES alunos(id)
            )
        """)
        conexao.commit()
    except mysql.connector.Error as e:
        print(f"Erro ao criar a tabela: {e}")
    finally:
        cursor.close()
        conexao.close()

def adicionar_aluno(nome):
    conexao, cursor = conectar()
    try:
        sql = "INSERT INTO alunos (nome) VALUES (%s)"
        val = (nome,)
        cursor.execute(sql, val)
        conexao.commit()
        cursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome,))
        resultado = cursor.fetchone()
        aluno_id = resultado[0] if resultado else None
        print(f"Aluno adicionado com ID: {aluno_id}, Nome: {nome}")
        return aluno_id
    except mysql.connector.Error as e:
        print(f"Erro ao adicionar aluno: {e}")
        return None
    finally:
        cursor.close()
        conexao.close()

def buscar_id_por_nome(nome):
    conexao, cursor = conectar()
    try:
        cursor.execute("SELECT id FROM alunos WHERE nome = %s", (nome,))
        resultado = cursor.fetchone()
        if resultado:
            return resultado[0]
        
        return None
    except mysql.connector.Error as e:
        print(f"Erro ao buscar id por nome: {e}")
        return None
    finally:
        cursor.close()
        conexao.close()

def registrar_presenca(aluno_id):
    conexao, cursor = conectar()
    try:
        # Verifica se o aluno existe
        cursor.execute("SELECT id FROM alunos WHERE id = %s", (aluno_id,))
        resultado = cursor.fetchone()
        if not resultado:
            print(f"Aluno ID {aluno_id} não existe!")
            return False
        sql = "INSERT INTO presencas (aluno_id) VALUES (%s)"
        val = (aluno_id,)
        cursor.execute(sql, val)
        conexao.commit()
        print(f"Presença registrada para o aluno ID: {aluno_id}")
        return True
    except mysql.connector.Error as e:
        print(f"Erro ao registrar presença: {e}")
        return False
    finally:
        cursor.close()
        conexao.close()
def listar_alunos():
    conexao, cursor = conectar()
    try:
        cursor.execute("SELECT id, nome FROM alunos")
        alunos = cursor.fetchall()
        return alunos
    except mysql.connector.Error as e:
        print(f"Erro ao listar alunos: {e}")
        return []
    finally:
        cursor.close()
        conexao.close()

def listar_presencas():
    conexao, cursor = conectar()
    try:
        cursor.execute("SELECT p.id, a.nome, p.data_hora FROM presencas p JOIN alunos a ON p.aluno_id = a.id")
        presencas = cursor.fetchall()
        return presencas
    except mysql.connector.Error as e:
        print(f"Erro ao listar presenças: {e}")
        return []
    finally:
        cursor.close()
        conexao.close()

HOST = 'localhost'
PORT = 65432

criar_bd_se_nao_existir()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((HOST, PORT))
server_socket.listen()

print(f"Servidor a escutar em {HOST}:{PORT}")
while True:
    conexao, addr = server_socket.accept()
    print("Conectado por ", addr)

    data = conexao.recv(1024)
    if not data:
        print("Cliente desconectado")
        conexao.close()
        continue
    dados = data.decode()

    print("Dados recebidos: ", dados)
    linhas = dados.split("\n")
    comando = linhas[0].split(":")[0]
    
    match comando:
        case "ADICIONAR_ALUNO":
            if len(linhas) >= 2 and linhas[1].startswith("NOME:"):
                nome = linhas[1].split(":")[1].strip()
                aluno_id = adicionar_aluno(nome)
                conexao.sendall(f"ID_ALUNO:{aluno_id}".encode())
        case "BUSCAR_ID":
            if len(linhas) >= 2 and linhas[1].startswith("NOME:"):
                nome = linhas[1].split(":")[1].strip()
                aluno_id = buscar_id_por_nome(nome)
                conexao.sendall(f"ID_ALUNO:{aluno_id}".encode())
        case "REGISTRAR_PRESENCA":
            if len(linhas) >= 2 and linhas[1].startswith("ID_ALUNO:"):
                aluno_id = linhas[1].split(":")[1].strip()
                sucesso = registrar_presenca(aluno_id)
                if sucesso:
                    conexao.sendall(f"PRESENCA_REGISTRADA:{aluno_id}".encode())
                else:
                    conexao.sendall(f"ERRO: Aluno ID {aluno_id} não existe".encode())
        case "LISTAR_ALUNOS":
            alunos = listar_alunos()
            resposta = "\n".join([f"{a[0]}: {a[1]}" for a in alunos])
            conexao.sendall(resposta.encode())
        case "LISTAR_PRESENCAS":
            presencas = listar_presencas()
            resposta = "\n".join([f"{p[0]}: {p[1]} - {p[2]}" for p in presencas])
            conexao.sendall(resposta.encode())
        case _:
            print("Formato de dados inválido")
    conexao.close()