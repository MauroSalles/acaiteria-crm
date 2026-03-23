# 📊 Modelo Entidade-Relacionamento (MER)

## Diagrama Crow's Foot (Notação)

```
CLIENTE ||--o{ VENDA
VENDA ||--o{ ITEM_VENDA
PRODUTO ||--o{ ITEM_VENDA
VENDA ||--|| PAGAMENTO
```

### Legenda:
- `||` = Um (One)
- `o{` = Muitos (Many)
- `--` = Relacionamento obrigatório
- `o-` = Relacionamento opcional

---

## Entidades e Atributos

### 1. CLIENTE
Armazena informações dos clientes da açaiteria.

| Atributo | Tipo | Restrições | Descrição |
|----------|------|-----------|-----------|
| **id_cliente** | INT | PK, AI | Chave primária (auto-incremento) |
| nome | VARCHAR(150) | NOT NULL | Nome completo do cliente |
| telefone | VARCHAR(20) | NULL | Telefone para contato |
| email | VARCHAR(100) | NULL | E-mail para comunicação |
| data_cadastro | DATETIME | DEFAULT CURRENT_TIMESTAMP | Data de criação do registro |
| observacoes | TEXT | NULL | Anotações (alergias, preferências) |
| consentimento_lgpd | BOOLEAN | DEFAULT FALSE | Consentimento explícito para LGPD |
| data_consentimento | DATETIME | NULL | Data/hora do consentimento |
| data_exclusao | DATETIME | NULL | Data de anonimização (LGPD) |
| ativo | BOOLEAN | DEFAULT TRUE | Status do cliente |

**Índices:**
- `idx_cliente_nome` (nome) - Para buscas rápidas
- `idx_cliente_telefone` (telefone) - Para identificação por telefone
- `idx_cliente_email` (email) - Para busca por e-mail
- `idx_cliente_ativo` (ativo) - Para filtros de ativos/inativos

---

### 2. PRODUTO
Catálogo de sabores e bebidas oferecidas.

| Atributo | Tipo | Restrições | Descrição |
|----------|------|-----------|-----------|
| **id_produto** | INT | PK, AI | Chave primária |
| nome_produto | VARCHAR(100) | NOT NULL | Nome do produto/sabor |
| categoria | VARCHAR(50) | NULL | Categoria (Açaí Premium, Bebidas, etc) |
| descricao | TEXT | NULL | Descrição detalhada |
| preco | DECIMAL(10,2) | NOT NULL | Preço unitário |
| ativo | BOOLEAN | DEFAULT TRUE | Disponível para venda |
| data_criacao | DATETIME | DEFAULT CURRENT_TIMESTAMP | Data de criação |
| data_atualizacao | DATETIME | DEFAULT CURRENT_TIMESTAMP | Última modificação |

**Índices:**
- `idx_produto_nome` (nome_produto)
- `idx_produto_categoria` (categoria)
- `idx_produto_ativo` (ativo)

---

### 3. VENDA
Registro principal de cada transação de venda.

| Atributo | Tipo | Restrições | Descrição |
|----------|------|-----------|-----------|
| **id_venda** | INT | PK, AI | Chave primária |
| **id_cliente** | INT | FK | Chave estrangeira para CLIENTE |
| data_venda | DATETIME | DEFAULT CURRENT_TIMESTAMP | Data/hora da venda |
| valor_total | DECIMAL(10,2) | NOT NULL | Valor final com descontos/taxas |
| forma_pagamento | VARCHAR(50) | NULL | Dinheiro, Débito, Crédito, PIX |
| status_pagamento | VARCHAR(50) | DEFAULT 'Pendente' | Pendente, Concluído |
| observacoes | TEXT | NULL | Observações da venda |
| recibo_gerado | BOOLEAN | DEFAULT FALSE | Recibo foi emitido |
| data_atualizacao | DATETIME | DEFAULT CURRENT_TIMESTAMP | Última modificação |

**Índices:**
- `idx_venda_cliente` (id_cliente)
- `idx_venda_data` (data_venda)
- `idx_venda_status` (status_pagamento)

**Constraints:**
- FK: id_cliente REFERENCES CLIENTE(id_cliente) ON DELETE RESTRICT

---

### 4. ITEM_VENDA
Detalhamento dos produtos em cada venda (linhas).

| Atributo | Tipo | Restrições | Descrição |
|----------|------|-----------|-----------|
| **id_item** | INT | PK, AI | Chave primária |
| **id_venda** | INT | FK | Chave estrangeira para VENDA |
| **id_produto** | INT | FK | Chave estrangeira para PRODUTO |
| quantidade | INT | NOT NULL | Quantidade do produto |
| preco_unitario | DECIMAL(10,2) | NOT NULL | Preço no momento da venda |
| subtotal | DECIMAL(10,2) | NOT NULL | quantidade × preco_unitario |

**Índices:**
- `idx_item_venda` (id_venda)
- `idx_item_produto` (id_produto)

**Constraints:**
- FK: id_venda REFERENCES VENDA(id_venda) ON DELETE CASCADE
- FK: id_produto REFERENCES PRODUTO(id_produto) ON DELETE RESTRICT

---

### 5. PAGAMENTO
Detalhes de como a venda foi paga.

| Atributo | Tipo | Restrições | Descrição |
|----------|------|-----------|-----------|
| **id_pagamento** | INT | PK, AI | Chave primária |
| **id_venda** | INT | FK | Chave estrangeira para VENDA |
| data_pagamento | DATETIME | DEFAULT CURRENT_TIMESTAMP | Data/hora do pagamento |
| valor_pago | DECIMAL(10,2) | NOT NULL | Valor efetivamente pago |
| metodo | VARCHAR(50) | NOT NULL | Método (Dinheiro, Débito, Crédito, PIX) |
| status | VARCHAR(50) | DEFAULT 'Concluído' | Concluído, Pendente, Falha |
| referencia_transacao | VARCHAR(100) | NULL | Número transação (cartão, PIX) |
| notas | TEXT | NULL | Observações |

**Índices:**
- `idx_pagamento_venda` (id_venda)
- `idx_pagamento_data` (data_pagamento)
- `idx_pagamento_metodo` (metodo)

**Constraints:**
- FK: id_venda REFERENCES VENDA(id_venda) ON DELETE CASCADE

---

## Relacionamentos

### CLIENTE → VENDA (1:N)
- **Cardinalidade:** Um cliente pode ter muitas vendas
- **Tipo:** Obrigatório (não existe venda sem cliente)
- **Ação ao deletar:** RESTRICT (não permite deletar cliente com vendas)

### VENDA → ITEM_VENDA (1:N)
- **Cardinalidade:** Uma venda pode ter muitos itens
- **Tipo:** Obrigatório (todo item pertence a uma venda)
- **Ação ao deletar:** CASCADE (deleta itens quando venda é deletada)

### PRODUTO → ITEM_VENDA (1:N)
- **Cardinalidade:** Um produto pode estar em muitos itens
- **Tipo:** Obrigatório (todo item referencia um produto)
- **Ação ao deletar:** RESTRICT (não permite deletar produto em uso)

### VENDA → PAGAMENTO (1:1)
- **Cardinalidade:** Uma venda tem exatamente um pagamento
- **Tipo:** Obrigatório
- **Ação ao deletar:** CASCADE (deleta pagamento com a venda)

---

## Views (Consultas Úteis)

### vw_vendas_com_cliente
Mostra vendas com dados do cliente

### vw_itens_venda_detalhado
Lista itens com nome do produto

### vw_clientes_frequencia
Análise de fidelização por cliente

### vw_produtos_ranking
Ranking de produtos mais vendidos

### vw_faturamento_diario
Consolidação diária de faturamento

---

## Normalização

### 3ª Forma Normal (3FN)

✅ **1FN (Atomicidade)**
- Todos os valores são atômicos
- Sem atributos multivalorados

✅ **2FN (Dependência Parcial)**
- Toda coluna não-chave depende da chave primária
- Sem subconjuntos de dados repetidos

✅ **3FN (Dependência Transitiva)**
- Nenhum atributo não-chave depende de outro atributo não-chave
- Estrutura limpa e eficiente

---

## Exemplo de Queries SQL Típicas

### Vendas de um cliente
```sql
SELECT v.id_venda, v.data_venda, v.valor_total
FROM VENDA v
WHERE v.id_cliente = 1
ORDER BY v.data_venda DESC;
```

### Produtos de uma venda
```sql
SELECT p.nome_produto, iv.quantidade, iv.subtotal
FROM ITEM_VENDA iv
JOIN PRODUTO p ON iv.id_produto = p.id_produto
WHERE iv.id_venda = 5;
```

### Clientes frequentes (últimos 30 dias)
```sql
SELECT c.nome, COUNT(v.id_venda) as total_compras
FROM CLIENTE c
JOIN VENDA v ON c.id_cliente = v.id_cliente
WHERE v.data_venda >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY c.id_cliente
ORDER BY total_compras DESC;
```

### Faturamento diário
```sql
SELECT DATE(data_venda) as data, 
       COUNT(*) as total_vendas,
       SUM(valor_total) as faturamento
FROM VENDA
GROUP BY DATE(data_venda)
ORDER BY data DESC;
```

---

## Tabela de Proporções Esperadas

| Tabela | Volume Mensal | Volume Anual | Crescimento |
|--------|---------------|---|---|
| CLIENTE | 20-30 novos | 240-360 | 5-10% |
| VENDA | 200-300 | 2400-3600 | Sazonal |
| ITEM_VENDA | 400-600 | 4800-7200 | Sazonal |
| PRODUTO | 0-2 novos | 0-24 | Baixo |
| PAGAMENTO | 200-300 | 2400-3600 | Sazonal |

---

## Backup e Recuperação

### Estratégia
- **Frequência:** Diária (após fechamento de caixa)
- **Retenção:** 2 anos de backups
- **Teste:** Restauração mensal para validar

### SQL para Backup
```bash
mysqldump -u usuario -p acaiteria_db > backup_$(date +%Y%m%d).sql
```

### SQL para Restauração
```bash
mysql -u usuario -p acaiteria_db < backup_20260310.sql
```

---

## Considerações de Performance

### Índices Criados
- ✅ Todas as chaves estrangeiras indexadas
- ✅ Campos de busca frequente indexados
- ✅ Campos de filtro indexados

### Tamanho Estimado (1 ano)
- CLIENTE: ~360 registros (~50 KB)
- VENDA: ~3600 registros (~360 KB)
- ITEM_VENDA: ~7200 registros (~720 KB)
- PRODUTO: ~20 registros (~5 KB)
- PAGAMENTO: ~3600 registros (~360 KB)

**Total:** ~1.5 MB (muito compacto)

---

## Extensões Futuras (v2.0)

Possíveis melhorias do modelo:

### TABELA: USUARIO
Para gerenciam de acesso

### TABELA: CATEGORIA_PRODUTO
Para melhor organização de produtos

### TABELA: DESCONTO
Para programas de promoção estruturado

### TABELA: FEEDBACK_CLIENTE
Para coletas de avaliações

### TABELA: AUDITORIA
Para rastreamento completo de mudanças

---

**MER Versão:** 1.0  
**Data:** 10 de março de 2026  
**Status:** Validado e em produção ✅
