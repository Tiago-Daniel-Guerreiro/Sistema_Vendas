import consola
from enums import Cores

class Interface:
    @staticmethod
    def mostrar_cabecalho(texto):
        consola.importante_destacado(f"\n{texto}")

    @staticmethod
    def ler_com_sugestoes(rede, label, acao_listar, permitir_vazio=False):
        # Procurar sugestões do servidor
        resposta = rede.enviar_comando(acao_listar)
        sugestoes = []
        
        if resposta is not None and resposta.get('ok') is True:
            sugestoes = resposta.get('resultado', [])
        
        if len(sugestoes) > 0:
            consola.info(f"\n{Cores.CIANO}Valores existentes de {label}:{Cores.NORMAL}")
            # Mostrar apenas os primeiros 10
            for i, sugestao in enumerate(sugestoes[:10], 1):
                consola.info(f"  {i}. {sugestao}")
            consola.aviso("\nDica: Digite o número para selecionar ou escreva um novo valor")
        
        if not permitir_vazio:
            prompt = f"\n{label}:"
        else:
            prompt = f"\n{label} (vazio para manter):"
        
        entrada = consola.ler_texto(prompt, obrigatorio=not permitir_vazio)
        
        # Se permitir vazio e entrada for vazia ou None, retorna None
        if permitir_vazio and (entrada is None or len(entrada) == 0):
            return None
        
        # Se entrada é None (cancelado), retorna None
        if entrada is None:
            return None
        
        # Se for número, tentar selecionar da lista
        if entrada.isdigit():
            indice = int(entrada) - 1
            if 0 <= indice < len(sugestoes):
                valor_selecionado = sugestoes[indice]
                consola.sucesso(f"Selecionado: {valor_selecionado}")
                return valor_selecionado
        
        # Caso contrário, retornar o valor digitado
        return entrada
    
    @staticmethod
    def mostrar_tabela(lista_dados, configuracao_colunas):
        if not lista_dados:
            consola.aviso("Nenhuma informação para mostrar.")
            return

        if isinstance(lista_dados, dict):
            lista_dados = list(lista_dados.values())

        titulos = []
        separadores = []

        for coluna in configuracao_colunas:
            separadores.append("-" * coluna['largura'])
            titulos.append(coluna['titulo'].ljust(coluna['largura']))

        consola.info(f"\n{Cores.NEGRITO}{' '.join(titulos)}{Cores.NORMAL}")
        consola.info(f"{Cores.CINZA}{' '.join(separadores)}{Cores.NORMAL}")

        for item in lista_dados:
            colunas_linha = []

            for coluna in configuracao_colunas:
                valor = item.get(coluna['chave'], "N/A")

                if isinstance(valor, float):
                    texto_valor = f"{valor:.2f}"
                else:
                    texto_valor = str(valor)

                colunas_linha.append(texto_valor.ljust(coluna['largura']))

            consola.info(" ".join(colunas_linha))

        print("")  # Linha em branco no final

    @staticmethod
    def exibir_menu(titulo, opcoes, texto_sair="Sair", funcao_sair=None):
        return consola.exibir_menu(titulo, opcoes, texto_sair, funcao_sair)