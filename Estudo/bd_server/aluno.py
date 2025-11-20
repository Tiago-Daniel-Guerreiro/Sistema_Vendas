import socket

def conectar():
    cliente_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    cliente_socket.connect(("localhost", 65432))
    return cliente_socket

def mostrar_resposta(cliente_socket):
    resposta = cliente_socket.recv(1024).decode()
    print(f"{resposta}")
    cliente_socket.close()

def registrar_presenca(aluno_id):
    cliente_socket = conectar()
    mensagem = f"REGISTRAR_PRESENCA:\nID_ALUNO:{aluno_id}"
    cliente_socket.sendall(mensagem.encode())

    mostrar_resposta(cliente_socket)

def adicionar_aluno(nome):
    cliente_socket = conectar()
    mensagem = f"ADICIONAR_ALUNO:\nNOME:{nome}"
    cliente_socket.sendall(mensagem.encode())

    mostrar_resposta(cliente_socket)

def buscar_id_por_nome(nome):
    cliente_socket = conectar()
    mensagem = f"BUSCAR_ID:\nNOME:{nome}"
    cliente_socket.sendall(mensagem.encode())
    mostrar_resposta(cliente_socket)


def menu():
    while True:
        print("Menu de Presença")
        print("1. Adicionar Aluno (retorna ID)")
        print("2. Buscar ID pelo nome")
        print("3. Registrar Presença pelo ID")
        print("4. Listar Alunos")
        print("5. Listar Presenças")
        print("0. Sair")
        escolha = input("Escolha uma opção: ")

        match escolha:
            case"1":
                nome = input("Digite o nome do novo aluno: ")
                adicionar_aluno(nome)
            case "2":
                nome = input("Digite o nome do aluno: ")
                buscar_id_por_nome(nome)
            case "3":
                aluno_id = input("Digite o ID do aluno: ")
                registrar_presenca(aluno_id)
            case "4":
                    cliente_socket = conectar()
                    cliente_socket.sendall("LISTAR_ALUNOS:".encode())
                    mostrar_resposta(cliente_socket)
            case "5":
                    cliente_socket = conectar()
                    cliente_socket.sendall("LISTAR_PRESENCAS:".encode())
                    mostrar_resposta(cliente_socket)
            case "0":
                print("Saindo...")
                break

menu()