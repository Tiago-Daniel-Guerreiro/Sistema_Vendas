# Sistema_Vendas

e sua equipa foram contratados para o desenvolvimento de um sistema em Python para uma
loja de produtos saudáveis. Devem desenvolver um Sistema Gestor de Vendas de Produtos
Sustentáveis. A empresa solicita que seja desenvolvido duas aplicações: uma aplicação “servidor”, que
terá a função receber os diferentes pedidos dos seus clientes; e, uma aplicação “cliente”, que
possibilita a solicitação de diferentes operações. As informações devem ser salvas e geridas com o
uso de base de dados. O contratante solicitou que seja utilizado MySQL, Sockets, uso de herança e
módulos.
Atenção: todas as informações (por exemplo, utilizadores, funcionários, etc.) relacionadas com a
aplicação devem ser criadas durante a execução da aplicação.
Papéis de Utilizador:
• Administrador – responsável pela gestão global do sistema e controle de stock.
• Vendedor – responsável por registar vendas e atender clientes.
• Cliente – realiza consultas de produtos e efetua compras
O servidor é o núcleo do sistema, responsável por armazenar, validar e processar todas as operações
comerciais.

1. Autenticação

- Recebe credenciais do cliente (utilizador/senha).
- Verifica se o utilizador é admin, vendedor, cliente.
- Diferenciar permissões (apenas admin pode adicionar produtos).

2. Gestão de Produtos

- Adicionar produto:
- Recebe dados (nome, categoria, preço, stock, descrição).
- Retorna PRODUTO_ADICIONADO ou ERRO_DUPLICADO.
- Atualizar produto:
- Permite alterar preço, stock ou descrição.
- Retorna ATUALIZACAO_OK ou PRODUTO_NAO_ENCONTRADO.
- Remover produto:
- Elimina produto do catálogo.
- Retorna PRODUTO_REMOVIDO.
- Listar produtos:

o Envia a lista completa ou filtrada (por categoria, preço, disponibilidade).

3. Gestão de Vendas

• Registar venda:
o Recebe pedido do cliente com ID do produto e quantidade.
o Verifica stock e atualiza base de dados.
o Retorna VENDA_CONFIRMADA ou STOCK_INSUFICIENTE.
• Consultar histórico de vendas:
o Envia lista de todas as vendas realizadas, com datas e valores totais.

4. Gestão de Stock
• Monitoriza produtos com stock abaixo de um limite (ex: < 5 unidades).
• Envia alerta ALERTA_STOCK_BAIXO.

Funções do Cliente

1. Login
• Envia utilizador/senha para o servidor.
• Recebe resultado e ajusta o acesso conforme o tipo de utilizador.
• Se o utilizador não possuir credenciais, é necessário fazer o registo na aplicação.

2. Gestão de produtos (para admin ou vendedores)
• Adicionar novo produto (nome, preço, categoria, stock).
• Atualizar ou remover produtos.

3. Realizar vendas (para vendedores (se o cliente estiver presencialmente na loja) ou clientes)
• Selecionar produto e quantidade.
• Enviar pedido de venda ao servidor.
• Receber confirmação e total da compra.

4. Excluir produto (para admin)
• Solicita ao usuário o ID do produto.
• Envia pedido ao servidor e exibe resposta.

Critérios de avaliação:
• Cada aluno será avaliado individualmente.
• Nota = (Nota do Projeto * 0,75) + (Perguntas técnicas sobre projeto em exposição * 0,15) +
(Assiduidade * 0,10)
ALERTA:
• Está proibido o uso de qualquer ferramenta de geração de código que faça uso de inteligência
artificial.

• Caso algum integrante do grupo não participe do desenvolvimento do projeto, poderá receber
uma penalização de até 50% na nota final. Para isso, o professor deve ser notificado sobre o
problema. Nota Final = Nota - (Nota * 0,5)
• Se não houver comunicação, todos os membros da dupla poderão ser penalizados em até
50% da nota final. No entanto, se a comunicação for feita antes da metade do tempo previsto
para a realização do projeto, apenas o aluno que não estiver participando será penalizado.
Nota Final = Nota - (Nota * 0,5)
• Total de horas para o desenvolvimento: 5 horas


Basicamente o código que está no projeto é o código da atividade 1 que podemos nos basear, e um código que eu tinha feito que serve para criar o sql com python para simplificar o processo.