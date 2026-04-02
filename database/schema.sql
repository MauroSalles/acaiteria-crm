-- =============================================================================
-- SCHEMA SQL - CRM SIMPLES PARA AÇAITERIA COMBINA AÇAÍ
-- =============================================================================
-- Descrição: Modelo de banco de dados relacional para gerenciamento de clientes,
--            produtos, vendas, pagamentos, usuários e suporte da Açaiteria.
--            Compatível com SQLite (utilizado pela aplicação Flask).
--
-- Autor: Grupo 22 - Projeto Integrador UNIVESP (Eixo Computação)
-- Data: 2026
-- =============================================================================

-- Limpar banco de dados anterior (se existente)
DROP TABLE IF EXISTS mensagem_ticket;
DROP TABLE IF EXISTS ticket_suporte;
DROP TABLE IF EXISTS log_acao;
DROP TABLE IF EXISTS consentimento_historico;
DROP TABLE IF EXISTS pagamento;
DROP TABLE IF EXISTS item_venda;
DROP TABLE IF EXISTS venda;
DROP TABLE IF EXISTS produto;
DROP TABLE IF EXISTS cliente;
DROP TABLE IF EXISTS usuario;

-- =============================================================================
-- TABELA: USUARIO
-- =============================================================================
CREATE TABLE usuario (
    id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(150) NOT NULL,
    email VARCHAR(150) UNIQUE NOT NULL,
    senha_hash VARCHAR(256) NOT NULL,
    papel VARCHAR(20) NOT NULL DEFAULT 'operador',
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: CLIENTE
-- =============================================================================
CREATE TABLE cliente (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(100),
    data_cadastro DATETIME DEFAULT CURRENT_TIMESTAMP,
    observacoes TEXT,
    consentimento_lgpd BOOLEAN DEFAULT 0,
    data_consentimento DATETIME,
    consentimento_versao VARCHAR(20),
    data_exclusao DATETIME,
    ativo BOOLEAN DEFAULT 1,
    pontos_fidelidade INTEGER DEFAULT 0
);

CREATE INDEX idx_cliente_nome ON cliente(nome);
CREATE INDEX idx_cliente_telefone ON cliente(telefone);
CREATE INDEX idx_cliente_email ON cliente(email);
CREATE INDEX idx_cliente_ativo ON cliente(ativo);

-- =============================================================================
-- TABELA: CONSENTIMENTO_HISTORICO (Auditoria LGPD)
-- =============================================================================
CREATE TABLE consentimento_historico (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL REFERENCES cliente(id_cliente),
    acao VARCHAR(20) NOT NULL,
    versao_politica VARCHAR(20) NOT NULL DEFAULT 'v1.0',
    data_acao DATETIME DEFAULT CURRENT_TIMESTAMP,
    ip_address VARCHAR(45),
    user_agent VARCHAR(255)
);

-- =============================================================================
-- TABELA: PRODUTO
-- =============================================================================
CREATE TABLE produto (
    id_produto INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_produto VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL,
    estoque_atual INTEGER DEFAULT 0,
    estoque_minimo INTEGER DEFAULT 0,
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_produto_nome ON produto(nome_produto);
CREATE INDEX idx_produto_categoria ON produto(categoria);
CREATE INDEX idx_produto_ativo ON produto(ativo);

-- =============================================================================
-- TABELA: VENDA
-- =============================================================================
CREATE TABLE venda (
    id_venda INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL REFERENCES cliente(id_cliente),
    data_venda DATETIME DEFAULT CURRENT_TIMESTAMP,
    valor_total DECIMAL(10, 2) NOT NULL,
    forma_pagamento VARCHAR(50),
    status_pagamento VARCHAR(50) DEFAULT 'Pendente',
    observacoes TEXT,
    recibo_gerado BOOLEAN DEFAULT 0,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_venda_cliente ON venda(id_cliente);
CREATE INDEX idx_venda_data ON venda(data_venda);
CREATE INDEX idx_venda_status ON venda(status_pagamento);

-- =============================================================================
-- TABELA: ITEM_VENDA
-- =============================================================================
CREATE TABLE item_venda (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venda INTEGER NOT NULL REFERENCES venda(id_venda) ON DELETE CASCADE,
    id_produto INTEGER NOT NULL REFERENCES produto(id_produto),
    quantidade INTEGER NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

CREATE INDEX idx_item_venda ON item_venda(id_venda);
CREATE INDEX idx_item_produto ON item_venda(id_produto);

-- =============================================================================
-- TABELA: PAGAMENTO
-- =============================================================================
CREATE TABLE pagamento (
    id_pagamento INTEGER PRIMARY KEY AUTOINCREMENT,
    id_venda INTEGER NOT NULL REFERENCES venda(id_venda) ON DELETE CASCADE,
    data_pagamento DATETIME DEFAULT CURRENT_TIMESTAMP,
    valor_pago DECIMAL(10, 2) NOT NULL,
    metodo VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'Concluído',
    referencia_transacao VARCHAR(100),
    notas TEXT
);

CREATE INDEX idx_pagamento_venda ON pagamento(id_venda);
CREATE INDEX idx_pagamento_data ON pagamento(data_pagamento);

-- =============================================================================
-- TABELA: LOG_ACAO (Auditoria)
-- =============================================================================
CREATE TABLE log_acao (
    id_log INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER REFERENCES usuario(id_usuario),
    acao VARCHAR(50) NOT NULL,
    entidade VARCHAR(50) NOT NULL,
    id_entidade INTEGER,
    detalhes TEXT,
    ip VARCHAR(45),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: TICKET_SUPORTE
-- =============================================================================
CREATE TABLE ticket_suporte (
    id_ticket INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario),
    assunto VARCHAR(200) NOT NULL,
    categoria VARCHAR(50) NOT NULL DEFAULT 'duvida',
    status VARCHAR(20) NOT NULL DEFAULT 'aberto',
    prioridade VARCHAR(20) NOT NULL DEFAULT 'normal',
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: MENSAGEM_TICKET
-- =============================================================================
CREATE TABLE mensagem_ticket (
    id_mensagem INTEGER PRIMARY KEY AUTOINCREMENT,
    id_ticket INTEGER NOT NULL REFERENCES ticket_suporte(id_ticket) ON DELETE CASCADE,
    id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario),
    conteudo TEXT NOT NULL,
    data_envio DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- DADOS DE TESTE / SEED DATA
-- =============================================================================

-- Inserir clientes de exemplo
INSERT INTO cliente (nome, telefone, email, observacoes, consentimento_lgpd, data_consentimento, ativo) VALUES
('Gabriel da Silva', '1299999001', 'gabriel@email.com', 'Cliente frequente, prefere açaí com granola', 1, datetime('now'), 1),
('Marina Costa', '1299999002', 'marina@email.com', 'Alérgica a amendoim', 1, datetime('now'), 1),
('João Pereira', '1299999003', 'joao@email.com', 'Prefere diabético', 1, datetime('now'), 1),
('Ana Paula', '1299999004', 'ana@email.com', NULL, 1, datetime('now'), 1),
('Carlos Mendes', '1299999005', NULL, 'Compra grandes quantidades para eventos', 1, datetime('now'), 1),
('Paula Rodrigues', '1299999006', 'paula@email.com', 'Cliente nova', 0, NULL, 1);

-- Inserir produtos/sabores
INSERT INTO produto (nome_produto, categoria, descricao, preco, estoque_atual, estoque_minimo, ativo) VALUES
('Açaí com Granola', 'Açaí Premium', 'Açaí puro com granola caseira', 25.00, 50, 10, 1),
('Açaí com Banana', 'Açaí Premium', 'Açaí com banana fatiada', 24.00, 50, 10, 1),
('Açaí Simples', 'Açaí Básico', 'Açaí puro, sem adições', 18.00, 30, 5, 1),
('Açaí Diabético', 'Açaí Especial', 'Açaí com adoçante, sem açúcar', 22.00, 20, 5, 1),
('Açaí Festa (500ml)', 'Açaí Grande', 'Porção grande para compartilhar', 35.00, 15, 3, 1),
('Suco Natural - Laranja', 'Bebidas', 'Suco de laranja natural', 8.00, 40, 10, 1),
('Suco Natural - Morango', 'Bebidas', 'Suco de morango natural', 10.00, 40, 10, 1),
('Água', 'Bebidas', 'Água mineral', 3.00, 100, 20, 1),
('Refrigerante', 'Bebidas', 'Refrigerante 350ml', 5.00, 80, 15, 1),
('Granola Extra', 'Adicionais', 'Granola caseira extra', 5.00, 60, 10, 1);

-- Inserir vendas de exemplo (últimos 10 dias)
INSERT INTO venda (id_cliente, data_venda, valor_total, forma_pagamento, status_pagamento, recibo_gerado) VALUES
(1, datetime('now', '-10 days'), 25.00, 'Dinheiro', 'Concluído', 1),
(2, datetime('now', '-9 days'), 49.00, 'Débito', 'Concluído', 1),
(3, datetime('now', '-8 days'), 22.00, 'Dinheiro', 'Concluído', 1),
(1, datetime('now', '-7 days'), 35.00, 'Crédito', 'Concluído', 1),
(4, datetime('now', '-6 days'), 30.00, 'Dinheiro', 'Concluído', 1),
(5, datetime('now', '-5 days'), 105.00, 'Dinheiro', 'Concluído', 1),
(1, datetime('now', '-4 days'), 25.00, 'Dinheiro', 'Concluído', 1),
(2, datetime('now', '-3 days'), 34.00, 'Débito', 'Concluído', 1),
(3, datetime('now', '-2 days'), 50.00, 'Crédito', 'Concluído', 1),
(4, datetime('now', '-1 days'), 72.00, 'Dinheiro', 'Concluído', 1);

-- Inserir itens de venda
INSERT INTO item_venda (id_venda, id_produto, quantidade, preco_unitario, subtotal) VALUES
(1, 1, 1, 25.00, 25.00),
(2, 1, 1, 25.00, 25.00),
(2, 6, 1, 8.00, 8.00),
(2, 10, 1, 5.00, 5.00),
(3, 4, 1, 22.00, 22.00),
(4, 1, 1, 25.00, 25.00),
(4, 5, 1, 35.00, 35.00),
(5, 1, 2, 25.00, 50.00),
(5, 7, 1, 10.00, 10.00),
(5, 10, 1, 5.00, 5.00),
(6, 1, 3, 25.00, 75.00),
(6, 2, 2, 24.00, 48.00),
(6, 9, 2, 5.00, 10.00),
(7, 3, 1, 18.00, 18.00),
(7, 9, 1, 5.00, 5.00),
(7, 8, 1, 3.00, 3.00),
(8, 1, 1, 25.00, 25.00),
(8, 7, 1, 10.00, 10.00),
(9, 2, 2, 24.00, 48.00),
(9, 10, 1, 5.00, 5.00),
(10, 1, 2, 25.00, 50.00),
(10, 10, 2, 5.00, 10.00),
(10, 6, 1, 8.00, 8.00),
(10, 8, 1, 3.00, 3.00);

-- Inserir pagamentos
INSERT INTO pagamento (id_venda, data_pagamento, valor_pago, metodo, status, referencia_transacao) VALUES
(1, datetime('now', '-10 days'), 25.00, 'Dinheiro', 'Concluído', 'CASH-001'),
(2, datetime('now', '-9 days'), 49.00, 'Débito', 'Concluído', 'DEBIT-001'),
(3, datetime('now', '-8 days'), 22.00, 'Dinheiro', 'Concluído', 'CASH-002'),
(4, datetime('now', '-7 days'), 35.00, 'Crédito', 'Concluído', 'CREDIT-001'),
(5, datetime('now', '-6 days'), 30.00, 'Dinheiro', 'Concluído', 'CASH-003'),
(6, datetime('now', '-5 days'), 105.00, 'Dinheiro', 'Concluído', 'CASH-004'),
(7, datetime('now', '-4 days'), 25.00, 'Dinheiro', 'Concluído', 'CASH-005'),
(8, datetime('now', '-3 days'), 34.00, 'Débito', 'Concluído', 'DEBIT-002'),
(9, datetime('now', '-2 days'), 50.00, 'Crédito', 'Concluído', 'CREDIT-002'),
(10, datetime('now', '-1 days'), 72.00, 'Dinheiro', 'Concluído', 'CASH-006');

-- =============================================================================
-- VIEWS ÚTEIS PARA RELACIONAMENTO E ANÁLISES
-- =============================================================================

-- View: Vendas com dados de cliente
CREATE VIEW IF NOT EXISTS vw_vendas_com_cliente AS
SELECT
    v.id_venda,
    v.data_venda,
    c.nome AS cliente_nome,
    c.telefone,
    c.email,
    v.valor_total,
    v.forma_pagamento,
    v.status_pagamento
FROM venda v
JOIN cliente c ON v.id_cliente = c.id_cliente
WHERE c.ativo = 1;

-- View: Itens de venda com detalhes de produto
CREATE VIEW IF NOT EXISTS vw_itens_venda_detalhado AS
SELECT
    iv.id_item,
    iv.id_venda,
    p.nome_produto,
    p.categoria,
    iv.quantidade,
    iv.preco_unitario,
    iv.subtotal
FROM item_venda iv
JOIN produto p ON iv.id_produto = p.id_produto;

-- View: Total de vendas por cliente (análise de fidelização)
CREATE VIEW IF NOT EXISTS vw_clientes_frequencia AS
SELECT
    c.id_cliente,
    c.nome,
    c.telefone,
    COUNT(v.id_venda) AS total_compras,
    COALESCE(SUM(v.valor_total), 0) AS faturamento_total,
    MAX(v.data_venda) AS ultima_compra,
    ROUND(COALESCE(AVG(v.valor_total), 0), 2) AS ticket_medio
FROM cliente c
LEFT JOIN venda v ON c.id_cliente = v.id_cliente
WHERE c.ativo = 1
GROUP BY c.id_cliente, c.nome, c.telefone
ORDER BY total_compras DESC;

-- View: Produtos mais vendidos
CREATE VIEW IF NOT EXISTS vw_produtos_ranking AS
SELECT
    p.id_produto,
    p.nome_produto,
    p.categoria,
    COUNT(iv.id_item) AS quantidade_vendida,
    COALESCE(SUM(iv.subtotal), 0) AS faturamento,
    ROUND(COALESCE(AVG(iv.preco_unitario), 0), 2) AS preco_medio
FROM produto p
LEFT JOIN item_venda iv ON p.id_produto = iv.id_produto
WHERE p.ativo = 1
GROUP BY p.id_produto, p.nome_produto, p.categoria
ORDER BY quantidade_vendida DESC;

-- View: Faturamento por dia
CREATE VIEW IF NOT EXISTS vw_faturamento_diario AS
SELECT
    DATE(v.data_venda) AS data,
    COUNT(v.id_venda) AS total_vendas,
    SUM(v.valor_total) AS faturamento_dia,
    ROUND(AVG(v.valor_total), 2) AS ticket_medio
FROM venda v
GROUP BY DATE(v.data_venda)
ORDER BY data DESC;

-- =============================================================================
-- FIM DO SCHEMA
-- =============================================================================
-- Última atualização: 2026
-- Status: v2.0 - Schema completo compatível com SQLite, incluindo tabelas de
--         usuários, suporte, auditoria e fidelidade.
