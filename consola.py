import os
import getpass
import threading
from enums import Cores

def _executar_com_tratamento(funcao):
    try:
        funcao()
    except (KeyboardInterrupt, EOFError):
        pass

def _executar_com_retorno(funcao):
    try:
        return funcao()
    except (KeyboardInterrupt, EOFError):
        # Adiciona quebra de linha para não deixar texto na mesma linha (especialmente com getpass)
        print()
        return None

def limpar():
    if os.name == 'nt':
        comando = 'cls'
    else:
        comando = 'clear'

    pass
#_executar_com_tratamento(lambda: os.system(comando))

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
    _executar_com_tratamento(lambda: print(f"{Cores.ROXO}{Cores.NEGRITO}{mensagem}{Cores.NORMAL}", flush=True))

def importante(mensagem):
    _executar_com_tratamento(lambda: print(f"{Cores.ROXO}{mensagem}{Cores.NORMAL}", flush=True))

def info(mensagem):
    _executar_com_tratamento(lambda: print(f"{Cores.AZUL}{mensagem}{Cores.NORMAL}", flush=True))

def normal(mensagem):
    _executar_com_tratamento(lambda: print(f"{mensagem}", flush=True))
    
def ciano(mensagem):
    _executar_com_tratamento(lambda: print(f"{Cores.CIANO}{mensagem}{Cores.NORMAL}", flush=True))

def sucesso(mensagem):
    _executar_com_tratamento(lambda: print(f"{Cores.VERDE}{mensagem}{Cores.NORMAL}", flush=True))

def erro(mensagem):
    _executar_com_tratamento(lambda: print(f"{Cores.VERMELHO}{mensagem}{Cores.NORMAL}", flush=True))

def aviso(mensagem):
    print(f"{Cores.AMARELO}{mensagem}{Cores.NORMAL}", flush=True)

def pausar():
    try:
        # usa getpass para não mostrar nada no console antes do utilizador pressionar ENTER
        getpass.getpass(f"{Cores.CINZA}Pressione ENTER para continuar...{Cores.NORMAL}")
        print(Cores.NORMAL, end='', flush=True)
    except (KeyboardInterrupt, EOFError):
        # Adiciona quebra de linha para não deixar texto na mesma linha
        print()
        # Relança a exceção para que o menu possa lidar com ela
        raise

def info_adicional(mensagem):
    _executar_com_tratamento(lambda: print(f"{Cores.CINZA}{mensagem}{Cores.NORMAL}", flush=True))

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

def _ler_input(funcao_input, mensagem, obrigatorio=True, tentativas_max=0):
    # Formata a mensagem apenas uma vez fora do loop
    msg_formatada = f"{Cores.AZUL}{adicionar_dois_pontos(mensagem)}{Cores.NORMAL} "
    
    tentativas = 0
    tem_limite = tentativas_max > 0

    while True:
    
        valor = _executar_com_retorno(lambda: funcao_input(msg_formatada).strip())

        # Se o input retornou None (KeyboardInterrupt), retorna None
        if valor is None:
            return None
        
        # Se tem valor (não vazio) OU não é obrigatório, retorna o valor
        if valor or not obrigatorio:
            return valor

        # Campo Vazio e Obrigatório
        tentativas += 1

        # Verifica se excedeu o limite (se o limite existir)
        if tem_limite and tentativas >= tentativas_max:
            return None

        # Exibe a mensagem de erro
        if tem_limite: 
            info_tentativa = f" ({tentativas}/{tentativas_max})" 
        else:
            info_tentativa = ""

        msg_erro = f"{Cores.VERMELHO}Este campo não pode estar vazio.{info_tentativa}{Cores.NORMAL}"
        
        _executar_com_tratamento(lambda: print(msg_erro, flush=True))

def ler_texto(mensagem, obrigatorio=True, tentativas=5):
    return _ler_input(input, mensagem, obrigatorio, tentativas)

def ler_senha(mensagem, validar=True, tentativas=3):
    return _ler_input(getpass.getpass, mensagem, validar, tentativas)

def exibir_menu(titulo, opcoes, texto_sair="Sair", funcao_sair=None, atalho_callback=None, loop_externo=False):
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
            pausar()
            limpar()
            importante_destacado(f"\n{titulo}")

            if not opcoes:
                aviso("Nenhuma opção disponível.")
                return False

            for indice, (texto_opcao, _) in enumerate(opcoes, 1):
                print(f"{Cores.AZUL}{indice}){Cores.NORMAL} {texto_opcao}", flush=True)
            print(f"{Cores.AZUL}0){Cores.NORMAL} {texto_sair}", flush=True)

            escolha = ler_texto("Escolha uma opção", obrigatorio=False)
            
            if escolha is None:
                raise KeyboardInterrupt

            if len(escolha) == 0:
                erro("Por favor, escolha uma opção.")
                continue

            if not escolha.isdigit():
                erro("Por favor, introduza uma opção válida.")
                continue

            indice_escolhido = int(escolha)

            if indice_escolhido == 0:
                if funcao_sair is not None:
                    resultado = funcao_sair()
                    if resultado is True:
                        return True
                return False

            if 1 <= indice_escolhido <= len(opcoes):
                funcao_a_chamar = opcoes[indice_escolhido - 1][1]
                try:
                    resultado = funcao_a_chamar()
                    if resultado is True:
                        return True
                    if loop_externo:
                        return None
                except KeyboardInterrupt:
                    aviso("\nOperação cancelada.")
                    if loop_externo:
                        return None
            else:
                erro("Opção inválida.")
        except KeyboardInterrupt:
            raise
