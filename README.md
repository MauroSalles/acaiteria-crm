# CRM Simples - Açaiteria Combina Açaí

## 📋 Descrição do Projeto

Sistema Web de Gestão de Clientes e Vendas para a Açaiteria **Combina Açaí**, localizada em Lorena/SP. A solução centraliza o registro de vendas e o cadastro de clientes em uma aplicação web com banco de dados relacional, habilitando gestão de relacionamento (fidelização, métricas de recorrência/churn) e fechamento de caixa integrado.

### Problema Identificado
A açaiteria operava com controle de vendas por planilhas (Excel), sem vínculo entre as entidades "Venda" e "Cliente", impedindo:
- Mensuração de recorrência de clientes
- Execução de campanhas segmentadas
- Análise de tendências de consumo
- Contato direto com clientes fiéis

### Solução Proposta
Sistema CRM integrado com módulo de vendas, permitindo:
✅ Cadastro de clientes com consentimento LGPD
✅ Registro de vendas com associação automática á clientes
✅ Histórico de compras por cliente
✅ Fechamento de caixa diário integrado
✅ Exportação de contatos para campanhas de marketing
✅ Interface responsiva adequada ao balcão de atendimento

---

## 🎯 Requisitos Funcionais

| # | Requisito | Descrição |
|---|-----------|-----------|
| RF-01 | Cadastro de Cliente | Registrar nome, telefone, email, data de cadastro e observações |
| RF-02 | Registro de Venda | Criar venda com data, valor total e forma de pagamento |
| RF-03 | Associação Venda-Cliente | Vincular venda a cliente específico para rastreabilidade |
| RF-04 | Gestão de Produtos | Cadastrar produtos/sabores com preço e categoria |
| RF-05 | Itens da Venda | Registrar quantidade e preço unitário de cada produto na venda |
| RF-06 | Fechamento Diário | Consolidar vendas diárias com saldo de caixa |
| RF-07 | Relatórios | Gerar relatórios de clientes, vendas e recorrência |
| RF-08 | Exportação de Dados | Exportar contatos em CSV para campanhas de marketing |

---

## 🔒 Requisitos Não-Funcionais

| # | Requisito | Descrição |
|---|-----------|-----------|
| RNF-01 | Usabilidade Balcão | Interface simplificada e intuitiva para operador de balcão |
| RNF-02 | Responsividade | Compatível com tablets e smartphones |
| RNF-03 | Persistência SQL | Banco de dados relacional (SQLite / MySQL) |
| RNF-04 | Versionamento | Controle com Git e GitHub |
| RNF-05 | LGPD | Minimização de dados, consentimento explícito, termos visíveis no cadastro |
| RNF-06 | Performance | Resposta em menos de 2 segundos para operações de balcão |
| RNF-07 | Segurança | Senhas criptografadas, validação de entrada |

---

## 🏗️ Arquitetura Técnica

### Stack Tecnológico
- **Backend**: Python 3.9+ com Flask
- **Frontend**: HTML5, CSS3, JavaScript (vanilla)
- **Banco de Dados**: SQLite (dev) / MySQL (produção)
- **Versionamento**: Git & GitHub
- **Hospedagem**: Local (localhost:5000) ou servidor simples

### Estrutura de Pastas
```
AcaiteriaCRM/
├── backend/                    # Backend Flask
│   ├── app.py                 # Aplicação principal
│   ├── models.py              # Modelos de dados (SQLAlchemy)
│   ├── routes.py              # Rotas/endpoints
│   ├── database.py            # Configuração do banco
│   └── utils.py               # Funções auxiliares
├── frontend/                   # Frontend HTML/CSS/JS
│   ├── index.html             # Dashboard principal
│   ├── cadastro_cliente.html  # Formulário de cadastro
│   ├── venda.html             # Interface de vendas
│   ├── relatorios.html        # Relatórios e análises
│   ├── estilos.css            # Estilos globais
│   └── script.js              # JavaScript cliente
├── database/                   # Scripts SQL
│   ├── schema.sql             # Criação das tabelas
│   └── seed_data.sql          # Dados de teste
├── docs/                       # Documentação
│   ├── MER.md                 # Modelo Entidade-Relacionamento
│   ├── API.md                 # Documentação de endpoints
│   └── LGPD.md                # Política de privacidade
├── requirements.txt           # Dependências Python
├── .gitignore                # Arquivos ignorados no Git
└── README.md                 # Este arquivo
```

---

## 🗄️ Modelo de Dados (MER)

```
CLIENTE (1) ──── (N) VENDA
VENDA (1) ──── (N) ITEM_VENDA
PRODUTO (1) ──── (N) ITEM_VENDA
VENDA (1) ──── (1) PAGAMENTO
```

### Tabelas Principais

**CLIENTE**
```sql
id_cliente (PK) | nome | telefone | email | data_cadastro | observacoes | consentimento_lgpd | data_consentimento
```

**VENDA**
```sql
id_venda (PK) | id_cliente (FK) | data_venda | valor_total | forma_pagamento | status_pagamento
```

**ITEM_VENDA**
```sql
id_item (PK) | id_venda (FK) | id_produto (FK) | quantidade | preco_unitario | subtotal
```

**PRODUTO**
```sql
id_produto (PK) | nome_produto | categoria | preco | ativo
```

**PAGAMENTO**
```sql
id_pagamento (PK) | id_venda (FK) | data_pagamento | valor_pago | metodo | status
```

---

## 🚀 Instalação e Configuração

### Pré-requisitos
- Python 3.9 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Passos de Instalação

1. **Clonar o repositório**
   ```bash
   git clone https://github.com/[seu-usuario]/AcaiteriaCRM.git
   cd AcaiteriaCRM
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

4. **Criar banco de dados**
   ```bash
   # Windows
   python backend/database.py
   # Ou importar schema.sql em seu gerenciador SQL
   ```

5. **Executar aplicação**
   ```bash
   python backend/app.py
   ```

6. **Acessar no navegador**
   ```
   http://localhost:5000
   ```

---

## 📱 Fluxos Principais

### Fluxo 1: Cadastro de Cliente
1. Operador clica em "Novo Cliente"
2. Preenche nome, telefone, email (opcionais)
3. **Vê aviso de consentimento LGPD** com opção de aceitar/recusar
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

## 🔐 Conformidade LGPD

### Implementações Obrigatórias
✅ **Consentimento Explícito**: Termo de consentimento exibido no cadastro
✅ **Minimização de Dados**: Solicita apenas dados necessários (nome, telefone, email)
✅ **Direito ao Esquecimento**: Função para anonimizar/deletar dados de cliente
✅ **Transparência**: Política de privacidade visível na interface
✅ **Segurança**: Senhas criptografadas, validação de entrada, proteção contra SQL injection

### Política de Privacidade (resumida)
```
Coletamos nome, telefone e email para:
- Rastrear histórico de compras
- Enviar promoções segmentadas
- Melhorar relacionamento com clientela

Seus dados não serão:
- Compartilhados com terceiros
- Usados para fins diferentes
- Retidos após sua solicitação de exclusão
```

---

## 📊 Cronograma de Desenvolvimento

| Quinzena | Foco | Entregáveis |
|----------|------|-------------|
| 1-2 | Descoberta, definição problema, Plano de Ação | Visitação, MER, Wireframes |
| 3-4 | Prototipagem e fundamentação | MER validado, Wireframes finalizados, repositório estruturado |
| 4 | Relatório Parcial | Metodologia e arquitetura inicial |
| 5-6 | Desenvolvimento MVP e testes | MVP funcional, testes, validações com gestor |
| 7 | Ajustes e entrega final | Vídeo de apresentação, Relatório Final (ABNT) |

---

## 👥 Papéis e Responsabilidades

| Papel | Integrante(s) |
|-------|---------------|
| **Articulação Externa & Documentação** | Thamires + Mauro & Jorge |
| **Prospecção Setorial & Dados Públicos** | Gabriel + Marcos + Luiz |
| **Levantamento com Comércios & UX Balcão** | Thamires + Gabriel |
| **Backend (Python)** | Igor, Jorge, Mauro, Marcos |
| **Banco de Dados (SQL/MER)** | Jorge, Luiz, Mauro |
| **UI/UX & Wireframes** | Mauro |

---

## 🧪 Testes

### Testes Unitários
```bash
python -m pytest backend/tests/
```

### Testes de Integração
- Testar fluxo completo: Cadastro → Venda → Fechamento

### Testes em Campo
- Validar usabilidade com operador real no balcão
- Coletar feedback de velocidade e clareza

---

## 📚 Referências e Compliances

- **Regulamento Projeto Integrador**: UNIVESP (Versão VI/2023)
- **LGPD**: Lei Geral de Proteção de Dados Pessoais (Lei 13.709/2018)
- **Design Thinking**: Imersão, definição, ideação, prototipagem, testes

---

## 📧 Contato e Suporte

**Proprietário da Açaiteria**: Thomas Picconetto Silva  
**Endereço**: Rua Tenente Manoel Barbosa, nº 46 - Bairro da Cruz, Lorena/SP

---

## 📄 Licença

Este projeto foi desenvolvido para fins acadêmicos no Projeto Integrador em Computação I (PJI110) da UNIVESP, Polo Lorena/SP, Grupo 22.

---

**Última atualização**: 10 de março de 2026  
**Status**: Em desenvolvimento - Quinzena 3
