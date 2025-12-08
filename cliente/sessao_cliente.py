import os
import json
import consola

class Sessao:
    def __init__(self):
        self.nome_utilizador = None
        self.cargo = None
        self.token_sessao = None
        self.comandos_por_nome = {}
        self.tokens_locais = self._carregar_tokens_locais()

    def _obter_caminho_tokens(self):        
        # Tenta usar o diretório atual primeiro
        caminho_local = 'tokens.json'
        
        # Verifica se consegue escrever no diretório atual
        try:
            # Testa criando um ficheiro temporário
            with open(caminho_local, 'a', encoding='utf-8'):
                pass
            return caminho_local
        except (PermissionError, OSError):
            # Se falhar, usa a pasta do utilizador
            pasta_usuario = os.path.expanduser('~')
            pasta_app = os.path.join(pasta_usuario, '.sistema_vendas')
            
            # Cria a pasta se não existir
            try:
                os.makedirs(pasta_app, exist_ok=True)
                return os.path.join(pasta_app, 'tokens.json')
            except (PermissionError, OSError):
                # Se tudo falhar, retorna None
                return None

    def _carregar_tokens_locais(self):
        import os, json
        caminho_ficheiro_tokens = self._obter_caminho_tokens()
        
        if caminho_ficheiro_tokens is None:
            consola.aviso("Aviso: Não foi possível determinar local para guardar tokens.")
            return {}
        
        tokens = {}
        try:
            if os.path.exists(caminho_ficheiro_tokens):
                with open(caminho_ficheiro_tokens, 'r', encoding='utf-8') as ficheiro_tokens:
                    tokens = json.load(ficheiro_tokens)

        except (IOError, json.JSONDecodeError, PermissionError) as e:
            consola.aviso(f"Aviso: Não foi possível ler o ficheiro de tokens: {e}")
        return tokens
    
    def _guardar_tokens_locais_em_ficheiro(self):
        caminho_ficheiro_tokens = self._obter_caminho_tokens()
        
        if caminho_ficheiro_tokens is None:
            consola.aviso("Aviso: Não é possível guardar tokens (sem permissões).")
            return
        
        try:
            with open(caminho_ficheiro_tokens, 'w', encoding='utf-8') as ficheiro_tokens:
                json.dump(self.tokens_locais, ficheiro_tokens, ensure_ascii=False, indent=2)

        except PermissionError:
            consola.aviso("\nAviso: Não foi possível guardar o token (permissão negada).")
            consola.info("Possíveis causas:")
            consola.info("  • O ficheiro tokens.json está aberto noutra aplicação")
            consola.info("  • A pasta não tem permissões de escrita")
            consola.info("\nA sessão funcionará, mas o token não será guardado.")
        except (IOError, OSError) as erro:
            consola.aviso(f"\nAviso: Não foi possível guardar o token: {erro}")
            consola.info("A sessão funcionará, mas terá que fazer login novamente da próxima vez.")

    def guardar_token_local(self, utilizador, token):
        if utilizador is not None and len(utilizador) > 0:
            self.tokens_locais[utilizador] = token
        else:
            self.tokens_locais = {}
        self._guardar_tokens_locais_em_ficheiro()

    def remover_token_local(self, utilizador):
        # Remove do dicionário, mesmo que não haja token
        if utilizador in self.tokens_locais:
            del self.tokens_locais[utilizador]
            self._guardar_tokens_locais_em_ficheiro()

        # Limpa dados da sessão se for o utilizador atual
        if self.nome_utilizador == utilizador:
            self.nome_utilizador = None
            self.cargo = None
            self.token_sessao = None
            
    def iniciar_sessao(self, nome_utilizador, cargo, token_sessao):
        self.nome_utilizador = nome_utilizador
        self.cargo = cargo
        self.token_sessao = token_sessao

    def encerrar_sessao(self):
        self.nome_utilizador = None
        self.cargo = None
        self.token_sessao = None

    def esta_logado(self):
        return self.token_sessao is not None

    def obter_credenciais(self):
        if self.token_sessao is not None:
            return {'token_sessao': self.token_sessao}
        return {}

    def definir_comandos_disponiveis(self, comandos):
        self.comandos_por_nome = comandos