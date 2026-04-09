"""
Sprint v7 — Tests for XSS fixes, session idle timeout, new endpoints,
bulk update, audit log export, and other improvements.
"""
import pytest  # noqa: F401
from backend.models import Cliente, Produto, LogAcao
from datetime import datetime, timezone
from decimal import Decimal


# ── Helper fixtures ──────────────────────────────────────────────


@pytest.fixture()
def cliente_v7(client, db_session):
    c = Cliente(
        nome="Cliente V7",
        email="v7@teste.com",
        telefone="11999990007",
        consentimento_lgpd=True,
        data_consentimento=datetime.now(timezone.utc),
        ativo=True,
        pontos_fidelidade=0,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture()
def produto_v7(client, db_session):
    p = Produto(
        nome_produto="Açaí V7",
        categoria="Açaí",
        preco=Decimal("19.99"),
        ativo=True,
        estoque_atual=30,
        estoque_minimo=3,
    )
    db_session.add(p)
    db_session.commit()
    return p


@pytest.fixture()
def varios_produtos(client, db_session):
    """Create 3 products for bulk update tests."""
    prods = []
    for i in range(3):
        p = Produto(
            nome_produto=f"Prod Bulk {i}",
            categoria="Açaí",
            preco=Decimal("10.00"),
            ativo=True,
            estoque_atual=20,
            estoque_minimo=2,
        )
        db_session.add(p)
        prods.append(p)
    db_session.commit()
    return prods


# ══════════════════════════════════════════════════════════════════
# FIX — Rate limit on validar_cupom (brute-force prevention)
# ══════════════════════════════════════════════════════════════════


class TestCupomRateLimit:
    def test_cupom_endpoint_exists(self, client):
        resp = client.post("/api/cupons/validar", json={
            "codigo": "INEXISTENTE", "valor_pedido": 50,
        })
        assert resp.status_code in (400, 404)


# ══════════════════════════════════════════════════════════════════
# FIX — Pontos fidelidade rounding (was truncating with int())
# ══════════════════════════════════════════════════════════════════


class TestPontosRounding:
    def test_pontos_round_up(
        self, client, db_session, cliente_v7, produto_v7
    ):
        """R$19.99 should give 20 pontos (round), not 19 (int truncate)."""
        resp = client.post("/api/vendas", json={
            "id_cliente": cliente_v7.id_cliente,
            "itens": [
                {"id_produto": produto_v7.id_produto, "quantidade": 1}
            ],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["pontos_total"] == 20  # round(19.99) = 20, not int(19.99) = 19


# ══════════════════════════════════════════════════════════════════
# FIX — Session idle timeout
# ══════════════════════════════════════════════════════════════════


class TestSessionIdleTimeout:
    def test_session_stores_last_active(self, client):
        """Each request should update _last_active in session."""
        client.get("/api/health")
        with client.session_transaction() as sess:
            assert "_last_active" in sess
            assert isinstance(sess["_last_active"], float)

    def test_idle_session_clears_auth(self, client):
        """Session idle > 30 min should clear usuario_id."""
        # Set _last_active to 31 minutes ago
        import time
        with client.session_transaction() as sess:
            sess["_last_active"] = time.time() - 31 * 60

        resp = client.get("/api/clientes")
        assert resp.status_code == 401

    def test_active_session_stays_valid(self, client):
        """Fresh session should work normally."""
        import time
        with client.session_transaction() as sess:
            sess["_last_active"] = time.time() - 5 * 60  # 5 min ago

        resp = client.get("/api/clientes")
        assert resp.status_code == 200


# ══════════════════════════════════════════════════════════════════
# FIX — Vitrine limit (max 500)
# ══════════════════════════════════════════════════════════════════


class TestVitrineLimit:
    def test_vitrine_returns_limited_results(self, client, db_session):
        """Vitrine should return at most 500 products."""
        resp = client.get("/api/vitrine/produtos")
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) <= 500


# ══════════════════════════════════════════════════════════════════
# NEW FEATURE — Audit log CSV export
# ══════════════════════════════════════════════════════════════════


class TestAuditLogExport:
    def test_export_csv_empty(self, client):
        resp = client.get("/api/logs/export-csv")
        assert resp.status_code == 200
        assert resp.content_type == "text/csv; charset=utf-8"
        text = resp.data.decode("utf-8")
        assert "id,data_hora,acao,entidade" in text

    def test_export_csv_with_data(self, client, db_session):
        log = LogAcao(
            acao="criar",
            entidade="cliente",
            id_entidade=1,
            detalhes="Teste export",
        )
        db_session.add(log)
        db_session.commit()

        resp = client.get("/api/logs/export-csv")
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "Teste export" in text

    def test_export_csv_filter_by_entidade(self, client, db_session):
        db_session.add(LogAcao(acao="criar", entidade="cliente"))
        db_session.add(LogAcao(acao="criar", entidade="produto"))
        db_session.commit()

        resp = client.get("/api/logs/export-csv?entidade=cliente")
        text = resp.data.decode("utf-8")
        lines = text.strip().split("\n")
        assert len(lines) == 2  # header + 1 row

    def test_export_csv_filter_by_date(self, client, db_session):
        db_session.add(LogAcao(
            acao="criar", entidade="venda",
            data_hora=datetime(2026, 1, 15, 10, 0, 0, tzinfo=timezone.utc),
        ))
        db_session.commit()

        resp = client.get(
            "/api/logs/export-csv?data_inicio=2026-01-15&data_fim=2026-01-15"
        )
        assert resp.status_code == 200
        text = resp.data.decode("utf-8")
        assert "venda" in text

    def test_export_csv_requires_admin(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/logs/export-csv")
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════
# NEW FEATURE — Bulk product update
# ══════════════════════════════════════════════════════════════════


class TestBulkUpdateProdutos:
    def test_bulk_update_prices(self, client, db_session, varios_produtos):
        itens = [
            {"id_produto": p.id_produto, "preco": 25.0}
            for p in varios_produtos
        ]
        resp = client.patch("/api/produtos/bulk-update", json={
            "itens": itens,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_atualizados"] == 3
        assert len(data["erros"]) == 0

        for p in varios_produtos:
            db_session.refresh(p)
            assert float(p.preco) == 25.0

    def test_bulk_update_estoque(self, client, db_session, varios_produtos):
        itens = [
            {"id_produto": varios_produtos[0].id_produto, "estoque_atual": 100}
        ]
        resp = client.patch("/api/produtos/bulk-update", json={
            "itens": itens,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_atualizados"] == 1
        db_session.refresh(varios_produtos[0])
        assert varios_produtos[0].estoque_atual == 100

    def test_bulk_update_nonexistent(self, client):
        resp = client.patch("/api/produtos/bulk-update", json={
            "itens": [{"id_produto": 99999, "preco": 10}],
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_atualizados"] == 0
        assert len(data["erros"]) == 1

    def test_bulk_update_empty_rejects(self, client):
        resp = client.patch("/api/produtos/bulk-update", json={
            "itens": [],
        })
        assert resp.status_code == 400

    def test_bulk_update_max_100(self, client):
        itens = [{"id_produto": i, "preco": 5} for i in range(101)]
        resp = client.patch("/api/produtos/bulk-update", json={
            "itens": itens,
        })
        assert resp.status_code == 400
        assert "100" in resp.get_json()["erro"]

    def test_bulk_update_requires_admin(self, unauthenticated_client):
        resp = unauthenticated_client.patch(
            "/api/produtos/bulk-update", json={"itens": []}
        )
        assert resp.status_code == 401

    def test_bulk_update_toggle_ativo(
        self, client, db_session, varios_produtos
    ):
        pid = varios_produtos[0].id_produto
        resp = client.patch("/api/produtos/bulk-update", json={
            "itens": [{"id_produto": pid, "ativo": False}],
        })
        assert resp.status_code == 200
        db_session.refresh(varios_produtos[0])
        assert varios_produtos[0].ativo is False


# ══════════════════════════════════════════════════════════════════
# FIX — Fornecedor email index (model)
# ══════════════════════════════════════════════════════════════════


class TestFornecedorEmailIndex:
    def test_fornecedor_email_has_index(self):
        from backend.models import Fornecedor
        col = Fornecedor.__table__.columns["email"]
        assert col.index is True
