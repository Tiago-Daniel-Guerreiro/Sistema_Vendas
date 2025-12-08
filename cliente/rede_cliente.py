import json
import socket
import time
import consola

class ClienteRede:
    def __init__(self, endereco, porta, depuracao=False, sessao=None):
        self.endereco = endereco
        self.porta = porta
        self.depuracao = depuracao
        self.timeout = 10
        self.sessao = sessao
        self.ligacao = None
        self.conectado = False

    def conectar(self, tentativas_maximas=3):
        if self.conectado and self.ligacao is not None:
            consola.aviso("Já existe uma conexão ativa.")
            return True
        
        for tentativa in range(tentativas_maximas):
            try:
                self.ligacao = socket.create_connection(
                    (self.endereco, self.porta),
                    timeout=self.timeout
                )
                self.conectado = True
                return True
                
            except ConnectionRefusedError:
                if tentativa < tentativas_maximas - 1:
                    consola.aviso(
                        f"Ligação recusada. A tentar novamente... "
                        f"({tentativa + 1}/{tentativas_maximas})"
                    )
                    time.sleep(3)
                else:
                    consola.erro("O servidor pode estar offline.")
                    
            except socket.gaierror:
                consola.erro(f'Não foi possível encontrar o endereço: {self.endereco}')
                return False
                
            except Exception as erro:
                consola.erro(f'Erro ao conectar: {erro}')
                if tentativa < tentativas_maximas - 1:
                    time.sleep(3)
        
        return False

    def desconectar(self):
        if self.ligacao is not None:
            try:
                self.ligacao.close()
            except Exception:
                pass
            finally:
                self.ligacao = None
                self.conectado = False

    def reconectar(self, tentativas_maximas=3):
        consola.aviso("A tentar reconectar ao servidor...")
        self.desconectar()
        return self.conectar(tentativas_maximas)

    def enviar_comando(self, acao, parametros=None):
        if parametros is None:
            parametros = {}

        # Verifica se está conectado
        if not self.conectado or self.ligacao is None:
            return {
                'ok': False,
                'erro': 'Não há conexão ativa com o servidor.',
                'reconectar': True
            }

        pacote = {'acao': acao, 'parametros': parametros}
        dados_serializados = json.dumps(pacote) + '\n'

        try:
            # Envia o comando
            self.ligacao.sendall(dados_serializados.encode('utf-8'))

            if self.depuracao is True:
                consola.info_adicional(f">> {dados_serializados.strip()}")

            # Recebe a resposta
            resposta_bytes = b''

            while True:
                try:
                    parte = self.ligacao.recv(4096)
                    if len(parte) == 0:
                        # Servidor fechou a conexão
                        self.conectado = False
                        return {
                            'ok': False,
                            'erro': 'O servidor fechou a ligação.',
                            'reconectar': True
                        }
                    
                    resposta_bytes += parte
                    
                    # Protocolo simples: cada resposta termina com '\n'
                    if b'\n' in parte:
                        break
                        
                except socket.timeout:
                    return {
                        'ok': False,
                        'erro': 'O servidor demorou demasiado a responder.'
                    }

            resposta_texto = resposta_bytes.decode('utf-8').strip()

            if len(resposta_texto) == 0:
                self.conectado = False
                return {
                    'ok': False,
                    'erro': 'O servidor fechou a ligação sem resposta.',
                    'reconectar': True
                }

            if self.depuracao is True:
                consola.info_adicional(f"<< {resposta_texto}")

            try:
                resposta = json.loads(resposta_texto)
            except json.JSONDecodeError:
                return {
                    'ok': False,
                    'erro': 'Resposta inválida do servidor (JSON inválido).'
                }

            return resposta

        except ConnectionRefusedError:
            self.conectado = False
            return {
                'ok': False,
                'erro': 'Ligação recusada. O servidor pode estar offline.',
                'reconectar': True
            }
            
        except socket.gaierror:
            self.conectado = False
            return {
                'ok': False,
                'erro': f'Não foi possível encontrar o endereço: {self.endereco}'
            }

        except (ConnectionResetError, BrokenPipeError, OSError) as erro:
            # Conexão foi perdida
            self.conectado = False
            return {
                'ok': False,
                'erro': f'Conexão perdida: {erro}',
                'reconectar': True
            }
            
        except Exception as erro:
            self.conectado = False
            return {
                'ok': False,
                'erro': f'Erro de comunicação inesperado: {erro}',
                'reconectar': True
            }

    @property
    def tokens_locais(self):
        if self.sessao:
            return self.sessao.tokens_locais
        return {}

    def guardar_token_local(self, utilizador, token):
        if self.sessao:
            self.sessao.guardar_token_local(utilizador, token)

    def remover_token_local(self, utilizador):
        if self.sessao:
            self.sessao.remover_token_local(utilizador)