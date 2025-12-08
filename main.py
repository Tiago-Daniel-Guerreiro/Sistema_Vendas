import subprocess
import sys
import socket
import os
from enums import Cores, Dependencia
import consola

def obter_ip_local():
    try:
        # Obtem o id criando uma conexão UDP temporária e liga-o a um servidor DNS público do Google
        socket_temporario = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_temporario.settimeout(2.0)
        
        endereco_dns_google = ("8.8.8.8", 80)
        socket_temporario.connect(endereco_dns_google)
        endereco_ip = socket_temporario.getsockname()[0]
    except socket.error:
        endereco_ip = "127.0.0.1" 
    finally:
        socket_temporario.close()

    return endereco_ip

def reiniciar_programa():
    executavel_python = sys.executable
    os.execl(executavel_python, executavel_python, *sys.argv)

def instalar_pacote(nome_pacote):
    consola.info(f"A instalar {nome_pacote}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
        consola.sucesso(f"{nome_pacote} instalado com sucesso!\n")
        return True
    except subprocess.CalledProcessError:
        consola.erro(f"Falha ao instalar {nome_pacote}.\n")
        return False

def verificar_e_instalar_dependencias(tipo=Dependencia.AMBOS):
    # Todas as dependências com seu tipo de requisição
    # Formato: (nome_pacote, nome_import, obrigatoria, tipo_necessario)
    todas_dependencias = [
        # Comuns (sempre necessárias)
        ("colorama", "colorama", True, Dependencia.AMBOS),
        ("readkeys", "readkeys", True, Dependencia.AMBOS),
        
        # Servidor
        ("mysql-connector-python", "mysql.connector", True, Dependencia.SERVIDOR),
        
        # Opcionais
        ("pywin32", "win32api", False, Dependencia.AMBOS),
    ]
    
    # Filtrar dependências relevantes para o tipo solicitado
    lista_dependencias = []
    for nome, import_name, obrigatoria, tipo_necessario in todas_dependencias:
        if tipo_necessario == Dependencia.AMBOS or tipo_necessario == tipo:
            lista_dependencias.append((nome, import_name, obrigatoria))

    str_tipo = ""
    if tipo != Dependencia.AMBOS:
        str_tipo = f" ({str(tipo).lower()})"
    
    mensagens = []
    mensagens.append(lambda:consola.aviso(f"A verificar dependências{str_tipo}...\n"))

    faltam_obrigatorias = []
    faltam_opcionais = []
    
    for dependencia in lista_dependencias:
        nome_pacote, nome_import, obrigatoria = dependencia

        try:
            __import__(nome_import)
        except ImportError:
            if obrigatoria:
                consola.erro(f"Em Falta (Essencial): {nome_pacote}")
                mensagens.append(lambda:faltam_obrigatorias.append(nome_pacote))
            else:
                mensagens.append(lambda:consola.aviso(f"Em Falta (Opcional): {nome_pacote}"))
                faltam_opcionais.append(nome_pacote)
    
    if not faltam_obrigatorias and not faltam_opcionais:
        return True # Todas as dependências estão instaladas

    houve_instalacao = False
    
    for mensagem in mensagens:
        mensagem()

    if faltam_obrigatorias:
        consola.erro(f"\nDependências obrigatórias em falta: ")
        for pacote in faltam_obrigatorias:
            consola.erro(f"\t{pacote}")

        if not consola.sim_ou_nao("Confirma a instalação das dependências obrigatórias?"):
            consola.erro("Cancelado. As dependências essenciais são necessárias.")
            consola.pausar()
            return False
            
        consola.aviso("\nA instalar dependências obrigatórias...")
        for pacote in faltam_obrigatorias:
            if not instalar_pacote(pacote):
                return False 
        houve_instalacao = True

    if faltam_opcionais:
        consola.aviso(f"\nDependências opcionais em falta: ")
        for pacote in faltam_opcionais:
            consola.aviso(f"\t{pacote}")
            
        consola.info("Sem estas dependências, algumas funcionalidades podem estar desativadas.")
        consola.pausar()

        if consola.sim_ou_nao("Deseja instalá-las agora? (s/n):"):
            consola.aviso("\nA instalar dependências opcionais...")
            for pacote in faltam_opcionais:
                instalar_pacote(pacote)
            houve_instalacao = True
        else:
            consola.aviso("\nA continuar sem as dependências opcionais...")

    if houve_instalacao:
        consola.sucesso("\nInstalação concluída.")
        consola.aviso("A aplicação será reiniciada para carregar as novas bibliotecas.")
        consola.pausar()
        reiniciar_programa()
    
    return True

def configurar_rede(para_servidor):
    host = "127.0.0.1"
    porta = 5000
    
    if para_servidor:
        ip_local = obter_ip_local()
        consola.sucesso(f"Ip local detetado: {ip_local}")
        
        if consola.sim_ou_nao("Deseja usar este Ip? (s/n, Enter para 's'):", padrao=True):
            host = ip_local
        else:
            entrada_host = consola.ler_texto(f"Introduza o Ip desejado (Enter para {host}):", obrigatorio=False)
            # Verifica se entrada_host não é None e nem string vazia
            if entrada_host:
                host = entrada_host
    else: # para cliente
        entrada_host = consola.ler_texto(f"Ip do Servidor (Enter para {host}):", obrigatorio=False)
        if entrada_host:
            host = entrada_host
    
    # Permite formato IP:PORTA
    partes_endereco = host.split(":")
    
    if len(partes_endereco) == 2 and partes_endereco[1].isdigit():
        host = partes_endereco[0]
        porta = int(partes_endereco[1])
    else:
        entrada_porta = consola.ler_texto(f"Porta (Enter para {porta}):", obrigatorio=False)
        
        # Verifica se tem valor ANTES de tentar converter
        if entrada_porta:
            if entrada_porta.isdigit():
                porta = int(entrada_porta)
            else:
                consola.erro(f"Porta inválida. A usar a porta padrão {porta}.")

    return host, porta

def verificar_formato_ip(ip_str):
    if ':' in ip_str:
        ip, porta = ip_str.split(':', 1) # o 1 limita a divisão a 2 partes
    else:
        ip = ip_str

    partes = ip.split(".")
    if len(partes) != 4:
        return False
    for parte in partes:
        if not parte.isdigit():
            return False
        valor = int(parte)
        if valor < 0 or valor > 255:
            return False
    return True

def iniciar_aplicacao(iniciar_servidor, modo_debug, dados_exemplo_bd=False):
    nome_modulo = "servidor" if iniciar_servidor else "cliente"

    consola.limpar()
    consola.importante_destacado(f"A inicializar o {nome_modulo}")

    if iniciar_servidor:
        consola.limpar()
        consola.importante_destacado(f"Configuração do {nome_modulo}\n")

    consola.aviso("Configuração de Rede:\n")
    host, porta = configurar_rede(para_servidor=iniciar_servidor)

    texto_acao = "A iniciar servidor" if iniciar_servidor else "A conectar ao servidor"
    consola.sucesso(f"\n{texto_acao} em {host}:{porta}...")
    
    try:
        if iniciar_servidor:
            from servidor.servidor import iniciar as iniciar_servidor_func
            iniciar_servidor_func(host, porta, modo_debug, dados_exemplo_bd)
        else:
            from cliente.cliente import iniciar as iniciar_cliente_func
            iniciar_cliente_func(host, porta, modo_debug)
    except ImportError as e:
        consola.erro(f"\n{nome_modulo.capitalize()} indisponível.")
        consola.info_adicional(f"Detalhes: {e}")
    except Exception as excecao:
        consola.erro(f"\nOcorreu um erro inesperado ao executar o {nome_modulo}: {excecao}")
        import traceback
        traceback.print_exc()

def menu_principal():    
    consola.mostrar_mensagem_rede_escola()
    modo_debug = False
    popular_dados_exemplo = False
    
    def opcao_servidor():
        nonlocal popular_dados_exemplo
        iniciar_aplicacao(iniciar_servidor=True, modo_debug=modo_debug, dados_exemplo_bd=popular_dados_exemplo)
        popular_dados_exemplo = False
    
    def opcao_cliente():
        iniciar_aplicacao(iniciar_servidor=False, modo_debug=modo_debug)
    
    def opcao_debug():
        nonlocal modo_debug
        modo_debug = not modo_debug
        consola.info(f"\nModo de Debug alterado para: {consola.formatar_estado_debug(modo_debug)}")
        return False
    
    def opcao_sair():
        return True
    
    while True:
        # Criar opções dinamicamente a cada iteração para refletir estado atual
        opcoes = [
            (f"Iniciar {Cores.LARANJA}Servidor{Cores.NORMAL}", opcao_servidor),
            (f"Iniciar {Cores.CASTANHO}Cliente{Cores.NORMAL}", opcao_cliente),
            (f"Alterar modo de Debug ({consola.formatar_estado_debug(modo_debug)})", opcao_debug),
        ]
        
        try:
            resultado = consola.exibir_menu(
                "Sistema de Vendas - Menu de Arranque",
                opcoes,
                "Sair",
                opcao_sair,
                atalho_callback=None,
                loop_externo=True  # Permite recriação das opções
            )
            
            if resultado is True:
                break
            # Se resultado é None, continua o loop (recria opções)
        except KeyboardInterrupt:
            # Ctrl+C fecha o menu
            break

    consola.limpar()
    print("\n")
    consola.sucesso("Obrigado por usar o Sistema de Vendas!\n")

if __name__ == '__main__':
    # Tentar inicializar colorama, mas continuar sem ele se não estiver instalado
    try:
        import colorama
        colorama.init()
    except ImportError:
        pass  # Continua sem colorama, as cores funcionarão sem formatação especial
    
    # Verificar dependências ANTES de fazer qualquer coisa
    if not verificar_e_instalar_dependencias():
        # Se falhar, sai da aplicação
        exit(1)
        
    try:
        menu_principal()
    except KeyboardInterrupt:
        # Ctrl+C fecha o programa com mensagem de adeus
        consola.limpar()
        print("\n")
        consola.sucesso("Obrigado por usar o Sistema de Vendas!\n")
    except Exception as e:
        print(f"Erro não tratado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)