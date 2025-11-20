import sys
from typing import List, Tuple, Any, Dict, Optional, Sequence, Union
from abc import ABC, abstractmethod
from enum import Enum
import mysql.connector
import re

# Dados Base 
class TipoDadoSQLBase(Enum): 
    """ Tipos de dados SQL. """
    Inteiro = "INT"
    Inteiro_Grande = "BIGINT"
    Decimal = "DECIMAL"
    Varchar = "VARCHAR"
    Texto = "TEXT"
    Data = "DATE"
    Timestamp = "TIMESTAMP"
    Booleano = "BOOLEAN"

class TipoSQL:
    """ Representa um tipo de dado SQL, incluindo seus parâmetros. """
    def __init__(self, tipo_base: TipoDadoSQLBase, tamanho: int = None, precisao: int = None, escala: int = None):
        self._tipo_base = tipo_base
        self._tamanho = tamanho
        self._precisao = precisao
        self._escala = escala
        
        self._validar()

    def _validar(self):
        """Garante que os parâmetros foram fornecidos para o tipo base corretamente."""
        if self._tipo_base == TipoDadoSQLBase.Varchar and self._tamanho is None:
            raise ValueError("O tipo VARCHAR requer o parâmetro 'tamanho'.")
        
        if self._tipo_base == TipoDadoSQLBase.Decimal and (self._precisao is None or self._escala is None):
            raise ValueError("O tipo DECIMAL requer os parâmetros 'precisao' e 'escala'.")

    def __str__(self) -> str:
        """Formata o tipo de dado para uma string SQL, incluindo os parênteses."""
        tipo_str = self._tipo_base.value

        if self._tipo_base == TipoDadoSQLBase.Varchar:
            tipo_str += f"({self._tamanho})"
    
        if self._tipo_base == TipoDadoSQLBase.Decimal:
            tipo_str += f"({self._precisao}, {self._escala})"
            
        return tipo_str

    @classmethod
    def varchar(cls, tamanho: int) -> "TipoSQL":
        return cls(TipoDadoSQLBase.Varchar, tamanho=tamanho)

    @classmethod
    def decimal(cls, precisao: int, escala: int) -> "TipoSQL":
        return cls(TipoDadoSQLBase.Decimal, precisao=precisao, escala=escala)
    
    @classmethod
    def inteiro(cls) -> "TipoSQL":
        return cls(TipoDadoSQLBase.Inteiro)

    @classmethod
    def texto(cls) -> "TipoSQL":
        return cls(TipoDadoSQLBase.Texto)
        
    @classmethod
    def timestamp(cls) -> "TipoSQL":
        return cls(TipoDadoSQLBase.Timestamp)

class RestricaoColuna(Enum):
    """
    Restrições de coluna (constraints) que podem ser aplicadas.
    \nComo: chaves primárias, valores não nulos, unicos...
    """
    Chave_Primaria = "PRIMARY KEY"
    Nao_Nulo = "NOT NULL"
    Unico = "UNIQUE"
    Padrao = "DEFAULT"
    AutoIncremento = "AUTO_INCREMENT"

    def formatar_sql(self, valor=None) -> 'Script_SQL':
        """
        Formata a restrição como uma string SQL.
        \nA restrição 'Padrao', utiliza o valor fornecido.
        """

        if self == RestricaoColuna.Padrao:
            return Script_SQL(f"{self.value} {self._formatar_valor_default_str(valor)}") # Apenas o Default precisa de uma lógica diferente
        
        return Script_SQL(self.value)
    
    def _formatar_valor_default_str(self,valor) -> str:
        if valor is None:
            raise ValueError("A restrição 'Padrao' (DEFAULT) requer um valor.")
        
        if isinstance(valor, str): # Formata o valor dependendo do seu tipo
            return f"'{valor}'"
        
        # Usa a conversão "normal" para todos os outros tipos (ExpressaoSQL, int, float, bool, etc.),
        return str(valor) # A classe ExpressaoSQL tem um str proprio então não precisa de uma verificação adicional
   
class DirecaoOrdenacao(Enum):
    """ Direção da ordenação dos resultados em uma consulta SELECT. """
    Ascendente = "ASC"
    Descendente = "DESC"

class OperadorComparacao(Enum):
    """ Operadores de comparação para usar em WHERE. """
    Igual = "="
    Diferente = "!="
    Maior_Que = ">"
    Menor_Que = "<"
    Maior_Ou_Igual = ">="
    Menor_Ou_Igual = "<="
    Como = "LIKE"
    Em = "IN"

class OperadorLogico(Enum):
    """ Operadores lógicos para combinar múltiplas condições. """
    E = "AND"
    Ou = "OR"

class TipoJunta(Enum):
    """ Tipos de JOIN que podem ser realizados entre tabelas. """
    Ambas = "INNER JOIN"
    """ Retorna os registros que têm correspondência em ambas as tabelas. """
    Esquerda = "LEFT JOIN"
    """ Retorna todos os registros da tabela à esquerda e os correspondentes da tabela à direita. """
    Direita = "RIGHT JOIN"
    """ Retorna todos os registros da tabela à direita e os correspondentes da tabela à esquerda. """
    Tudo = "FULL OUTER JOIN"
    """ Retorna todos os registros quando há uma correspondência em qualquer uma das tabelas. """

class Conjunto_De_Dados_Para_Inserir:
    """
    Representa um Conjunto de dados formatados para inserir vários dados em um unico comando (executemany).
    \nNão suporta ExpressaoSQL, pois o sql deve ser único para todo o Conjunto.
    \nExemplo de dados: [["valor1_col1", 123, True], ["valor2_col1", 456, False], ...]
    """
    def __init__(self, tabela_alvo: str, colunas: List[str], dados: List[List[Any]]):
        if not tabela_alvo or not colunas or not dados:
            raise ValueError("A tabela, colunas ou dados não podem estar vazios.")
            
        self._tabela_alvo = tabela_alvo
        self._colunas = colunas
        self._dados = dados
        self._validar_consistencia()

    def _validar_consistencia(self):
        """Garante que a estrutura dos dados é consistente."""
        num_colunas = len(self._colunas)
        for i, linha in enumerate(self._dados):
            if len(linha) != num_colunas:
                raise ValueError(
                    f"Inconsistência de dados na linha {i} do Conjunto para a tabela '{self._tabela_alvo}': "
                    f"Esperava {num_colunas} valores, mas encontrou {len(linha)}."
                )

    def preparar_para_executor(self) -> 'Script_SQL': # Tuple[str, List[List[Any]]]

        """Gera o sql e a lista de dados no formato que o 'executemany' espera."""
        # Escapa nomes de colunas e de tabela apenas quando necessário
        nomes_colunas = []
        for coluna in self._colunas: 
            nomes_colunas.append(FormatadorSQL.identificador(coluna))

        nomes_colunas_str = ", ".join(nomes_colunas)
        placeholders_str = ", ".join(["%s"] * len(self._colunas))

        sql = f"INSERT INTO {FormatadorSQL.identificador(self._tabela_alvo)} ({nomes_colunas_str}) VALUES ({placeholders_str})"
        return Script_SQL(sql, self._dados)

    @property
    def colunas(self) -> List[str]:
        return self._colunas

    @property
    def dados(self) -> List[List[Any]]:
        return self._dados

# Scripts SQL e Validação
class Script_SQL:
    """ Representa um parte do script SQL, contendo o texto e os parâmetros associados. """
    def __init__(self, sql: str = "", params: List[Any] = None):
        """ Inicializa o script SQL. """
        self.__sql: str = sql.strip() # Remove espaços em branco no início/fim
        # Garante que params=None resulta numa lista vazia em vez de tentar iterar None
        self.__params: List[Any] = list(params) if params is not None else []

    @property
    def sql(self) -> str:
        """Retorna a string SQL."""
        return self.__sql

    @property
    def params(self) -> List[Any]:
        """Retorna a lista de parâmetros."""
        return list(self.__params)

    def __str__(self) -> str:
        """Representação simples, retorna apenas o SQL."""
        return self.__sql
      
    def __eq__(self, outro: object) -> bool:
        """Verifica se dois objetos Script_SQL são iguais (mesmo SQL e mesmos parâmetros)."""
        if not isinstance(outro, Script_SQL):
            return NotImplemented

        return self.sql == outro.sql and self.params == outro.params

    def __bool__(self) -> bool:
        """Permite verificar se o script não está vazio (ex: if meu_script:)."""
        return bool(self.__sql)

    def __add__(self, outro: 'Script_SQL') -> 'Script_SQL':
        """
        Combina dois scripts SQL usando o operador '+'.
        \nRetorna um novo objeto Script_SQL com o resultado.
        """
        if not isinstance(outro, Script_SQL):
            raise TypeError("Só é possível somar Script_SQL com outro Script_SQL.")

        # Junta apenas as partes não vazias com um espaço entre elas.
        partes: List[str] = []
            
        if self.sql:
            partes.append(self.sql)
        if outro.sql:
            partes.append(outro.sql)

        novo_sql = " ".join(partes)

        # Combina as listas de parâmetros (mantendo a ordem)
        novos_params = list(self.params) + list(outro.params)

        return Script_SQL(novo_sql, novos_params)

    @staticmethod
    def juntar(scripts: list['Script_SQL'], separador: str = " ") -> 'Script_SQL':
        """ Junta uma lista de objetos Script_SQL em um único script, usando um separador entre as partes de SQL. """
        sql_final = []
        params_finais = []
        scripts_validos = []

        # Filtra scripts vazios para não adicionar separadores desnecessários
        for script in scripts:
            if script:
                scripts_validos.append(script)

        for i, script in enumerate(scripts_validos):
            sql_final.append(script.sql)
            params_finais.extend(script.params)
            
            # Adiciona o separador, exceto após o último item
            if i < len(scripts_validos) - 1:
                sql_final.append(separador)

        return Script_SQL("".join(sql_final), params_finais)
    
class ExpressaoSQL:
    """
    Classe para expressões SQL literais, serve apenas como uma marcação de que tipo de valor é, para que não seja tratado como string.
    \n(Para usar valores como 'CURRENT_TIMESTAMP')
    """
    def __init__(self, valor: str):
        """
        Armazena a expressão SQL.
        \nExemplo: "CURRENT_TIMESTAMP".
        """
        self.valor = valor

    def __str__(self) -> str:
        """ Retorna a expressão SQL como uma string para ser usada diretamente no comando. """
        return self.valor

class ExcecaoSegurancaSQL(ValueError):
    """ Exceção personalizada para ser lançada quando uma potencial falha de segurança de SQL, como a injeção de comandos perigosos, é detectada. """
    pass

class VerificadorDeSeguranca:
    """ Valida scripts de SQL contra palavras-chave perigosas. """
    def __init__(self):
        """ Inicializa o verificador com uma lista de palavras-chave proibidas. """
        self._palavras_proibidas = [
            'drop',
            'truncate',
            'alter',
            'grant',
            'revoke',
            'commit',
            'rollback',
            'savepoint',
            '--',
            ';',
            'replace',
            'rename'
        ]

    def validar(self, script_obj: Script_SQL):
        """ Verifica o script SQL de um Script_SQL. """
        script_em_minusculas = script_obj.sql.lower()

        for palavra in self._palavras_proibidas:
            padrao = r'\b' + re.escape(palavra) + r'\b'
            if re.search(padrao, script_em_minusculas):
                raise ExcecaoSegurancaSQL(...)
                
        return True

class FormatadorSQL:
    """
    Classe de utilidades para a formatação de partes de SQL.
    \nCom a lógica de placeholders e outras convenções de sintaxe.
    """
    
    @staticmethod
    def placeholder() -> str:
        """Retorna a string de placeholder padrão (ex: '%s')."""
        return "%s"

    @staticmethod
    def lista_placeholders(quantidade: int) -> str:
        """ Gera uma string de placeholders separados por vírgula para cláusulas IN ou VALUES. """
        
        if quantidade < 1:
            return ""
        
        placeholder_unitario = FormatadorSQL.placeholder()
        return ", ".join([placeholder_unitario] * quantidade)
    
    @staticmethod
    def identificador(name: str) -> str:
        """Formata um identificador (simples ou pontuado) envolvendo cada parte com 'backticks'."""
        if name is None:
            return name

        partes = name.split('.')
        partes_escapadas = []

        for parte in partes:
            normalizada = parte.strip()
            if not normalizada:
                raise ValueError(f"Identificador inválido detectado em '{name}'.")

            # Remove pares exteriores de backticks para evitar duplicação
            if normalizada.startswith('`') and normalizada.endswith('`') and len(normalizada) >= 2:
                normalizada = normalizada[1:-1]

            normalizada = normalizada.replace('`', '``')
            partes_escapadas.append(f"`{normalizada}`")

        return '.'.join(partes_escapadas)
# Condições

class Condicao(ABC):
    def __init__(self, logica: Optional[OperadorLogico] = None):
        """Armazena o operador lógico (AND/OR) que precede esta condição, se houver."""
        self.logica = logica

    @abstractmethod
    def gerar_script(self) -> Script_SQL:
        pass

    @staticmethod
    def criar(coluna: str, operador: OperadorComparacao, valor: Any, logica: Optional[OperadorLogico] = None) -> 'Condicao':
        """Cria a instância da subclasse apropriada com base no operador e no tipo de valor.

        Aceita um parâmetro opcional 'logica' (OperadorLogico) que será repassado ao construtor
        da condição (quando aplicável).
        """
        is_expressao = isinstance(valor, ExpressaoSQL)
        is_in = (operador == OperadorComparacao.Em)

        if is_in and is_expressao:
            return CondicaoInExpressao(coluna, valor, logica)
        elif is_in and not is_expressao:
            return CondicaoIn(coluna, valor, logica)
        elif not is_in and is_expressao:
            return CondicaoExpressao(coluna, operador, valor, logica)
        else:
            return CondicaoSimples(coluna, operador, valor, logica)

class CondicaoSimples(Condicao):
    """
    Representa uma condição onde o valor será parametrizado de forma segura.
    \nEx: 'idade = %s'.
    """
    def __init__(self, coluna: str, operador: OperadorComparacao, valor: Any, logica: Optional[OperadorLogico]):
        super().__init__(logica)
        self.coluna = coluna
        self.operador = operador
        self.valor = valor

    def gerar_script(self) -> Script_SQL:
        sql_str = f"{self.coluna} {self.operador.value} %s"
        return Script_SQL(sql_str, [self.valor])
    
class CondicaoIn(Condicao):
    """Representa uma condição 'coluna IN (%s, %s, ...)'."""
    def __init__(self, coluna: str, valores: List[Any], logica: Optional[OperadorLogico]):
        super().__init__(logica)

        if not isinstance(valores, list) or not valores:
            raise ValueError("O valor para o operador IN deve ser uma lista não vazia.")
        
        self.coluna = coluna
        self.valores = valores

    def gerar_script(self) -> Script_SQL:
        placeholders = ", ".join(["%s"] * len(self.valores))
        sql_str = f"{self.coluna} IN ({placeholders})"
        return Script_SQL(sql_str, self.valores)

class CondicaoExpressao(Condicao):
    """
    Representa uma condição onde o valor é uma expressão SQL literal.
    \nEx: 'data_cadastro > NOW()' ou 'pontos = pontos + 1'.
    """
    def __init__(self, coluna: str, operador: OperadorComparacao, expressao: ExpressaoSQL, logica: Optional[OperadorLogico]):
        super().__init__(logica)
        self.coluna = coluna
        self.operador = operador
        self.expressao = expressao

    def gerar_script(self) -> Script_SQL:
        return Script_SQL(f"{self.coluna} {self.operador.value} {self.expressao}")

class CondicaoInExpressao(Condicao):
    """Representa uma condição 'coluna IN (expressao)' com uma expressão literal."""
    def __init__(self, coluna: str, expressao: ExpressaoSQL, operador_logico: Optional[OperadorLogico]):
        super().__init__(operador_logico)
        self.coluna = coluna
        self.expressao = expressao

    def gerar_script(self) -> Script_SQL:
        return Script_SQL(f"{self.coluna} IN {self.expressao}")
    
# Definições dos conjuntos principais: Coluna, Tabela, BaseDeDados e ChaveEstrangeira que serve como ligação
class AcaoReferencial(Enum):
    """Ações suportadas para cláusulas ON UPDATE / ON DELETE em chaves estrangeiras."""
    Cascade = "CASCADE"
    Restrict = "RESTRICT"
    No_Action = "NO ACTION"
    Set_Null = "SET NULL"
    Set_Default = "SET DEFAULT"

class ChaveEstrangeira:
    """Representa uma chave estrangeira (FOREIGN KEY) entre duas tabelas."""

    def __init__(
        self,
        colunas_locais: Union[str, Sequence[str]],
        tabela_referenciada: str,
        colunas_referenciadas: Union[str, Sequence[str]],
        on_delete: Optional[AcaoReferencial] = None,
        on_update: Optional[AcaoReferencial] = None,
    ):
        """Permite definir chaves simples ou compostas, com ações de atualização/remoção."""
        self.colunas_locais = self._normalizar_colunas(colunas_locais, "colunas_locais")
        self.colunas_referenciadas = self._normalizar_colunas(colunas_referenciadas, "colunas_referenciadas")
        if len(self.colunas_locais) != len(self.colunas_referenciadas):
            raise ValueError("O número de colunas locais e referenciadas deve ser o mesmo em uma chave estrangeira.")

        self.tabela_referenciada = tabela_referenciada
        self.on_delete = on_delete
        self.on_update = on_update

        # Compatibilidade retroativa para atributos antigos (coluna singular)
        self.coluna_local = self.colunas_locais[0]
        self.coluna_referenciada = self.colunas_referenciadas[0]

    @classmethod
    def Simples(
        cls,
        coluna_local: str,
        tabela_referenciada: str,
        coluna_referenciada: str,
        on_delete: Optional[AcaoReferencial] = None,
        on_update: Optional[AcaoReferencial] = None,
    ) -> "ChaveEstrangeira":
        """Facilita a criação de chaves estrangeiras simples usando strings individuais."""
        for valor, nome in (
            (coluna_local, "coluna_local"),
            (tabela_referenciada, "tabela_referenciada"),
            (coluna_referenciada, "coluna_referenciada"),
        ):
            if not isinstance(valor, str) or not valor.strip():
                raise ValueError(f"{nome} deve ser uma string não vazia para ChaveEstrangeira.Simples().")

        return cls(
            coluna_local.strip(),
            tabela_referenciada.strip(),
            coluna_referenciada.strip(),
            on_delete=on_delete,
            on_update=on_update,
        )

    @classmethod
    def Composta(
        cls,
        colunas_locais: Sequence[str],
        tabela_referenciada: str,
        colunas_referenciadas: Sequence[str],
        on_delete: Optional[AcaoReferencial] = None,
        on_update: Optional[AcaoReferencial] = None,
    ) -> "ChaveEstrangeira":
        """Cria uma chave estrangeira composta, exigindo pelo menos duas colunas em cada lado."""
        cols_locais = list(colunas_locais or [])
        cols_ref = list(colunas_referenciadas or [])

        if len(cols_locais) < 2 or len(cols_ref) < 2:
            raise ValueError("ChaveEstrangeira.Composta requer pelo menos duas colunas em cada lado.")

        return cls(
            cols_locais,
            tabela_referenciada,
            cols_ref,
            on_delete=on_delete,
            on_update=on_update,
        )

    @staticmethod
    def _normalizar_colunas(colunas: Union[str, Sequence[str]], nome_parametro: str) -> List[str]:
        if isinstance(colunas, str):
            colunas_normalizadas = [colunas]
        else:
            colunas_normalizadas = list(colunas or [])

        if not colunas_normalizadas:
            raise ValueError(f"'{nome_parametro}' deve conter pelo menos uma coluna para a chave estrangeira.")

        return colunas_normalizadas

    def construir_sql_criar(self) -> Script_SQL:
        """Retorna o SQL da definição da chave estrangeira dentro de um comando CREATE TABLE."""
        colunas_locais_sql = ", ".join(FormatadorSQL.identificador(col) for col in self.colunas_locais)
        colunas_referenciadas_sql = ", ".join(FormatadorSQL.identificador(col) for col in self.colunas_referenciadas)

        partes = [
            f"FOREIGN KEY ({colunas_locais_sql})",
            f"REFERENCES {FormatadorSQL.identificador(self.tabela_referenciada)} ({colunas_referenciadas_sql})",
        ]

        if self.on_delete:
            partes.append(f"ON DELETE {self.on_delete.value}")
        if self.on_update:
            partes.append(f"ON UPDATE {self.on_update.value}")

        return Script_SQL(" ".join(partes))

class ChavePrimaria:
    """Representa uma definição de chave primária (simples ou composta)."""

    def __init__(self, colunas: Sequence[str]):
        self._colunas = tuple(self._normalizar_colunas(colunas))

    @classmethod
    def Simples(cls, coluna: str) -> "ChavePrimaria":
        """Cria uma chave primária composta por uma única coluna."""
        if not isinstance(coluna, str):
            raise TypeError("A coluna da chave primária simples deve ser uma string.")
        coluna_limpa = coluna.strip()
        if not coluna_limpa:
            raise ValueError("O nome da coluna da chave primária simples não pode ser vazio.")
        return cls([coluna_limpa])

    @classmethod
    def Composta(cls, colunas: Sequence[str]) -> "ChavePrimaria":
        """Cria uma chave primária composta por múltiplas colunas."""
        colunas_lista = list(colunas or [])
        if len(colunas_lista) < 2:
            raise ValueError("Uma chave primária composta requer pelo menos duas colunas.")
        return cls(colunas_lista)

    @staticmethod
    def _normalizar_colunas(colunas: Sequence[str]) -> List[str]:
        if isinstance(colunas, str):
            colunas_normalizadas = [colunas]
        else:
            colunas_normalizadas = list(colunas or [])

        if not colunas_normalizadas:
            raise ValueError("Uma chave primária deve conter ao menos uma coluna.")

        resultado: List[str] = []
        for coluna in colunas_normalizadas:
            if not isinstance(coluna, str):
                raise TypeError("Os nomes das colunas da chave primária devem ser strings.")
            coluna_limpa = coluna.strip()
            if not coluna_limpa:
                raise ValueError("Os nomes das colunas da chave primária não podem ser vazios.")
            resultado.append(coluna_limpa)

        return resultado

    @property
    def colunas(self) -> List[str]:
        return list(self._colunas)

    def construir_sql(self) -> Script_SQL:
        colunas_sql = ", ".join(FormatadorSQL.identificador(nome) for nome in self._colunas)
        return Script_SQL(f"PRIMARY KEY ({colunas_sql})")

    def __str__(self) -> str:
        return self.construir_sql().sql

# Alias para manter a assinatura sugerida pelo utilizador
Chave_Primaria = ChavePrimaria

class Coluna:
    """ Define uma coluna de uma tabela, incluindo seu nome, tipo, restrições e parâmetros. """
    def __init__(
        self,
        nome: str,
        tipo_sql: TipoSQL,
        restricoes: List[RestricaoColuna] = None,
        valor_padrao: Any = None
        ):
        """ Inicializa a coluna e valida a consistência dos parâmetros fornecidos. """

        self.nome = nome
        self.tipo_sql = tipo_sql
        self.restricoes = restricoes or []
        self.valor_padrao = valor_padrao

    def construir_sql_criar(self) -> Script_SQL:
        """
        Constrói o SQL para a definição desta coluna dentro de um comando CREATE TABLE.
        \nExemplo: "id INT PRIMARY KEY AUTO_INCREMENT".
        """
        partes_sql = [Script_SQL(FormatadorSQL.identificador(self.nome)), Script_SQL(str(self.tipo_sql))]

        for restricao in self.restricoes:
            if restricao is not None:
                if restricao == RestricaoColuna.Padrao:
                    partes_sql.append(restricao.formatar_sql(self.valor_padrao))  # Se for DEFAULT, usa o valor fornecido
                else:
                    partes_sql.append(restricao.formatar_sql())

        # Junta as partes com um espaço (ex: "nome VARCHAR(50) NOT NULL")
        return Script_SQL.juntar(partes_sql, separador=" ")

class Tabela:
    """ Representa uma tabela. Serve como a definição do esquema e cria os comandos SQL relacionados à tabela. """
    def __init__(
        self,
        nome: str,
        colunas: List[Coluna],
        chaves_estrangeiras: Optional[List[ChaveEstrangeira]] = None,
        chave_primaria: Optional[ChavePrimaria] = None,
    ):
        """Inicializa a tabela com seu nome, colunas e chaves estrangeiras."""
        self._nome = nome
        self._colunas: Dict[str, Coluna] = {}

        for coluna in colunas:
            if(coluna.nome in self._colunas):
                raise ValueError(f"Coluna '{coluna.nome}' já definida na tabela '{self._nome}'. Nomes de colunas devem ser únicos.")
            
            self._colunas[coluna.nome] = coluna

        self.chaves_estrangeiras = chaves_estrangeiras or []
        self._chave_primaria = self._normalizar_chave_primaria(chave_primaria)
        self._validar_chave_primaria()

    @property
    def nome(self) -> str:
        return self._nome

    @property
    def colunas(self) -> List[Coluna]:
        return list(self._colunas.values())

    @property
    def chave_primaria(self) -> List[str]:
        if not self._chave_primaria:
            return []
        return self._chave_primaria.colunas

    @staticmethod
    def _normalizar_chave_primaria(chave_primaria: Optional[ChavePrimaria]) -> Optional[ChavePrimaria]:
        if chave_primaria is None:
            return None

        if not isinstance(chave_primaria, ChavePrimaria):
            raise TypeError("A chave primária deve ser uma instância de ChavePrimaria.")

        return chave_primaria

    def _validar_chave_primaria(self):
        if not self._chave_primaria:
            return

        for coluna in self._chave_primaria.colunas:
            if coluna not in self._colunas:
                raise ValueError(f"Coluna '{coluna}' não existe na tabela '{self._nome}' para a chave primária.")

        for coluna in self._colunas.values():
            if RestricaoColuna.Chave_Primaria in (coluna.restricoes or []):
                raise ValueError(
                    "Remova RestricaoColuna.Chave_Primaria das colunas quando utilizar uma chave primária composta definida na tabela."
                )

    def _construir_chave_primaria(self) -> Optional[Script_SQL]:
        if not self._chave_primaria:
            return None

        return self._chave_primaria.construir_sql()

    def construir_sql_criar(self) -> Script_SQL:
        """Cria o Script_SQL `CREATE TABLE` completo para esta tabela."""
        definicoes = []
        
        for coluna in self.colunas:
            definicoes.append(coluna.construir_sql_criar())

        for chave in self.chaves_estrangeiras:
            definicoes.append(chave.construir_sql_criar())

        chave_primaria = self._construir_chave_primaria()
        if chave_primaria:
            definicoes.append(chave_primaria)

        corpo_tabela = Script_SQL.juntar(definicoes, separador=",\n    ")
        
        # Protege o nome da tabela com backticks quando necessário.
        script_inicio = Script_SQL(f"CREATE TABLE {FormatadorSQL.identificador(self._nome)} (\n    ")
        script_fim = Script_SQL("\n)")

        return script_inicio + corpo_tabela + script_fim

    def preparar_conjunto_insercao(self, dados: List[Dict[str, Any]]) -> 'Conjunto_De_Dados_Para_Inserir':
        """ Cria um Conjunto_De_Dados_Para_Inserir para inserção em massa de dados puros (sem ExpressaoSQL). """
        if not dados:
            raise ValueError("A lista de dados para inserção em conjunto não pode estar vazia.")
            
        colunas_ordenadas = list(dados[0].keys())
        
        dados_em_listas = []

        for registro in dados:
            linha = []
            for coluna in colunas_ordenadas:
                valor = registro.get(coluna)
                if isinstance(valor, ExpressaoSQL):
                    raise ValueError(
                        f"ExpressaoSQL não é suportada em inserções em conjunto (preparar_conjunto_insercao). "
                        f"Use 'preparar_insert_simples' para o registro com a coluna '{coluna}'."
                    )
                linha.append(valor)
            dados_em_listas.append(linha)
            
        return Conjunto_De_Dados_Para_Inserir(
            tabela_alvo=self.nome,
            colunas=colunas_ordenadas,
            dados=dados_em_listas
        )

    def preparar_insert_simples(self, dado: Dict[str, Any]) -> Script_SQL:
        """ Cria um Script_SQL para uma única inserção, suportando ExpressaoSQL. """
        if not dado:
            raise ValueError("O dicionário de dados para inserção simples não pode estar vazio.")

        colunas: List[str] = []
        valores_sql: List[str] = []
        parametros: List[Any] = []

        for col, valor in dado.items():
            colunas.append(f"{FormatadorSQL.identificador(col)}")
            
            if isinstance(valor, ExpressaoSQL):
                valores_sql.append(str(valor)) # Injeta a expressão diretamente
            else:
                valores_sql.append("%s") # Usa um placeholder
                parametros.append(valor)
        
        nomes_colunas_str = ", ".join(colunas)
        valores_str = ", ".join(valores_sql)

        sql = f"INSERT INTO {FormatadorSQL.identificador(self.nome)} ({nomes_colunas_str}) VALUES ({valores_str})"

        return Script_SQL(sql, parametros)

class BaseDeDados:
    """ Representa uma Base de dados, com a lista das tabelas um esquema para criar o sql """
    def __init__(self, nome: str):
        self.nome = nome
        self._tabelas: Dict[str, Tabela] = {}
        self._verificador_seguranca = VerificadorDeSeguranca()

    def adicionar_tabela(self, tabela: Tabela):
        """ Adiciona uma definição de Tabela ao esquema da base de dados. """
        if tabela.nome in self._tabelas:
            raise ValueError(f"A tabela '{tabela.nome}' já foi adicionada á base de dados '{self.nome}'. Nomes de tabelas devem ser únicos.")
        
        self._tabelas[tabela.nome] = tabela
        print(f"Tabela '{tabela.nome}' adicionada à definição da base de dados '{self.nome}'.")

    def construir_sql_criar_tabelas(self) -> str:
        """
        Cria o script SQL para criar todas as tabelas do esquema.
        \nAs tabelas são ordenadas para respeitar as dependências de chaves estrangeiras, prevenindo erros de criação.
        """
        # Ordena as tabelas para criar primeiro aquelas com menos (ou nenhuma) chave estrangeira
        nomes_ordenados = sorted(
            self._tabelas.keys(),
            key=lambda nome_tabela: len(self._tabelas[nome_tabela].chaves_estrangeiras)
        )
        
        sql_tabelas = []
        for nome in nomes_ordenados:
            # cada item retornado por construir_sql_criar() é um Script_SQL
            sql_tabelas.append(self._tabelas[nome].construir_sql_criar())

        # Convertemos para strings antes de juntar. Cada CREATE TABLE deve terminar com
        # ponto-e-vírgula para permitir execução independente por parte do executor.
        script_final = ";\n\n".join(s.sql for s in sql_tabelas) + ";"
        self._verificador_seguranca.validar(Script_SQL(script_final))  # Valida o script completo antes de retornar

        return script_final

# Cláusulas SQL para consultas e comandos

class ClausulaBase(ABC):
    """
    Classe base abstrata para todos os componentes que representam uma cláusula SQL.
    Define um contrato comum para a geração de Script_SQL e para verificação de existência.
    """
    @abstractmethod
    def gerar_script(self) -> Script_SQL:
        """
        Gera e retorna o objeto Script_SQL correspondente a esta cláusula.
        Se a cláusula não tiver conteúdo para gerar (ex: nenhuma condição WHERE),
        deve retornar um objeto Script_SQL vazio.
        """
        pass

    @abstractmethod
    def __bool__(self) -> bool:
        """
        Retorna True se a cláusula contém dados para gerar SQL, False caso contrário.
        Isto é usado para verificações de lógica (ex: if clausula_where:).
        """
        pass

class ClausulaWhere(ClausulaBase):
    """Gere e monta uma cláusula WHERE completa a partir de várias condições."""
    
    def __init__(self):
        self._condicoes: List[Condicao] = []

    def adicionar(self, coluna: str, operador: OperadorComparacao, valor: Any, operador_logico: OperadorLogico = OperadorLogico.E):
        """Adiciona uma nova condição à cláusula usando o método fábrica 'Condicao.criar'."""
        condicao = Condicao.criar(coluna, operador, valor, operador_logico)
        self._condicoes.append(condicao)

    def gerar_script(self) -> Script_SQL:
        """
        Monta a cláusula WHERE completa, unindo as condições com a lógica correta.
        Retorna um Script_SQL pronto para ser usado.
        """
        if not self:  # Usa o __bool__ para verificar se há condições
            return Script_SQL()

        scripts_condicionais: List[Script_SQL] = []

        # Primeira condição sem operador lógico à frente
        primeiro = True
        for cond in self._condicoes:
            if primeiro:
                scripts_condicionais.append(cond.gerar_script())
                primeiro = False
            else:
                operador = cond.logica.value if cond.logica else OperadorLogico.E.value
                scripts_condicionais.append(Script_SQL(operador))
                scripts_condicionais.append(cond.gerar_script())

        # Junta todas as partes com um espaço e adiciona o "WHERE" no início
        script_corpo_where = Script_SQL.juntar(scripts_condicionais, separador=" ")
        return Script_SQL("WHERE ") + script_corpo_where

    def __bool__(self) -> bool:
        """Retorna True se houver pelo menos uma condição adicionada."""
        return bool(self._condicoes)

class ClausulaJoin(ClausulaBase):
    """Gere e monta uma ou mais cláusulas JOIN."""
    def __init__(self):
        self._scripts_join: List[Script_SQL] = []

    def adicionar(self, tabela_base: 'Tabela', outra_tabela: 'Tabela', tipo: TipoJunta):
        """Adiciona uma cláusula JOIN, inferindo a condição ON a partir das chaves estrangeiras."""
        clausulas_on_str = self._encontrar_clausulas_on(tabela_base, outra_tabela)
        clausulas_on_str.extend(self._encontrar_clausulas_on(outra_tabela, tabela_base))

        if not clausulas_on_str:
            raise ValueError(f"Não foi possível encontrar uma relação de chave estrangeira entre '{tabela_base.nome}' e '{outra_tabela.nome}'.")

        # Constrói o JOIN sem parâmetros, escapando identificadores quando necessário
        clausula_on_final = " AND ".join(clausulas_on_str)
        script_join = Script_SQL(f"{tipo.value} {FormatadorSQL.identificador(outra_tabela.nome)} ON {clausula_on_final}")
        self._scripts_join.append(script_join)

    def _encontrar_clausulas_on(self, tabela_origem: 'Tabela', tabela_destino: 'Tabela') -> List[str]:
        """Lógica privada para encontrar condições ON baseadas em Foreign Keys."""
        clausulas = []
        for chave in tabela_origem.chaves_estrangeiras:
            if chave.tabela_referenciada == tabela_destino.nome:
                for coluna_local, coluna_referenciada in zip(chave.colunas_locais, chave.colunas_referenciadas):
                    clausula = (
                        f"{FormatadorSQL.identificador(tabela_origem.nome)}.{FormatadorSQL.identificador(coluna_local)} = "
                        f"{FormatadorSQL.identificador(tabela_destino.nome)}.{FormatadorSQL.identificador(coluna_referenciada)}"
                    )
                    clausulas.append(clausula)
        return clausulas

    def gerar_script(self) -> Script_SQL:
        """Junta todos os scripts de JOIN num só, separados por espaço."""
        return Script_SQL.juntar(self._scripts_join, separador=" ")
    
    def __bool__(self) -> bool:
        """Retorna True se houver pelo menos um JOIN adicionado."""
        return bool(self._scripts_join)

class ClausulaOrderBy(ClausulaBase):
    """Gere e monta a cláusula ORDER BY."""
    def __init__(self):
        self._clausulas: List[str] = []

    def adicionar(self, coluna: str, direcao: DirecaoOrdenacao):
        """Adiciona uma coluna e direção à ordenação."""
        self._clausulas.append(f"{coluna} {direcao.value}")

    def gerar_script(self) -> Script_SQL:
        """Gera o script da cláusula ORDER BY. Não contém parâmetros."""
        if not self:
            return Script_SQL()
        
        corpo_order_by = ", ".join(self._clausulas)
        return Script_SQL(f"ORDER BY {corpo_order_by}")
    
    def __bool__(self) -> bool:
        """Retorna True se houver pelo menos uma regra de ordenação."""
        return bool(self._clausulas)

class ClausulaLimit(ClausulaBase):
    """Gere e monta a cláusula LIMIT."""
    def __init__(self):
        self._limite: int = None

    def definir(self, quantidade: int):
        """Define o número máximo de registos a retornar."""
        if not isinstance(quantidade, int) or quantidade <= 0:
            raise ValueError("O valor de LIMIT deve ser um inteiro positivo.")
        self._limite = quantidade

    def gerar_script(self) -> Script_SQL:
        """Gera o script da cláusula LIMIT, usando um parâmetro para segurança."""
        if not self:
            return Script_SQL()
        
        return Script_SQL("LIMIT %s", [self._limite])
    
    def __bool__(self) -> bool:
        """Retorna True se um limite foi definido."""
        return self._limite is not None

class ClausulaSet(ClausulaBase):
    """
    Gere e monta a cláusula SET para um comando UPDATE, garantindo que os valores
    sejam parametrizados de forma segura.
    """
    def __init__(self):
        """Inicializa o gestor da cláusula SET."""
        self._definicoes: Dict[str, Any] = {}

    def adicionar(self, coluna: str, valor: Any):
        """
        Adiciona um par coluna/valor que será usado para construir a cláusula SET.
        Se a mesma coluna for adicionada várias vezes, a última prevalece.

        Args:
            coluna (str): O nome da coluna a ser atualizada.
            valor (Any): O novo valor para a coluna.
        """
        self._definicoes[coluna] = valor

    def gerar_script(self) -> Script_SQL:
        """
        Constrói e retorna o Script_SQL para a cláusula SET completa.
        Exemplo de saída: Script_SQL(sql="SET nome = %s, ativo = %s", params=["Novo Nome", True])

        Returns:
            Script_SQL: Um objeto Script_SQL com o comando e os parâmetros,
                        ou um Script_SQL vazio se não houver nada a definir.
        """
        if not self:  # Utiliza o __bool__ para verificar se há definições
            return Script_SQL()

        # Cria uma lista de "coluna = %s" para cada item nas definições
        partes_set = [f"{coluna} = %s" for coluna in self._definicoes.keys()]
        
        # Extrai os valores na mesma ordem que as colunas
        # (garantido em Python 3.7+)
        parametros = list(self._definicoes.values())

        # Junta as partes com vírgula e adiciona "SET" no início
        corpo_set = ", ".join(partes_set)
        script_set = Script_SQL(f"SET {corpo_set}", parametros)
        
        return script_set

    def __bool__(self) -> bool:
        """
        Retorna True se houver pelo menos um valor definido para a cláusula SET,
        False caso contrário.
        """
        return bool(self._definicoes)

# Construtores de SQL para as 3 operações principais: SELECT, UPDATE, DELETE

class ConstrutorBase(ABC):
    """
    Classe base abstrata para construtores de queries (SELECT, UPDATE, DELETE).
    Centraliza a gestão da cláusula WHERE através de delegação.
    """
    def __init__(self, tabela: 'Tabela'):
        self._tabela = tabela
        self._clausula_where = ClausulaWhere() # Delega a responsabilidade para a classe especialista

    def onde(self, coluna: str, operador: OperadorComparacao, valor: Any, logica: OperadorLogico = OperadorLogico.E) -> 'ConstrutorBase':
        """
        Adiciona uma condição à cláusula WHERE.
        Este método agora simplesmente delega a chamada para a ClausulaWhere.
        """
        self._clausula_where.adicionar(coluna, operador, valor, logica)
        return self  # Retorna self para permitir encadeamento de métodos (fluent interface)

    def _gerar_script_where(self) -> Script_SQL:
        """
        Delega a geração do script da cláusula WHERE para o objeto especialista.
        O nome foi simplificado para refletir a ação.
        """
        return self._clausula_where.gerar_script()

    @abstractmethod
    def gerar_script(self) -> Script_SQL:
        """
        Método abstrato que as subclasses devem implementar para gerar
        o seu Script_SQL completo e final.
        """
        pass

class ConstrutorSelect(ConstrutorBase):
    """
    Constrói consultas SELECT de forma fluente, segura e parametrizada,
    utilizando a composição de objetos Script_SQL.
    """
    def __init__(self, tabela_principal: 'Tabela'):
        """Inicializa o construtor de consulta com a tabela principal."""
        super().__init__(tabela_principal)
        
        # Delega a gestão das cláusulas para objetos especialistas
        self._clausula_join = ClausulaJoin()
        self._clausula_order_by = ClausulaOrderBy()
        self._clausula_limit = ClausulaLimit()
        
        # Atributos específicos do SELECT
        self._colunas_selecionadas: List[str] = []
        self._distinto: bool = False

    def distinto(self) -> 'ConstrutorSelect':
        """Adiciona a cláusula DISTINCT à consulta."""
        self._distinto = True
        return self

    def juntar(self, outra_tabela: 'Tabela', tipo: TipoJunta = TipoJunta.Ambas) -> 'ConstrutorSelect':
        """Delega a adição de uma cláusula JOIN para o objeto especialista."""
        self._clausula_join.adicionar(self._tabela, outra_tabela, tipo)
        return self

    def selecionar(self, *nomes_colunas: str) -> 'ConstrutorSelect':
        """Define as colunas a serem retornadas. Se vazio, o padrão '*' será usado."""
        self._colunas_selecionadas.extend(nomes_colunas)
        return self

    def ordenar_por(self, coluna: str, direcao: DirecaoOrdenacao = DirecaoOrdenacao.Ascendente) -> 'ConstrutorSelect':
        """Delega a adição de uma cláusula ORDER BY para o objeto especialista."""
        self._clausula_order_by.adicionar(coluna, direcao)
        return self

    def limitar(self, quantidade: int) -> 'ConstrutorSelect':
        """Delega a definição da cláusula LIMIT para o objeto especialista."""
        self._clausula_limit.definir(quantidade)
        return self

    def gerar_script(self) -> Script_SQL:
        """Monta a consulta SELECT completa compondo os objetos Script_SQL de cada cláusula."""
        
        # Cláusula SELECT
        select_str = "SELECT"

        if self._distinto:
            select_str = "SELECT DISTINCT"

        if self._colunas_selecionadas:
            colunas_str = ", ".join([FormatadorSQL.identificador(c) for c in self._colunas_selecionadas])
        else:
            # Padrão melhorado: seleciona TUDO da tabela principal explicitamente
            colunas_str = f"{FormatadorSQL.identificador(self._tabela.nome)}.*"
            
        script_select = Script_SQL(f"{select_str} {colunas_str}")

        # Cláusula FROM
        script_from = Script_SQL(f"FROM {FormatadorSQL.identificador(self._tabela.nome)}")

        # Cada objeto cria o seu script
        script_join = self._clausula_join.gerar_script()
        script_where = self._gerar_script_where() # Método herdado do ConstrutorBase
        script_order_by = self._clausula_order_by.gerar_script()
        script_limit = self._clausula_limit.gerar_script()
    
        # A ordem da combinação é fundamental para um SQL válido.
        script_final = Script_SQL.juntar([
            script_select,
            script_from,
            script_join,
            script_where,
            script_order_by,
            script_limit
        ])

        return script_final

class ConstrutorUpdate(ConstrutorBase):
    """Constrói comandos UPDATE de forma segura, compondo objetos Script_SQL."""
    
    def __init__(self, tabela: 'Tabela'):
        """Inicializa o construtor de atualização com a tabela alvo."""
        super().__init__(tabela)
        self._clausula_set = ClausulaSet() # Delega a responsabilidade para a classe especialista

    def definir(self, coluna: str, valor: Any) -> 'ConstrutorUpdate':
        """ Delega a especificação de um par coluna=valor para a ClausulaSet. """
        self._clausula_set.adicionar(coluna, valor)
        return self

    def gerar_script(self) -> Script_SQL:
        """
        Cria o comando UPDATE completo compondo os Script_SQL das suas cláusulas.
        
        Raises:
            ValueError: Se nenhuma cláusula WHERE for definida, para evitar a atualização acidental de toda a tabela.
            ValueError: Se nenhum valor for definido para a cláusula SET.
        """
        # Validação de segurança: exige uma cláusula WHERE.
        if not self._clausula_where: # Usa a verificação booleana do objeto!
            raise ValueError("Operação UPDATE sem cláusula WHERE não é permitida por segurança.")

        # Validação de dados: exige pelo menos um valor a ser atualizado.
        if not self._clausula_set:
            raise ValueError("Nenhum valor definido para a atualização (use o método .definir()).")

        # 1. Cláusula UPDATE
        script_update = Script_SQL(f"UPDATE {FormatadorSQL.identificador(self._tabela.nome)}")

        # 2. Pede aos objetos especialistas para gerarem os seus scripts
        script_set = self._clausula_set.gerar_script()
        script_where = self._gerar_script_where() # Método herdado do ConstrutorBase

        # 3. Compõe tudo usando a sobrecarga do operador '+' de Script_SQL
        script_final = script_update + script_set + script_where
        
        return script_final

class ConstrutorDelete(ConstrutorBase):
    """
    Constrói comandos DELETE de forma segura, prevenindo exclusões em massa acidentais
    através da composição de objetos Script_SQL.
    """
    def gerar_script(self) -> Script_SQL:
        """
        Cria o comando DELETE completo, exigindo uma cláusula WHERE para segurança.
        
        Raises:
            ValueError: Se nenhuma condição WHERE for definida, para evitar a exclusão
                        acidental de todos os dados da tabela.
        """
        # Validação de segurança: exige uma cláusula WHERE.
        if not self._clausula_where: # Verificação idiomática usando o objeto especialista
            raise ValueError("Operação DELETE sem cláusula WHERE não é permitida por segurança.")

        # 1. Cláusula DELETE FROM
        script_delete = Script_SQL(f"DELETE FROM {FormatadorSQL.identificador(self._tabela.nome)}")

        # 2. Pede à ClausulaWhere para gerar o seu script
        script_where = self._gerar_script_where() # Método herdado do ConstrutorBase

        # 3. Compõe os dois scripts. A mágica da junção de parâmetros acontece aqui.
        script_final = script_delete + script_where
        
        return script_final


# Gerenciador de Conexão e Execução SQL

class ExecutorSQL:
    """
    Gerencia a conexão e a execução de comandos na base de dados.

    Usa o padrão de gerenciador de contexto para garantir que a conexão seja aberta e fechada corretamente, e que as transações sejam tratadas automaticamente (commit/rollback).
    """
    def __init__(self, host: str, user: str, password: str, port: int = 3306):
        """Inicializa o executor com os parâmetros de conexão."""
        self._config_bd = {
            "host": host,
            "user": user,
            "password": password,
            "port": port
        }
        self._conexao = None

    def __enter__(self):
        """
        Abre a conexão com a base de dados ao entrar no bloco 'with'.
        Retorna a própria instância do executor.
        """
        self._conexao = mysql.connector.connect(**self._config_bd)
        return self

    def __exit__(self, tipo_excecao, valor_excecao, traceback): # <--- CORRIGIDO
        """
        Fecha a conexão ao sair do bloco 'with'.
        Realiza commit em caso de sucesso ou rollback em caso de erro.
        """
        try:
            if self._conexao and self._conexao.is_connected():
                if tipo_excecao:
                    print(f"\n[AVISO] Ocorreu um erro. A executar um rollback: {valor_excecao}")
                    self._conexao.rollback()
                else:
                    self._conexao.commit()
        finally:
            if self._conexao and self._conexao.is_connected():
                self._conexao.close()
        
        # Retornar False (ou não retornar nada) garante que a exceção seja propagada.
        return False

    def preparar_base_limpa(self, nome_base: str):
        """ Executa os comandos DROP, CREATE e define a base de dados para a conexão. """
        if not self._conexao:
            raise RuntimeError("A conexão com a base de dados não está ativa. Use dentro de um bloco 'with'.")
            
        print(f"A limpar e recriar a base de dados '{nome_base}'...")
        # Estes comandos DDL têm commit implícito.
        with self._conexao.cursor() as cursor:
            cursor.execute(f"DROP DATABASE IF EXISTS `{nome_base}`")
            cursor.execute(f"CREATE DATABASE `{nome_base}`")
            # Garantir que a criação da base foi aplicada
            try:
                self._conexao.commit()
            except Exception:
                # Alguns drivers fazem commit implícito; não falhar se commit não for suportado
                pass

        # Define a base de dados padrão para todas as operações subsequentes na conexão.
        self._conexao.database = nome_base

    def executar_script(self, script):
        """
        Executa um Script_SQL ou uma string que pode conter múltiplos comandos (ex: CREATE TABLE),
        separados por ponto e vírgula.

        Aceita tanto um objeto Script_SQL quanto uma str. Se receber str, converte internamente
        em Script_SQL para manter uma API consistente com os outros métodos do Executor.
        """
        if not self._conexao:
            raise RuntimeError("A conexão com a base de dados não está ativa.")

        # Normaliza o input para um Script_SQL
        if isinstance(script, Script_SQL):
            script_obj = script
        elif isinstance(script, str):
            script_obj = Script_SQL(script)
        else:
            raise TypeError("O parâmetro 'script' deve ser um Script_SQL ou uma str contendo SQL.")

        # Executa todos os statements sequencialmente. Isso é mais portátil entre
        # diferentes drivers e evita erros quando o cursor não aceita parâmetros
        # extras como `multi=True`.
        with self._conexao.cursor() as cursor:
            # Divide por ';' e executa cada statement não vazio.
            statements = [s.strip() for s in script_obj.sql.split(";") if s.strip()]
            for stmt in statements:
                print(f"[EXECUTANDO STATEMENT] {stmt[:200]}", flush=True)
                try:
                    cursor.execute(stmt)
                except Exception as exc:
                    # Enriquecer a exceção com o statement que falhou para diagnóstico
                    print(f"[ERRO] Falha ao executar statement: {stmt[:200]}", flush=True)
                    raise
                # Tentativa defensiva de detectar se o comando retornou linhas.
                # Alguns cursores/implementações expõem `with_rows` no resultado, outros
                # no próprio cursor; aqui tentamos de forma simples e não crítica.
                has_rows = getattr(cursor, 'with_rows', False)
                if has_rows:
                    try:
                        statement_preview = (getattr(cursor, 'statement', stmt) or stmt)[:50]
                    except Exception:
                        statement_preview = stmt[:50]
                    print(f"Comando '{statement_preview}...' executado e retornou linhas.")
            # Commit explícito após execução dos statements (pode ser redundante para DDL)
            try:
                self._conexao.commit()
            except Exception:
                pass

    def modificar(self, script: Script_SQL) -> int:
        """
        Executa um único comando de modificação (INSERT, UPDATE, DELETE) a partir de um Script_SQL.
        Retorna o número de linhas afetadas.
        """
        if not self._conexao:
            raise RuntimeError("A conexão com a base de dados não está ativa.")

        with self._conexao.cursor() as cursor:
            cursor.execute(script.sql, script.params)
            return cursor.rowcount

    def inserir_conjunto(self, conjunto: 'Conjunto_De_Dados_Para_Inserir') -> int:
        """ Executa a inserção de um Conjunto_De_Dados_Para_Inserir usando executemany. """
        if not self._conexao:
            raise RuntimeError("A conexão com a base de dados não está ativa.")
            
        script_SQL = conjunto.preparar_para_executor()
        
        with self._conexao.cursor() as cursor:
            print(f"[EXECUTANDO executemany] {script_SQL.sql[:200]}", flush=True)
            try:
                cursor.executemany(script_SQL.sql, script_SQL.params)
            except Exception:
                raise ValueError(f"[ERRO] executemany falhou para template: {script_SQL.sql[:200]}")
            # Commit explícito para garantir que as inserções fiquem visíveis
            try:
                self._conexao.commit()
            except Exception:
                pass
            return cursor.rowcount

    def consultar(self, script: Script_SQL) -> List[Dict[str, Any]]:
        """
        Executa uma consulta (SELECT) e retorna os resultados como uma lista de dicionários.
        """
        if not self._conexao:
            raise RuntimeError("A conexão com a base de dados não está ativa.")

        with self._conexao.cursor(dictionary=True) as cursor:
            cursor.execute(script.sql, script.params)
            return cursor.fetchall()
            
    def consultar_um(self, script: Script_SQL) -> Dict[str, Any] | None:
        """
        Executa uma consulta (SELECT) e retorna apenas o primeiro resultado como um dicionário,
        ou None se não houver resultados.
        """
        if not self._conexao:
            raise RuntimeError("A conexão com a base de dados não está ativa.")
            
        with self._conexao.cursor(dictionary=True) as cursor:
            cursor.execute(script.sql, script.params)
            return cursor.fetchone()

class TesteSQL:
    """
    Classe de orquestração para executar um teste de integração completo da biblioteca de construção e execução de SQL.
    """
    def __init__(self, host: str, user: str, password: str, port: int = 3306, bd_nome_teste: str = "TesteBD_Final"):
        self.host = host
        self.user = user
        self.password = password
        self.port = port
        self.BD_Nome_Teste = bd_nome_teste

    def exibir_resultados(self, titulo: str, script: Script_SQL, resultados: List[Dict]):
        """Exibe os resultados de uma consulta de forma formatada a partir de um Script_SQL."""
        print("\n" + "=" * 80, flush=True)
        print(f"RESULTADO DO TESTE: {titulo}", flush=True)
        print("=" * 80, flush=True)

        # Normaliza o script para um objeto Script_SQL, se necessário
        if isinstance(script, Script_SQL):
            script_obj = script
        else:
            script_obj = Script_SQL(str(script))

        print("\n[SQL Gerado]", flush=True)
        print(script_obj.sql.strip(), flush=True)

        if script_obj.params:
            print("\n[Parâmetros]", flush=True)
            print(script_obj.params, flush=True)

        print("\n[Resultado da Consulta]", flush=True)
        if not resultados:
            print(" -> Nenhum resultado encontrado.", flush=True)
            print("=" * 80 + "\n", flush=True)
            return

        # Extrai os nomes das colunas do primeiro dicionário
        nomes_colunas = list(resultados[0].keys())

        # Calcula a largura máxima de cada coluna para formatação
        larguras = {nome: len(nome) for nome in nomes_colunas}
        for linha in resultados:
            for nome, valor in linha.items():
                larguras[nome] = max(larguras[nome], len(str(valor)))

        # Imprime o cabeçalho
        cabecalho = " | ".join(nome.ljust(larguras[nome]) for nome in nomes_colunas)
        separador = "-+-".join("-" * larguras[nome] for nome in nomes_colunas)

        print(cabecalho, flush=True)
        print(separador, flush=True)

        # Imprime cada linha de dados
        for linha in resultados:
            linha_formatada = " | ".join(str(linha.get(nome, "")).ljust(larguras[nome]) for nome in nomes_colunas)
            print(linha_formatada, flush=True)

        print("=" * 80 + "\n", flush=True)

    def executar_testes(self):
        """Executa um conjunto completo de testes: cria, insere, atualiza, deleta e consulta."""
        print("--- INÍCIO DOS TESTES DE INTEGRAÇÃO ---")

        # 1. Definição do Esquema (DDL)
        print("\n[PASSO 1/5] A definir o esquema da base de dados...")
        bd_teste = BaseDeDados(self.BD_Nome_Teste)
        tabela_clientes = Tabela(
            "clientes",
            [
                Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
                Coluna("nome", TipoSQL.varchar(tamanho=50), [RestricaoColuna.Nao_Nulo]),
                Coluna("email", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo, RestricaoColuna.Unico])
            ],
            chave_primaria=ChavePrimaria.Simples("id")
        )

        tabela_pedidos = Tabela(
            "pedidos",
            [
                Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
                Coluna("cliente_id", TipoSQL.inteiro(), [RestricaoColuna.Nao_Nulo]),
                Coluna("data_pedido", TipoSQL.timestamp(), [RestricaoColuna.Nao_Nulo, RestricaoColuna.Padrao], valor_padrao=ExpressaoSQL("CURRENT_TIMESTAMP")),
                Coluna("valor_total", TipoSQL.decimal(precisao=10, escala=2), [RestricaoColuna.Nao_Nulo])
            ],
            chaves_estrangeiras=[ChaveEstrangeira.Simples("cliente_id", "clientes", "id")],
            chave_primaria=ChavePrimaria.Simples("id")
        )
        # Adiciona as tabelas ao objeto da base para construir corretamente o DDL
        bd_teste.adicionar_tabela(tabela_clientes)
        bd_teste.adicionar_tabela(tabela_pedidos)
        # (O código de definição do esquema que você já tem está perfeito)

        try:
            with ExecutorSQL(self.host, self.user, self.password, self.port) as executor:
                # 2. Preparação do Ambiente e Criação das Tabelas
                print("\n[PASSO 2/5] A preparar o ambiente da base de dados...")
                executor.preparar_base_limpa(bd_teste.nome)
                
                # Assumindo que BaseDeDados tem um método para gerar o script de criação completo
                script_criar = bd_teste.construir_sql_criar_tabelas() 
                executor.executar_script(str(script_criar))
                print(" -> Base de dados e tabelas criadas com sucesso.")

                # 3. Inserção de Dados (DML - INSERT)
                print("\n[PASSO 3/5] A inserir dados de teste...")
                
                # 3.1 - Inserção em Conjunto (via rápida e segura)
                print(" -> Testando inserção em conjunto...")
                dados_clientes = [
                    {"nome": "Ana Guedes", "email": "ana.guedes@email.com"},
                    {"nome": "Rui Matos", "email": "rui.matos@email.com"},
                    {"nome": "Sofia Lima", "email": "sofia.lima@email.com"}
                ]
                conjunto_cli = tabela_clientes.preparar_conjunto_insercao(dados_clientes)
                num_inseridos = executor.inserir_conjunto(conjunto_cli)
                print(f"    -> {num_inseridos} registos inseridos em 'clientes'.")

                # 3.2 - Inserção Simples (via flexível com ExpressaoSQL)
                print(" -> Testando inserção simples com ExpressaoSQL...")
                dado_pedido_flexivel = {
                    "cliente_id": 1, 
                    "valor_total": 99.90,
                    "data_pedido": ExpressaoSQL("CURRENT_TIMESTAMP")
                }
                script_insert_simples = tabela_pedidos.preparar_insert_simples(dado_pedido_flexivel)
                num_inseridos = executor.modificar(script_insert_simples)
                print(f"    -> {num_inseridos} registo inserido em 'pedidos' com data dinâmica.")
                
                # Inserindo o resto dos pedidos via conjunto
                dados_outros_pedidos = [
                    {"cliente_id": 2, "valor_total": 45.00},
                    {"cliente_id": 1, "valor_total": 88.00},
                    {"cliente_id": 3, "valor_total": 250.75}
                ]
                conjunto_ped = tabela_pedidos.preparar_conjunto_insercao(dados_outros_pedidos)
                num_inseridos = executor.inserir_conjunto(conjunto_ped)
                print(f"    -> {num_inseridos} registos adicionais inseridos em 'pedidos'.")


                # 4. Modificação de Dados (DML - UPDATE e DELETE)
                print("\n[PASSO 4/5] A modificar dados...")
                
                # UPDATE
                script_update = ConstrutorUpdate(tabela_clientes).definir("email", "rui.matos.novo@email.com").onde("id", OperadorComparacao.Igual, 2).gerar_script()
                linhas_afetadas = executor.modificar(script_update)
                print(f" -> A atualizar email do cliente 2: {linhas_afetadas} linha(s) afetada(s).")
                
                # DELETE
                # Usar o membro correto do Enum (Menor_Que)
                script_delete = ConstrutorDelete(tabela_pedidos).onde("valor_total", OperadorComparacao.Menor_Que, 50).gerar_script()
                linhas_afetadas = executor.modificar(script_delete)
                print(f" -> A excluir pedidos com valor < 50: {linhas_afetadas} linha(s) afetada(s).")

                # 5. Consulta de Dados (DML - SELECT)
                print("\n[PASSO 5/5] A consultar os dados finais...")
                script_select = (
                    ConstrutorSelect(tabela_clientes)
                    .juntar(tabela_pedidos)
                    .selecionar("clientes.nome", "pedidos.valor_total", "pedidos.data_pedido")
                    .ordenar_por("clientes.nome")
                ).gerar_script()
                
                resultados_finais = executor.consultar(script_select)
                self.exibir_resultados("Consulta Final: Clientes e Pedidos", script_select, resultados_finais)

        except (mysql.connector.Error, ValueError, RuntimeError) as erro:
            print(f"\n[ERRO FATAL] A operação foi interrompida: {erro}")
        
        finally:
            print("\n--- FIM DOS TESTES DE INTEGRAÇÃO ---")

    def gerar_sql_esquema(self) -> str:
        """Gera e retorna o SQL completo para criação do esquema de teste sem tocar no BD.

        Útil para inspeção/printing em modo seguro (--print-sql).
        """
        bd_teste = BaseDeDados(self.BD_Nome_Teste)
        tabela_clientes = Tabela(
            "clientes",
            [
                Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
                Coluna("nome", TipoSQL.varchar(tamanho=50), [RestricaoColuna.Nao_Nulo]),
                Coluna("email", TipoSQL.varchar(tamanho=255), [RestricaoColuna.Nao_Nulo, RestricaoColuna.Unico])
            ],
            chave_primaria=ChavePrimaria.Simples("id")
        )

        tabela_pedidos = Tabela(
            "pedidos",
            [
                Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
                Coluna("cliente_id", TipoSQL.inteiro(), [RestricaoColuna.Nao_Nulo]),
                Coluna("data_pedido", TipoSQL.timestamp(), [RestricaoColuna.Nao_Nulo, RestricaoColuna.Padrao], valor_padrao=ExpressaoSQL("CURRENT_TIMESTAMP")),
                Coluna("valor_total", TipoSQL.decimal(precisao=10, escala=2), [RestricaoColuna.Nao_Nulo])
            ],
            chaves_estrangeiras=[ChaveEstrangeira.Simples("cliente_id", "clientes", "id")],
            chave_primaria=ChavePrimaria.Simples("id")
        )

        bd_teste.adicionar_tabela(tabela_clientes)
        bd_teste.adicionar_tabela(tabela_pedidos)

        return bd_teste.construir_sql_criar_tabelas()

def gerarEsquema():
    bd = BaseDeDados("PSI_JOSE")
    tabela_alunos = Tabela(
        "alunos",
        [
            Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
            Coluna("nome", TipoSQL.varchar(tamanho=30), [RestricaoColuna.Nao_Nulo]),
            Coluna("Morada", TipoSQL.varchar(tamanho=50)),
            Coluna("Localidade", TipoSQL.varchar(tamanho=30)),
            Coluna("data_nascimento", TipoSQL.timestamp())
        ],
        chave_primaria=ChavePrimaria.Simples("id")
    )
    tabela_Diciplinas = Tabela(
        "Diciplinas",
        [
            Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
            Coluna("Cod_Disc", TipoSQL.varchar(tamanho=5), [RestricaoColuna.Nao_Nulo]),
            Coluna("Descricao", TipoSQL.varchar(tamanho=50))
        ],
        chave_primaria=ChavePrimaria.Simples("id")
    )
    tablela_inscricoes = Tabela(
        "Inscricoes",
        [
            Coluna("id", TipoSQL.inteiro(), [RestricaoColuna.AutoIncremento]),
            Coluna("Aluno_id", TipoSQL.inteiro(), [RestricaoColuna.Nao_Nulo]),
            Coluna("Diciplina_id", TipoSQL.inteiro(), [RestricaoColuna.Nao_Nulo]),
            Coluna("data_inscricao", TipoSQL.timestamp(), [RestricaoColuna.Nao_Nulo])
        ],
        chave_primaria=ChavePrimaria.Simples("id"),
        chaves_estrangeiras=[
            ChaveEstrangeira.Simples("Aluno_id", "alunos", "id"),
            ChaveEstrangeira.Simples("Diciplina_id", "Diciplinas", "id")
        ]
    )
    bd.adicionar_tabela(tabela_alunos)
    bd.adicionar_tabela(tabela_Diciplinas)
    bd.adicionar_tabela(tablela_inscricoes)
    sql = bd.construir_sql_criar_tabelas()
    print(sql)

if __name__ == "__main__":
    gerarEsquema()
    """
    # Ponto de entrada do script.
    # Configure com os dados de acesso ao seu servidor MySQL.
    testes = TesteSQL(
        host="localhost",
        user="root",
        password="",
        port=3306
    )
    # Modo seguro: apenas imprimir o SQL do esquema sem aceder ao MySQL
    if '--print-sql' in sys.argv or '--dry-run' in sys.argv:
        sql = testes.gerar_sql_esquema()
        print(sql)
    else:
        testes.executar_testes()

    """