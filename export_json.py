import json
from backend.app import app
from backend.models import Cliente

with app.app_context():
    clientes = Cliente.query.all()
    data = [{"id": c.id_cliente, "nome": c.nome, "telefone": c.telefone, "email": c.email} for c in clientes]
    print(json.dumps(data, indent=2, ensure_ascii=False))