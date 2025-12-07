import json
import socket
import os
import consola

class ClienteRede:
    def __init__(self, endereco, porta, depuracao=False, sessao=None):
        self.endereco = endereco
        self.porta = porta
        self.depuracao = depuracao
        self.timeout = 10
        self.sessao = sessao

    def enviar_comando(self, acao, parametros=None):
        if parametros is None:
            parametros = {}

        pacote = {'acao': acao, 'parametros': parametros}
        dados_serializados = json.dumps(pacote) + '\n'

        try:
            with socket.create_connection((self.endereco, self.porta), timeout=self.timeout) as ligacao:
                ligacao.sendall(dados_serializados.encode('utf-8'))

                if self.depuracao is True:
                    consola.info_adicional(f">> {dados_serializados.strip()}")

                resposta_bytes = b''

                while True:
                    try:
                        parte = ligacao.recv(4096)
                        if len(parte) == 0:
                            break # Ligação fechada pelo servidor
                        resposta_bytes += parte
                        # Protocolo simples: cada resposta termina com '\n'
                        if b'\n' in parte:
                            break
                    except socket.timeout:
                        return {
                            'ok': False,
                            'erro': ('O servidor demorou demasiado a responder.')
                        }

                resposta_texto = resposta_bytes.decode('utf-8').strip()

                if len(resposta_texto) == 0:
                    return {
                        'ok': False,
                        'erro': ('O servidor fechou a ligação sem resposta.')
                    }

                if self.depuracao is True:
                    consola.info_adicional(f"<< {resposta_texto}")

                try:
                    resposta = json.loads(resposta_texto)
                except json.JSONDecodeError:
                    return {
                        'ok': False,
                        'erro': ('Resposta inválida do servidor (JSON inválido).')
                    }

                return resposta

        except ConnectionRefusedError:
            return {
                'ok': False,
                'erro': (
                    'Ligação recusada. '
                    'O servidor pode estar offline.'
                )
            }
        except socket.gaierror:
            return {
                'ok': False,
                'erro': ( f'Não foi possível encontrar o endereço: {self.endereco}')
            }
        except Exception as erro:
            return {
                'ok': False,
                'erro': f'Erro de comunicação inesperado: {erro}'
            }

    @property
    def tokens_locais(self):
        """Delegador para tokens_locais da sessão."""
        if self.sessao:
            return self.sessao.tokens_locais
        return {}

    def guardar_token_local(self, utilizador, token):
        """Delegador para guardar token na sessão."""
        if self.sessao:
            self.sessao.guardar_token_local(utilizador, token)

    def remover_token_local(self, utilizador):
        """Delegador para remover token da sessão."""
        if self.sessao:
            self.sessao.remover_token_local(utilizador)