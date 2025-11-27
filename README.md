# Sistema de Vendas

Você e sua equipa foram contratados para o desenvolvimento de um sistema em Python para uma loja de produtos saudáveis. Devem desenvolver um Sistema Gestor de Vendas de Produtos.

A empresa solicita que sejam desenvolvidas duas aplicações:

1. **Aplicação Servidor**: Terá a função de receber os diferentes pedidos dos seus clientes.
2. **Aplicação Cliente**: Possibilita a solicitação de diferentes operações.

As informações devem ser salvas e geridas com o uso de base de dados. O contratante solicitou que seja utilizado **MySQL**, **Sockets**, uso de **herança** e **módulos**.

> **Atenção**: Todas as informações (por exemplo, utilizadores, funcionários, etc.) relacionadas com a aplicação devem ser criadas durante a execução da aplicação.

## Papéis de Utilizador

* **Administrador**: Responsável pela gestão global do sistema e controle de stock.
* **Vendedor**: Responsável por registrar vendas e atender clientes.
* **Cliente**: Realiza consultas de produtos e efetua compras.

## Funcionalidades do Servidor

O servidor é o núcleo do sistema, responsável por armazenar, validar e processar todas as operações comerciais.

### 1. Autenticação

* Recebe credenciais do cliente (utilizador/senha).
* Verifica se o utilizador é admin, vendedor ou cliente.
* Diferencia permissões (apenas admin pode adicionar produtos).

### 2. Gestão de Produtos

* **Adicionar produto**:
  * Recebe dados (nome, categoria, preço, stock, descrição).
  * Retorna `PRODUTO_ADICIONADO` ou `ERRO_DUPLICADO`.
* **Atualizar produto**:
  * Permite alterar preço, stock ou descrição.
  * Retorna `ATUALIZACAO_OK` ou `PRODUTO_NAO_ENCONTRADO`.
* **Remover produto**:
  * Elimina produto do catálogo.
  * Retorna `PRODUTO_REMOVIDO`.
* **Listar produtos**:
  * Envia a lista completa ou filtrada (por categoria, preço, disponibilidade).

### 3. Gestão de Vendas

* **registrar venda**:
  * Recebe pedido do cliente com ID do produto e quantidade.
  * Verifica stock e atualiza base de dados.
  * Retorna `VENDA_CONFIRMADA` ou `STOCK_INSUFICIENTE`.
* **Consultar histórico de vendas**:
  * Envia lista de todas as vendas realizadas, com datas e valores totais.

### 4. Gestão de Stock

* Monitoriza produtos com stock abaixo de um limite (ex: < 5 unidades).
* Envia alerta `ALERTA_STOCK_BAIXO`.

## Funções do Cliente

### 1. Login

* Envia utilizador/senha para o servidor.
* Recebe resultado e ajusta o acesso conforme o tipo de utilizador.
* Se o utilizador não possuir credenciais, é necessário fazer o registo na aplicação.

### 2. Gestão de produtos (para admin ou vendedores)

* Adicionar novo produto (nome, preço, categoria, stock).
* Atualizar ou remover produtos.

### 3. Realizar vendas (para vendedores ou clientes)

* Vendedores: Se o cliente estiver presencialmente na loja.
* Clientes: Compra direta.
* Selecionar produto e quantidade.
* Enviar pedido de venda ao servidor.
* Receber confirmação e total da compra.

### 4. Excluir produto (para admin)

* Solicita ao utilizador o ID do produto.
* Envia pedido ao servidor e exibe resposta.

---

## Critérios de Avaliação

* Cada aluno será avaliado individualmente.
* **Nota** = (Nota do Projeto \* 0.75) + (Perguntas técnicas sobre projeto em exposição \* 0.15) + (Assiduidade \* 0.10)
