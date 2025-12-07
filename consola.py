import os
import getpass
import threading
import time
from readkeys import getkey
from enums import Cores

def limpar():
    try:
        os.system('cls')
    except (KeyboardInterrupt, EOFError):
        pass

def formatar_estado_debug(valor, *mensagens):
    texto_true, texto_false = ("ativado", "desativado")
    if mensagens:
        if len(mensagens) == 1:
            texto_true = texto_false = mensagens[0]
        else:
            texto_true, texto_false = mensagens[0], mensagens[1]

    if valor:
        texto = texto_true 
        cor = Cores.VERDE
    else:
        cor = Cores.VERMELHO
        texto = texto_false


    return f"{cor}{texto}{Cores.NORMAL}"

def mostrar_mensagem_rede_escola():
    aviso(f"\n{Cores.NEGRITO}Atenção:{Cores.NORMAL}")
    print("Caso estejam a testar na escola e o cliente não consiga comunicar com o servidor, foi identificado um problema relacionado à rede/firewall local.", flush=True)
    print(f"\n{Cores.AMARELO}Solução sugerida:{Cores.NORMAL} Colocar o servidor em outro computador.", flush=True)

def importante_destacado(mensagem):
    try:
        print(f"{Cores.ROXO}{Cores.NEGRITO}{mensagem}{Cores.NORMAL}", flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

def importante(mensagem):
    try:
        print(f"{Cores.ROXO}{mensagem}{Cores.NORMAL}", flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

def info(mensagem):
    try:
        print(f"{Cores.AZUL}{mensagem}{Cores.NORMAL}", flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

def normal(mensagem):
    try:
        print(f"{mensagem}", flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

def sucesso(mensagem):
    try:
        print(f"{Cores.VERDE}{mensagem}{Cores.NORMAL}", flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

def erro(mensagem):
    try:
        print(f"{Cores.VERMELHO}{mensagem}{Cores.NORMAL}", flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

def aviso(mensagem):
    print(f"{Cores.AMARELO}{mensagem}{Cores.NORMAL}", flush=True)

def pausar():
    try:
        input(f"\n{Cores.CINZA}Pressione ENTER para continuar...{Cores.NORMAL}")
    except (KeyboardInterrupt, EOFError):
        pass

def info_adicional(mensagem):
    print(f"{Cores.CINZA}{mensagem}{Cores.NORMAL}", flush=True)

def adicionar_dois_pontos(mensagem):
    if not mensagem.endswith(':'):
        mensagem += ':'
    return mensagem

def sim_ou_nao(mensagem, padrao=True):
    while True:
        mensagem = adicionar_dois_pontos(mensagem)
        resposta = input(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip().lower()

        if len(resposta) == 0 and padrao is not None:
            return padrao
        
        match resposta:
            case 's' | 'sim':
                return True
            case 'n' | 'nao' | 'não':
                return False
            case _:
                if padrao is not None:
                    return padrao
                
                erro("Resposta inválida. Por favor, responda com 's' ou 'n'.")

def ler_texto(mensagem, obrigatorio=True):
    mensagem = adicionar_dois_pontos(mensagem)
    while True:
        try:
            valor = input(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip()
            
            if obrigatorio is True:
                if len(valor) == 0:
                    print(f"{Cores.VERMELHO}Este campo não pode estar vazio.{Cores.NORMAL}", flush=True)
                    continue
            
            return valor
        except (KeyboardInterrupt, EOFError):
            raise

def ler_senha(mensagem, validar=True):
    mensagem = adicionar_dois_pontos(mensagem)
    tentativas = 0
    while True:
        # O getpass esconde o input do utilizador na consola por segurança
        valor = getpass.getpass(f"{Cores.AZUL}{mensagem}{Cores.NORMAL} ").strip()

        if validar is False:
            return valor # Se não for preciso validar, permite retornar string vazia
        
        if len(valor) == 0:
            tentativas += 1

            if tentativas >= 3:
                return None
            
            print(f"{Cores.VERMELHO}A senha não pode estar vazia. Tentativa {tentativas}/3.{Cores.NORMAL}", flush=True)
            continue

        return valor

def exibir_menu(titulo, opcoes, texto_sair="Sair", funcao_sair=None, atalho_callback=None):    
    # Inicia thread para monitorizar atalhos se houver callback
    thread_atalhos = None
    if atalho_callback is not None:
        thread_atalhos = threading.Thread(
            target=atalho_callback,
            daemon=True
        )
        thread_atalhos.start()
    
    while True:
        try:
            # Pausa antes de mostrar o menu
            pausar()
            
            try:
                limpar()
            except (KeyboardInterrupt, EOFError):
                # Se Ctrl+C durante limpeza, sai do menu
                raise
            
            importante_destacado(f"\n{titulo}")

            if opcoes is None or len(opcoes) == 0:
                aviso("Nenhuma opção disponível.")
                return False

            for indice, (texto_opcao, _) in enumerate(opcoes, 1):
                print(f"{Cores.AZUL}{indice}){Cores.NORMAL} {texto_opcao}", flush=True)

            print(f"{Cores.AZUL}0){Cores.NORMAL} {texto_sair}", flush=True)

            try:
                escolha = ler_texto("Escolha uma opcao", obrigatorio=False)
            except (KeyboardInterrupt, EOFError):
                # Ctrl+C ou EOF fecha o menu imediatamente, sem mensagem
                return False
            
            # Se escolha está vazia, pede novamente
            if len(escolha) == 0:
                erro("Por favor, introduza um número válido.")
                continue

            if not escolha.isdigit():
                erro("Por favor, introduza um número válido.")
                continue

            indice_escolhido = int(escolha)

            if indice_escolhido == 0:
                # Opção de saída
                if funcao_sair is not None:
                    resultado = funcao_sair()
                    if resultado is True:
                        return True
                return False  # Sair do menu

            if 1 <= indice_escolhido <= len(opcoes):
                funcao_a_chamar = opcoes[indice_escolhido - 1][1]

                try:
                    # Se a função retornar True, significa que o menu deve ser fechado
                    resultado = funcao_a_chamar()
                    if resultado is True:
                        return True  # Retorna True para indicar sucesso
                    # Se retornar False ou None, continua no menu
                except KeyboardInterrupt:
                    # Ctrl+C durante função volta ao menu
                    aviso("\nOperação cancelada.")
                    continue
            else:
                erro("Opção inválida.")
        
        except KeyboardInterrupt:
            raise