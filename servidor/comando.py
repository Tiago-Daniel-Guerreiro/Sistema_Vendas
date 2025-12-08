from enums import Mensagem

class Comando:
    def __init__(self, nome, acao, descricao='', permissao_minima=None, categoria=None, mensagens_sucesso=None, parametros=None):
        self.nome = nome
        self.acao = acao  # A função a ser executada
        self.descricao = descricao
        self.permissao_minima = permissao_minima  # Níveis: None (público), 'cliente', 'vendedor', 'admin'
        self.categoria = categoria
        
        if parametros is None:
            self.parametros = {}
        else:
            self.parametros = parametros  # Dicionário com a configuração dos parâmetros

        # Validação e atribuição das mensagens de sucesso
        if mensagens_sucesso is None:
            self.mensagens_sucesso = []
        elif isinstance(mensagens_sucesso, list):
            # Garante que apenas instâncias de Mensagem são adicionadas
            lista_filtrada = []
            for msg in mensagens_sucesso:
                if isinstance(msg, Mensagem):
                    lista_filtrada.append(msg)
            self.mensagens_sucesso = lista_filtrada
        elif isinstance(mensagens_sucesso, Mensagem):
            self.mensagens_sucesso = [mensagens_sucesso]
        else:
            self.mensagens_sucesso = []

    def validar_parametros(self, parametros_recebidos):
        # Verifica se todos os parâmetros obrigatórios foram recebidos.
        # Por enquanto, não valida o tipo, para manter a simplicidade.
        for nome_param, config_param in self.parametros.items():
            if config_param.get('obrigatorio', False) and nome_param not in parametros_recebidos:
                return False
        return True

    def validar_permissao(self, utilizador):
        # Se não há permissão mínima, qualquer um pode executar.
        if self.permissao_minima is None:
            return True
        
        # Se o comando requer permissão, mas não há utilizador, nega o acesso.
        if utilizador is None:
            return False

        cargo_utilizador = getattr(utilizador, 'cargo', None)
        niveis_permissao = {
            'cliente': ['cliente', 'vendedor', 'admin'],
            'vendedor': ['vendedor', 'admin'],
            'admin': ['admin']
        }
        
        # Verifica se o cargo do utilizador está na lista de cargos permitidos
        # para a permissão mínima exigida.
        if self.permissao_minima in niveis_permissao:
            if cargo_utilizador in niveis_permissao[self.permissao_minima]:
                return True
        
        return False

    def para_json(self):
        # Converte os metadados do comando para um formato JSON-serializável.
        mensagens_sucesso_str = []
        for msg in self.mensagens_sucesso:
            mensagens_sucesso_str.append(msg.name) # Usa .name para obter a string 'SUCESSO'

        return {
            'comando': self.nome,
            'parametros': self.parametros,
            'descricao': self.descricao,
            'permissao_minima': self.permissao_minima,
            'categoria': self.categoria,
            'mensagens_sucesso': mensagens_sucesso_str
        }