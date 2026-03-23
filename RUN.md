# 🚀 GUIA DE EXECUÇÃO RÁPIDA

## ⚡ Início Rápido (3 minutos)

### 1️⃣ Instalar Dependências

```bash
# Windows
pip install -r requirements.txt

# Linux/Mac
pip3 install -r requirements.txt
```

### 2️⃣ Executar a Aplicação

```bash
# Opção 1: Usando o script servidor
python run.py

# Opção 2: Diretamente do backend
python backend/app.py

# Opção 3: Linux/Mac
python3 run.py
```

### 3️⃣ Acessar no Navegador

Abra seu navegador e acesse:

```
http://localhost:5000
```

---

## 📋 Fluxo Básico de Uso

1. **Dashboard** (`/`) - Visualizar estatísticas
2. **Novo Cliente** (`/cadastro-cliente`) - Cadastrar cliente com consentimento LGPD
3. **Nova Venda** (`/nova-venda`) - Registrar venda selecionando cliente e produtos
4. **Relatórios** (`/relatorios`) - Visualizar análises de vendas e clientes
5. **Política de Privacidade** (`/politica-privacidade`) - Ler política LGPD

---

## 🛠️ Requisitos do Sistema

- **Python 3.9+**
- **pip (gerenciador de pacotes Python)**
- **Navegador moderno (Chrome, Firefox, Edge)**

---

## 📁 Estrutura do Projeto

```
AcaiteriaCRM/
├── backend/
│   ├── app.py              # Aplicação Flask principal
│   ├── models.py           # Modelos de dados (SQLAlchemy)
│   └── database.py         # Configuração do banco (criado automaticamente)
├── frontend/
│   ├── index.html          # Dashboard
│   ├── cadastro_cliente.html
│   ├── venda.html
│   ├── relatorios.html
│   ├── politica_privacidade.html
│   ├── estilos.css         # Estilos responsivos
│   ├── script.js           # JavaScript principal
│   └── script_venda.js     # JavaScript da página de vendas
├── database/
│   └── schema.sql          # Schema SQL completo
├── docs/
│   ├── API.md              # Documentação de endpoints
│   ├── MER.md              # Modelo Entidade-Relacionamento
│   └── LGPD.md             # Documentação LGPD
├── requirements.txt        # Dependências Python
├── .gitignore             # Arquivos ignorados no Git
├── run.py                 # Script para executar servidor
├── README.md              # Documentação do projeto
└── RUN.md                 # Este arquivo
```

---

## 🔐 Dados de Teste

**Clientes com histórico (já cadastrados):**
- Gabriel da Silva (frequente)
- Marina Costa
- João Pereira
- Ana Paula
- Carlos Mendes
- Paula Rodrigues

**Produtos disponíveis:**
- Açaí com Granola - R$ 25.00
- Açaí com Banana - R$ 24.00
- Açaí Simples - R$ 18.00
- E mais 7 produtos...

---

## 🐛 Troubleshooting

### Erro: "ModuleNotFoundError: No module named 'flask'"

**Solução:** Instale as dependências:
```bash
pip install -r requirements.txt
```

### Erro: "Port 5000 already in use"

**Solução:** Mude a porta no código:
```python
app.run(debug=True, host='0.0.0.0', port=5001)  # Use 5001
```

### Banco de dados vazio

**Solução:** O banco é criado automaticamente com dados de teste ao iniciar.

### Estilo CSS não carregando

**Certifique-se de que:**
- Está usando caminho relativo correto
- Acredita via http:// (não file://)
- Não está usando `Ctrl+Shift+Delet` para limpar cache

---

## 📊 API Endpoints (Resumo)

| Método | Endpoint | Descrição |
|--------|----------|-----------|
| GET | `/api/clientes` | Listar clientes |
| POST | `/api/clientes` | Criar cliente |
| GET | `/api/produtos` | Listar produtos |
| POST | `/api/vendas` | Criar venda |
| GET | `/api/relatorios/dia-atual` | Vendas do dia |
| GET | `/api/relatorios/clientes-frequentes` | Top clientes |
| GET | `/api/exportar/clientes-csv` | Exportar clientes |

---

## 📱 Responsividade

O sistema é totalmente responsivo:
- ✅ Desktop (1024px+)
- ✅ Tablet (768px - 1024px)
- ✅ Mobile (até 768px)

---

## 🔐 Conformidade LGPD

✅ **Implementado:**
- Consentimento explícito no cadastro
- Termos de privacidade visíveis
- Direito ao esquecimento (anonimização)
- Minimização de dados coletados
- Segurança de senhas (hashing)

---

## 👥 Papéis do Projeto

| Papel | Integrantes |
|-------|------------|
| Articulação Externa | Thamires, Mauro, Jorge |
| Backend Python | Igor, Jorge, Mauro, Marcos |
| Banco de Dados | Jorge, Luiz, Mauro |
| UI/UX | Mauro |

---

## 📅 Cronograma

| Quinzena | Status | Foco |
|----------|--------|------|
| 1-2 | ✅ Concluído | Descoberta, definição |
| 3-4 | 🔄 Em Andamento | Prototipagem |
| 5-6 | ⏰ Próximo | MVP e testes |
| 7 | ⏰ Final | Entrega e vídeo |

---

## 📧 Suporte

**Proprietário Açaiteria:**
🍓 Thomas Picconetto Silva
📍 Rua Tenente Manoel Barbosa, nº 46 - Lorena/SP

**Tutora:**
👩‍🏫 Sra. Valdeth S. De Souza

---

## 📚 Referências

- UNIVESP - Regulamento Projeto Integrador (v VI/2023)
- LGPD - Lei 13.709/2018
- ANPD - Autoridade Nacional de Proteção de Dados

---

**Desenvolvido com ❤️ pelo Grupo 22 - UNIVESP Polo Lorena/SP**

Última atualização: 10 de março de 2026
