
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


CREATE TABLE `categories` (
  `id` int(11) NOT NULL,
  `nome` varchar(50) DEFAULT NULL
);

INSERT INTO `categories` (`id`, `nome`) VALUES
(1, 'Fruta'),
(2, 'Itens da Padaria');

CREATE TABLE `descriptions` (
  `id` int(11) NOT NULL,
  `texto` text DEFAULT NULL
);

INSERT INTO `descriptions` (`id`, `texto`) VALUES
(1, 'Fruta madura vinda de Espanha'),
(2, 'Pão feito na hora');


CREATE TABLE `orders` (
  `id` int(11) NOT NULL,
  `buyer_user_id` int(11) DEFAULT NULL,
  `store_id` int(11) DEFAULT NULL,
  `seller_user_id` int(11) DEFAULT NULL,
  `status` enum('pendente','concluida') DEFAULT 'pendente',
  `total_price` decimal(10,2) DEFAULT 0.00,
  `order_date` datetime DEFAULT current_timestamp()
);

CREATE TABLE `order_items` (
  `id` int(11) NOT NULL,
  `order_id` int(11) DEFAULT NULL,
  `product_id` int(11) DEFAULT NULL,
  `quantity` int(11) DEFAULT NULL,
  `unit_price` decimal(10,2) DEFAULT NULL
);

CREATE TABLE `products` (
  `id` int(11) NOT NULL,
  `store_id` int(11) DEFAULT NULL,
  `product_name_id` int(11) DEFAULT NULL,
  `category_id` int(11) DEFAULT NULL,
  `description_id` int(11) DEFAULT NULL,
  `preco` decimal(10,2) DEFAULT NULL,
  `stock` int(11) DEFAULT NULL
);

INSERT INTO `products` (`id`, `store_id`, `product_name_id`, `category_id`, `description_id`, `preco`, `stock`) VALUES
(1, 2, 1, 1, 1, 2.00, 20),
(2, 1, 2, 2, 2, 20.00, 20);

CREATE TABLE `product_names` (
  `id` int(11) NOT NULL,
  `nome` varchar(100) DEFAULT NULL
);

INSERT INTO `product_names` (`id`, `nome`) VALUES
(1, 'Novo'),
(2, 'Pão');

CREATE TABLE `stores` (
  `id` int(11) NOT NULL,
  `nome` varchar(50) DEFAULT NULL,
  `localizacao` varchar(100) DEFAULT NULL
);

INSERT INTO `stores` (`id`, `nome`, `localizacao`) VALUES
(1, 'Loja de Lisboa', 'Baixa-Chiado, Lisboa'),
(2, 'Nova loja', 'Sintra');

CREATE TABLE `users` (
  `id` int(11) NOT NULL,
  `username` varchar(50) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  `cargo` enum('admin','vendedor','cliente') DEFAULT NULL,
  `store_id` int(11) DEFAULT NULL
);

INSERT INTO `users` (`id`, `username`, `password`, `cargo`, `store_id`) VALUES
(1, '1', '1', 'admin', NULL),
(2, '2', '2', 'cliente', NULL),
(3, '3', '3', 'vendedor', 1),
(4, 'Tiago', 'Guerreiro', 'vendedor', 1);

ALTER TABLE `categories`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nome` (`nome`);

ALTER TABLE `descriptions`
  ADD PRIMARY KEY (`id`);

ALTER TABLE `orders`
  ADD PRIMARY KEY (`id`),
  ADD KEY `buyer_user_id` (`buyer_user_id`),
  ADD KEY `store_id` (`store_id`),
  ADD KEY `seller_user_id` (`seller_user_id`);

ALTER TABLE `order_items`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_product_per_order` (`order_id`,`product_id`),
  ADD KEY `product_id` (`product_id`);

ALTER TABLE `products`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `unique_prod_store` (`store_id`,`product_name_id`),
  ADD KEY `product_name_id` (`product_name_id`),
  ADD KEY `category_id` (`category_id`),
  ADD KEY `description_id` (`description_id`);

ALTER TABLE `product_names`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nome` (`nome`);


ALTER TABLE `stores`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `nome` (`nome`);

ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `username` (`username`),
  ADD KEY `store_id` (`store_id`);

ALTER TABLE `categories`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

ALTER TABLE `descriptions`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

ALTER TABLE `orders`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `order_items`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT;

ALTER TABLE `products`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

ALTER TABLE `product_names`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

ALTER TABLE `stores`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=3;

ALTER TABLE `users`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=5;

ALTER TABLE `orders`
  ADD CONSTRAINT `orders_ibfk_1` FOREIGN KEY (`buyer_user_id`) REFERENCES `users` (`id`),
  ADD CONSTRAINT `orders_ibfk_2` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`),
  ADD CONSTRAINT `orders_ibfk_3` FOREIGN KEY (`seller_user_id`) REFERENCES `users` (`id`);

ALTER TABLE `order_items`
  ADD CONSTRAINT `order_items_ibfk_1` FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`) ON DELETE CASCADE,
  ADD CONSTRAINT `order_items_ibfk_2` FOREIGN KEY (`product_id`) REFERENCES `products` (`id`);

ALTER TABLE `products`
  ADD CONSTRAINT `products_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`),
  ADD CONSTRAINT `products_ibfk_2` FOREIGN KEY (`product_name_id`) REFERENCES `product_names` (`id`),
  ADD CONSTRAINT `products_ibfk_3` FOREIGN KEY (`category_id`) REFERENCES `categories` (`id`),
  ADD CONSTRAINT `products_ibfk_4` FOREIGN KEY (`description_id`) REFERENCES `descriptions` (`id`);

ALTER TABLE `users`
  ADD CONSTRAINT `users_ibfk_1` FOREIGN KEY (`store_id`) REFERENCES `stores` (`id`);
COMMIT;
