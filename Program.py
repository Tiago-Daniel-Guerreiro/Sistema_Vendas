import subprocess
import sys
import socket
from enums import Cores
from console import *

def obter_ip_local():
    # Usa UDP (SOCK_DGRAM) para obter o IP local sem fazer uma ligação TC (que é mais complexo).
    # A chamada connect em UDP não envia pacotes, apenas define o endereço remoto para que getsockname() retorne o ip.
    socket_temporario = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    socket_temporario.settimeout(2.0)
    endereco_google_dns = ("8.8.8.8", 80) # Usado apenas para obter o IP local
    try:
        socket_temporario.connect(endereco_google_dns)
        endereco_ip = socket_temporario.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        socket_temporario.close()

    return endereco_ip

def instalar_pacote(nome_pacote):
    print(f"A instalar {nome_pacote}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
        sucesso(f"{nome_pacote} instalado com sucesso!\n")
        return True
    except subprocess.CalledProcessError:
        erro(f"Erro ao instalar {nome_pacote}.\n")
        return False

def verificar_e_instalar_dependencias():
    aviso("A verificar dependências do servidor...\n")
    
    # Estrutura: (Nome no PIP, Nome no Import, Obrigatória?)
    # True = Obrigatória (Se faltar, para tudo)
    # False = Opcional (Se faltar, pergunta, mas pode continuar sem)
    lista_dependencias = [
        ("mysql-connector-python", "mysql.connector", True),
        ("pywin32", "win32api", False)
    ]
    
    faltam_obrigatorias = []
    faltam_opcionais = []
    
    # Verificação do que está instalado
    for nome_pip, nome_import, obrigatoria in lista_dependencias:
        try:
            __import__(nome_import)
            sucesso(f"Instalado: {nome_pip}")
        except ImportError:
            if obrigatoria is True:
                erro(f"Em Falta (Essencial): {nome_pip}")
                faltam_obrigatorias.append(nome_pip)
            else:
                aviso(f"Em Falta (Opcional): {nome_pip}")
                faltam_opcionais.append(nome_pip)
    
    # Se não falta nada, sucesso imediato
    if len(faltam_obrigatorias) == 0 and len(faltam_opcionais) == 0:
        sucesso("\nTodas as dependências estão instaladas!\n")
        pausar()
        return True

    # Para as obrigatórias
    if len(faltam_obrigatorias) > 0:
        erro(f"\nDependências obrigatórias em falta: {', '.join(faltam_obrigatorias)}")
        resposta = input(f"{Cores.CIANO}Instalar agora? (s/n): {Cores.NORMAL}").strip().lower()
        
        if resposta != 's':
            erro("Cancelado. Não é possível iniciar sem as dependências obrigatórias.")
            pausar()
            return False
            
        aviso("\nA instalar...")
        for pacote in faltam_obrigatorias:
            if instalar_pacote(pacote) is False:
                return False

    # Para as opcionais
    if len(faltam_opcionais) > 0:
        aviso(f"\nDependências opcionais em falta: {', '.join(faltam_opcionais)}")
        print(f"{Cores.CINZA}Se não instalar, algumas funções específicas serão desativadas.{Cores.NORMAL}")
        resposta = input(f"{Cores.CIANO}Instalar agora? (s/n): {Cores.NORMAL}").strip().lower()
        
        if resposta == 's':
            aviso("\nA instalar...")
            for pacote in faltam_opcionais:
                instalar_pacote(pacote)
        else:
            aviso("\nContinuando sem dependências opcionais...")

    sucesso("\nVerificação finalizada. A iniciar...\n")
    pausar()
    
    return True
    
def iniciar_sessao(servidor=False, modo_debug=False):
    if servidor is True:
        tipo = "servidor"
        modulo = "server"
    else:
        tipo = "cliente"
        modulo = "client"

    limpar()
    print(f"{Cores.CIANO}{Cores.NEGRITO}A inicializar {tipo}{Cores.NORMAL}\n")
    
    if servidor is True:
        if verificar_e_instalar_dependencias() is False:
            return
            
        limpar()
        print(f"{Cores.CIANO}{Cores.NEGRITO}Configuração do Servidor{Cores.NORMAL}\n")

    importante_destacado("Configuração de Rede:\n")

    host = "127.0.0.1"
    porta = 5000
    porta_ja_definida = False

    if servidor is True:
        ip_local = obter_ip_local()
        sucesso(f"Ip Local detectado: {ip_local}")
        
        resposta_ip = input(f"{Cores.CIANO}Deseja usar este Ip? (s/n - Enter para S): {Cores.NORMAL}").strip().lower()
        
        # Se a resposta for vazia ou 's', usa o IP local
        # Se for 'n' ou qualquer outro valor, pede um novo IP
        if resposta_ip == '' or resposta_ip == 's':
            host = ip_local
        else:
            entrada_host = input(f"{Cores.CIANO}Introduza o Ip desejado (Enter para 127.0.0.1): {Cores.NORMAL}").strip()
            if len(entrada_host) > 0:
                host = entrada_host
            
    else:
        entrada_host = input(f"{Cores.CIANO}Ip do Servidor (Enter para 127.0.0.1): {Cores.NORMAL}").strip()
        if len(entrada_host) > 0:
            host = entrada_host

    partes = host.split(":")
    host = partes[0]
    # A pessoa pode colocar a porta diretamente no ip
    if len(partes) == 2 and partes[1].isdigit():
        porta = int(partes[1])
        porta_ja_definida = True
        
    if porta_ja_definida is False:
        entrada_porta = input(f"{Cores.CIANO}Porta (Enter para 5000): {Cores.NORMAL}").strip()
        if len(entrada_porta) > 0:
            if entrada_porta.isdigit():
                porta = int(entrada_porta)
            else:
                erro("Porta inválida, usando 5000.")

    if servidor is True:
        verbo = "A iniciar servidor"
    else:
        verbo = "A conectar ao servidor"
        
    sucesso(f"\n{verbo} em {host}:{porta}...")
    pausar()
    
    try:
        # Faz a importação de forma dinamica para não causar erros por falta de bibliotecas
        modulo_importado = __import__(modulo)
        modulo_importado.run(host, porta, modo_debug)
    except (KeyboardInterrupt, EOFError):
        pass
    except Exception as excecao:
        erro(f"\nErro ao iniciar {tipo}: {excecao}")
        pausar()

def menu_principal():
    mostrar_mensagem_rede_escola()
    modo_debug = False
    
    while True:
        pausar()
        limpar()
        print(f"{Cores.CIANO}{Cores.NEGRITO}Sistema de Vendas - Menu de Arranque{Cores.NORMAL}")        
        print(f"{Cores.VERDE}1){Cores.NORMAL} Iniciar {Cores.LARANJA}Servidor{Cores.NORMAL}")
        print(f"{Cores.VERDE}2){Cores.NORMAL} Iniciar {Cores.CASTANHO}Cliente{Cores.NORMAL}")
        print(f"{Cores.AMARELO}3){Cores.NORMAL} Alterar Debug: {formatar_estado_debug(modo_debug)}")
        print(f"{Cores.VERMELHO}0){Cores.NORMAL} Sair\n")
        
        opcao = input(f"{Cores.CIANO}Opção: {Cores.NORMAL}").strip()

        match opcao:
            case '1':
                iniciar_sessao(True, modo_debug)
            case '2':
                iniciar_sessao(False, modo_debug)
            case '3':
                modo_debug = not modo_debug
            case '0':
                limpar()
                sucesso("Obrigado por usar o Sistema de Vendas!\n")
                break
            case _:
                erro("Opção inválida!")

if __name__ == '__main__':
    menu_principal()