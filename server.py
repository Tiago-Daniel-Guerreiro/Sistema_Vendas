import json
import socketserver
import threading
import socket
import os
import time
from database import DatabaseManager
from entities import Admin, Vendedor, Cliente, Produto, User
from enums import Mensagem, Cores
from typing import Any, Dict
from comando import Comando
from comando import ComandosSistema

class ConfiguracaoServidor:
    HOST_PADRAO = '127.0.0.1'
    PORTA_PADRAO = 5000
    DEBUG:bool = False
    CHAVE_CRIACAO_ADMIN = "ESTA_SENHA_É_USADA_NA_CRIAÇÃO_DE_NOVOS_ADMIN_PROVAVELMENTE_SERÁ_REMOVIDA_DEPOIS__POIS_ESTA_SENHA_É_MUITO_GRANDE!_OK?"

class GerenciadorComandos:
    def __init__(self):
        self.comandos = {}
        self._registrar_comandos_padrao()


    def _registrar_comandos_padrao(self):
        self.registrar(Comando(
            nome='ping',
            acao=lambda *args, **kwargs: AcoesComandos.ping(),
            descricao='Retorna pong',
            permissao_minima=None,
            categoria='utilidades',
            mensagens_sucesso=[Mensagem.PONG, Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='help',
            acao=lambda utilizador_atual=None, *args, **kwargs: AcoesComandos.help(utilizador_atual),
            descricao='Lista todos os comandos disponíveis',
            permissao_minima=None,
            categoria='utilidades',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='autenticar',
            acao=lambda *args, **kwargs: AcoesComandos.autenticar(*args, **kwargs),
            descricao='Autentica o usuário e retorna o cargo',
            permissao_minima=None,
            categoria='minha conta',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='ping',
            acao=lambda *args, **kwargs: ComandosSistema.ping(),
            descricao='Retorna pong',
            permissao_minima=None,
            categoria='utilidades',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='help',
            acao=lambda *args, **kwargs: ComandosSistema.help(*args, **kwargs),
            descricao='Lista todos os comandos disponíveis',
            permissao_minima=None,
            categoria='utilidades',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='registrar',
            acao=lambda *args, **kwargs: ComandosSistema.registrar(*args, **kwargs),
            descricao='Registra um novo usuário',
            permissao_minima=None,
            categoria='minha conta',
            mensagens_sucesso=[Mensagem.UTILIZADOR_CRIADO]
        ))
        # ...existing code...
        self.registrar(Comando(
            nome='apagar_utilizador',
            acao=lambda *args, **kwargs: AcoesComandos.apagar_utilizador(*args, **kwargs),
            descricao='Remove o usuário logado',
            permissao_minima='cliente',
            categoria='minha conta',
            mensagens_sucesso=[Mensagem.REMOVIDO]
        ))
        self.registrar(Comando(
            nome='promover_para_admin',
            acao=lambda *args, **kwargs: AcoesComandos.promover_para_admin(*args, **kwargs),
            parametros={'chave': {'obrigatorio': True, 'tipo': str}},
            descricao='Promove o usuário para admin',
            permissao_minima='cliente',
            categoria='minha conta',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='criar_funcionario',
            acao=lambda *args, **kwargs: AcoesComandos.criar_funcionario(*args, **kwargs),
            parametros={'username_func': {'obrigatorio': True, 'tipo': str}, 'password_func': {'obrigatorio': True, 'tipo': str}, 'cargo': {'obrigatorio': True, 'tipo': str}, 'loja_id': {'obrigatorio': False, 'tipo': int}},
            descricao='Cria um novo funcionário',
            permissao_minima='admin',
            categoria='gestao',
            mensagens_sucesso=[Mensagem.UTILIZADOR_CRIADO]
        ))
        self.registrar(Comando(
            nome='listar_utilizadores',
            acao=lambda *args, **kwargs: AcoesComandos.listar_utilizadores(*args, **kwargs),
            descricao='Lista todos os utilizadores',
            permissao_minima='admin',
            categoria='gestao',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='list_products',
            acao=lambda *args, **kwargs: AcoesComandos.listar_produtos(*args, **kwargs),
            descricao='Lista produtos disponíveis',
            permissao_minima='cliente',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='realizar_venda',
            acao=lambda *args, **kwargs: AcoesComandos.realizar_venda(*args, **kwargs),
            parametros={'itens': {'obrigatorio': True, 'tipo': dict}},
            descricao='Realiza uma venda',
            permissao_minima='cliente',
            categoria='compras',
            mensagens_sucesso=[Mensagem.CONCLUIDA]
        ))
        self.registrar(Comando(
            nome='ver_meu_historico',
            acao=lambda *args, **kwargs: AcoesComandos.ver_meu_historico(*args, **kwargs),
            descricao='Exibe o histórico de compras',
            permissao_minima='cliente',
            categoria='compras',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='editar_produto',
            acao=lambda *args, **kwargs: AcoesComandos.editar_produto(*args, **kwargs),
            parametros={'product_id': {'obrigatorio': True, 'tipo': int}},
            descricao='Edita um produto',
            permissao_minima='vendedor',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.ATUALIZADO]
        ))
        self.registrar(Comando(
            nome='deletar_produto',
            acao=lambda *args, **kwargs: AcoesComandos.deletar_produto(*args, **kwargs),
            parametros={'product_id': {'obrigatorio': True, 'tipo': int}},
            descricao='Deleta um produto',
            permissao_minima='admin',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.REMOVIDO]
        ))
        self.registrar(Comando(
            nome='concluir_pedido',
            acao=lambda *args, **kwargs: AcoesComandos.concluir_pedido(*args, **kwargs),
            parametros={'order_id': {'obrigatorio': True, 'tipo': int}},
            descricao='Conclui um pedido',
            permissao_minima='vendedor',
            categoria='pedidos',
            mensagens_sucesso=[Mensagem.CONCLUIDA]
        ))
        self.registrar(Comando(
            nome='listar_pedidos',
            acao=lambda *args, **kwargs: AcoesComandos.listar_pedidos(*args, **kwargs),
            descricao='Lista pedidos do vendedor',
            permissao_minima='vendedor',
            categoria='pedidos',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='verificar_stock_baixo',
            acao=lambda *args, **kwargs: AcoesComandos.verificar_stock_baixo(*args, **kwargs),
            descricao='Verifica produtos com baixo estoque',
            permissao_minima='vendedor',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.ALERTA_STOCK_BAIXO]
        ))
        self.registrar(Comando(
            nome='deletar_pedido',
            acao=lambda *args, **kwargs: AcoesComandos.deletar_pedido(*args, **kwargs),
            parametros={'order_id': {'obrigatorio': True, 'tipo': int}},
            descricao='Deleta um pedido',
            permissao_minima='admin',
            categoria='pedidos',
            mensagens_sucesso=[Mensagem.REMOVIDO]
        ))
        self.registrar(Comando(
            nome='listar_lojas',
            acao=lambda *args, **kwargs: AcoesComandos.listar_lojas(*args, **kwargs),
            descricao='Lista todas as lojas',
            permissao_minima='cliente',
            categoria='lojas',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='criar_loja',
            acao=lambda *args, **kwargs: AcoesComandos.criar_loja(*args, **kwargs),
            parametros={'nome': {'obrigatorio': True, 'tipo': str}, 'localizacao': {'obrigatorio': True, 'tipo': str}},
            descricao='Cria uma nova loja',
            permissao_minima='admin',
            categoria='lojas',
            mensagens_sucesso=[Mensagem.ADICIONADO]
        ))
        self.registrar(Comando(
            nome='editar_loja',
            acao=lambda *args, **kwargs: AcoesComandos.editar_loja(*args, **kwargs),
            parametros={'store_id': {'obrigatorio': True, 'tipo': int}},
            descricao='Edita uma loja',
            permissao_minima='admin',
            categoria='lojas',
            mensagens_sucesso=[Mensagem.ATUALIZADO]
        ))
        self.registrar(Comando(
            nome='apagar_loja',
            acao=lambda *args, **kwargs: AcoesComandos.apagar_loja(*args, **kwargs),
            parametros={'store_id': {'obrigatorio': True, 'tipo': int}},
            descricao='Apaga uma loja',
            permissao_minima='admin',
            categoria='lojas',
            mensagens_sucesso=[Mensagem.REMOVIDO]
        ))
        self.registrar(Comando(
            nome='buscar_produto_por_nome',
            acao=lambda *args, **kwargs: AcoesComandos.buscar_produto_por_nome(*args, **kwargs),
            parametros={'nome_produto': {'obrigatorio': True, 'tipo': str}},
            descricao='Busca produto pelo nome',
            permissao_minima='cliente',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='listar_categorias',
            acao=lambda *args, **kwargs: AcoesComandos.listar_categorias(*args, **kwargs),
            descricao='Lista categorias de produtos',
            permissao_minima='cliente',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='listar_nomes_produtos',
            acao=lambda *args, **kwargs: AcoesComandos.listar_nomes_produtos(*args, **kwargs),
            descricao='Lista nomes dos produtos',
            permissao_minima='cliente',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))
        self.registrar(Comando(
            nome='listar_descricoes',
            acao=lambda *args, **kwargs: AcoesComandos.listar_descricoes(*args, **kwargs),
            descricao='Lista descrições dos produtos',
            permissao_minima='cliente',
            categoria='produtos',
            mensagens_sucesso=[Mensagem.SUCESSO]
        ))

    def registrar(self, comando):
        self.comandos[comando.nome] = comando

    def obter_comando(self, nome):
        return self.comandos.get(nome)

    def todos_comandos_json(self):
        return [cmd.to_json() for cmd in self.comandos.values()]

# Instância global
gerenciador_comandos = GerenciadorComandos()

class ProcessadorDeComandos:

    @staticmethod
    def obter_comandos_permitidos(utilizador):    
        # Centraliza comandos permitidos usando GerenciadorComandos
        if utilizador is None:
            cargo = None
        else:
            cargo = getattr(utilizador, 'cargo', None)

        comandos_permitidos = []
        for comando in gerenciador_comandos.comandos.values():
            if comando.validar_permissao(utilizador):
                comandos_permitidos.append(comando.nome)

        resposta: Dict[str, Any] = {
            'comandos_permitidos': comandos_permitidos,
            'cargo': cargo
        }
        return resposta
    
    @staticmethod
    def executar(base_de_dados, acao, parametros):
        from entities import Sessao
        # Obtém o utilizador atual via Sessao (token ou credenciais)
        utilizador_atual = Sessao.obter_utilizador(base_de_dados, parametros)
        Sessao.remover_expiradas(base_de_dados)
        # Busca o comando registrado
        comando = gerenciador_comandos.obter_comando(acao)
        if comando is None:
            return Mensagem.NAO_ENCONTRADO
        # Valida permissões
        if not comando.validar_permissao(utilizador_atual):
            return Mensagem.PERMISSAO_NEGADA
        # Valida parâmetros
        erros_param = comando.validar_parametros(parametros)
        if erros_param:
            return Mensagem.ERRO_PROCESSAMENTO
        # Executa ação do comando
        try:
            return comando.acao(utilizador_atual, parametros, base_de_dados=base_de_dados)
        except Exception as e:
            return Mensagem.ERRO_GENERICO

class AcoesComandos(object): # Definir como classe estática
    @staticmethod
    def ping():
        return 'pong'

    @staticmethod
    def autenticar(utilizador_atual):
        # Autentica o utilizador e retorna o cargo
        if utilizador_atual is None:
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        match utilizador_atual:
            case Admin():
                return {'cargo': 'admin'}
            case Vendedor():
                return {'cargo': 'vendedor'}
            case Cliente():
                return {'cargo': 'cliente'}
            
        return Mensagem.LOGIN_INVALIDO

    @staticmethod
    def help(utilizador_atual=None):
        # Agrupa comandos por categoria e permissão mínima, filtrando por permissões do utilizador
        comandos_agrupados = {}
        for comando_atual in gerenciador_comandos.comandos.values():
            if comando_atual.validar_permissao(utilizador_atual):
                categoria = comando_atual.categoria if comando_atual.categoria else 'outros'
                permissao = comando_atual.permissao_minima if comando_atual.permissao_minima else 'publico'
                if categoria not in comandos_agrupados:
                    comandos_agrupados[categoria] = {'publico': [], 'cliente': [], 'vendedor': [], 'admin': []}
                # Adiciona apenas se não existe comando com mesmo nome
                existe = False
                for comando_existente in comandos_agrupados[categoria][permissao]:
                    if comando_existente.get('nome') == comando_atual.nome:
                        existe = True
                        break
                if not existe:
                    comandos_agrupados[categoria][permissao].append(comando_atual.to_json())
        return {'comandos': comandos_agrupados}
    
    @staticmethod
    def editar_senha(utilizador_atual,parametros):
        if utilizador_atual is None:
            return Mensagem.LOGIN_INVALIDO
        
        nova_senha = parametros.get('nova_senha')
        return utilizador_atual.editar_senha(nova_senha)
    
    @staticmethod
    def editar_username(utilizador_atual, parametros):
        if utilizador_atual is None:
            return Mensagem.LOGIN_INVALIDO
        
        novo_username = parametros.get('novo_username')
        if novo_username is None:
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        resultado = utilizador_atual.editar_username(novo_username)
        return resultado
    
    @staticmethod
    def apagar_utilizador(utilizador_atual):
        if utilizador_atual is None:
            return Mensagem.LOGIN_INVALIDO
        
        # Só permite apagar se for Cliente (lógica de segurança)
        if isinstance(utilizador_atual, Cliente):
            return utilizador_atual.remover_seguranca()
        
        return Mensagem.ERRO_GENERICO

    @staticmethod
    def promover_para_admin(utilizador_atual, parametros):
        if utilizador_atual is None:
            return Mensagem.LOGIN_INVALIDO
        
        chave = parametros.get('chave')
        if not chave or chave != ConfiguracaoServidor.CHAVE_CRIACAO_ADMIN:
            return Mensagem.PERMISSAO_NEGADA
        
        return utilizador_atual.promover_a_admin()

    @staticmethod
    def criar_funcionario(base_de_dados, utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        user_func = parametros.get('username_func')
        pass_func = parametros.get('password_func')
        cargo = parametros.get('cargo')
        loja_id = parametros.get('loja_id')
        
        if user_func is None or pass_func is None or cargo is None:
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        if cargo == 'vendedor' and not loja_id:
            return Mensagem.O_VENDEDOR_TEM_QUE_SER_ASSOCIADO_A_LOJA
                        
        try:
            if cargo == 'admin':
                return Admin.registrar(base_de_dados, user_func, pass_func, store_id=None)
            elif cargo == 'vendedor':
                return Vendedor.registrar(base_de_dados, user_func, pass_func, loja_id)
            else:
                return Mensagem.CARGO_INVALIDO

        except Exception:
            base_de_dados.conn.rollback()
            return Mensagem.UTILIZADOR_JA_EXISTE
        
    @staticmethod
    def listar_utilizadores(utilizador_atual,parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        filtro_cargo = parametros.get('filtro_cargo')
        filtro_loja = parametros.get('filtro_loja')
        
        if filtro_loja is not None:
            try:
                filtro_loja = int(filtro_loja)
            except (ValueError, TypeError):
                filtro_loja = None
                
        return utilizador_atual.listar_utilizadores(filtro_cargo, filtro_loja)

    @staticmethod
    def listar_produtos(utilizador_atual, parametros):
        id_loja = parametros.get('store_id')
        if id_loja is not None:
            try:
                id_loja = int(id_loja)
            except (ValueError, TypeError):
                id_loja = None
        
        filtros = {}
        if 'categoria' in parametros:
            filtros['categoria'] = parametros['categoria']
        
        if 'preco_max' in parametros:
            try:
                filtros['preco_max'] = float(parametros['preco_max'])
            except (ValueError, TypeError):
                pass
        
        return AcoesComandos._listar_produtos_da_loja(utilizador_atual, id_loja, filtros)
    
    @staticmethod
    def buscar_produto_por_nome(base_de_dados, parametros):
        nome_produto = parametros.get('nome_produto')
        id_loja = parametros.get('store_id')
        if nome_produto is None:
            return Mensagem.NAO_ENCONTRADO
        return Produto.obter_id_pelo_nome_e_loja(base_de_dados, nome_produto, id_loja)

    @staticmethod
    def add_product(utilizador_atual,parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        try:
            nome = parametros.get('nome')
            categoria = parametros.get('categoria')
            descricao = parametros.get('descricao')
            preco = float(parametros.get('preco'))
            stock = int(parametros.get('stock'))
            loja = int(parametros.get('store_id'))
        except (ValueError, TypeError):
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        return utilizador_atual.adicionar_produto(nome, categoria, descricao, preco, stock, loja)
    
    @staticmethod
    def realizar_venda(utilizador_atual,parametros):
        if utilizador_atual is None:
            return Mensagem.LOGIN_INVALIDO
        
        itens = parametros.get('itens')
        if itens is None or not isinstance(itens, dict):
            return Mensagem.ERRO_PROCESSAMENTO
        
        try:
            itens_validados = {}
            for produto_id, quantidade in itens.items():
                produto_id = int(produto_id)
                quantidade = int(quantidade)
                if quantidade <= 0:
                    return Mensagem.CREDENCIAIS_INVALIDAS
                itens_validados[str(produto_id)] = quantidade
        except (ValueError, TypeError):
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        return utilizador_atual.realizar_venda(itens_validados)
    
    @staticmethod    
    def ver_meu_historico(utilizador_atual, parametros):
        if utilizador_atual is None:
            return Mensagem.LOGIN_INVALIDO
        return utilizador_atual.ver_meu_historico()
    
    @staticmethod
    def editar_produto(utilizador_atual, parametros):
        prod_id = parametros.get('product_id')
        if not prod_id:
            return Mensagem.NAO_ENCONTRADO
        
        # Parâmetros opcionais
        novos_dados = {
            'novo_preco': parametros.get('novo_preco'),
            'novo_stock': parametros.get('novo_stock'),
            'nova_descricao': parametros.get('nova_descricao'),
            'novo_nome': parametros.get('novo_nome'),
            'nova_categoria': parametros.get('nova_categoria')
        }
        
        if isinstance(utilizador_atual, Admin):
            novos_dados['novo_id_da_loja'] = parametros.get('novo_id_da_loja')
            return utilizador_atual.atualizar_produto(prod_id, **novos_dados)
        elif isinstance(utilizador_atual, Vendedor):
            return utilizador_atual.atualizar_produto(prod_id, **novos_dados)
        else:
            return Mensagem.ERRO_PERMISSAO
    
    @staticmethod
    def deletar_produto(base_de_dados, utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        prod_id = parametros.get('product_id')
        if not prod_id:
            return Mensagem.NAO_ENCONTRADO
        
        return Produto.remover_produto(base_de_dados, prod_id)

    @staticmethod
    def concluir_pedido(utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Vendedor) and not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        order_id = parametros.get('order_id')
        if not order_id:
            return Mensagem.ERRO_PROCESSAMENTO
        
        return utilizador_atual.concluir_pedido(order_id)
    
    @staticmethod
    def listar_pedidos(utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Vendedor):
            return Mensagem.PERMISSAO_NEGADA
        
        filtro = parametros.get('filtro_status')
        return utilizador_atual.listar_pedidos(filtro)
    
    @staticmethod
    def verificar_stock_baixo(base_de_dados, utilizador_atual):
        if not isinstance(utilizador_atual, Vendedor):
            return Mensagem.PERMISSAO_NEGADA
        return Vendedor.verificar_stock_baixo(base_de_dados)
    
    @staticmethod
    def deletar_pedido(utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        order_id = parametros.get('order_id')
        return utilizador_atual.deletar_pedido(order_id)

    @staticmethod
    def listar_lojas(utilizador_atual):
        if utilizador_atual is None:
                return Mensagem.LOGIN_INVALIDO
        return utilizador_atual.listar_lojas()

    @staticmethod
    def criar_loja(utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        nome = parametros.get('nome')
        local = parametros.get('localizacao')
        return utilizador_atual.criar_loja(nome, local)
    
    @staticmethod
    def editar_loja(utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        store_id = parametros.get('store_id')
        nome = parametros.get('novo_nome')
        local = parametros.get('nova_localizacao')
        
        if store_id is None:
            return Mensagem.NAO_ENCONTRADO
        
        try:
            store_id = int(store_id)
        except (ValueError, TypeError):
            return Mensagem.CREDENCIAIS_INVALIDAS
            
        return utilizador_atual.editar_loja(store_id, nome, local)
    
    @staticmethod
    def apagar_loja(utilizador_atual, parametros):
        if not isinstance(utilizador_atual, Admin):
            return Mensagem.PERMISSAO_NEGADA
        
        store_id = parametros.get('store_id')
        if store_id is None:
            return Mensagem.NAO_ENCONTRADO
        
        try:
            store_id = int(store_id)
        except (ValueError, TypeError):
            return Mensagem.CREDENCIAIS_INVALIDAS
        
        return utilizador_atual.apagar_loja(store_id)
    
    @staticmethod
    def listar_categorias(base_de_dados):
        return Produto.listar_categorias(base_de_dados)
    
    @staticmethod
    def listar_nomes_produtos(base_de_dados):
        return Produto.listar_nomes_produtos(base_de_dados)
    
    @staticmethod
    def listar_descricoes(base_de_dados):
        return Produto.listar_descricoes(base_de_dados)

    @staticmethod
    def _listar_produtos_da_loja(utilizador, id_loja, filtros):
        try:
            base_de_dados = DatabaseManager()
            if not base_de_dados.connect() and base_de_dados.conn is None:
                print('Erro ao conectar BD')
                return []
            
            # Se for vendedor e não especificou loja, usa a loja dele
            if id_loja is None and utilizador is not None:
                if isinstance(utilizador, Vendedor):
                    id_loja = utilizador.store_id

            produtos = Produto.listar_todos(base_de_dados, store_id=id_loja, filtros=filtros)
            
            if base_de_dados.conn is not None:
                base_de_dados.conn.close()
                
            return produtos
        except Exception as e:
            print(f'Erro ao listar produtos: {str(e)}')
            return []
        
class ManipuladorRequisicao(socketserver.StreamRequestHandler):    
    def _enviar_resposta_json(self, sucesso, resultado=None, erro=None):
        pacote_resposta = {'ok': sucesso}
        #o json converte a tupla em lista
        if resultado is not None:
            pacote_resposta['resultado'] = resultado
        
        if erro is not None:
            pacote_resposta['erro'] = erro
        
        try:
            mensagem_serializada = json.dumps(pacote_resposta, ensure_ascii=False, default=str) + '\n'
            self.wfile.write(mensagem_serializada.encode('utf-8'))
            self.wfile.flush()
        except Exception as e:
            print(f"Erro ao enviar resposta: {e}")

    def _ler_comando_json(self):
        try:
            linha_bytes = self.rfile.readline()
            if not linha_bytes:
                return None
            
            dados = json.loads(linha_bytes.decode('utf-8'))
            
            if not isinstance(dados, dict):
                return None
            
            if ConfiguracaoServidor.DEBUG:
                print(f"{Cores.CINZA}{dados}{Cores.NORMAL}")

            return dados
        except Exception as erro:
            self._enviar_resposta_json(False, erro=f'JSON inválido: {erro}')
            return None

    def handle(self): # Nome do método padrão
        entrada = self._ler_comando_json()
        if entrada is None:
            return

        acao = entrada.get('acao')
        parametros = entrada.get('parametros', {})

        gerenciador_db = DatabaseManager()
        if not gerenciador_db.connect():
            self._enviar_resposta_json(False, erro='Falha crítica no banco de dados.')
            return

        try:
            resultado = ProcessadorDeComandos.executar(gerenciador_db, acao, parametros)
            # Normalizar retornos do Processador:
            # - Se for um valor do Enum Mensagem, considera-se erro salvo se for um token de sucesso
            # - Tokens considerados sucesso: SUCESSO, ADICIONADO, REMOVIDO, ATUALIZADO, UTILIZADOR_CRIADO
            if isinstance(resultado, Mensagem):
                sucessos = {Mensagem.SUCESSO, Mensagem.ADICIONADO, Mensagem.REMOVIDO, Mensagem.ATUALIZADO, Mensagem.UTILIZADOR_CRIADO}
                if resultado in sucessos:
                    # Envia o nome do enum (ex: 'SUCESSO') como resultado
                    self._enviar_resposta_json(True, str(resultado))
                else:
                    # Envia como erro
                    self._enviar_resposta_json(False, erro=str(resultado))
            else:
                # Strings e payloads (dict/list) são enviados como resultado com ok=True
                self._enviar_resposta_json(True, resultado)
        except Exception as erro:
            self._enviar_resposta_json(False, erro=str(erro))
        finally:
            try:
                if gerenciador_db.conn:
                    gerenciador_db.conn.close()
            except:
                pass

class UtilitariosServidor:
    @staticmethod
    def limpar_tela_servidor(mensagem):
        os.system('cls')
        if mensagem is not None:
             print(f'{mensagem}')

    @staticmethod
    def limpar_base_dados_debug():
        if not ConfiguracaoServidor.DEBUG:
            return
# Verifica novamente para não haver erro
        try:
            bd = DatabaseManager(limpar_base_de_dados=True)
            if not bd.connect() and bd.conn is None:
                print('Erro ao conectar para limpeza.')
                return

            print('Base de dados limpa e resetada com sucesso!')
        except Exception as e:
            print(f'Erro ao limpar BD: {str(e)}')

    @staticmethod
    def monitorar_atalhos_debug():
        if not ConfiguracaoServidor.DEBUG:
            return

        print('Atalho de Debug ativo: Pressione Ctrl+Alt+P para limpar a base de dados...')

        try:
            import win32api
            import win32con
            
            while True:
                try:
                    # Se todas as teclas estiverem pressionadas
                    ctrl_pressionado = win32api.GetKeyState(win32con.VK_CONTROL) < 0
                    alt_pressionado = win32api.GetKeyState(win32con.VK_MENU) < 0
                    p_pressionado = win32api.GetKeyState(ord('P')) < 0

                    if ctrl_pressionado and alt_pressionado and p_pressionado:
                        print('Atalho Ctrl+Alt+P detectado!')
                        UtilitariosServidor.limpar_base_dados_debug()
                        os._exit(0) # Força reinício/saída após limpar
                        
                    time.sleep(0.1) # Evita uso excessivo de CPU
                except ImportError:
                    print("As bibliotecas necessárias para o atalho não foram encontradas. Atalho desativado.")
                    break
                except Exception:
                    pass
        except ImportError:
            print("As bibliotecas necessárias para o atalho não foram encontradas. Atalho desativado.")
        except Exception as e:
            print(f'Erro na thread de atalhos: {str(e)}')

    @staticmethod
    def verificar_porta_em_uso(ip, port):
        try:
            # Af_INET = IPv4, SOCK_STREAM = TCP
            sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_STREAM)
            resultado = sock.connect_ex((ip, port)) # connect_ex retorna 0 se a conexão for bem sucedida (porta ocupada)
            sock.close()
            return resultado == 0 
        except:
            return False

def run_server(host, port, debug=False):
    ConfiguracaoServidor.DEBUG = debug
    
    # Verificação prévia
    if UtilitariosServidor.verificar_porta_em_uso(host, port):
        print(f'{Cores.VERMELHO}A porta {port} já está em uso. Feche a aplicação que está a usá-la ou mude a porta.{Cores.NORMAL}')
        return
    
    # Iniciar Thread de Debug se necessário
    if ConfiguracaoServidor.DEBUG:
        thread_atalhos = threading.Thread(target=UtilitariosServidor.monitorar_atalhos_debug, daemon=True)
        thread_atalhos.start()

    try:
        # Inicia o servidor TCP com Threading (permite múltiplos clientes)
        servidor = socketserver.ThreadingTCPServer((host, port), ManipuladorRequisicao)
        # Permitir reutilização imediata do endereço após encerramento
        servidor.allow_reuse_address = True
        # Marcar as threads do servidor como daemon para encerramento limpo
        servidor.daemon_threads = True
        
        print(f'{Cores.VERDE}Servidor online e aguardando pedidos em {host}:{port}{Cores.NORMAL}')
        print(f'{Cores.CIANO}Pressione Ctrl+C para encerrar.{Cores.NORMAL}')
        
        try:
            servidor.serve_forever()
        except KeyboardInterrupt:
            UtilitariosServidor.limpar_tela_servidor(f"{Cores.ROXO}Servidor encerrado manualmente.{Cores.NORMAL}")
        except Exception as e:
            UtilitariosServidor.limpar_tela_servidor(f"{Cores.VERMELHO}{Cores.NEGRITO}Erro fatal: {e}{Cores.NORMAL}")
        finally:
            print(f"{Cores.AMARELO}A encerrar servidor...{Cores.NORMAL}")
            servidor.shutdown()
            servidor.server_close()
            # Aguardar um momento para threads finalizarem
            time.sleep(0.5)
            
    except Exception as e:
        UtilitariosServidor.limpar_tela_servidor(f"{Cores.VERMELHO}{Cores.NEGRITO}Erro ao iniciar o socket: {e}{Cores.NORMAL}")

def run(host='127.0.0.1', port=5000, debug=False):
    # Suprimir warnings de threading durante shutdown
    import warnings
    warnings.filterwarnings("ignore", category=DeprecationWarning)
    
    try:
        run_server(host, port, debug)
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as erro:
        print(f"\n{Cores.VERMELHO}Erro fatal no servidor: {erro}{Cores.NORMAL}")


if __name__ == '__main__':
    run_server(ConfiguracaoServidor.HOST_PADRAO, ConfiguracaoServidor.PORTA_PADRAO, debug=False)