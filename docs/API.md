# 📚 DOCUMENTAÇÃO DE API - Açaiteria CRM

## Base URL

```
http://localhost:5000/api
```

---

## 🔐 Clientes

### 📋 Listar Clientes

**GET** `/api/clientes`

Retorna lista de todos os clientes ativos.

**Resposta (200):**
```json
[
  {
    "id_cliente": 1,
    "nome": "Gabriel da Silva",
    "telefone": "1299999001",
    "email": "gabriel@email.com",
    "data_cadastro": "2026-03-10T10:00:00",
    "observacoes": "Cliente frequente",
    "consentimento_lgpd": true,
    "ativo": true
  }
]
```

---

### ➕ Criar Cliente

**POST** `/api/clientes`

Cria um novo cliente com consentimento LGPD.

**Body:**
```json
{
  "nome": "João Silva",
  "telefone": "(12) 99999-9999",
  "email": "joao@email.com",
  "observacoes": "Alérgico a amendoim",
  "consentimento_lgpd": true
}
```

**Resposta (201):**
```json
{
  "id_cliente": 7,
  "nome": "João Silva",
  "telefone": "(12) 99999-9999",
  "email": "joao@email.com",
  "data_cadastro": "2026-03-10T15:30:00",
  "consentimento_lgpd": true,
  "ativo": true
}
```

---

### 👤 Obter Cliente

**GET** `/api/clientes/:id_cliente`

Retorna detalhes de um cliente específico com histórico de vendas.

**Resposta (200):**
```json
{
  "id_cliente": 1,
  "nome": "Gabriel da Silva",
  "telefone": "1299999001",
  "email": "gabriel@email.com",
  "total_vendas": 5,
  "faturamento_total": 150.50,
  "ativo": true
}
```

---

### ✏️ Atualizar Cliente

**PUT** `/api/clientes/:id_cliente`

Atualiza dados de um cliente.

**Body:**
```json
{
  "nome": "Gabriel da Silva",
  "telefone": "(12) 99999-0001",
  "email": "gabriel.new@email.com",
  "observacoes": "Atualizado em 10/03/2026"
}
```

---

### 🗑️ Deletar Cliente (LGPD)

**DELETE** `/api/clientes/:id_cliente`

Anonimiza e desativa um cliente (direito ao esquecimento - LGPD).

**Resposta (200):**
```json
{
  "mensagem": "Cliente anonimizado conforme LGPD"
}
```

---

## 🛍️ Produtos

### 📋 Listar Produtos

**GET** `/api/produtos`

Retorna lista de todos os produtos ativos.

**Resposta (200):**
```json
[
  {
    "id_produto": 1,
    "nome_produto": "Açaí com Granola",
    "categoria": "Açaí Premium",
    "descricao": "Açaí puro com granola caseira",
    "preco": 25.00,
    "ativo": true
  }
]
```

---

### ➕ Criar Produto

**POST** `/api/produtos`

Cria um novo produto.

**Body:**
```json
{
  "nome_produto": "Açaí Especial",
  "categoria": "Açaí Premium",
  "descricao": "Novo sabor",
  "preco": 28.50
}
```

**Resposta (201):**
```json
{
  "id_produto": 11,
  "nome_produto": "Açaí Especial",
  "categoria": "Açaí Premium",
  "preco": 28.50,
  "ativo": true
}
```

---

## 🛒 Vendas

### 📋 Listar Vendas

**GET** `/api/vendas`

Retorna todas as vendas registradas.

**Resposta (200):**
```json
[
  {
    "id_venda": 1,
    "id_cliente": 1,
    "cliente_nome": "Gabriel da Silva",
    "data_venda": "2026-03-10T14:30:00",
    "valor_total": 50.00,
    "forma_pagamento": "Dinheiro",
    "status_pagamento": "Concluído",
    "itens": [
      {
        "id_item": 1,
        "id_produto": 1,
        "produto_nome": "Açaí com Granola",
        "quantidade": 2,
        "preco_unitario": 25.00,
        "subtotal": 50.00
      }
    ]
  }
]
```

---

### ➕ Criar Venda

**POST** `/api/vendas`

Cria uma nova venda com itens.

**Body:**
```json
{
  "id_cliente": 1,
  "forma_pagamento": "Débito",
  "observacoes": "Entrega no local",
  "itens": [
    {
      "id_produto": 1,
      "quantidade": 2
    },
    {
      "id_produto": 6,
      "quantidade": 1
    }
  ]
}
```

**Resposta (201):**
```json
{
  "id_venda": 11,
  "id_cliente": 1,
  "cliente_nome": "Gabriel da Silva",
  "data_venda": "2026-03-10T15:45:00",
  "valor_total": 58.00,
  "forma_pagamento": "Débito",
  "status_pagamento": "Concluído",
  "itens": [...]
}
```

---

### 📄 Obter Venda

**GET** `/api/vendas/:id_venda`

Retorna detalhes de uma venda específica.

**Resposta (200):**
```json
{
  "id_venda": 11,
  "id_cliente": 1,
  "cliente_nome": "Gabriel da Silva",
  "data_venda": "2026-03-10T15:45:00",
  "valor_total": 58.00,
  "forma_pagamento": "Débito",
  "status_pagamento": "Concluído",
  "itens": [...]
}
```

---

## 📊 Relatórios

### 📅 Vendas do Dia Atual

**GET** `/api/relatorios/dia-atual`

Retorna estatísticas de vendas do dia.

**Resposta (200):**
```json
{
  "data": "2026-03-10",
  "total_vendas": 5,
  "faturamento_total": 250.50,
  "ticket_medio": 50.10,
  "por_forma_pagamento": {
    "Dinheiro": 150.00,
    "Débito": 100.50
  }
}
```

---

### 👥 Clientes Mais Frequentes

**GET** `/api/relatorios/clientes-frequentes`

Retorna top 10 clientes dos últimos 30 dias.

**Resposta (200):**
```json
[
  {
    "id_cliente": 1,
    "nome": "Gabriel da Silva",
    "telefone": "1299999001",
    "total_compras": 5,
    "faturamento": 150.50,
    "ultima_compra": "2026-03-10T14:30:00"
  },
  {
    "id_cliente": 2,
    "nome": "Marina Costa",
    "telefone": "1299999002",
    "total_compras": 3,
    "faturamento": 98.00,
    "ultima_compra": "2026-03-09T16:00:00"
  }
]
```

---

### 🏆 Produtos Ranking

**GET** `/api/relatorios/produtos-ranking`

Retorna produtos mais vendidos.

**Resposta (200):**
```json
[
  {
    "id_produto": 1,
    "nome_produto": "Açaí com Granola",
    "quantidade_vendida": 15,
    "faturamento": 375.00
  },
  {
    "id_produto": 3,
    "nome_produto": "Açaí Simples",
    "quantidade_vendida": 8,
    "faturamento": 144.00
  }
]
```

---

## 📥 Exportação

### 📄 Exportar Clientes em CSV

**GET** `/api/exportar/clientes-csv`

Faz download de lista de clientes em formato CSV.

**Resposta:** Arquivo CSV
```
Nome,Telefone,Email,Data de Cadastro
Gabriel da Silva,1299999001,gabriel@email.com,2026-03-10
Marina Costa,1299999002,marina@email.com,2026-03-10
```

---

## 🔄 Códigos HTTP

| Código | Significado | Exemplo |
|--------|-----------|---------|
| 200 | OK - Sucesso | GET, PUT bem-sucedidos |
| 201 | Created - Criado com sucesso | POST bem-sucedido |
| 400 | Bad Request - Requisição inválida | Dados faltando |
| 404 | Not Found - Não encontrado | Cliente inexistente |
| 500 | Server Error - Erro do servidor | Erro no banco de dados |

---

## 📋 Exemplo de Fluxo Completo

### 1. Criar cliente
```bash
POST /api/clientes
{
  "nome": "João Silva",
  "telefone": "(12) 99999-9999",
  "email": "joao@email.com",
  "consentimento_lgpd": true
}
```

### 2. Listar produtos
```bash
GET /api/produtos
```

### 3. Criar venda
```bash
POST /api/vendas
{
  "id_cliente": 7,
  "forma_pagamento": "Dinheiro",
  "itens": [
    {"id_produto": 1, "quantidade": 1}
  ]
}
```

### 4. Consultar relatório
```bash
GET /api/relatorios/dia-atual
GET /api/relatorios/clientes-frequentes
```

---

## 🛠️ Testando a API

### Usando curl

```bash
# Listar clientes
curl http://localhost:5000/api/clientes

# Criar cliente
curl -X POST http://localhost:5000/api/clientes \
  -H "Content-Type: application/json" \
  -d '{
    "nome": "João Silva",
    "telefone": "(12) 99999-9999",
    "email": "joao@email.com",
    "consentimento_lgpd": true
  }'
```

### Usando Insomnia ou Postman

1. Importe a coleção de endpoints
2. Configure Base URL: `http://localhost:5000/api`
3. Teste cada endpoint

---

## 📝 Notas Importantes

- Todas as datas estão em formato ISO 8601 (UTC)
- Valores monetários em BRL (Reais)
- Consentimento LGPD é obrigatório para clientes
- Deletar cliente anonimiza ao invés de remover (LGPD)

---

**Última atualização:** 10 de março de 2026
