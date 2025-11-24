# Mensagem informativa sobre problemas de rede na escola
print("\nATENÇÃO: Caso estejam a testar na escola onde o projeto foi desenvolvido, e um computador cliente não se consiga comunicar com o computador servidor, foi identificado um problema relacionado à rede. A solução é colocar o servidor em outro computador.\n")

import subprocess
import sys
import socket
from enums import Cores

def limpar_tela():
    import os
    os.system('cls')

def pausar():
    input("Pressione ENTER para continuar...")

def obter_ip_local():
    try:
        # Cria socket temporário para descobrir IP
        socket_temporario = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_temporario.connect(("8.8.8.8", 80))
        ip = socket_temporario.getsockname()[0]
        socket_temporario.close()
        return ip
    except:
        return "127.0.0.1"

def verificar_instalar_dependencias():
    print(f"{Cores.AMARELO}Verificando dependências do servidor...{Cores.NORMAL}\n")
    
    dependencias = [
        ("pywin32", "win32api"),
        ("mysql-connector-python", "mysql.connector")
    ]
    
    faltando = []
    
    for pacote_pip, nome_import in dependencias:
        try:
            __import__(nome_import)
            print(f"{Cores.VERDE}Instalado: {pacote_pip} instalado{Cores.NORMAL}")
        except ImportError:
            print(f"{Cores.VERMELHO}Em Falta: {pacote_pip} não encontrado{Cores.NORMAL}")
            faltando.append(pacote_pip)
    
    if faltando:
        print(f"\n{Cores.AMARELO}Dependências faltando: {', '.join(faltando)}{Cores.NORMAL}")
        resposta = input(f"\n{Cores.CIANO}Deseja instalar automaticamente? (s/n): {Cores.NORMAL}").strip().lower()
        
        if resposta == 's':
            print(f"\n{Cores.AMARELO}Instalando dependências...{Cores.NORMAL}\n")
            for pacote in faltando:
                print(f"Instalando {pacote}...")
                try:
                    subprocess.check_call([sys.executable, "-m", "pip", "install", pacote])
                    print(f"{Cores.VERDE}{pacote} instalado com sucesso!{Cores.NORMAL}\n")
                except subprocess.CalledProcessError:
                    print(f"{Cores.VERMELHO}Erro ao instalar {pacote}{Cores.NORMAL}\n")
                    return False
            
            print(f"{Cores.VERDE}Todas as dependências foram instaladas!{Cores.NORMAL}\n")
            pausar()
            return True
        else:
            print(f"{Cores.VERMELHO}Não é possível iniciar o servidor sem as dependências.{Cores.NORMAL}")
            pausar()
            return False
    else:
        print(f"\n{Cores.VERDE}Todas as dependências estão instaladas!{Cores.NORMAL}\n")
        pausar()
        return True

def iniciar_servidor(debug=False):
    limpar_tela()
    print(f"{Cores.CIANO}{Cores.NEGRITO}{'A inicializar Servidor'}{Cores.NORMAL}\n")
    
    # Verificar e instalar dependências
    if not verificar_instalar_dependencias():
        return
    
    limpar_tela()
    print(f"{Cores.CIANO}{Cores.NEGRITO}{'Servidor - Sistema de Vendas'}{Cores.NORMAL}\n")
    
    ip_local = obter_ip_local()
    print(f"{Cores.VERDE}Ip Local da Máquina: {ip_local}{Cores.NORMAL}")
    print(f"{Cores.AMARELO}O servidor será iniciado em: {ip_local}:5000{Cores.NORMAL}\n")
    
    resposta = input(f"{Cores.CIANO}Deseja usar este IP? (s/n): {Cores.NORMAL}").strip().lower()
    
    if resposta == 'n':
        host = input(f"{Cores.CIANO}Digite o IP desejado (ou ENTER para 127.0.0.1): {Cores.NORMAL}").strip()
        if not host:
            host = "127.0.0.1"
    else:
        host = ip_local

    port_input = input(f"{Cores.CIANO}Digite a port (ou ENTER para 5000): {Cores.NORMAL}").strip()
    if port_input:
        port = int(port_input)
    else:
        port = 5000


    print(f"\n{Cores.VERDE}Iniciando servidor em {host}:{port}...{Cores.NORMAL}\n")
    
    try:
        import server
        server.run(host,port,debug)
    except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Cores.ROXO}Servidor encerrado pelo utilizador.{Cores.NORMAL}")
    except Exception as e:
        print(f"\n{Cores.VERMELHO}Erro ao iniciar servidor: {e}{Cores.NORMAL}")
        input("\nPressione ENTER para voltar ao menu...")

def iniciar_cliente(debug=False):
    limpar_tela()
    print(f"{Cores.CIANO}{Cores.NEGRITO}{'Cliente - Sistema de Vendas'}{Cores.NORMAL}\n")
    
    print(f"{Cores.AMARELO}Configure a conexão com o servidor:{Cores.NORMAL}\n")
    
    host = input(f"{Cores.CIANO}Ip do Servidor (ou ENTER para 127.0.0.1): {Cores.NORMAL}").strip()
    if not host:
        host = "127.0.0.1"
    
    port_input = input(f"{Cores.CIANO}port do Servidor (ou ENTER para 5000): {Cores.NORMAL}").strip()
    if port_input:
        port = int(port_input) 
    else:
        port = 5000
    
    print(f"\n{Cores.VERDE}Conectando ao servidor {host}:{port}...{Cores.NORMAL}\n")
    
    try:
        import client
        client.run(host, port, debug)
    except (KeyboardInterrupt, EOFError):
            print(f"\n\n{Cores.ROXO}Cliente encerrado pelo utilizador.{Cores.NORMAL}")
    except Exception as e:
        print(f"\n{Cores.VERMELHO}Erro ao iniciar cliente: {e}{Cores.NORMAL}")
        input("\nPressione ENTER para voltar ao menu...")
def mostrar_bool(valor):
    if valor == True:
        return f"{Cores.VERDE}True{Cores.NORMAL}"
    
    return f"{Cores.VERMELHO}False{Cores.NORMAL}"
def menu_principal():
    debug = False
    while True:
        limpar_tela()
        print(f"{Cores.CIANO}{Cores.NEGRITO}Sistema de Vendas - Inicializador - Debug = {mostrar_bool(debug)}\n")
        print(f"{Cores.AMARELO}Escolha uma opção:{Cores.NORMAL}\n")
        print(f"  {Cores.VERDE}1){Cores.NORMAL} Iniciar {Cores.LARANJA}Servidor{Cores.NORMAL}")
        print(f"  {Cores.VERDE}2){Cores.NORMAL} Iniciar {Cores.CASTANHO}Cliente{Cores.NORMAL}")
        print(f"  {Cores.AMARELO}3){Cores.NORMAL} Mudar {Cores.AMARELO}DEBUG{Cores.NORMAL} para {mostrar_bool(not debug)}")
        print(f"  {Cores.VERMELHO}0){Cores.NORMAL} Sair\n")
        
        opcao = input(f"{Cores.CIANO}Escolha uma opção: {Cores.NORMAL}").strip()

        match opcao:
            case '1':
                iniciar_servidor(debug)
            case '2':
                iniciar_cliente(debug)
            case '3':
                debug = not debug
            case '0':
                limpar_tela()
                print(f"{Cores.VERDE}Obrigado por usar o Sistema de Vendas!{Cores.NORMAL}\n")
                break
            case _:
                print(f"{Cores.VERMELHO}Opção inválida!{Cores.NORMAL}")
                input("Pressione ENTER para continuar...")

if __name__ == '__main__':
    try:
        menu_principal()
    except (KeyboardInterrupt, EOFError):
        print(f"\n\n{Cores.ROXO}Programa encerrado pelo utilizador.{Cores.NORMAL}")
    except SystemExit as e: # Quando usa exit
        if e.code == 0:
            print(f"\n{Cores.VERDE}Programa encerrado com sucesso.{Cores.NORMAL}")
        else:
            print(f"\n{Cores.VERMELHO}Programa encerrado com erro.{Cores.NORMAL}")
    except Exception as e:
        print(f"\n{Cores.VERMELHO}{Cores.NEGRITO}Erro fatal: {e}{Cores.NORMAL}")