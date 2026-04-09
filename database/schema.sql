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
-- Ordem inversa de dependência para evitar FK violations
DROP TABLE IF EXISTS item_venda_complemento;
DROP TABLE IF EXISTS combo_kit_item;
DROP TABLE IF EXISTS assinatura_cliente;
DROP TABLE IF EXISTS item_compra;
DROP TABLE IF EXISTS mensagem_ticket;
DROP TABLE IF EXISTS ticket_suporte;
DROP TABLE IF EXISTS log_acao;
DROP TABLE IF EXISTS consentimento_historico;
DROP TABLE IF EXISTS badge_cliente;
DROP TABLE IF EXISTS two_factor_secret;
DROP TABLE IF EXISTS indicacao;
DROP TABLE IF EXISTS lancamento_financeiro;
DROP TABLE IF EXISTS webhook_config;
DROP TABLE IF EXISTS pagamento;
DROP TABLE IF EXISTS item_venda;
DROP TABLE IF EXISTS venda;
DROP TABLE IF EXISTS complemento;
DROP TABLE IF EXISTS compra_estoque;
DROP TABLE IF EXISTS fornecedor;
DROP TABLE IF EXISTS cupom_desconto;
DROP TABLE IF EXISTS combo_kit;
DROP TABLE IF EXISTS assinatura;
DROP TABLE IF EXISTS loja;
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

CREATE INDEX idx_usuario_email ON usuario(email);

-- =============================================================================
-- TABELA: CLIENTE
-- =============================================================================
CREATE TABLE cliente (
    id_cliente INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(150) NOT NULL,
    telefone VARCHAR(20),
    email VARCHAR(100),
    senha_hash VARCHAR(256),
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
    volume VARCHAR(20),
    estoque_atual INTEGER DEFAULT 0,
    estoque_minimo INTEGER DEFAULT 0,
    preco_promocional DECIMAL(10, 2),
    foto_url VARCHAR(500),
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_produto_nome ON produto(nome_produto);
CREATE INDEX idx_produto_categoria ON produto(categoria);
CREATE INDEX idx_produto_ativo ON produto(ativo);

-- =============================================================================
-- TABELA: COMPLEMENTO (toppings para self-service)
-- =============================================================================
CREATE TABLE complemento (
    id_complemento INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(100) NOT NULL,
    categoria VARCHAR(50),
    unidade_medida VARCHAR(30),
    preco_adicional DECIMAL(10, 2) DEFAULT 0,
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

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
    status_pedido VARCHAR(30) DEFAULT 'Recebido',
    observacoes TEXT,
    motivo_cancelamento TEXT,
    desconto_aplicado DECIMAL(10, 2) DEFAULT 0,
    data_agendamento DATETIME,
    recibo_gerado BOOLEAN DEFAULT 0,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_venda_cliente ON venda(id_cliente);
CREATE INDEX idx_venda_data ON venda(data_venda);
CREATE INDEX idx_venda_status ON venda(status_pagamento);
CREATE INDEX ix_venda_data_status ON venda(data_venda, status_pagamento);

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
-- TABELA: ITEM_VENDA_COMPLEMENTO
-- =============================================================================
CREATE TABLE item_venda_complemento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_item INTEGER NOT NULL REFERENCES item_venda(id_item) ON DELETE CASCADE,
    id_complemento INTEGER NOT NULL REFERENCES complemento(id_complemento),
    preco_unitario DECIMAL(10, 2) DEFAULT 0
);

CREATE INDEX idx_ivc_item ON item_venda_complemento(id_item);
CREATE INDEX idx_ivc_complemento ON item_venda_complemento(id_complemento);

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
    id_usuario INTEGER REFERENCES usuario(id_usuario) ON DELETE SET NULL,
    acao VARCHAR(50) NOT NULL,
    entidade VARCHAR(50) NOT NULL,
    id_entidade INTEGER,
    detalhes TEXT,
    ip VARCHAR(45),
    data_hora DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX ix_log_data_entidade ON log_acao(data_hora, entidade);

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
-- TABELA: FORNECEDOR
-- =============================================================================
CREATE TABLE fornecedor (
    id_fornecedor INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(200) NOT NULL,
    cnpj VARCHAR(18) UNIQUE,
    telefone VARCHAR(20),
    email VARCHAR(150),
    endereco TEXT,
    observacoes TEXT,
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: COMPRA_ESTOQUE
-- =============================================================================
CREATE TABLE compra_estoque (
    id_compra INTEGER PRIMARY KEY AUTOINCREMENT,
    id_fornecedor INTEGER NOT NULL REFERENCES fornecedor(id_fornecedor),
    data_compra DATETIME DEFAULT CURRENT_TIMESTAMP,
    valor_total DECIMAL(10, 2) NOT NULL DEFAULT 0,
    nota_fiscal VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Pendente',
    observacoes TEXT,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_compra_fornecedor ON compra_estoque(id_fornecedor);
CREATE INDEX idx_compra_data ON compra_estoque(data_compra);

-- =============================================================================
-- TABELA: ITEM_COMPRA
-- =============================================================================
CREATE TABLE item_compra (
    id_item INTEGER PRIMARY KEY AUTOINCREMENT,
    id_compra INTEGER NOT NULL REFERENCES compra_estoque(id_compra) ON DELETE CASCADE,
    id_produto INTEGER NOT NULL REFERENCES produto(id_produto),
    quantidade INTEGER NOT NULL,
    preco_unitario DECIMAL(10, 2) NOT NULL,
    subtotal DECIMAL(10, 2) NOT NULL
);

CREATE INDEX idx_item_compra ON item_compra(id_compra);

-- =============================================================================
-- TABELA: CUPOM_DESCONTO
-- =============================================================================
CREATE TABLE cupom_desconto (
    id_cupom INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo VARCHAR(30) UNIQUE NOT NULL,
    descricao VARCHAR(200),
    tipo_desconto VARCHAR(20) NOT NULL DEFAULT 'percentual',
    valor_desconto DECIMAL(10, 2) NOT NULL,
    valor_minimo_pedido DECIMAL(10, 2) DEFAULT 0,
    usos_maximos INTEGER DEFAULT 0,
    usos_realizados INTEGER DEFAULT 0,
    ativo BOOLEAN DEFAULT 1,
    data_inicio DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_fim DATETIME,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_cupom_codigo ON cupom_desconto(codigo);

-- =============================================================================
-- TABELA: BADGE_CLIENTE (gamificação)
-- =============================================================================
CREATE TABLE badge_cliente (
    id_badge INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente INTEGER NOT NULL REFERENCES cliente(id_cliente),
    codigo VARCHAR(50) NOT NULL,
    nome VARCHAR(100) NOT NULL,
    descricao VARCHAR(200),
    icone VARCHAR(10) DEFAULT '🏅',
    data_conquista DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_badge_cliente ON badge_cliente(id_cliente);

-- =============================================================================
-- TABELA: LANCAMENTO_FINANCEIRO (receitas / despesas manuais)
-- =============================================================================
CREATE TABLE lancamento_financeiro (
    id_lancamento INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo VARCHAR(20) NOT NULL,
    categoria VARCHAR(100) NOT NULL,
    descricao VARCHAR(300),
    valor DECIMAL(10, 2) NOT NULL,
    data_lancamento DATE NOT NULL,
    forma_pagamento VARCHAR(50),
    status VARCHAR(30) DEFAULT 'Pago',
    comprovante VARCHAR(100),
    observacoes TEXT,
    id_usuario INTEGER REFERENCES usuario(id_usuario),
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP,
    data_atualizacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_lanc_tipo ON lancamento_financeiro(tipo);
CREATE INDEX idx_lanc_data ON lancamento_financeiro(data_lancamento);
CREATE INDEX ix_lanc_data_tipo ON lancamento_financeiro(data_lancamento, tipo);

-- =============================================================================
-- TABELA: TWO_FACTOR_SECRET (2FA)
-- =============================================================================
CREATE TABLE two_factor_secret (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_usuario INTEGER NOT NULL UNIQUE REFERENCES usuario(id_usuario),
    secret VARCHAR(32) NOT NULL,
    ativo BOOLEAN DEFAULT 0,
    data_ativacao DATETIME
);

-- =============================================================================
-- TABELA: COMBO_KIT
-- =============================================================================
CREATE TABLE combo_kit (
    id_combo INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(150) NOT NULL,
    descricao TEXT,
    preco_combo DECIMAL(10, 2) NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: COMBO_KIT_ITEM
-- =============================================================================
CREATE TABLE combo_kit_item (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_combo INTEGER NOT NULL REFERENCES combo_kit(id_combo) ON DELETE CASCADE,
    id_produto INTEGER NOT NULL REFERENCES produto(id_produto),
    quantidade INTEGER DEFAULT 1
);

-- =============================================================================
-- TABELA: INDICACAO (programa de referral)
-- =============================================================================
CREATE TABLE indicacao (
    id_indicacao INTEGER PRIMARY KEY AUTOINCREMENT,
    id_cliente_indicador INTEGER NOT NULL REFERENCES cliente(id_cliente),
    id_cliente_indicado INTEGER REFERENCES cliente(id_cliente),
    codigo_indicacao VARCHAR(20) NOT NULL,
    bonus_concedido BOOLEAN DEFAULT 0,
    data_indicacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_indicacao_codigo ON indicacao(codigo_indicacao);

-- =============================================================================
-- TABELA: ASSINATURA (planos mensais)
-- =============================================================================
CREATE TABLE assinatura (
    id_assinatura INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_plano VARCHAR(100) NOT NULL,
    descricao TEXT,
    preco_mensal DECIMAL(10, 2) NOT NULL,
    limite_usos INTEGER DEFAULT 10,
    ativo BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: ASSINATURA_CLIENTE
-- =============================================================================
CREATE TABLE assinatura_cliente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    id_assinatura INTEGER NOT NULL REFERENCES assinatura(id_assinatura),
    id_cliente INTEGER NOT NULL REFERENCES cliente(id_cliente),
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    usos_realizados INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'ativa',
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: WEBHOOK_CONFIG
-- =============================================================================
CREATE TABLE webhook_config (
    id_webhook INTEGER PRIMARY KEY AUTOINCREMENT,
    evento VARCHAR(50) NOT NULL,
    url VARCHAR(500) NOT NULL,
    ativo BOOLEAN DEFAULT 1,
    secret VARCHAR(64),
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- =============================================================================
-- TABELA: LOJA (multi-unidade)
-- =============================================================================
CREATE TABLE loja (
    id_loja INTEGER PRIMARY KEY AUTOINCREMENT,
    nome VARCHAR(150) NOT NULL,
    endereco TEXT,
    telefone VARCHAR(20),
    cnpj VARCHAR(18),
    ativa BOOLEAN DEFAULT 1,
    data_criacao DATETIME DEFAULT CURRENT_TIMESTAMP
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

-- Inserir complementos
INSERT INTO complemento (nome, categoria, unidade_medida, preco_adicional, ativo) VALUES
('Granola', 'Farináceo', 'g', 2.00, 1),
('Leite Condensado', 'Calda', 'ml', 3.00, 1),
('Morango', 'Fruta', 'unidade', 2.50, 1),
('Banana', 'Fruta', 'unidade', 1.50, 1),
('Leite em Pó', 'Extra', 'g', 2.00, 1);

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
-- Status: v3.0 - Schema completo sincronizado com models.py (26 tabelas),
--         incluindo complementos, combos, assinaturas, indicações, cupons,
--         financeiro, 2FA, webhooks, multi-loja e gamificação.
