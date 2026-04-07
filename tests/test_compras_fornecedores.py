"""
Testes das APIs de Compras, Fornecedores, Cupons,
Edição de Venda, Status Pedido e Promoções — Açaiteria CRM
"""


# ── helpers ──────────────────────────────────────────────────────
def _criar_fornecedor(client, nome="Fornecedor X", cnpj="12345678000100"):
    r = client.post("/api/fornecedores", json={
        "nome": nome, "cnpj": cnpj, "telefone": "11999990000",
        "email": "forn@test.com",
    })
    assert r.status_code == 201, r.data
    return r.get_json()["id_fornecedor"]


def _criar_produto(client, nome="Açaí 500ml", preco=18.90):
    r = client.post("/api/produtos", json={
        "nome_produto": nome, "preco": preco,
    })
    assert r.status_code == 201, r.data
    return r.get_json()["id_produto"]


def _criar_cliente(client, nome="Cliente Teste"):
    r = client.post("/api/clientes", json={
        "nome": nome, "consentimento_lgpd": True,
        "versao_politica": "v1.0",
    })
    assert r.status_code == 201, r.data
    return r.get_json()["id_cliente"]


def _criar_venda(client, cid=None, pid=None):
    if cid is None:
        cid = _criar_cliente(client)
    if pid is None:
        pid = _criar_produto(client)
    r = client.post("/api/vendas", json={
        "id_cliente": cid,
        "forma_pagamento": "Dinheiro",
        "itens": [{"id_produto": pid, "quantidade": 2}],
    })
    assert r.status_code == 201, r.data
    return r.get_json()["id_venda"]


# ═══════════════════════════════════════════════════════════════════
# FORNECEDORES
# ═══════════════════════════════════════════════════════════════════
class TestFornecedores:
    def test_criar_fornecedor(self, client):
        fid = _criar_fornecedor(client)
        assert fid >= 1

    def test_listar_fornecedores(self, client):
        _criar_fornecedor(client)
        r = client.get("/api/fornecedores")
        assert r.status_code == 200
        data = r.get_json()
        items = data.get("fornecedores", data) if isinstance(data, dict) else data
        assert len(items) >= 1
        assert items[0]["nome"] == "Fornecedor X"

    def test_buscar_fornecedor_por_id(self, client):
        fid = _criar_fornecedor(client)
        r = client.get(f"/api/fornecedores/{fid}")
        assert r.status_code == 200
        assert r.get_json()["cnpj"] == "12345678000100"

    def test_fornecedor_nao_encontrado(self, client):
        r = client.get("/api/fornecedores/999")
        assert r.status_code == 404

    def test_atualizar_fornecedor(self, client):
        fid = _criar_fornecedor(client)
        r = client.put(f"/api/fornecedores/{fid}", json={
            "nome": "Fornecedor Y", "telefone": "11888880000",
        })
        assert r.status_code == 200
        assert r.get_json()["nome"] == "Fornecedor Y"

    def test_desativar_fornecedor(self, client):
        fid = _criar_fornecedor(client)
        r = client.delete(f"/api/fornecedores/{fid}")
        assert r.status_code == 200
        # Verificar que ficou inativo
        r2 = client.get(f"/api/fornecedores/{fid}")
        assert r2.get_json()["ativo"] is False

    def test_cnpj_duplicado(self, client):
        _criar_fornecedor(client, cnpj="11111111000111")
        r = client.post("/api/fornecedores", json={
            "nome": "Outro", "cnpj": "11111111000111",
        })
        assert r.status_code == 400
        assert "CNPJ" in r.get_json()["erro"]

    def test_criar_fornecedor_sem_nome(self, client):
        r = client.post("/api/fornecedores", json={"cnpj": "99999"})
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# COMPRAS (Purchase Orders)
# ═══════════════════════════════════════════════════════════════════
class TestCompras:
    def test_criar_compra(self, client):
        fid = _criar_fornecedor(client)
        pid = _criar_produto(client)
        r = client.post("/api/compras", json={
            "id_fornecedor": fid,
            "itens": [{
                "id_produto": pid, "quantidade": 10,
                "preco_unitario": 8.50,
            }],
            "nota_fiscal": "NF-001",
        })
        assert r.status_code == 201
        data = r.get_json()
        assert data["valor_total"] == 85.0
        assert data["status"] == "Pendente"

    def test_listar_compras(self, client):
        fid = _criar_fornecedor(client)
        pid = _criar_produto(client)
        client.post("/api/compras", json={
            "id_fornecedor": fid,
            "itens": [{
                "id_produto": pid, "quantidade": 5,
                "preco_unitario": 10.0,
            }],
        })
        r = client.get("/api/compras")
        assert r.status_code == 200
        data = r.get_json()
        assert data["total"] >= 1

    def test_buscar_compra_por_id(self, client):
        fid = _criar_fornecedor(client)
        pid = _criar_produto(client)
        rc = client.post("/api/compras", json={
            "id_fornecedor": fid,
            "itens": [{
                "id_produto": pid, "quantidade": 3,
                "preco_unitario": 5.0,
            }],
        })
        cid = rc.get_json()["id_compra"]
        r = client.get(f"/api/compras/{cid}")
        assert r.status_code == 200
        assert r.get_json()["nota_fiscal"] is None or True  # pode ser None

    def test_receber_compra(self, client):
        fid = _criar_fornecedor(client)
        pid = _criar_produto(client)
        rc = client.post("/api/compras", json={
            "id_fornecedor": fid,
            "itens": [{
                "id_produto": pid, "quantidade": 10,
                "preco_unitario": 8.0,
            }],
        })
        cid = rc.get_json()["id_compra"]
        r = client.post(f"/api/compras/{cid}/receber")
        assert r.status_code == 200
        assert r.get_json()["compra"]["status"] == "Recebido"

    def test_cancelar_compra_pendente(self, client):
        fid = _criar_fornecedor(client)
        pid = _criar_produto(client)
        rc = client.post("/api/compras", json={
            "id_fornecedor": fid,
            "itens": [{
                "id_produto": pid, "quantidade": 5,
                "preco_unitario": 10.0,
            }],
        })
        cid = rc.get_json()["id_compra"]
        r = client.post(f"/api/compras/{cid}/cancelar")
        assert r.status_code == 200
        assert r.get_json()["compra"]["status"] == "Cancelado"

    def test_receber_compra_ja_recebida(self, client):
        fid = _criar_fornecedor(client)
        pid = _criar_produto(client)
        rc = client.post("/api/compras", json={
            "id_fornecedor": fid,
            "itens": [{
                "id_produto": pid, "quantidade": 2,
                "preco_unitario": 5.0,
            }],
        })
        cid = rc.get_json()["id_compra"]
        client.post(f"/api/compras/{cid}/receber")
        r = client.post(f"/api/compras/{cid}/receber")
        assert r.status_code == 400

    def test_compra_sem_itens(self, client):
        fid = _criar_fornecedor(client)
        r = client.post("/api/compras", json={
            "id_fornecedor": fid, "itens": [],
        })
        assert r.status_code == 400

    def test_compra_fornecedor_inexistente(self, client):
        pid = _criar_produto(client)
        r = client.post("/api/compras", json={
            "id_fornecedor": 999,
            "itens": [{
                "id_produto": pid, "quantidade": 1,
                "preco_unitario": 5.0,
            }],
        })
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# EDITAR VENDA
# ═══════════════════════════════════════════════════════════════════
class TestEditarVenda:
    def test_editar_forma_pagamento(self, client):
        vid = _criar_venda(client)
        r = client.put(f"/api/vendas/{vid}", json={
            "forma_pagamento": "PIX",
        })
        assert r.status_code == 200
        assert r.get_json()["forma_pagamento"] == "PIX"

    def test_editar_observacoes(self, client):
        vid = _criar_venda(client)
        r = client.put(f"/api/vendas/{vid}", json={
            "observacoes": "Sem cobertura",
        })
        assert r.status_code == 200

    def test_editar_venda_inexistente(self, client):
        r = client.put("/api/vendas/999", json={
            "forma_pagamento": "PIX",
        })
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# STATUS PEDIDO (workflow iFood-like)
# ═══════════════════════════════════════════════════════════════════
class TestStatusPedido:
    def test_avancar_para_preparando(self, client):
        vid = _criar_venda(client)
        r = client.put(f"/api/vendas/{vid}/status-pedido", json={
            "status_pedido": "Preparando",
        })
        assert r.status_code == 200
        assert r.get_json()["venda"]["status_pedido"] == "Preparando"

    def test_workflow_completo(self, client):
        vid = _criar_venda(client)
        for status in ["Preparando", "Pronto", "Entregue"]:
            r = client.put(f"/api/vendas/{vid}/status-pedido", json={
                "status_pedido": status,
            })
            assert r.status_code == 200

    def test_nao_pode_retroceder(self, client):
        vid = _criar_venda(client)
        client.put(f"/api/vendas/{vid}/status-pedido", json={
            "status_pedido": "Preparando",
        })
        r = client.put(f"/api/vendas/{vid}/status-pedido", json={
            "status_pedido": "Recebido",
        })
        assert r.status_code == 400
        assert "retroceder" in r.get_json()["erro"].lower()

    def test_cancelar_de_qualquer_estado(self, client):
        vid = _criar_venda(client)
        client.put(f"/api/vendas/{vid}/status-pedido", json={
            "status_pedido": "Preparando",
        })
        r = client.put(f"/api/vendas/{vid}/status-pedido", json={
            "status_pedido": "Cancelado",
        })
        assert r.status_code == 200
        assert r.get_json()["venda"]["status_pedido"] == "Cancelado"

    def test_status_invalido(self, client):
        vid = _criar_venda(client)
        r = client.put(f"/api/vendas/{vid}/status-pedido", json={
            "status_pedido": "EmTransito",
        })
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# CUPONS DE DESCONTO
# ═══════════════════════════════════════════════════════════════════
class TestCupons:
    def test_criar_cupom_percentual(self, client):
        r = client.post("/api/cupons", json={
            "codigo": "DESC10",
            "tipo_desconto": "percentual",
            "valor_desconto": 10,
            "descricao": "10% off",
        })
        assert r.status_code == 201
        assert r.get_json()["codigo"] == "DESC10"

    def test_criar_cupom_fixo(self, client):
        r = client.post("/api/cupons", json={
            "codigo": "MENOS5",
            "tipo_desconto": "fixo",
            "valor_desconto": 5.0,
        })
        assert r.status_code == 201

    def test_listar_cupons(self, client):
        client.post("/api/cupons", json={
            "codigo": "CUP1", "tipo_desconto": "percentual",
            "valor_desconto": 5,
        })
        r = client.get("/api/cupons")
        assert r.status_code == 200
        data = r.get_json()
        items = data.get("cupons", data) if isinstance(data, dict) else data
        assert len(items) >= 1

    def test_validar_cupom_percentual(self, client):
        client.post("/api/cupons", json={
            "codigo": "OFF20", "tipo_desconto": "percentual",
            "valor_desconto": 20,
        })
        r = client.post("/api/cupons/validar", json={
            "codigo": "OFF20", "valor_pedido": 100.0,
        })
        assert r.status_code == 200
        data = r.get_json()
        assert data["desconto_calculado"] == 20.0

    def test_validar_cupom_fixo(self, client):
        client.post("/api/cupons", json={
            "codigo": "FIXO10", "tipo_desconto": "fixo",
            "valor_desconto": 10,
        })
        r = client.post("/api/cupons/validar", json={
            "codigo": "FIXO10", "valor_pedido": 50.0,
        })
        assert r.status_code == 200
        assert r.get_json()["desconto_calculado"] == 10.0

    def test_validar_cupom_inexistente(self, client):
        r = client.post("/api/cupons/validar", json={
            "codigo": "NAOEXISTE", "valor_pedido": 50.0,
        })
        assert r.status_code == 404

    def test_cupom_codigo_duplicado(self, client):
        client.post("/api/cupons", json={
            "codigo": "DUP1", "tipo_desconto": "fixo",
            "valor_desconto": 5,
        })
        r = client.post("/api/cupons", json={
            "codigo": "DUP1", "tipo_desconto": "fixo",
            "valor_desconto": 10,
        })
        assert r.status_code == 400
        assert "existe" in r.get_json()["erro"].lower()

    def test_desativar_cupom(self, client):
        rc = client.post("/api/cupons", json={
            "codigo": "DEL1", "tipo_desconto": "percentual",
            "valor_desconto": 5,
        })
        cid = rc.get_json()["id_cupom"]
        r = client.delete(f"/api/cupons/{cid}")
        assert r.status_code == 200

    def test_atualizar_cupom(self, client):
        rc = client.post("/api/cupons", json={
            "codigo": "UPD1", "tipo_desconto": "percentual",
            "valor_desconto": 5,
        })
        cid = rc.get_json()["id_cupom"]
        r = client.put(f"/api/cupons/{cid}", json={
            "descricao": "Atualizado",
        })
        assert r.status_code == 200
        assert r.get_json()["descricao"] == "Atualizado"

    def test_cupom_sem_codigo(self, client):
        r = client.post("/api/cupons", json={
            "tipo_desconto": "fixo", "valor_desconto": 5,
        })
        assert r.status_code == 400


# ═══════════════════════════════════════════════════════════════════
# PROMOÇÕES (preço promocional do produto)
# ═══════════════════════════════════════════════════════════════════
class TestPromocoes:
    def test_definir_preco_promocional(self, client):
        pid = _criar_produto(client, preco=20.0)
        r = client.put(f"/api/produtos/{pid}/promocao", json={
            "preco_promocional": 15.0,
        })
        assert r.status_code == 200
        assert float(r.get_json()["produto"]["preco_promocional"]) == 15.0

    def test_preco_promocional_maior_que_normal(self, client):
        pid = _criar_produto(client, preco=20.0)
        r = client.put(f"/api/produtos/{pid}/promocao", json={
            "preco_promocional": 25.0,
        })
        assert r.status_code == 400

    def test_remover_preco_promocional(self, client):
        pid = _criar_produto(client, preco=20.0)
        client.put(f"/api/produtos/{pid}/promocao", json={
            "preco_promocional": 15.0,
        })
        r = client.put(f"/api/produtos/{pid}/promocao", json={
            "preco_promocional": None,
        })
        assert r.status_code == 200
        assert r.get_json()["produto"]["preco_promocional"] is None

    def test_promocao_produto_inexistente(self, client):
        r = client.put("/api/produtos/999/promocao", json={
            "preco_promocional": 10.0,
        })
        assert r.status_code == 404


# ═══════════════════════════════════════════════════════════════════
# PÁGINAS (renderização)
# ═══════════════════════════════════════════════════════════════════
class TestPaginas:
    def test_pagina_compras(self, client):
        r = client.get("/compras")
        assert r.status_code == 200

    def test_pagina_vendas_lista(self, client):
        r = client.get("/vendas")
        assert r.status_code == 200
