# Modularização em Blueprints — Plano de Migração

> **Status:** Skeleton criado. Migração gradual planejada.

## Estrutura Alvo

```
backend/
├── app.py              ← factory create_app(), registro de blueprints
├── models.py           ← permanece centralizado
├── extensions.py       ← db, limiter, cache, login instâncias
├── blueprints/
│   ├── __init__.py
│   ├── auth.py         ← login, logout, 2fa, registro
│   ├── clientes.py     ← CRUD clientes, extrato, badges, indicações
│   ├── produtos.py     ← CRUD produtos, foto, estoque, combos
│   ├── vendas.py       ← CRUD vendas, cursor, agendamentos, nfce
│   ├── financeiro.py   ← lançamentos, fechamento, relatórios
│   ├── suporte.py      ← tickets, ia chatbot
│   ├── admin.py        ← webhooks, lojas, usuários, logs
│   ├── painel.py       ← painel do cliente (favoritos, reordenar)
│   └── api_meta.py     ← /api/version, /api/openapi.json, health
```

## Estratégia de Migração

1. Criar `extensions.py` com instâncias compartilhadas
2. Migrar um blueprint por vez (começar por `api_meta` — menor risco)
3. Manter `app.py` funcional durante toda a migração
4. Cada PR migra no máximo 1 blueprint + testes correspondentes

## Roteiro

| Sprint | Blueprint     | ~Rotas | Risco  |
|--------|--------------|--------|--------|
| 1      | api_meta     | 3      | Baixo  |
| 2      | auth         | 8      | Médio  |
| 3      | admin        | 12     | Médio  |
| 4      | produtos     | 10     | Médio  |
| 5      | clientes     | 12     | Médio  |
| 6      | vendas       | 10     | Alto   |
| 7      | financeiro   | 8      | Alto   |
| 8      | suporte      | 6      | Baixo  |
| 9      | painel       | 3      | Baixo  |
