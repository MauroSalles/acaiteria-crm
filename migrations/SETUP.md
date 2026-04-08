# Alembic — Migrações de Banco de Dados

> **Status:** Skeleton criado. Pronto para inicialização.

## Setup Inicial (quando necessário)

```bash
# No diretório cloud_version/
pip install alembic
alembic init migrations
```

Depois editar `migrations/env.py`:
```python
from backend.models import db
target_metadata = db.metadata
```

E `alembic.ini`:
```ini
sqlalchemy.url = %(DATABASE_URL)s
```

## Comandos Úteis

```bash
# Gerar migração automaticamente a partir dos modelos
alembic revision --autogenerate -m "descricao da mudanca"

# Aplicar migrações pendentes
alembic upgrade head

# Reverter última migração
alembic downgrade -1

# Ver histórico
alembic history
```

## Notas

- O `db.create_all()` atual continuará funcionando para SQLite em testes
- Alembic é necessário apenas para PostgreSQL em produção (Render)
- Cada novo modelo ou alteração de coluna deve gerar uma migração
- Não usar `alembic stamp head` em produção sem conferir o estado real
