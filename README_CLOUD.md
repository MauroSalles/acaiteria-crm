# Açaiteria CRM — Versão Nuvem (Deploy Cloud)

## Grupo 22 - UNIVESP 2026

> Versão configurada para deploy gratuito na nuvem com PostgreSQL.
> Suporta **Render.com** (recomendado), **Railway**, e **Docker**.
> O projeto localhost (`AcaiteriaCRM/`) **permanece intacto e funcional**.

---

## 📦 O que foi modificado nesta versão

| Arquivo | Mudança |
| --- | --- |
| `backend/app.py` | `DATABASE_URL` via variável de ambiente; porta dinâmica; LGPD enforced em `criar_venda` |
| `backend/models.py` | Campo `consentimento_versao`; modelo `ConsentimentoHistorico` |
| `frontend/static/script.js` | **API Client Module** — `ClienteAPI`, `VendaAPI`, `ProdutoAPI`, `RelatorioAPI`, `ExportAPI` |
| `requirements.txt` | `psycopg2-binary` adicionado para PostgreSQL |
| `Procfile` | `web: gunicorn backend.app:app` |
| `Dockerfile` | Build otimizado multi-stage, Python 3.13, gunicorn |
| `docker-compose.yml` | Flask + PostgreSQL para testes locais com Docker |
| `render.yaml` | Blueprint para deploy Render.com (1-clique) |
| `.dockerignore` | Exclui venv, testes, IDE do build Docker |

---

## 🎯 Escolha sua plataforma de deploy

| Plataforma | Custo | Dificuldade | PostgreSQL grátis | Docker necessário |
| --- | --- | --- | --- | --- |
| **Render.com** ⭐ | Gratuito | Fácil | Sim (90 dias) | Não |
| **Railway** | Gratuito (500h/mês) | Fácil | Sim (1 GB) | Não |
| **Docker local** | Gratuito | Médio | Sim (container) | Sim |

---

## 🚀 OPÇÃO 1 — Deploy no Render.com (RECOMENDADO)

### ETAPA 0 — Contas necessárias (ambas gratuitas)

| Serviço | Link |
| --- | --- |
| GitHub | <https://github.com> |
| Render | <https://render.com> |

### ETAPA 1 — Subir o código para o GitHub

#### 1.1 Criar repositório

1. Acesse <https://github.com> → faça login
2. Clique **"+"** → **"New repository"**
3. Nome: `acaiteria-crm` | Visibilidade: **Public** | **Não** marque "Add README"
4. Clique **"Create repository"**

#### 1.2 Fazer upload via navegador (mais fácil)

1. Na página do repositório, clique **"uploading an existing file"**
2. Abra o Explorador de Arquivos: `Downloads/.../AcaiteriaCRM/cloud_version/`
3. `Ctrl+A` para selecionar tudo (exceto `venv313/`) → arraste para a área de upload
4. Role para baixo → **"Commit changes"**

#### 1.3 Alternativa via PowerShell (se tiver Git instalado)

```powershell
cd "C:\Users\Home\Downloads\Projeto Integrador Univesp (eixo computação)\AcaiteriaCRM\cloud_version"
git init
git add .
git commit -m "CRM Açaiteria - deploy cloud"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/acaiteria-crm.git
git push -u origin main
```

### ETAPA 2 — Deploy no Render (Blueprint automático)

1. Acesse <https://render.com> → faça login com GitHub
2. Clique **"New +"** → **"Blueprint"**
3. Conecte seu repositório `acaiteria-crm`
4. Render detecta o `render.yaml` e configura automaticamente:
   - Serviço web (Flask/gunicorn)
   - Banco PostgreSQL gratuito
   - SECRET_KEY gerada automaticamente
5. Clique **"Apply"** → aguarde o build (~3-5 min)
6. Sua URL pública será: `https://acaiteria-crm.onrender.com`

### ETAPA 3 — Verificar funcionamento

- [ ] Dashboard carrega com estatísticas
- [ ] `https://sua-url.onrender.com/api/clientes` retorna JSON
- [ ] `https://sua-url.onrender.com/health` retorna `{"status": "ok"}`
- [ ] Cadastrar um novo cliente (com consentimento LGPD)
- [ ] Registrar uma venda
- [ ] Relatório do dia: `/api/relatorios/dia-atual`

### Atualizar o site futuramente

```powershell
git add .
git commit -m "Descrição da mudança"
git push
# Render detecta e faz redeploy automático em ~3 minutos
```

### Limites do plano gratuito Render

| Recurso | Limite |
| --- | --- |
| Horas web | 750h/mês |
| PostgreSQL | Gratuito por 90 dias |
| RAM | 512 MB |
| Bandwidth | 100 GB/mês |
| Cold start | ~30s após inatividade |

---

## 🐳 OPÇÃO 2 — Docker (teste local ou servidor próprio)

### Pré-requisito: Docker Desktop instalado

Download: <https://www.docker.com/products/docker-desktop/>

### Subir com docker-compose (Flask + PostgreSQL)

```powershell
cd "cloud_version"
docker-compose up --build
```

Acesse: `http://localhost:5000`

### Parar os containers

```powershell
docker-compose down
```

### Parar e apagar dados do banco

```powershell
docker-compose down -v
```

---

## ❓ Problemas comuns

| Erro | Solução |
| --- | --- |
| `ModuleNotFoundError` | Verifique se `requirements.txt` foi incluído no GitHub |
| `No module named 'psycopg2'` | Já incluso em `requirements.txt` — confira o commit |
| `DATABASE_URL not set` | No Render: Blueprint configura automaticamente. No Railway: adicione PostgreSQL no projeto |
| Página demora ~30s | Normal — plano gratuito hiberna após inatividade |
| CSS/JS não carregam | Verifique se `frontend/static/` foi incluída no commit |
| Build falha no Docker | Verifique se Docker Desktop está rodando |

---

## 📁 Arquivos de deploy

| Arquivo | Finalidade |
| --- | --- |
| `Dockerfile` | Container otimizado Python 3.13 + gunicorn |
| `docker-compose.yml` | Flask + PostgreSQL locais via Docker |
| `render.yaml` | Blueprint Render.com (1-clique) |
| `Procfile` | Comando de inicialização (Railway/Heroku) |
| `.dockerignore` | Exclui venv/testes do build |
| `.env.example` | Template de variáveis de ambiente |

---

## 🗄️ Novos endpoints LGPD (implementados nesta versão)

```text
PUT  /api/clientes/:id/consentimento
     Body: { "consentimento_lgpd": true, "versao_politica": "v1.0" }
     → Concede ou revoga consentimento, registra no histórico de auditoria

GET  /api/clientes/:id/consentimento/historico
     → Retorna todo o histórico de concessões/revogações (compliance ANPD)
```

**Regra LGPD em vigor:** `POST /api/vendas` retorna **HTTP 400** se o cliente não tiver `consentimento_lgpd = true`.

---

## 🧩 API Client Module (script.js)

O arquivo `frontend/static/script.js` agora inclui um módulo de API completo ao final.
Use diretamente em qualquer template HTML do projeto:

```javascript
// Buscar clientes
ClienteAPI.listar().then(clientes => console.log(clientes));

// Criar venda (com validação LGPD no frontend)
async function registrarVendaComLGPD(id_cliente, itens, forma) {
    const cliente = await ClienteAPI.obter(id_cliente);
    if (!cliente.consentimento_lgpd) {
        mostrarAlerta('Solicite o consentimento LGPD antes de registrar venda.', 'aviso');
        return;
    }
    const venda = await VendaAPI.criar({ id_cliente, itens, forma_pagamento: forma });
    mostrarAlerta(`Venda #${venda.id_venda} — ${formatarMoeda(venda.valor_total)}`, 'sucesso');
}

// Histórico de auditoria LGPD
ClienteAPI.historicoConsentimento(1).then(hist => console.table(hist.historico));

// Fechamento do dia
RelatorioAPI.diaAtual().then(rel =>
    console.log(`Faturamento: R$ ${rel.faturamento_total.toFixed(2)}`)
);
```

---

## 🔵 Apêndice C++ — Conceitos para Engenharia de Computação

> Para os alunos que estão estudando C++ nas matérias de Computação.
> O código abaixo mostra como os conceitos do CRM se traduzem em C++.

### Stack vs Heap (o mais importante)

```cpp
// STACK — automático, destruído ao sair do escopo
Produto acai(1, "Açaí 500ml", 18.50);   // criado aqui
// some aqui quando a função termina — sem ação do programador

// HEAP — manual, você aloca e DEVE liberar
Produto* acai = new Produto(1, "Açaí 500ml", 18.50);
delete acai;   // OBRIGATÓRIO — sem isso = memory leak

// SMART POINTER — C++ moderno, libera automaticamente (como Python)
auto acai = std::make_unique<Produto>(1, "Açaí 500ml", 18.50);
// liberado automaticamente no fim do escopo — sem delete manual
```

### Ponteiros (o que Python esconde de você)

```cpp
double preco = 18.50;
double* ptr = &preco;   // ptr guarda o ENDEREÇO na RAM

std::cout << preco;    // 18.5
std::cout << ptr;      // 0x7ffe... (endereço)
std::cout << *ptr;     // 18.5 (valor via ponteiro — "desreferenciação")

*ptr = 20.00;          // modifica 'preco' através do ponteiro
// Python faz isso implicitamente com objetos — C++ exige que você veja
```

### Classes — equivalente a models.py

```cpp
// Python:                          C++:
// class Produto(db.Model):         class Produto {
//   nome = Column(String)          private:
//   preco = Column(DECIMAL)            std::string nome;
//                                      double preco;
//   def calcSubtotal(self, q):     public:
//       return self.preco * q          double calcSubtotal(int q) const {
//                                          return preco * q;
//                                      }
//                                  };
```

### std::vector — equivalente à lista Python

```cpp
// Python: itens = []; itens.append(item)
// C++:
std::vector<ItemVenda> itens;
itens.push_back({id_produto: 2, quantidade: 1, preco_unitario: 18.50});

double total = 0.0;
for (const auto& item : itens) {   // 'auto' deduz o tipo (como var no JS)
    total += item.preco_unitario * item.quantidade;
}
```

### Onde C++ se encaixaria neste projeto

| Camada                        | Tecnologia atual | Substituição C++ se necessário                        |
| ----------------------------- | ---------------- | ----------------------------------------------------- |
| Web/API                       | Python + Flask   | Não vale a pena — Python é mais produtivo             |
| Banco de dados                | PostgreSQL       | Sem mudança — SQL é universal                         |
| Hardware (PDV, impressora)    | —                | **C++ seria ideal** — controle direto de dispositivo  |
| Motor de cálculo em lote      | Python           | **C++ para volume >1M transações/s**                  |
| Sistema embarcado offline     | —                | **C++ ou C** — microcontroladores                     |

> **Conclusão:** Para web e CRMs, Python/Flask é a escolha certa.
> C++ é escolhido quando você precisa controlar **onde os dados ficam na memória**
> e **quando são destruídos** — crítico em hardware embarcado, tempo real e alta performance.

---

## 🔧 Configuração Local (Teste)

Para testar localmente com PostgreSQL:

1. **Instale PostgreSQL** no seu sistema
2. **Crie um banco**: `createdb acaiteria_crm`
3. **Configure .env**:

   ```text
   DATABASE_URL=postgresql://localhost/acaiteria_crm
   ```

4. **Instale dependências**: `pip install psycopg2-binary`
5. **Execute**: `python run.py`

---

## 📋 Arquivos Modificados

- `requirements.txt`: Adicionado psycopg2-binary
- `backend/app.py`: DATABASE_URL via variável de ambiente
- `run.py`: Porta dinâmica para nuvem
- `Procfile`: Configuração para deploy
- `.env.example`: Exemplo de variáveis

---

## 🌐 Acesso

Após deploy, você receberá uma URL como:
`https://acaiteria-crm-production.up.railway.app`

---

## 💰 Custos

- **Railway**: Gratuito até 512MB RAM + 1GB PostgreSQL
- **PostgreSQL**: 1GB gratuito, depois $0.00015/GB/hora

---

## 🔄 Migração de Dados

Para migrar dados do SQLite local:

1. Exporte dados: `python export_json.py`
2. Modifique script para importar no PostgreSQL
3. Execute na nuvem: `railway run python import_data.py`

---

## 📊 Monitoramento

- **Logs**: `railway logs`
- **Banco**: Acesse via Railway dashboard
- **Uptime**: Railway monitora automaticamente
