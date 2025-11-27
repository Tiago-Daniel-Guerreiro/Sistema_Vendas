
from enums import Mensagem

class Comando:
    def __init__(self, nome, acao, parametros=None, descricao='', permissao_minima=None, categoria=None, mensagens_sucesso=None):
        self.nome = nome
        self.acao = acao # parâmetro obrigatório, não vai para o json
        if parametros is None:
            parametros = {}
        self.parametros = parametros  # dict: nome -> {'obrigatorio': bool, 'tipo': type}
        self.descricao = descricao
        self.permissao_minima = permissao_minima  # None, 'cliente', 'vendedor', 'admin'
        self.categoria = categoria
        # Aceita lista ou único valor do Enum Mensagem
        if mensagens_sucesso is None:
            self.mensagens_sucesso = []
        elif isinstance(mensagens_sucesso, list):
            self.mensagens_sucesso = [m for m in mensagens_sucesso if isinstance(m, Mensagem)]
        elif isinstance(mensagens_sucesso, Mensagem):
            self.mensagens_sucesso = [mensagens_sucesso]
        else:
            self.mensagens_sucesso = []

    def validar_parametros(self, parametros_recebidos):
        erros = []
        for nome, config in self.parametros.items():
            if config.get('obrigatorio', False) and nome not in parametros_recebidos:
                erros.append(f'Parâmetro obrigatório ausente: {nome}')
            if nome in parametros_recebidos and 'tipo' in config:
                if not isinstance(parametros_recebidos[nome], config['tipo']):
                    erros.append(f'Tipo inválido para {nome}: esperado {config["tipo"].__name__}')
        return erros

    def validar_permissao(self, user):
        if self.permissao_minima is None:
            return True
        if user is None:
            return False # Se o comando requer permissão, mas o user é None, falha automática
        cargo = getattr(user, 'cargo', None)
        match self.permissao_minima:
            case 'cliente':
                if cargo in ['cliente', 'vendedor', 'admin']:
                    return True
            case 'vendedor':
                if cargo in ['vendedor', 'admin']:
                    return True
            case 'admin':
                if cargo == 'admin':
                    return True
        return False

    def resultado_json(self, mensagem=None, dados=None, **extra):
        retorno = {}
        if mensagem is not None:
            retorno['mensagem'] = str(mensagem) if isinstance(mensagem, Mensagem) else mensagem
        if dados is not None:
            retorno['dados'] = dados
        for key, value in extra.items():
            retorno[key] = value
        return retorno

    def to_json(self):
        return {
            'comando': self.nome,
            'parametros': self.parametros,
            'descricao': self.descricao,
            'permissao_minima': self.permissao_minima,
            'categoria': self.categoria,
            'mensagens_sucesso': [str(m) for m in self.mensagens_sucesso]
        }

# Exemplo de métodos para cada comando
class ComandosSistema:
    @staticmethod
    def ping(*args, **kwargs):
        return Mensagem.SUCESSO

    @staticmethod
    def help(*args, **kwargs):
        # A lógica do help deve ser chamada do server.py
        from server import ProcessadorDeComandos
        return ProcessadorDeComandos.help()

    @staticmethod
    def registrar(*args, **kwargs):
        return Mensagem.UTILIZADOR_CRIADO

    # Adicione métodos para cada comando conforme necessário
