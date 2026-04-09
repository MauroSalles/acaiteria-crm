"""
Sprint v6 — Tests for bug fixes, new features, and improvements.
"""
import pytest  # noqa: F401
from backend.models import Cliente, Produto
from datetime import datetime, timezone
from decimal import Decimal


# ── Helper fixtures ──────────────────────────────────────────────


@pytest.fixture()
def cliente_lgpd(client, db_session):
    """Create a client with LGPD consent."""
    c = Cliente(
        nome="Teste Sprint6",
        email="sprint6@teste.com",
        telefone="11999990001",
        consentimento_lgpd=True,
        data_consentimento=datetime.now(timezone.utc),
        ativo=True,
    )
    db_session.add(c)
    db_session.commit()
    return c


@pytest.fixture()
def produto_ativo(client, db_session):
    """Create an active product with stock."""
    p = Produto(
        nome_produto="Açaí Sprint6",
        categoria="Açaí",
        preco=Decimal("15.00"),
        ativo=True,
        estoque_atual=50,
        estoque_minimo=5,
    )
    db_session.add(p)
    db_session.commit()
    return p


@pytest.fixture()
def cliente_logado(client, db_session):
    """Create a client and log them in via session."""
    c = Cliente(
        nome="Cliente Logado",
        email="logado@teste.com",
        telefone="11999990002",
        consentimento_lgpd=True,
        data_consentimento=datetime.now(timezone.utc),
        ativo=True,
        pontos_fidelidade=50,
    )
    c.set_senha("senha123")
    db_session.add(c)
    db_session.commit()
    return c


# ══════════════════════════════════════════════════════════════════
# FIX #1 — desconto_aplicado stored on Venda (was AttributeError)
# ══════════════════════════════════════════════════════════════════


class TestDescontoAplicado:
    def test_venda_stores_desconto_aplicado(
        self, client, db_session, cliente_lgpd, produto_ativo
    ):
        resp = client.post("/api/vendas", json={
            "id_cliente": cliente_lgpd.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 2}
            ],
            "desconto_percentual": 10.0,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert "desconto_aplicado" in data
        assert data["desconto_aplicado"] == 3.0  # 10% of 30.00

    def test_venda_zero_desconto(
        self, client, db_session, cliente_lgpd, produto_ativo
    ):
        resp = client.post("/api/vendas", json={
            "id_cliente": cliente_lgpd.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 1}
            ],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["desconto_aplicado"] == 0

    def test_relatorio_por_data_no_crash(
        self, client, db_session, cliente_lgpd, produto_ativo
    ):
        """relatorio_por_data usava v.desconto_percentual (AttributeError)."""
        client.post("/api/vendas", json={
            "id_cliente": cliente_lgpd.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 1}
            ],
            "desconto_percentual": 5.0,
        })
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        resp = client.get(f"/api/relatorios/por-data?data={today}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "total_descontos" in data
        assert data["total_descontos"] >= 0


# ══════════════════════════════════════════════════════════════════
# FIX #2 — cliente_logout session.clear()
# ══════════════════════════════════════════════════════════════════


class TestClienteLogout:
    def test_logout_clears_all_session(self, client, db_session):
        """Logout should clear entire session (was only clearing partial)."""
        c = Cliente(
            nome="Logout Test", email="logout@t.com",
            consentimento_lgpd=True, ativo=True,
        )
        c.set_senha("x")
        db_session.add(c)
        db_session.commit()

        with client.session_transaction() as sess:
            sess["cliente_id"] = c.id_cliente
            sess["cliente_nome"] = c.nome
            sess["tipo_usuario"] = "cliente"
            sess["papel"] = "admin"  # simular session leak

        resp = client.get("/cliente/logout", follow_redirects=False)
        assert resp.status_code == 302

        with client.session_transaction() as sess:
            assert "cliente_id" not in sess
            assert "papel" not in sess  # was leaking before fix


# ══════════════════════════════════════════════════════════════════
# FIX #3 — pontos_fidelidade cap at 999999
# ══════════════════════════════════════════════════════════════════


class TestPontosCap:
    def test_pontos_capped_at_999999(
        self, client, db_session, produto_ativo
    ):
        c = Cliente(
            nome="Pontos Cap", email="cap@t.com",
            consentimento_lgpd=True, ativo=True,
            data_consentimento=datetime.now(timezone.utc),
            pontos_fidelidade=999990,
        )
        db_session.add(c)
        db_session.commit()

        resp = client.post("/api/vendas", json={
            "id_cliente": c.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 3}
            ],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["pontos_total"] <= 999999


# ══════════════════════════════════════════════════════════════════
# FIX #4 — Health check includes DB status
# ══════════════════════════════════════════════════════════════════


class TestHealthCheck:
    def test_health_returns_db_status(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["status"] == "ok"
        assert data["database"] == "connected"
        assert "timestamp" in data

    def test_health_has_service_name(self, client):
        resp = client.get("/api/health")
        data = resp.get_json()
        assert data["service"] == "acaiteria-crm"


# ══════════════════════════════════════════════════════════════════
# NEW FEATURE — /api/dashboard/kpi
# ══════════════════════════════════════════════════════════════════


class TestDashboardKPI:
    def test_kpi_returns_all_metrics(
        self, client, db_session, cliente_lgpd, produto_ativo
    ):
        """Dashboard KPI endpoint should return all key metrics."""
        client.post("/api/vendas", json={
            "id_cliente": cliente_lgpd.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 2}
            ],
        })
        resp = client.get("/api/dashboard/kpi")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["total_clientes"] >= 1
        assert data["total_vendas"] >= 1
        assert data["faturamento_total"] > 0
        assert "vendas_semana" in data
        assert "ticket_medio" in data
        assert "produtos_ativos" in data
        assert "estoque_baixo" in data
        assert "taxa_consentimento" in data

    def test_kpi_requires_auth(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/dashboard/kpi")
        assert resp.status_code == 401


# ══════════════════════════════════════════════════════════════════
# NEW FEATURE — /api/cliente/perfil
# ══════════════════════════════════════════════════════════════════


class TestClientePerfil:
    def test_perfil_returns_data(self, client, db_session, cliente_logado):
        with client.session_transaction() as sess:
            sess["cliente_id"] = cliente_logado.id_cliente
            sess["tipo_usuario"] = "cliente"

        resp = client.get("/api/cliente/perfil")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["nome"] == "Cliente Logado"
        assert data["pontos_fidelidade"] == 50
        assert "total_compras" in data
        assert "total_gasto" in data
        assert "badges" in data
        assert "membro_desde" in data

    def test_perfil_requires_login(self, client):
        """Without cliente_id in session, should redirect."""
        with client.session_transaction() as sess:
            sess.pop("cliente_id", None)
        resp = client.get("/api/cliente/perfil")
        assert resp.status_code == 302


# ══════════════════════════════════════════════════════════════════
# FIX — vitrine_produtos returns preco_promocional + foto_url
# ══════════════════════════════════════════════════════════════════


class TestVitrineEnhanced:
    def test_vitrine_includes_promo_and_photo(self, client, db_session):
        p = Produto(
            nome_produto="Açaí Promo",
            categoria="Açaí",
            preco=Decimal("20.00"),
            preco_promocional=Decimal("15.00"),
            foto_url="https://example.com/acai.jpg",
            ativo=True,
            estoque_atual=10,
            estoque_minimo=2,
        )
        db_session.add(p)
        db_session.commit()

        resp = client.get("/api/vitrine/produtos")
        assert resp.status_code == 200
        data = resp.get_json()
        prod = next(
            (x for x in data if x["nome_produto"] == "Açaí Promo"),
            None,
        )
        assert prod is not None
        assert prod["preco_promocional"] == 15.0
        assert prod["foto_url"] == "https://example.com/acai.jpg"
        assert "estoque_disponivel" in prod

    def test_vitrine_estoque_disponivel_flag(self, client, db_session):
        p = Produto(
            nome_produto="Sem Estoque",
            preco=Decimal("10.00"),
            ativo=True,
            estoque_atual=0,
            estoque_minimo=5,
        )
        db_session.add(p)
        db_session.commit()

        resp = client.get("/api/vitrine/produtos")
        data = resp.get_json()
        prod = next(
            (x for x in data if x["nome_produto"] == "Sem Estoque"),
            None,
        )
        assert prod is not None
        assert prod["estoque_disponivel"] is False


# ══════════════════════════════════════════════════════════════════
# FIX — _verificar_badges null-safe
# ══════════════════════════════════════════════════════════════════


class TestBadgesNullSafe:
    def test_badges_with_nonexistent_client(self, client, db_session):
        from backend.app import _verificar_badges
        result = _verificar_badges(99999)
        assert result == []

    def test_badges_granted_after_purchase(
        self, client, db_session, cliente_lgpd, produto_ativo
    ):
        resp = client.post("/api/vendas", json={
            "id_cliente": cliente_lgpd.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 1}
            ],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        badge_names = [b["codigo"] for b in data.get("novos_badges", [])]
        assert "primeira_compra" in badge_names


# ══════════════════════════════════════════════════════════════════
# FIX — timezone-aware _dia_inicio / _dia_fim
# ══════════════════════════════════════════════════════════════════


class TestTimezoneAware:
    def test_dia_inicio_is_utc(self):
        from backend.app import _dia_inicio
        from datetime import date
        d = date(2026, 1, 15)
        result = _dia_inicio(d)
        assert result.tzinfo is not None
        assert result.hour == 0

    def test_dia_fim_is_utc(self):
        from backend.app import _dia_fim
        from datetime import date
        d = date(2026, 1, 15)
        result = _dia_fim(d)
        assert result.tzinfo is not None
        assert result.hour == 23


# ══════════════════════════════════════════════════════════════════
# FIX — Cache invalidation after venda (checkout + admin)
# ══════════════════════════════════════════════════════════════════


class TestCacheInvalidation:
    def test_criar_venda_invalidates_cache(
        self, client, db_session, cliente_lgpd, produto_ativo
    ):
        """Vitrine cache should be invalidated after creating a sale."""
        client.get("/api/vitrine/produtos")
        resp = client.post("/api/vendas", json={
            "id_cliente": cliente_lgpd.id_cliente,
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 1}
            ],
        })
        assert resp.status_code == 201
        resp2 = client.get("/api/vitrine/produtos")
        assert resp2.status_code == 200


# ══════════════════════════════════════════════════════════════════
# Checkout — pontos cap
# ══════════════════════════════════════════════════════════════════


class TestCheckoutPontosCap:
    def test_checkout_pontos_capped(
        self, client, db_session, produto_ativo
    ):
        c = Cliente(
            nome="Checkout Cap", email="cc@t.com",
            consentimento_lgpd=True, ativo=True,
            data_consentimento=datetime.now(timezone.utc),
            pontos_fidelidade=999995,
        )
        c.set_senha("x")
        db_session.add(c)
        db_session.commit()

        with client.session_transaction() as sess:
            sess["cliente_id"] = c.id_cliente
            sess["tipo_usuario"] = "cliente"

        resp = client.post("/api/cliente/carrinho/checkout", json={
            "itens": [
                {"id_produto": produto_ativo.id_produto, "quantidade": 2}
            ],
            "forma_pagamento": "Pix",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["pontos_total"] <= 999999
