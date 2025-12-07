class Sessao:
    def __init__(self):
        self.nome_utilizador = None
        self.cargo = None
        self.token_sessao = None
        self.comandos_por_nome = {}
        self.tokens_locais = self._carregar_tokens_locais()

    def _carregar_tokens_locais(self):
        import os, json
        caminho_ficheiro_tokens = 'tokens.json'
        tokens = {}
        try:
            if os.path.exists(caminho_ficheiro_tokens):
                with open(caminho_ficheiro_tokens, 'r', encoding='utf-8') as ficheiro_tokens:
                    tokens = json.load(ficheiro_tokens)

        except (IOError, json.JSONDecodeError, PermissionError):
            print("Não foi possível ler o ficheiro de tokens.")
        return tokens
    
    def _guardar_tokens_locais_em_ficheiro(self):
        import os, json
        caminho_ficheiro_tokens = 'tokens.json'
        try:
            pasta_tokens = os.path.dirname(os.path.abspath(caminho_ficheiro_tokens))
            if not os.path.exists(pasta_tokens):
                os.makedirs(pasta_tokens, exist_ok=True)
            with open(caminho_ficheiro_tokens, 'w', encoding='utf-8') as ficheiro_tokens:
                json.dump(self.tokens_locais, ficheiro_tokens, ensure_ascii=False, indent=2)

        except (IOError, PermissionError) as erro:
            print(f"Não foi possível guardar o token no ficheiro: {erro}")

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