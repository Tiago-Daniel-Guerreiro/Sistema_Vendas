import os
import getpass
from enums import Cores

def limpar():
    # Verifica o nome do sistema operativo para executar o comando de limpeza correto
    # 'nt' é o identificador para sistemas Windows
    nome_sistema = os.name
    match nome_sistema:
        case 'nt':
            os.system('cls')
        case _:
            os.system('clear')

def formatar_estado_debug(valor, *mensagens):
    texto_true = "ativado"
    texto_false = "desativado"

    quantidade_mensagens = len(mensagens)
    match quantidade_mensagens:
        case 1:
            texto_true = mensagens[0]
            texto_false = mensagens[0]
        case 2:
            texto_true = mensagens[0]
            texto_false = mensagens[1]

    if valor is True:
        return f"{Cores.VERDE}{texto_true}{Cores.NORMAL}"
    
    return f"{Cores.VERMELHO}{texto_false}{Cores.NORMAL}"

def mostrar_mensagem_rede_escola():
    limpar()
    aviso(f"\n{Cores.VERMELHO}{Cores.NEGRITO}Atenção:{Cores.NORMAL}")
    print("Caso estejam a testar na escola e o cliente não consiga comunicar com o servidor, foi identificado um problema relacionado à rede/firewall local.")
    aviso(f"\n{Cores.VERMELHO}Solução sugerida:{Cores.NORMAL} Colocar o servidor em outro computador.")

def importante_destacado(mensagem):
    print(f"{Cores.ROXO}{Cores.NEGRITO}{mensagem}{Cores.NORMAL}")

def importante(mensagem):
    print(f"{Cores.ROXO}{mensagem}{Cores.NORMAL}")

def info(mensagem):
    print(f"{Cores.AZUL}{mensagem}{Cores.NORMAL}")

def sucesso(mensagem):
    print(f"{Cores.VERDE}{mensagem}{Cores.NORMAL}")

def erro(mensagem):
    print(f"{Cores.VERMELHO}Erro: {mensagem}{Cores.NORMAL}")

def aviso(mensagem):
    print(f"{Cores.AMARELO}Aviso: {mensagem}{Cores.NORMAL}")

def pausar():
    input(f"\n{Cores.CINZA}Pressione ENTER para continuar...{Cores.NORMAL}")

def ler_texto(mensagem, obrigatorio=True):
    while True:
        valor = input(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip()
        
        # Verifica se o campo é obrigatório e se o comprimento é zero
        if obrigatorio is True:
            if len(valor) == 0:
                print(f"{Cores.VERMELHO}Este campo não pode estar vazio.{Cores.NORMAL}")
                continue
        
        return valor

def ler_senha(mensagem, validar=True):
    # Se for para validar, permite até 3 tentativas vazias e depois retorna None
    tentativas = 0
    while True:
        # O getpass esconde o input do utilizador na consola por segurança
        valor = getpass.getpass(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip()

        if validar is False:
            return valor # Se não for preciso validar, permite retornar string vazia
        
        if len(valor) == 0:
            tentativas += 1
            if tentativas >= 3:
                # Sinaliza cancelamento após múltiplas tentativas falhadas
                return None
            
            print(f"{Cores.VERMELHO}A senha não pode estar vazia. Tentativa {tentativas}/3.{Cores.NORMAL}")
            continue
        

        return valor