import json
import socketserver
import threading
import socket
import select
import os
import time
import warnings
from servidor.base_de_dados import GestorBaseDados, ErroConexaoBD
from enums import Mensagem, Cores
from servidor.configuracao import ConfiguracaoServidor
from servidor.comandos import ProcessadorComandos, gestor_comandos_global
import consola

def carregar_dados_exemplo():
    try:
        # Tentar múltiplos caminhos possíveis
        caminhos_possiveis = [
            os.path.join(os.path.dirname(os.path.dirname(__file__)), 'Exemplo.sql'),
            os.path.join(os.getcwd(), 'Exemplo.sql'),
            'Exemplo.sql'
        ]
        
        caminho_sql = None
        for caminho in caminhos_possiveis:
            if os.path.exists(caminho):
                caminho_sql = caminho
                break
        
        if caminho_sql is None:
            consola.erro(f"Arquivo Exemplo.sql não encontrado. Procuraram em: {caminhos_possiveis}")
            return False
        
        consola.info_adicional(f"Carregando SQL de: {caminho_sql}")
        
        bd = GestorBaseDados()
        try:
            bd.conectar()
        except ErroConexaoBD:
            consola.erro("Erro ao conectar à base de dados.")
            return False
        
        if bd.cursor is None or bd.conexao is None:
            consola.erro("Cursor ou conexão da base de dados não estão disponíveis.")
            return False
        
        try:
            with open(caminho_sql, 'r', encoding='utf-8') as arquivo:
                conteudo_sql = arquivo.read()
        except Exception as e:
            consola.erro(f"Erro ao ler arquivo Exemplo.sql: {e}")
            return False
        
        # Dividir por ';' para executar cada comando separadamente
        comandos = conteudo_sql.split(';')
        total_comandos = len([c for c in comandos if c.strip()])
        executados = 0
        
        for i, comando in enumerate(comandos):
            comando = comando.strip()
            if len(comando) > 0:
                try:
                    consola.info_adicional(f"Executando comando {i+1}/{total_comandos}...")
                    bd.cursor.execute(comando)
                    executados += 1
                except Exception as e:
                    consola.aviso(f"Aviso ao executar comando SQL: {e}")
        
        bd.conexao.commit()
        consola.sucesso(f"Dados de exemplo carregados com sucesso! ({executados} comandos executados)")
        return True
        
    except Exception as e:
        consola.erro(f"Erro ao carregar dados de exemplo: {e}")
        import traceback
        traceback.print_exc()
        return False

class GestorPedidosTCP(socketserver.StreamRequestHandler):
    # Flag de classe para sinalizar shutdown
    servidor_encerrando = False
    
    def _enviar_resposta(self, sucesso, resultado=None, erro=None):
        pacote_resposta = {'ok': sucesso}
        if resultado is not None:
            pacote_resposta['resultado'] = resultado
        if erro is not None:
            pacote_resposta['erro'] = erro
        
        try:
            # O `default=str` é um recurso para serializar tipos não-padrão (como datetime).
            mensagem_serializada = json.dumps(pacote_resposta, ensure_ascii=False, default=str) + '\n'
            if ConfiguracaoServidor.MODO_DEPURACAO is True:
                consola.info_adicional(f">> {mensagem_serializada}")
            self.wfile.write(mensagem_serializada.encode('utf-8'))
            self.wfile.flush()
        except Exception as e:
            consola.erro(f"Erro ao enviar resposta para {self.client_address}: {e}")

    def _ler_pedido(self):
        try:
            # Usa select para verificar se há dados disponíveis com timeout de 1 segundo
            # Isso permite verificar a flag de shutdown periodicamente
            pronto, _, _ = select.select([self.request], [], [], 1.0)
            
            if not pronto:
                # Timeout - nenhum dado disponível ainda
                return 'TIMEOUT'
            
            # Há dados disponíveis, agora podemos ler com segurança
            linha_bytes = self.rfile.readline()
            if not linha_bytes:
                return 'DESCONECTADO'
            
            dados = json.loads(linha_bytes.decode('utf-8'))
            
            if not isinstance(dados, dict):
                return None
            
            if ConfiguracaoServidor.MODO_DEPURACAO is True:
                consola.info_adicional(f"<< {dados}")
            return dados
        except json.JSONDecodeError as e:
            self._enviar_resposta(False, erro='Formato JSON inválido.')
            return None
        except Exception as e:
            return 'DESCONECTADO'

    def handle(self):
        # Não define timeout no socket - select() em _ler_pedido() cuida do timeout
        # Isso evita o problema de "cannot read from timed out object"
        
        gestor_bd = GestorBaseDados()
        try:
            gestor_bd.conectar()
        except ErroConexaoBD:
            self._enviar_resposta(False, erro='Falha crítica na base de dados.')
            return
        
        try:
            # Loop para processar múltiplos comandos na mesma conexão
            while not GestorPedidosTCP.servidor_encerrando:
                try:
                    pedido = self._ler_pedido()
                    
                    # Timeout - continua aguardando
                    if pedido == 'TIMEOUT':
                        continue
                    
                    # Cliente fechou a conexão
                    if pedido == 'DESCONECTADO' or pedido is None:
                        break
                    
                    # pedido é um dict válido
                    acao = pedido.get('acao')
                    parametros = pedido.get('parametros', {})

                    try:
                        resultado = ProcessadorComandos.processar_pedido(
                            gestor_bd,
                            gestor_comandos_global,
                            acao,
                            parametros
                        )

                        comando = gestor_comandos_global.obter(acao)

                        if comando is None:
                            self._enviar_resposta(
                                False,
                                erro='Comando não encontrado.'
                            )
                            continue

                        mensagens_sucesso = comando.mensagens_sucesso

                        if mensagens_sucesso is None:
                            mensagens_sucesso = []

                        match resultado:
                            # Caso em que o resultado é diretamente uma Mensagem
                            case Mensagem() as mensagem_resultado:
                                if mensagem_resultado in mensagens_sucesso:
                                    self._enviar_resposta(True,resultado=str(mensagem_resultado))
                                else:
                                    self._enviar_resposta(False,erro=str(mensagem_resultado))

                            # Caso em que o resultado é uma tupla (Mensagem, dados)
                            case (Mensagem() as mensagem_resultado, conteudo_resultado):
                                if mensagem_resultado in mensagens_sucesso:
                                    self._enviar_resposta(
                                        True,
                                        resultado=conteudo_resultado
                                    )
                                else: # Mensagem de erro
                                    self._enviar_resposta(False, erro=str(mensagem_resultado))

                            # Qualquer outro tipo de resultado é considerado sucesso direto
                            case _:
                                self._enviar_resposta(True, resultado=resultado)

                    except Exception as e:
                        self._enviar_resposta(False, erro=f"Erro inesperado no servidor: {e}")
                        # Continua processando outros comandos mesmo após erro
                
                except socket.timeout:
                    # Timeout - verifica flag de shutdown e continua aguardando
                    continue
                except (ConnectionResetError, BrokenPipeError):
                    # Cliente desconectou abruptamente
                    break
                except KeyboardInterrupt:
                    # Servidor está sendo encerrado
                    raise  # Re-lança para o handler externo
                except Exception:
                    # Outro erro - fecha a conexão
                    break
                    
        finally:
            # Fecha a conexão com o banco de dados ao finalizar
            if gestor_bd.conexao:
                gestor_bd.conexao.close()

class UtilitariosServidor:
    @staticmethod
    def limpar_base_dados_depuracao():
        if not ConfiguracaoServidor.MODO_DEPURACAO: return
        try:
            bd = GestorBaseDados(limpar_base_dados=True)
            if bd.conectar():
                consola.sucesso('Base de dados limpa e recriada com sucesso!')
            else:
                consola.erro('Erro ao conectar para limpeza da base de dados.')
        except Exception as e:
            consola.erro(f'Erro ao limpar base de dados: {e}')

    @staticmethod
    def monitorizar_atalho(verificar_atalho_func, mensagem_info, mensagem_sucesso, acao, apenas_windows=True, modo_depuracao=False, sleep_apos_acao=0.5): 
        if apenas_windows and os.name != 'nt':
            return
        if modo_depuracao and not ConfiguracaoServidor.MODO_DEPURACAO:
            return
        if modo_depuracao and os.name != 'nt':
            consola.aviso("Atalhos de depuração disponíveis apenas em Windows.")
            return
        consola.info_adicional(mensagem_info)
        try:
            import win32api
            import win32con
            while True:
                if verificar_atalho_func(win32api, win32con):
                    consola.sucesso(mensagem_sucesso)
                    acao()
                    time.sleep(sleep_apos_acao)
                time.sleep(0.1)
        except ImportError:
            consola.erro("Biblioteca 'pywin32' não encontrada. Atalhos de depuração desativados.")
        except Exception as e:
            consola.erro(f'Erro no monitorizador de atalhos: {e}')

    @staticmethod
    def monitorizar_atalhos_depuracao():
        def verificar_ctrl_alt_p(win32api, win32con): 
            # Verifica se Ctrl+Alt+P está pressionado
            ctrl = win32api.GetKeyState(win32con.VK_CONTROL) < 0
            alt = win32api.GetKeyState(win32con.VK_MENU) < 0
            p = win32api.GetKeyState(ord('P')) < 0
            return ctrl and alt and p
        
        UtilitariosServidor.monitorizar_atalho(
            verificar_atalho_func=verificar_ctrl_alt_p,
            mensagem_info='Atalho de depuração ativo: Pressione Ctrl+Alt+P para limpar a base de dados...',
            mensagem_sucesso='Atalho Ctrl+Alt+P detetado! A limpar base de dados...',
            acao=lambda: (UtilitariosServidor.limpar_base_dados_depuracao(), os._exit(1)),
            apenas_windows=True,
            modo_depuracao=True,
            sleep_apos_acao=0.1
        )

    @staticmethod
    def monitorizar_shift_p():
        def verificar_shift_p(win32api, win32con):
            # Verifica se Shift+P está pressionado
            shift = win32api.GetKeyState(win32con.VK_SHIFT) < 0
            p = win32api.GetKeyState(ord('P')) < 0
            return shift and p
        
        UtilitariosServidor.monitorizar_atalho(
            verificar_atalho_func=verificar_shift_p,
            mensagem_info='Atalho disponível: Pressione Shift+P para carregar dados de exemplo...',
            mensagem_sucesso='Atalho Shift+P detetado! A carregar dados de exemplo...',
            acao=carregar_dados_exemplo,
            apenas_windows=True,
            modo_depuracao=False,
            sleep_apos_acao=0.5
        )

    @staticmethod
    def verificar_porta_ocupada(endereco, porta):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            # connect_ex retorna 0 se a porta estiver ocupada (conexão bem-sucedida).
            return sock.connect_ex((endereco, porta)) == 0
        finally:
            sock.close()

def executar_servidor(endereco, porta, depuracao=False, dados_exemplo_bd=False, funcoes_atalhos=None):
    ConfiguracaoServidor.MODO_DEPURACAO = depuracao
    consola.info_adicional("A verificar as configurações do servidor...")
    if UtilitariosServidor.verificar_porta_ocupada(endereco, porta):
        print(f'{Cores.VERMELHO}A porta {porta} já está em uso.{Cores.NORMAL}')
        return
    
    # Verificar conexão com a base de dados antes de iniciar o servidor
    consola.info_adicional("A verificar conexão com a base de dados...")
    bd_teste = GestorBaseDados()
    try:
        bd_teste.conectar()
        if bd_teste.conexao:
            bd_teste.conexao.close()
    except ErroConexaoBD as e:
        # O método conectar() já mostrou as mensagens de erro detalhadas
        # via exibir_erro_conexao() durante as tentativas
        consola.erro("\nServidor não pode iniciar sem conexão com a base de dados.")
        try:
            consola.pausar()
        except (KeyboardInterrupt, EOFError):
            pass
        return

    # Se dados_exemplo_bd é True, carrega dados de exemplo
    if dados_exemplo_bd:
        carregar_dados_exemplo()

    # Iniciar threads para cada função de atalho fornecida
    if funcoes_atalhos is None:
        funcoes_atalhos = []
        if ConfiguracaoServidor.MODO_DEPURACAO:
            funcoes_atalhos.append(UtilitariosServidor.monitorizar_atalhos_depuracao)
            funcoes_atalhos.append(UtilitariosServidor.monitorizar_shift_p)

    for func in funcoes_atalhos:
        threading.Thread(target=func, daemon=True).start()
    
    try:
        # ThreadingTCPServer cria uma nova thread para cada ligação de cliente.
        servidor = socketserver.ThreadingTCPServer((endereco, porta), GestorPedidosTCP)
        # Permite que o servidor reinicie e reutilize o mesmo endereço imediatamente.
        servidor.allow_reuse_address = True
        # As threads dos clientes são marcadas como 'daemon' para que não impeçam
        # o programa principal de sair.
        servidor.daemon_threads = True
        
        print(f'{Cores.VERDE}Servidor online em {endereco}:{porta}{Cores.NORMAL}')
        print(f'{Cores.CIANO}Pressione Ctrl+C para encerrar.{Cores.NORMAL}')
        
        servidor.serve_forever()

    except KeyboardInterrupt:
        consola.limpar()
        print(f"{Cores.ROXO}Servidor encerrado manualmente.{Cores.NORMAL}")
    except Exception as e:
        consola.limpar()
        print(f"{Cores.VERMELHO}{Cores.NEGRITO}Erro fatal: {e}{Cores.NORMAL}")
    finally:
        if 'servidor' in locals() and servidor:
            print(f"{Cores.AMARELO}A encerrar servidor...{Cores.NORMAL}")
            # Sinaliza todas as threads para encerrarem
            GestorPedidosTCP.servidor_encerrando = True
            # Aguarda um pouco para threads detectarem a flag (select tem timeout de 1s)
            time.sleep(1.5)
            servidor.shutdown()
            servidor.server_close()
            # Reseta o flag para próxima execução
            GestorPedidosTCP.servidor_encerrando = False
            print(f"{Cores.VERDE}Servidor encerrado com sucesso.{Cores.NORMAL}")

def iniciar(endereco=None, porta=None, depuracao=False, dados_exemplo_bd=False):
    # Esconde avisos que podem ocorrer no shutdown do threading.
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    host = endereco or ConfiguracaoServidor.ENDERECO_PADRAO
    port = porta or ConfiguracaoServidor.PORTA_PADRAO
    
    executar_servidor(host, port, depuracao, dados_exemplo_bd)