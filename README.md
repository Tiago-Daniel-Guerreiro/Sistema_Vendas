# Sistema de Vendas (Cliente-Servidor)

![Language](https://img.shields.io/badge/Python-3.13%2B-blue.svg)
![Database](https://img.shields.io/badge/Database-MySQL-orange.svg)
![Architecture](https://img.shields.io/badge/Architecture-Client--Server-green.svg)
![Status](https://img.shields.io/badge/Status-Funcional-brightgreen.svg)

Sistema completo de gestão de vendas com arquitetura cliente-servidor, desenvolvido em Python com comunicação via sockets TCP e base de dados MySQL.

Este projeto académico foi desenvolvido em equipa (5 elementos) sob um **prazo muito curto**, onde tive o papel de **gestor de equipa e líder técnico**. Após a apresentação oficial, continuei o desenvolvimento de forma autónoma para refatorar e melhorar significativamente a arquitetura e funcionalidades.

O desafio não era apenas criar um sistema funcional, mas construir uma solução que demonstrasse conhecimento de **programação orientada a objetos**, **comunicação em rede** e **integração com bases de dados**, tudo isto num prazo apertado e com uma equipa a coordenar.

## 🚀 Tecnologias Utilizadas

- **Linguagem:** Python 3.13+
- **Base de Dados:** MySQL
- **Comunicação:** JSON por Sockets TCP + UDP (descoberta de IP do servidor)
- **Extras:** PyWin32 (atalhos de teclado no Windows)

## 🎯 Objetivo Principal

O projeto foi guiado por requisitos académicos específicos definidos no guião:

- **Arquitetura Cliente-Servidor:** Dois módulos distintos a comunicar via sockets
- **Multi-utilizador:** Suporte a múltiplas conexões simultâneas
- **Sistema de Permissões:** Três níveis de acesso (Admin, Vendedor, Cliente)
- **Gestão Completa:** Produtos, vendas, stock e utilizadores
- **POO Obrigatória:** Uso explícito de herança e módulos
- **MySQL:** Todas as informações geridas em base de dados

## 🏗️ Arquitetura

O sistema segue uma arquitetura **cliente-servidor** com separação clara de responsabilidades, implementando uma API sobre sockets TCP com protocolo JSON para comunicação estruturada.

### 💻 Componentes do Cliente

- **Interface:** Menus e interação com o utilizador
- **Controlador:** Gere a lógica, coordenando a interface e os dados
- **Sessão:** Gere tokens locais e ficheiros JSON de configuração
- **Rede:** Módulo dedicado à comunicação via Sockets

### 🖧 Componentes do Servidor

- **Servidor TCP:** Utiliza Threading para aceitar múltiplas conexões
- **Processador de Comandos:** Valida e verifica permissões
- **Ações:** Execução prática dos pedidos
- **Comando:** Definição e estrutura dos comandos
- **Entidades:** Classes com herança (Utilizador, Produto, etc.)
- **Base de Dados:** Conexão e queries ao MySQL

### 📨 Protocolo de Comunicação (API sobre Sockets)

A comunicação entre cliente e servidor funciona como uma API, mas em vez de HTTP utiliza sockets TCP com mensagens JSON. Cada pedido contém uma ação e parâmetros, e o servidor responde com um resultado estruturado.

#### Exemplos

- **Cliente → Servidor:** `{"acao": "autenticar", "email": "...", "senha": "..."}`
- **Servidor → Cliente:** `{"ok": true, "token": "abc123...", "utilizador": {...}}`
- **Cliente → Servidor:** `{"acao": "listar_produtos", "token": "Fe53j..."}`
- **Servidor → Cliente:** `{"ok": true, "dados": [...]}`

Esta abordagem oferece as vantagens de uma API (estrutura, validação, respostas padronizadas) com as vantagens de conexões via sockets.

## 🔒 Sistema de Autenticação

- **Tokens de Sessão:** Tokens únicos gerados com `secrets.token_hex(32)` para cada sessão
**Persistência Local:** Tokens guardados em ficheiro JSON no cliente
- **Expiração de Sessões** Tokens expiram automaticamente após 24 horas
- **Reutilização Inteligente:** Tokens são reutilizados se ainda faltarem mais de 6h para expirar
- **Multi-nível:** Admin, Vendedor, Cliente, Não Autenticado
- **Registo Automático:** Novos clientes podem registar-se diretamente

## 👤 Funcionalidades por Tipo de Utilizador

### Cliente

- Realizar encomendas (produto + quantidade)
- Ver histórico de compras pessoal
- Listar produtos (com filtros por categoria, preço, disponibilidade)
- Consultar categorias disponíveis
- Editar dados pessoais (nome, senha)
- Apagar própria conta

### Vendedor

- Todas as funcionalidades de Cliente
- Editar produtos da sua loja (preço, stock, descrição)
- Concluir encomendas pendentes
- Ver histórico de vendas da loja
- Receber alertas de stock baixo (<5 unidades)
- Listar encomendas pendentes

### Admin

- Todas as funcionalidades anteriores
- Adicionar novos produtos ao catálogo
- Remover produtos
- Criar/editar/apagar lojas
- Criar funcionários (vendedores)
- Listar todos os utilizadores do sistema
- Promover clientes a admin (com chave secreta)

## 🌟 Funcionalidades Extra

### Atalhos de Teclado

- `Shift+P:` Carregar dados de exemplo (Exemplo.sql)
- `Ctrl+Alt+P:` Limpar base de dados (modo depuração)

Os atalhos são monitorizados em threads paralelas.

### Modo Depuração

- Logs de comunicação cliente-servidor

### Melhorias na Interface

- Menus mais intuitivos e organizados
- Mensagens de erro/sucesso padronizadas com cores
- Tratamento robusto de interrupções (Ctrl+C)
- Comando `help` dinâmico que lista comandos disponíveis conforme permissões

### Gestão de Erros e Validações

- **Try/Except:** Tratamento de exceções específicas
- **Enums:** Mensagens de erro/sucesso padronizadas com mensagens bem definidas
- **Validação de Input:** Verificação de parâmetros obrigatórios
- **Logging:** Mensagens informativas com cores

## ⚙️ Desafios Encontrados

### 👥 Durante o Desenvolvimento em Equipa

- **Restrições de Tempo:** Prazo apertado impediu conclusão de 100% das funcionalidades antes da apresentação
- **Sincronização:** Coordenar trabalho em equipa com diferentes ritmos de desenvolvimento
- **Complexidade da Arquitetura:** Integrar corretamente servidor, cliente, base de dados e múltiplas threads
- **Debugging de Rede:** Identificar e corrigir problemas de comunicação entre cliente e servidor

### 🔧 Desafios Técnicos e Soluções

| Desafio                      | Problema                                                      | Solução                                                            |
| ---------------------------- | ------------------------------------------------------------- | ------------------------------------------------------------------ |
| **Sincronização de Threads** | Múltiplas threads a aceder à BD simultaneamente               | Cada thread cria a sua própria conexão MySQL                       |
| **Gestão de Sessões**        | Manter utilizadores autenticados sem login repetido           | Tokens únicos com expiração, guardados localmente em JSON          |
| **Herança de Permissões**    | Admin deve poder executar todas as ações de níveis inferiores | Hierarquia de herança onde cada classe herda da anterior           |
| **Bugs de Credenciais**      | Alguns comandos não enviavam o token de sessão                | Refatoração para incluir token automaticamente em todos os pedidos |

## ⏱️ Desenvolvimento Pós-Apresentação

Após a apresentação oficial, tomei a decisão de **continuar o desenvolvimento de forma autónoma** para:

1. Concluir funcionalidades pendentes
2. Refatorar completamente o código
3. Aplicar melhores práticas de desenvolvimento
4. Melhorar a arquitetura e modularidade
5. Adicionar/melhorar funcionalidades extras (tokens de sessão, atalhos, modo debug, etc.)

### 📈 Evolução da Arquitetura

| Fase                 | Estado               | Características                                                     |
| -------------------- | -------------------- | ------------------------------------------------------------------- |
| **Apresentação**     | Código monolítico    | Funções longas, lógica misturada com interface                      |
| **Pós-Apresentação** | Refatoração completa | Arquitetura modular, padrões aplicados, responsabilidades separadas |

### 📊 Estado na Apresentação vs Final

| Funcionalidade              | Apresentação            | Versão Final                              |
| --------------------------- | ----------------------- | ----------------------------------------- |
| Servidor funcional          | ✅                      | ✅                                        |
| Autenticação básica         | ✅                      | ✅ Tokens + persistência + expiração      |
| Funcionalidades essenciais  | ✅                      | ✅ 30+ comandos                           |
| Arquitetura                 | ⚠️ Monolítica           | ✅ Modular com padrões                    |
| Tratamento de erros         | ⚠️ Inconsistente        | ✅ Centralizado com enums e help melhorado|
| Funcionalidades secundárias | ⚠️ Incompletas          | ✅ Todas implementadas                    |
| Bugs nas requisições        | ❌ Credenciais em falta | ✅ Corrigido                              |
| Documentação                | ⚠️ Incompleta           | ✅ Completa                               |

## 👨‍💼 O Meu Papel

Fui **gestor de equipa e líder técnico**, responsável por:

- **Gestão de Membros:** Distribuição de tarefas, acompanhamento do progresso, coordenação de atividades
- **Arquitetura:** Definição da estrutura modular
- **Resolução de Conflitos:** Mediação técnica e tomada de decisões críticas
- **Documentação:** Relatórios, comentários
- **Refatoração Pós-Apresentação:** Desenvolvimento autónomo de todas as melhorias

Após a apresentação, decidi continuar o desenvolvimento sozinho para transformar código funcional mas problemático numa solução robusta e bem arquitetada. Esta decisão reflete o compromisso com a qualidade e a aprendizagem contínua.

## 📥 Como Utilizar

A aplicação está disponível como executável único, gerado com PyInstaller.

1. Aceda à secção **[Releases](../../releases)** deste repositório.
2. Faça o download da versão mais recente (cliente e servidor).
3. Execute diretamente no Windows (não é necessário ter Python instalado).

### Como Utilizar o Servidor

1. **Inicie o MySQL:**
    - Abra o XAMPP e inicie o serviço MySQL
    - Ou utilize outro servidor MySQL

2. **Configure as credenciais:**
    - Edite `servidor/configuracao.py` com os dados da sua BD

3. **Execute o servidor:**
    - Via executável: `program.exe`
    - Via Python: `python main.py`

4. **Dados de exemplo (opcional):**
    - Use `Shift+P` para carregar dados de teste automaticamente

### Como Utilizar o Cliente

1. **Execute o cliente:**
    - Via executável: `program.exe`
    - Via Python: `python main.py`

2. **Conecte ao servidor:**
    - Introduza o IP do servidor (ex: `127.0.0.1` para local)
    - Introduza a porta (padrão: `5000`)

3. **Autentique-se ou registe-se:**
    - Login com credenciais existentes
    - Ou registe uma nova conta de cliente

## 📚 Aprendizagens

### Competências Técnicas

- **Redes:** Sockets TCP/UDP, comunicação cliente-servidor, protocolo JSON, threading
- **Design de API:** Criação de protocolo de comunicação estruturado
- **Base de Dados:** Modelação relacional, JOINs
- **POO:** Herança, encapsulamento e polimorfismo

### Soft Skills

- **Gestão de Equipa:** Coordenação, distribuição de tarefas, resolução de conflitos
- **Gestão de Tempo:** Priorização sob pressão, foco no essencial
- **Pragmatismo:** Código com o essencial para a entrega vs perfeccionismo
- **Perseverança:** Continuar desenvolvimento após entrega oficial
- **Auto-Gestão:** Trabalho autónomo na refatoração completa

## 🔮 Próximos Passos

### Curto Prazo

- Testes automatizados
- encriptação de senhas com bcrypt

### Médio Prazo

- Interface gráfica (Tkinter)
- comunicação encriptada
