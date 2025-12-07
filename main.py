import subprocess
import sys
import socket
import os
from enums import Cores
import consola

def obter_ip_local():
    # Obtém o Ip local criando um socket UDP e conectando ao DNS do Google.
    # Não envia dados, mas faz o Sistema operativo escolher o Ip local.
    # UDP só é usado porque não há uma conexão real e é mais rápido.
    try:
        socket_temporario = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        socket_temporario.settimeout(2.0)
        
        # Endereço de um servidor público para forçar a resolução do Ip local.
        endereco_dns_google = ("8.8.8.8", 80)
        socket_temporario.connect(endereco_dns_google)
        endereco_ip = socket_temporario.getsockname()[0]
    except socket.error:
        endereco_ip = "127.0.0.1" # Se falhar retorna o Ip do localhost
    finally:
        socket_temporario.close()

    return endereco_ip

def reiniciar_programa():
    # Substitui o processo atual por uma nova instância do mesmo programa.
    executavel_python = sys.executable
    os.execl(executavel_python, executavel_python, *sys.argv)

def instalar_pacote(nome_pacote):
    # Instala um pacote Python usando o comando "pip" do cmd.
    consola.info(f"A instalar {nome_pacote}...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", nome_pacote])
        consola.sucesso(f"{nome_pacote} instalado com sucesso!\n")
        return True
    except subprocess.CalledProcessError:
        consola.erro(f"Falha ao instalar {nome_pacote}.\n")
        return False

def verificar_e_instalar_dependencias():
    consola.aviso("A verificar dependências do servidor...\n")
    
    lista_dependencias = [
        ("mysql-connector-python", "mysql.connector", True),
        ("pywin32", "win32api", False)
    ]
    
    faltam_obrigatorias = []
    faltam_opcionais = []
    houve_instalacao = False
    
    for dependencia in lista_dependencias:
        nome_pacote, nome_import, obrigatoria = dependencia

        try:
            __import__(nome_import)
            consola.sucesso(f"Instalado: {nome_pacote}")
        except ImportError:
            match obrigatoria:
                case True:
                    consola.erro(f"Em Falta (Essencial): {nome_pacote}")
                    faltam_obrigatorias.append(nome_pacote)
                case False:
                    consola.aviso(f"Em Falta (Opcional): {nome_pacote}")
                    faltam_opcionais.append(nome_pacote)
    
    if len(faltam_obrigatorias) == 0 and len(faltam_opcionais) == 0:
        consola.sucesso("\nTodas as dependências estão instaladas!\n")
        consola.pausar()
        return True

    if len(faltam_obrigatorias) > 0:
        consola.erro(f"\nDependências obrigatórias em falta: ")
        for pacote in faltam_obrigatorias:
            consola.erro(f"\t{pacote}")

        if consola.sim_ou_nao("Confirma a instalação das dependências obrigatórias?") is False:
            consola.erro("Cancelado. O servidor não pode iniciar sem as dependências obrigatórias.")
            consola.pausar()
            return False
            
        consola.aviso("\nA instalar dependências obrigatórias...")
        for pacote in faltam_obrigatorias:
            if instalar_pacote(pacote) is False:
                return False # A instalação falhou, não é continua pois é essencial

    houve_instalacao = True # Só chega aqui se todas as obrigatórias foram instaladas

    if len(faltam_opcionais) > 0:
        consola.aviso(f"\nDependências opcionais em falta: ")
        for pacote in faltam_opcionais:
            consola.aviso(f"\t{pacote}")
            
        consola.info("Sem estas dependências, algumas funcionalidades podem estar desativadas.")
        consola.pausar()

        if consola.sim_ou_nao("Deseja instalá-las agora? (s/n):") is True:
            consola.aviso("\nA instalar dependências opcionais...")
            for pacote in faltam_opcionais:
                instalar_pacote(pacote) # Se a opcional falhar, não impede o arranque
            houve_instalacao = True
        else:
            consola.aviso("\nA continuar sem as dependências opcionais...")

    if houve_instalacao is True:
        consola.sucesso("\nInstalação concluída.")
        consola.aviso("É necessário reiniciar a aplicação para carregar as novas bibliotecas.")
        consola.pausar()
        reiniciar_programa()
    
    return True # Isto só acontece se algo não foi instalado

def configurar_rede(para_servidor):
    host_padrao = "127.0.0.1"
    porta_padrao = 5000

    host = host_padrao
    porta = porta_padrao

    if para_servidor is True:
        ip_local = obter_ip_local()
        consola.sucesso(f"Ip local detetado: {ip_local}")
        if consola.sim_ou_nao("Deseja usar este Ip? (s/n, Enter para 's'):", padrao=True) is False:
            host = consola.ler_texto(f"Introduza o Ip desejado (Enter para {host_padrao}):", obrigatorio=False)
            if host is not None and len(host) == 0: # Se estiver vazio, usa o padrão
                host = host_padrao
        else:
            host = ip_local
    else: # para cliente
        host = consola.ler_texto(f"Ip do Servidor (Enter para {host_padrao}):", obrigatorio=False)
        if len(host) == 0:
            host = host_padrao

    # Permite que o utilizador defina a porta juntamente com o Ip (ex: 192.168.1.10:8000)
    partes_endereco = host.split(":")
    if len(partes_endereco) == 2 and partes_endereco[1].isdigit():
        host = partes_endereco[0]
        porta = int(partes_endereco[1])
    else:
        entrada_porta = consola.ler_texto(f"Porta (Enter para {porta_padrao}):", obrigatorio=False)
        if len(entrada_porta) > 0:
            if entrada_porta.isdigit():
                porta = int(entrada_porta)
            else:
                consola.erro(f"Porta inválida. A usar a porta padrão {porta_padrao}.")

    return host, porta

def iniciar_aplicacao(iniciar_servidor, modo_debug, dados_exemplo_bd=False):
    if iniciar_servidor is True:
        nome_modulo = "servidor" 
    else:
        nome_modulo = "cliente"

    consola.limpar()
    consola.importante_destacado(f"A inicializar o {nome_modulo}")

    if iniciar_servidor is True:
        if verificar_e_instalar_dependencias() is False:
            return # Não continua se as dependências obrigatórias não forem instaladas.
        
        consola.limpar()
        consola.importante_destacado(f"Configuração do {nome_modulo}\n")

    consola.aviso("Configuração de Rede:\n")
    host, porta = configurar_rede(para_servidor=iniciar_servidor)

    if iniciar_servidor is True:
        texto_acao = "A iniciar servidor" 
    else: # cliente
        texto_acao = "A conectar ao servidor"

    consola.sucesso(f"\n{texto_acao} em {host}:{porta}...")
    
    try:
        # Importa aqui para evitar erros de importação devido a dependências.
        if iniciar_servidor is True:
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
    
    # Definir funções para as opções do menu
    def opcao_servidor():
        nonlocal popular_dados_exemplo
        iniciar_aplicacao(iniciar_servidor=True, modo_debug=modo_debug, dados_exemplo_bd=popular_dados_exemplo)
        popular_dados_exemplo = False  # Reseta após usar
    
    def opcao_cliente():
        iniciar_aplicacao(iniciar_servidor=False, modo_debug=modo_debug)
    
    # Função para alternar debug (especial pois modifica modo_debug)
    def opcao_debug():
        nonlocal modo_debug
        modo_debug = not modo_debug
        consola.normal(f"Modo de Debug: {consola.formatar_estado_debug(modo_debug)}")
        # Retorna False para continuar no menu
        return False
    
    def opcao_sair():
        return True
    
    # Callback para gerenciar atalhos
    def atalho_callback_wrapper():
        nonlocal popular_dados_exemplo
        if consola.sim_ou_nao("Deseja carregar dados de exemplo (Exemplo.sql) no servidor?"):
            popular_dados_exemplo = True
            consola.sucesso("Dados de exemplo serão carregados na próxima inicialização do servidor.")
        else:
            popular_dados_exemplo = False
            consola.info("Carregamento de dados de exemplo cancelado.")
    
# Loop principal - recria opções a cada iteração para atualizar debug
    opcoes = [
        (f"Iniciar {Cores.LARANJA}Servidor{Cores.NORMAL}", opcao_servidor),
        (f"Iniciar {Cores.CASTANHO}Cliente{Cores.NORMAL}", opcao_cliente),
        (f"Alterar modo de Debug (Padrão: {consola.formatar_estado_debug(False)})", opcao_debug),
    ]
    
    # Executar menu - volta aqui após cada opção (sem callback de atalhos para evitar erro de threading)
    _ = consola.exibir_menu(
        "Sistema de Vendas - Menu de Arranque",
        opcoes,
        "Sair",
        opcao_sair,
        atalho_callback=None
    )    

    consola.limpar()
    print("\n")
    consola.sucesso("Obrigado por usar o Sistema de Vendas!\n")

if __name__ == '__main__':
    try:
        import colorama
        colorama.init()
    except ImportError:
        print("Módulo 'colorama' não encontrado. As cores podem não funcionar corretamente no Windows.")
        print("Para instalar, execute: pip install colorama\n")
        consola.pausar()
        
    try:
        menu_principal()
    except Exception as e:
        print(f"Erro não tratado: {e}")
        import traceback
        traceback.print_exc()
        exit(1)