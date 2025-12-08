from enum import Enum

class Cores(Enum):
    ROXO = '\033[95m'
    AZUL = '\033[94m'
    CIANO = '\033[96m'
    VERDE = '\033[92m'
    AMARELO = '\033[93m'
    VERMELHO = '\033[91m'
    LARANJA = '\033[38;5;208m'
    MAGENTA = '\033[35m'
    CASTANHO = '\033[38;5;130m'
    CINZA = '\033[90m'
    NORMAL = '\033[0m'
    NEGRITO = '\033[1m'
    INVISIVEL = '\033[08m' 
    # Texto invisível para o "ENTER para continuar..." 
    # Pois não queremos que o utilizador veja o texto
    # E a tentativa de usar algo como readkeys não funcionou bem em todos os terminais

    def __str__(self):
        return self.value
    
class Dependencia(Enum):
    SERVIDOR = "servidor"
    CLIENTE = "cliente"
    AMBOS = "ambos"

class Mensagem(Enum):
    PONG = "Pong"
    SUCESSO = "Operação concluída com sucesso"
    ERRO_GENERICO = "Ocorreu um erro inesperado"
    UTILIZADOR_CRIADO = "Utilizador criado com sucesso"
    UTILIZADOR_JA_EXISTE = "Este utilizador já existe"
    LOGIN_INVALIDO = "Login inválido"
    CREDENCIAIS_INVALIDAS = "Credenciais inválidas"
    PERMISSAO_NEGADA = "Permissão negada"
    O_PERFIL_JA_E_ADMIN = "O perfil já é administrador"
    O_VENDEDOR_TEM_QUE_SER_ASSOCIADO_A_LOJA = "O vendedor tem que ser associado a uma loja"
    CARGO_INVALIDO = "Cargo inválido"
    REGISTRO_INDISPONIVEL = "Registo indisponível"
    LOJA_NAO_ENCONTRADA = "Loja não encontrada"
    COMANDO_DESCONHECIDO = "Comando desconhecido"
    ADICIONADO = "Adicionado com sucesso"
    ERRO_DUPLICADO = "Registo duplicado"
    ATUALIZADO = "Atualizado com sucesso"
    NAO_ENCONTRADO = "Não encontrado"
    REMOVIDO = "Removido com sucesso"
    ERRO_LOJA_OBRIGATORIA = "Loja obrigatória"
    ERRO_PERMISSAO = "Erro de permissão"
    PENDENTE = "Pendente"
    CONFIRMADA = "Confirmada"
    CONCLUIDA = "Concluída"
    STOCK_INSUFICIENTE = "Stock insuficiente"
    PRODUTO_NAO_ENCONTRADO = "Produto não encontrado"
    ERRO_PROCESSAMENTO = "Erro no processamento"
    ALERTA_STOCK_BAIXO = "Alerta: Stock baixo"
    COMANDO_NAO_ENCONTRADO = "Comando não encontrado"
    PARAMETROS_INVALIDOS = "Parâmetros inválidos"
    
    def __str__(self):
        return self.value