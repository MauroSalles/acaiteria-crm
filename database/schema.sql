-- =============================================================================
-- SCHEMA SQL - CRM SIMPLES PARA AÇAITERIA COMBINA AÇAÍ
-- =============================================================================
-- Descrição: Modelo de banco de dados relacional para gerenciamento de clientes,
--            produtos, vendas e pagamentos da Açaiteria Combina Açaí
-- 
-- Autor: Grupo 22 - Projeto Integrador UNIVESP (Eixo Computação)
-- Data: 2026
-- =============================================================================

-- Limpar banco de dados anterior (se existente)
DROP TABLE IF EXISTS PAGAMENTO;
DROP TABLE IF EXISTS ITEM_VENDA;
DROP TABLE IF EXISTS VENDA;
DROP TABLE IF EXISTS PRODUTO;
DROP TABLE IF EXISTS CLIENTE;

-- =============================================================================
-- TABELA: CLIENTE
-- =============================================================================
-- Armazena dados dos clientes da açaiteria
-- Inclui campos para LGPD: consentimento_lgpd e data_consentimento
CREATE TABLE CLIENTE (
    id_cliente INT AUTO_INCREMENT PRIMARY KEY,
    nome VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(100),
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    consentimento_lgpd BOOLEAN DEFAULT FALSE,
    data_consentimento DATETIME,
    data_exclusao DATETIME NULL,
    ativo BOOLEAN DEFAULT TRUE,
    
    -- Índices para melhor performance
    INDEX idx_cliente_nome (nome),
    INDEX idx_cliente_telefone (telefone),
    INDEX idx_cliente_email (email),
    INDEX idx_cliente_ativo (ativo)
);

-- =============================================================================
-- TABELA: PRODUTO
-- =============================================================================
-- Armazena os produtos/sabores oferecidos pela açaiteria
CREATE TABLE PRODUTO (
    id_produto INT AUTO_INCREMENT PRIMARY KEY,
    nome_produto VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL,
    ativo BOOLEAN DEFAULT TRUE,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Índices
    INDEX idx_produto_nome (nome_produto),
    INDEX idx_produto_categoria (categoria),
    INDEX idx_produto_ativo (ativo)
);

-- =============================================================================
-- TABELA: VENDA
-- =============================================================================
-- Registro principal de transações de venda
CREATE TABLE VENDA (
    id_venda INT AUTO_INCREMENT PRIMARY KEY,
    id_cliente INT NOT NULL,
    data_venda DATETIME DEFAULT CURRENT_TIMESTAMP,
    valor_total DECIMAL(10, 2) NOT NULL,
    forma_pagamento VARCHAR(50),
    status_pagamento VARCHAR(50) DEFAULT 'Pendente',
    observacoes TEXT,
    recibo_gerado BOOLEAN DEFAULT FALSE,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    
    -- Chave estrangeira
    CONSTRAINT fk_venda_cliente FOREIGN KEY (id_cliente)
        REFERENCES CLIENTE(id_cliente) ON DELETE RESTRICT,
    
    -- Índices
    INDEX idx_venda_cliente (id_cliente),
    INDEX idx_venda_data (data_venda),
    INDEX idx_venda_status (status_pagamento)
);

-- =============================================================================
-- TABELA: ITEM_VENDA
-- =============================================================================
-- Detalhamento dos produtos dentro de cada venda (linha por linha)
CREATE TABLE ITEM_VENDA (
    id_item INT AUTO_INCREMENT PRIMARY KEY,
    id_venda INT NOT NULL,
    id_produto INT NOT NULL,
    quantidade INT NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL,
    
    -- Chaves estrangeiras
    CONSTRAINT fk_item_venda FOREIGN KEY (id_venda)
        REFERENCES VENDA(id_venda) ON DELETE CASCADE,
    CONSTRAINT fk_item_produto FOREIGN KEY (id_produto)
        REFERENCES PRODUTO(id_produto) ON DELETE RESTRICT,
    
    -- Índices
    INDEX idx_item_venda (id_venda),
    INDEX idx_item_produto (id_produto)
);

-- =============================================================================
-- TABELA: PAGAMENTO
-- =============================================================================
-- Rastreamento de pagamentos e formas de pagamento
CREATE TABLE PAGAMENTO (
    id_pagamento INT AUTO_INCREMENT PRIMARY KEY,
    id_venda INT NOT NULL,
    data_pagamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    valor_pago DECIMAL(10, 2) NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Concluído',
    referencia_transacao VARCHAR(100),
    notas TEXT,
    
    -- Chave estrangeira
    CONSTRAINT fk_pagamento_venda FOREIGN KEY (id_venda)
        REFERENCES VENDA(id_venda) ON DELETE CASCADE,
    
    -- Índices
    INDEX idx_pagamento_venda (id_venda),
    INDEX idx_pagamento_data (data_pagamento),
    INDEX idx_pagamento_metodo (metodo)
);

-- =============================================================================
-- DADOS DE TESTE / SEED DATA
-- =============================================================================

-- Inserir clientes de exemplo
INSERT INTO CLIENTE (nome, telefone, email, observacoes, consentimento_lgpd, data_consentimento, ativo) VALUES
('Gabriel da Silva', '1299999001', 'gabriel@email.com', 'Cliente frequente, prefere açaí com granola', TRUE, NOW(), TRUE),
('Marina Costa', '1299999002', 'marina@email.com', 'Alérgica a amendoim', TRUE, NOW(), TRUE),
('João Pereira', '1299999003', 'joao@email.com', 'Prefere diabético', TRUE, NOW(), TRUE),
('Ana Paula', '1299999004', 'ana@email.com', NULL, TRUE, NOW(), TRUE),
('Carlos Mendes', '1299999005', NULL, 'Compra grandes quantidades para eventos', TRUE, NOW(), TRUE),
('Paula Rodrigues', '1299999006', 'paula@email.com', 'Cliente nova', FALSE, NULL, TRUE);

-- Inserir produtos/sabores
INSERT INTO PRODUTO (nome_produto, categoria, descricao, preco, ativo) VALUES
('Açaí com Granola', 'Açaí Premium', 'Açaí puro com granola caseira', 25.00, TRUE),
('Açaí com Banana', 'Açaí Premium', 'Açaí com banana fatiada', 24.00, TRUE),
('Açaí Simples', 'Açaí Básico', 'Açaí puro, sem adições', 18.00, TRUE),
('Açaí Diabético', 'Açaí Especial', 'Açaí com adoçante, sem açúcar', 22.00, TRUE),
('Açaí Festa (500ml)', 'Açaí Grande', 'Porção grande para compartilhar', 35.00, TRUE),
('Suco Natural - Laranja', 'Bebidas', 'Suco de laranja natural', 8.00, TRUE),
('Suco Natural - Morango', 'Bebidas', 'Suco de morango natural', 10.00, TRUE),
('Água', 'Bebidas', 'Água mineral', 3.00, TRUE),
('Refrigerante', 'Bebidas', 'Refrigerante 350ml', 5.00, TRUE),
('Granola Extra', 'Adicionais', 'Granola caseira extra', 5.00, TRUE);

-- Inserir vendas de exemplo (últimos 10 dias)
INSERT INTO VENDA (id_cliente, data_venda, valor_total, forma_pagamento, status_pagamento, recibo_gerado) VALUES
(1, DATE_SUB(NOW(), INTERVAL 10 DAY), 25.00, 'Dinheiro', 'Concluído', TRUE),
(2, DATE_SUB(NOW(), INTERVAL 9 DAY), 49.00, 'Débito', 'Concluído', TRUE),
(3, DATE_SUB(NOW(), INTERVAL 8 DAY), 22.00, 'Dinheiro', 'Concluído', TRUE),
(1, DATE_SUB(NOW(), INTERVAL 7 DAY), 35.00, 'Crédito', 'Concluído', TRUE),
(4, DATE_SUB(NOW(), INTERVAL 6 DAY), 30.00, 'Dinheiro', 'Concluído', TRUE),
(5, DATE_SUB(NOW(), INTERVAL 5 DAY), 105.00, 'Dinheiro', 'Concluído', TRUE),
(1, DATE_SUB(NOW(), INTERVAL 4 DAY), 25.00, 'Dinheiro', 'Concluído', TRUE),
(2, DATE_SUB(NOW(), INTERVAL 3 DAY), 34.00, 'Débito', 'Concluído', TRUE),
(3, DATE_SUB(NOW(), INTERVAL 2 DAY), 50.00, 'Crédito', 'Concluído', TRUE),
(4, DATE_SUB(NOW(), INTERVAL 1 DAY), 72.00, 'Dinheiro', 'Concluído', TRUE);

-- Inserir itens de venda
INSERT INTO ITEM_VENDA (id_venda, id_produto, quantidade, preco_unitario, subtotal) VALUES
(1, 1, 1, 25.00, 25.00),
(2, 1, 1, 25.00, 25.00),
(2, 6, 1, 8.00, 8.00),
(2, 9, 1, 5.00, 5.00),
(3, 4, 1, 22.00, 22.00),
(4, 1, 1, 25.00, 25.00),
(4, 5, 1, 35.00, 35.00),
(5, 1, 2, 25.00, 50.00),
(5, 7, 1, 10.00, 10.00),
(5, 9, 1, 5.00, 5.00),
(6, 1, 3, 25.00, 75.00),
(6, 2, 2, 24.00, 48.00),
(6, 10, 2, 5.00, 10.00),
(7, 3, 1, 18.00, 18.00),
(7, 10, 1, 5.00, 5.00),
(7, 8, 1, 3.00, 3.00),
(8, 1, 1, 25.00, 25.00),
(8, 7, 1, 10.00, 10.00),
(9, 2, 2, 24.00, 48.00),
(9, 10, 1, 5.00, 5.00),
(10, 1, 2, 25.00, 50.00),
(10, 9, 2, 5.00, 10.00),
(10, 6, 1, 8.00, 8.00),
(10, 8, 1, 3.00, 3.00);

-- Inserir pagamentos
INSERT INTO PAGAMENTO (id_venda, data_pagamento, valor_pago, metodo, status, referencia_transacao) VALUES
(1, DATE_SUB(NOW(), INTERVAL 10 DAY), 25.00, 'Dinheiro', 'Concluído', 'CASH-001'),
(2, DATE_SUB(NOW(), INTERVAL 9 DAY), 49.00, 'Débito', 'Concluído', 'DEBIT-001'),
(3, DATE_SUB(NOW(), INTERVAL 8 DAY), 22.00, 'Dinheiro', 'Concluído', 'CASH-002'),
(4, DATE_SUB(NOW(), INTERVAL 7 DAY), 35.00, 'Crédito', 'Concluído', 'CREDIT-001'),
(5, DATE_SUB(NOW(), INTERVAL 6 DAY), 30.00, 'Dinheiro', 'Concluído', 'CASH-003'),
(6, DATE_SUB(NOW(), INTERVAL 5 DAY), 105.00, 'Dinheiro', 'Concluído', 'CASH-004'),
(7, DATE_SUB(NOW(), INTERVAL 4 DAY), 25.00, 'Dinheiro', 'Concluído', 'CASH-005'),
(8, DATE_SUB(NOW(), INTERVAL 3 DAY), 34.00, 'Débito', 'Concluído', 'DEBIT-002'),
(9, DATE_SUB(NOW(), INTERVAL 2 DAY), 50.00, 'Crédito', 'Concluído', 'CREDIT-002'),
(10, DATE_SUB(NOW(), INTERVAL 1 DAY), 72.00, 'Dinheiro', 'Concluído', 'CASH-006');

-- =============================================================================
-- VIEWS ÚTEIS PARA RELACIONAMENTO E ANÁLISES
-- =============================================================================

-- View: Vendas com dados de cliente
CREATE VIEW vw_vendas_com_cliente AS
SELECT 
    v.id_venda,
    v.data_venda,
    c.nome AS cliente_nome,
    c.telefone,
    c.email,
    v.valor_total,
    v.forma_pagamento,
    v.status_pagamento
FROM VENDA v
JOIN CLIENTE c ON v.id_cliente = c.id_cliente
WHERE c.ativo = TRUE;

-- View: Itens de venda com detalhes de produto
CREATE VIEW vw_itens_venda_detalhado AS
SELECT 
    iv.id_item,
    iv.id_venda,
    p.nome_produto,
    p.categoria,
    iv.quantidade,
    iv.preco_unitario,
    iv.subtotal
FROM ITEM_VENDA iv
JOIN PRODUTO p ON iv.id_produto = p.id_produto;

-- View: Total de vendas por cliente (análise de fidelização)
CREATE VIEW vw_clientes_frequencia AS
SELECT 
    c.id_cliente,
    c.nome,
    c.telefone,
    COUNT(v.id_venda) AS total_compras,
    SUM(v.valor_total) AS faturamento_total,
    MAX(v.data_venda) AS ultima_compra,
    ROUND(AVG(v.valor_total), 2) AS ticket_medio
FROM CLIENTE c
LEFT JOIN VENDA v ON c.id_cliente = v.id_cliente
WHERE c.ativo = TRUE
GROUP BY c.id_cliente, c.nome, c.telefone
ORDER BY total_compras DESC;

-- View: Produtos mais vendidos
CREATE VIEW vw_produtos_ranking AS
SELECT 
    p.id_produto,
    p.nome_produto,
    p.categoria,
    COUNT(iv.id_item) AS quantidade_vendida,
    SUM(iv.subtotal) AS faturamento,
    ROUND(AVG(iv.preco_unitario), 2) AS preco_medio
FROM PRODUTO p
LEFT JOIN ITEM_VENDA iv ON p.id_produto = iv.id_produto
WHERE p.ativo = TRUE
GROUP BY p.id_produto, p.nome_produto, p.categoria
ORDER BY quantidade_vendida DESC;

-- View: Faturamento por dia
CREATE VIEW vw_faturamento_diario AS
SELECT 
    DATE(v.data_venda) AS data,
    COUNT(v.id_venda) AS total_vendas,
    SUM(v.valor_total) AS faturamento_dia,
    ROUND(AVG(v.valor_total), 2) AS ticket_medio
FROM VENDA v
GROUP BY DATE(v.data_venda)
ORDER BY data DESC;

-- =============================================================================
-- FIM DO SCHEMA
-- =============================================================================
-- Última atualização: 10 de março de 2026
-- Status: v1.0 - Schema completo com dados de teste
