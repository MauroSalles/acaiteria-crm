# CRM Simples - Açaiteria Combina Açaí

[![CI](https://github.com/MauroSalles/acaiteria-crm/actions/workflows/ci.yml/badge.svg)](https://github.com/MauroSalles/acaiteria-crm/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/MauroSalles/acaiteria-crm/branch/main/graph/badge.svg)](https://codecov.io/gh/MauroSalles/acaiteria-crm)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Deploy: Render](https://img.shields.io/badge/deploy-Render-blueviolet.svg)](https://acaiteria-crm.onrender.com)

## Descrição do Projeto

Sistema Web de Gestão de Clientes e Vendas para a Açaiteria **Combina Açaí**, localizada em Lorena/SP. A solução centraliza o registro de vendas e o cadastro de clientes em uma aplicação web com banco de dados relacional, habilitando gestão de relacionamento (fidelização, métricas de recorrência/churn) e fechamento de caixa integrado.

### Problema Identificado

A açaiteria operava com controle de vendas por planilhas (Excel), sem vínculo entre as entidades "Venda" e "Cliente", impedindo:

- Mensuração de recorrência de clientes
- Execução de campanhas segmentadas
- Análise de tendências de consumo
- Contato direto com clientes fiéis

### Solução Proposta

Sistema CRM integrado com módulo de vendas, permitindo:
Cadastro de clientes com consentimento LGPD,
Registro de vendas com associação automática a clientes,
Histórico de compras por cliente,
Fechamento de caixa diário integrado,
Exportação de contatos para campanhas de marketing,
Interface responsiva adequada ao balcão de atendimento.

---

## Requisitos Funcionais

| # | Requisito | Descrição |
| --- | --- | --- |
| RF-01 | Cadastro de Cliente | Registrar nome, telefone, email, data de cadastro e observações |
| RF-02 | Registro de Venda | Criar venda com data, valor total e forma de pagamento |
| RF-03 | Associação Venda-Cliente | Vincular venda a cliente específico para rastreabilidade |
| RF-04 | Gestão de Produtos | Cadastrar produtos/sabores com preço e categoria |
| RF-05 | Itens da Venda | Registrar quantidade e preço unitário de cada produto na venda |
| RF-06 | Fechamento Diário | Consolidar vendas diárias com saldo de caixa |
| RF-07 | Relatórios | Gerar relatórios de clientes, vendas e recorrência |
| RF-08 | Exportação de Dados | Exportar contatos em CSV para campanhas de marketing |

---

## Requisitos Não-Funcionais

| # | Requisito | Descrição |
| --- | --- | --- |
| RNF-01 | Usabilidade Balcão | Interface simplificada e intuitiva para operador de balcão |
| RNF-02 | Responsividade | Compatível com tablets e smartphones |
| RNF-03 | Persistência SQL | Banco de dados relacional (SQLite / MySQL) |
| RNF-04 | Versionamento | Controle com Git e GitHub |
| RNF-05 | LGPD | Minimização de dados, consentimento explícito, termos visíveis no cadastro |
| RNF-06 | Performance | Resposta em menos de 2 segundos para operações de balcão |
| RNF-07 | Segurança | Senhas criptografadas, validação de entrada |

---

## Arquitetura Técnica

### Stack Tecnológico

- **Backend**: Python 3.11+ com Flask
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Banco de Dados**: SQLite (dev) / PostgreSQL (produção — Render)
- **IA/ML**: Motor TF-IDF + Cosine Similarity (hand-coded, zero dependências externas)
- **Versionamento**: Git e GitHub
- **CI/CD**: GitHub Actions (flake8 + pytest + Codecov)
- **Hospedagem**: Render (Docker + PostgreSQL)

### Estrutura de Pastas

```text
cloud_version/
├── backend/                    # Backend Flask
│   ├── app.py                 # Aplicação principal (rotas, API, IA/ML)
│   ├── models.py              # Modelos de dados (SQLAlchemy)
│   └── __init__.py
├── frontend/                   # Frontend HTML/CSS/JS
│   ├── index.html             # Dashboard principal (Chart.js)
│   ├── vitrine.html           # Vitrine pública com carrinho
│   ├── cliente_login.html     # Login do cliente
│   ├── cliente_cadastro.html  # Cadastro com LGPD
│   ├── cliente_painel.html    # Painel do cliente (pontos/fidelidade)
│   └── static/                # CSS, JS, imagens
├── tests/                      # Testes automatizados (199 testes)
│   ├── conftest.py            # Fixtures compartilhadas
│   ├── test_clientes.py
│   ├── test_e2e.py
│   ├── test_health_relatorios.py
│   ├── test_ia_ml.py          # Testes IA/ML
│   ├── test_produtos.py
│   ├── test_suporte.py
│   └── test_vendas.py
├── docs/                       # Documentação
│   ├── MER.md                 # Modelo Entidade-Relacionamento
│   └── LGPD.md                # Política de privacidade
├── requirements.txt           # Dependências Python
├── pyproject.toml             # Configuração pytest/tools
├── Dockerfile                 # Container para deploy
├── render.yaml                # Configuração Render
├── .github/workflows/ci.yml  # GitHub Actions CI/CD
└── README.md                  # Este arquivo
```

---

## Modelo de Dados (MER)

```text
CLIENTE (1) ──── (N) VENDA
VENDA (1) ──── (N) ITEM_VENDA
PRODUTO (1) ──── (N) ITEM_VENDA
VENDA (1) ──── (1) PAGAMENTO
```

### Tabelas Principais

Tabela CLIENTE:

```sql
id_cliente (PK) | nome | telefone | email | data_cadastro | observacoes | consentimento_lgpd | data_consentimento
```

Tabela VENDA:

```sql
id_venda (PK) | id_cliente (FK) | data_venda | valor_total | forma_pagamento | status_pagamento
```

Tabela ITEM_VENDA:

```sql
id_item (PK) | id_venda (FK) | id_produto (FK) | quantidade | preco_unitario | subtotal
```

Tabela PRODUTO:

```sql
id_produto (PK) | nome_produto | categoria | preco | ativo
```

Tabela PAGAMENTO:

```sql
id_pagamento (PK) | id_venda (FK) | data_pagamento | valor_pago | metodo | status
```

---

## Instalação e Configuração

### Pré-requisitos

- Python 3.11 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Passos de Instalação

1. **Clonar o repositório**

   ```bash
   git clone https://github.com/MauroSalles/acaiteria-crm.git
   cd AcaiteriaCRM/cloud_version
   ```

2. **Criar ambiente virtual**

   ```bash
   python -m venv venv
   # Windows
   venv\Scripts\activate
   # Linux/Mac
   source venv/bin/activate
   ```

3. **Instalar dependências**

   ```bash
   pip install -r requirements.txt
   ```

4. **Executar aplicação**

   ```bash
   python -m backend.app
   ```

5. **Acessar no navegador**

   ```text
   http://localhost:5000
   ```

---

## Fluxos Principais

### Fluxo 1: Cadastro de Cliente

1. Operador clica em "Novo Cliente"
2. Preenche nome, telefone, email (opcionais)
3. Ve aviso de consentimento LGPD com opção de aceitar/recusar
4. Sistema salva cliente com data de consentimento
5. Cliente aparece em lista disponível para próximas vendas

### Fluxo 2: Registro de Venda

1. Operador clica em "Nova Venda"
2. Seleciona cliente da lista (ou cadastra novo na hora)
3. Adiciona produtos/sabores com quantidade
4. Sistema calcula subtotal automaticamente
5. Seleciona forma de pagamento
6. Clica em "Finalizar Venda"
7. Sistema gera recibo e atualiza histórico de cliente

### Fluxo 3: Fechamento Diário

1. Ao final do expediente, operador acessa "Fechamento Diário"
2. Sistema exibe todas as vendas do dia
3. Calcula total de dinheiro, débito, crédito
4. Permite ajustes manuais se necessário
5. Gera arquivo de backup do dia
6. Fecha o caixa

### Fluxo 4: Relatórios

1. Gerente acessa "Relatórios"
2. Escolhe período (dia, semana, mês)
3. Visualiza:
   - Clientes mais frequentes
   - Produtos mais vendidos
   - Faturamento por período
   - Taxa de retorno de clientes (churn)
4. Exporta dados em CSV para campanha de marketing

---

## Conformidade LGPD

### Implementações Obrigatórias

- Consentimento Explícito: Termo de consentimento exibido no cadastro
- Minimização de Dados: Solicita apenas dados necessários (nome, telefone, email)
- Direito ao Esquecimento: Função para anonimizar/deletar dados de cliente
- Transparência: Política de privacidade visível na interface
- Segurança: Senhas criptografadas, validação de entrada, proteção contra SQL injection

### Política de Privacidade (resumida)

Coletamos nome, telefone e email para:
rastrear histórico de compras,
enviar promoções segmentadas,
melhorar relacionamento com clientela.

Seus dados não serão compartilhados com terceiros,
usados para fins diferentes, nem retidos após sua solicitação de exclusão.

---

## Módulos de Inteligência Artificial e Machine Learning

O sistema incorpora **IA/ML iterativa** 100% hand-coded (zero dependências externas), aplicando técnicas de NLP e análise estatística para potencializar a gestão do CRM.

### 1. Chatbot IA — TF-IDF + Cosine Similarity

- **Endpoint**: `POST /api/suporte/ia-resposta`
- Motor NLP com pipeline completo para português: normalização Unicode → tokenização → remoção de stopwords (pt-BR) → stemming RSLP simplificado
- 12 documentos de treinamento cobrindo: login, vendas, cadastro, LGPD, estoque, relatórios, fidelidade, atalhos, suporte, cardápio, WhatsApp, erros técnicos
- Classificação por similaridade do cosseno com threshold adaptativo

### 2. Recomendação de Produtos — Collaborative Filtering (KNN)

- **Endpoint**: `GET /api/ia/recomendacoes/<id_cliente>`
- Filtragem colaborativa baseada em histórico de compras
- KNN com Top-10 vizinhos por similaridade do cosseno
- Cold start: fallback para ranking de popularidade global
- Score normalizado 0-1 para cada recomendação

### 3. Segmentação de Clientes — Análise RFM

- **Endpoint**: `GET /api/ia/segmentacao`
- Recency, Frequency, Monetary analysis
- Percentil rank (1-5) para cada dimensão
- 6 segmentos automáticos: Campeão, Cliente Fiel, Novo Promissor, Regular, Em Risco, Hibernando
- Resumo agregado por segmento com receita total

### 4. Tendências de Vendas — Regressão Linear

- **Endpoint**: `GET /api/ia/tendencias?dias=30`
- Regressão linear simples (mínimos quadrados) sobre receita diária
- R² (coeficiente de determinação) para qualidade do modelo
- Projeção automática de receita para 7 dias futuros
- Classificação: tendência de alta, baixa ou estável
- Produto mais vendido no período

### 5. Feedback Loop — Melhoria Contínua

- **Endpoint**: `POST /api/suporte/ia-feedback`
- Registro de satisfação (util/não util) por resposta da IA
- Taxa de sucesso calculada em tempo real
- Estatísticas do motor: `GET /api/ia/stats`

---

## Cronograma de Desenvolvimento

| Quinzena | Foco | Entregáveis |
| --- | --- | --- |
| 1-2 | Descoberta, definição problema, Plano de Ação | Visitação, MER, Wireframes |
| 3-4 | Prototipagem e fundamentação | MER validado, Wireframes finalizados, repositório estruturado |
| 4 | Relatório Parcial | Metodologia e arquitetura inicial |
| 5-6 | Desenvolvimento MVP e testes | MVP funcional, testes, validações com gestor |
| 7 | Ajustes e entrega final | Vídeo de apresentação, Relatório Final (ABNT) |

---

## Papéis e Responsabilidades

| Papel | Integrante(s) |
| --- | --- |
| Articulação Externa e Documentação | Thamires + Mauro e Jorge |
| Prospecção Setorial e Dados Públicos | Gabriel + Marcos + Luiz |
| Levantamento com Comércios e UX Balcão | Thamires + Gabriel |
| Backend (Python) | Igor, Jorge, Mauro, Marcos |
| Banco de Dados (SQL/MER) | Jorge, Luiz, Mauro |
| UI/UX e Wireframes | Mauro |

---

## Testes

### Testes Unitários

```bash
python -m pytest backend/tests/
```

### Testes de Integração

- Testar fluxo completo: Cadastro, Venda, Fechamento

### Testes em Campo

- Validar usabilidade com operador real no balcão
- Coletar feedback de velocidade e clareza

---

## Referências e Compliances

- Regulamento Projeto Integrador: UNIVESP (Versão VI/2023)
- LGPD: Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018)
- Design Thinking: Imersão, definição, ideação, prototipagem, testes

---

## Contato e Suporte

Proprietário da Açaiteria: Thomas Picconetto Silva
Endereço: Rua Tenente Manoel Barbosa, nº 46 - Bairro da Cruz, Lorena/SP

---

## Licença

Este projeto foi desenvolvido para fins acadêmicos no Projeto Integrador em Computação I (PJI110) da UNIVESP, Polo Lorena/SP, Grupo 22.

---

**Última atualização**: 10 de março de 2026  
**Status**: Em desenvolvimento - Quinzena 3
