"""
Testes das novas features — Dashboard KPI, Filtros Avançados,
Gamificação (Badges), Extrato do Cliente, Previsão de Estoque
"""
from decimal import Decimal
from backend.models import db, Cliente, Produto, Venda, ItemVenda, BadgeCliente


# =====================================================================
# Helpers
# =====================================================================

def _criar_cliente(consentimento=True):
    """Cria um cliente ativo com consentimento LGPD."""
    c = Cliente(
        nome="Cliente Teste",
        email="teste@email.com",
        telefone="12999990000",
        consentimento_lgpd=consentimento,
        ativo=True,
        pontos_fidelidade=0,
    )
    db.session.add(c)
    db.session.commit()
    return c


def _criar_produto(nome="Açaí 500ml", preco=15.0, estoque=100):
    p = Produto(
        nome_produto=nome,
        preco=Decimal(str(preco)),
        categoria="Açaí",
        ativo=True,
        estoque_atual=estoque,
        estoque_minimo=5,
    )
    db.session.add(p)
    db.session.commit()
    return p


def _criar_venda(cliente, produto, qtd=1, valor=None):
    v = Venda(
        id_cliente=cliente.id_cliente,
        forma_pagamento="PIX",
        status_pagamento="Concluído",
        status_pedido="Entregue",
        valor_total=valor or Decimal(str(produto.preco * qtd)),
    )
    item = ItemVenda(
        id_produto=produto.id_produto,
        quantidade=qtd,
        preco_unitario=produto.preco,
        subtotal=produto.preco * qtd,
    )
    v.itens.append(item)
    db.session.add(v)
    db.session.commit()
    return v


# =====================================================================
# Dashboard KPI
# =====================================================================

class TestDashboardKPI:
    def test_kpi_sem_dados(self, client):
        resp = client.get("/api/dashboard/kpi")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["hoje"]["faturamento"] == 0
        assert d["hoje"]["vendas"] == 0
        assert d["hoje"]["ticket_medio"] == 0
        assert d["pedidos_ativos"] == 0
        assert "estoque_critico" in d

    def test_kpi_com_vendas(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            _criar_venda(c, p, qtd=2, valor=Decimal("30.00"))
            db.session.expire_all()
        resp = client.get("/api/dashboard/kpi")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["hoje"]["faturamento"] == 30.0
        assert d["hoje"]["vendas"] == 1
        assert d["hoje"]["ticket_medio"] == 30.0

    def test_kpi_requer_auth(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/dashboard/kpi")
        assert resp.status_code in (401, 302)


# =====================================================================
# Relatório com Filtros Avançados
# =====================================================================

class TestRelatorioFiltrado:
    def test_filtro_sem_dados(self, client):
        resp = client.get("/api/relatorios/vendas-filtradas")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["total"] == 0
        assert d["totalizadores"]["faturamento"] == 0

    def test_filtro_por_forma_pagamento(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            _criar_venda(c, p)
            db.session.expire_all()
        resp = client.get(
            "/api/relatorios/vendas-filtradas?forma_pagamento=PIX"
        )
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["total"] >= 1

    def test_filtro_pagamento_inexistente(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            _criar_venda(c, p)
            db.session.expire_all()
        resp = client.get(
            "/api/relatorios/vendas-filtradas"
            "?forma_pagamento=Crypto"
        )
        d = resp.get_json()
        assert d["total"] == 0

    def test_filtro_paginacao(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            for _ in range(3):
                _criar_venda(c, p)
            db.session.expire_all()
        resp = client.get(
            "/api/relatorios/vendas-filtradas?por_pagina=2&pagina=1"
        )
        d = resp.get_json()
        assert d["total"] == 3
        assert len(d["vendas"]) == 2
        assert d["total_paginas"] == 2

    def test_filtro_valor_min_max(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto(preco=10.0)
            _criar_venda(c, p, qtd=1, valor=Decimal("10.00"))
            _criar_venda(c, p, qtd=5, valor=Decimal("50.00"))
            db.session.expire_all()
        resp = client.get(
            "/api/relatorios/vendas-filtradas"
            "?valor_min=40&valor_max=60"
        )
        d = resp.get_json()
        assert d["total"] == 1
        assert d["totalizadores"]["faturamento"] == 50.0


# =====================================================================
# Gamificação — Badges
# =====================================================================

class TestBadges:
    def test_badges_cliente_sem_compras(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            cid = c.id_cliente
        resp = client.get(f"/api/clientes/{cid}/badges")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["total_conquistados"] == 0
        assert len(d["disponiveis"]) > 0

    def test_badge_primeira_compra(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            _criar_venda(c, p)
            cid = c.id_cliente
        resp = client.get(f"/api/clientes/{cid}/badges")
        d = resp.get_json()
        codigos = [b["codigo"] for b in d["badges"]]
        assert "primeira_compra" in codigos

    def test_badge_gastador_100(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto(preco=110.0)
            _criar_venda(c, p, valor=Decimal("110.00"))
            cid = c.id_cliente
        resp = client.get(f"/api/clientes/{cid}/badges")
        d = resp.get_json()
        codigos = [b["codigo"] for b in d["badges"]]
        assert "gastador_100" in codigos

    def test_badge_cliente_inexistente(self, client):
        resp = client.get("/api/clientes/99999/badges")
        assert resp.status_code == 404

    def test_badge_nao_duplica(self, client, app):
        """Chamar badges 2x não deve duplicar."""
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            _criar_venda(c, p)
            cid = c.id_cliente
        client.get(f"/api/clientes/{cid}/badges")
        resp = client.get(f"/api/clientes/{cid}/badges")
        d = resp.get_json()
        codigos = [b["codigo"] for b in d["badges"]]
        assert codigos.count("primeira_compra") == 1


# =====================================================================
# Extrato do Cliente
# =====================================================================

class TestExtratoCliente:
    def test_extrato_sem_compras(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            cid = c.id_cliente
        resp = client.get(f"/api/clientes/{cid}/extrato")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["resumo"]["total_compras"] == 0
        assert d["resumo"]["total_gasto"] == 0
        assert d["timeline"] == []

    def test_extrato_com_compras(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            _criar_venda(c, p, qtd=2, valor=Decimal("30.00"))
            cid = c.id_cliente
        resp = client.get(f"/api/clientes/{cid}/extrato")
        d = resp.get_json()
        assert d["resumo"]["total_compras"] == 1
        assert d["resumo"]["total_gasto"] == 30.0
        assert len(d["timeline"]) == 1
        assert d["timeline"][0]["tipo"] == "compra"
        assert len(d["timeline"][0]["itens"]) == 1

    def test_extrato_cliente_inexistente(self, client):
        resp = client.get("/api/clientes/99999/extrato")
        assert resp.status_code == 404


# =====================================================================
# Previsão de Estoque
# =====================================================================

class TestPrevisaoEstoque:
    def test_previsao_sem_produtos(self, client):
        resp = client.get("/api/estoque/previsao")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["total_produtos"] == 0
        assert d["dias_analise"] == 30

    def test_previsao_com_produtos(self, client, app):
        with app.app_context():
            _criar_produto(estoque=10)
            db.session.expire_all()
        resp = client.get("/api/estoque/previsao?dias=30")
        assert resp.status_code == 200
        d = resp.get_json()
        assert d["total_produtos"] >= 1
        p = d["previsoes"][0]
        assert "estoque_atual" in p
        assert "media_diaria" in p
        assert "nivel" in p

    def test_previsao_dias_custom(self, client, app):
        with app.app_context():
            _criar_produto()
            db.session.expire_all()
        resp = client.get("/api/estoque/previsao?dias=7")
        d = resp.get_json()
        assert d["dias_analise"] == 7

    def test_previsao_dias_clamped(self, client, app):
        """Dias < 7 devem virar 7, > 365 devem virar 365."""
        with app.app_context():
            _criar_produto()
            db.session.expire_all()
        resp = client.get("/api/estoque/previsao?dias=1")
        d = resp.get_json()
        assert d["dias_analise"] == 7

        resp2 = client.get("/api/estoque/previsao?dias=999")
        d2 = resp2.get_json()
        assert d2["dias_analise"] == 365

    def test_previsao_requer_auth(self, unauthenticated_client):
        resp = unauthenticated_client.get("/api/estoque/previsao")
        assert resp.status_code in (401, 302)


# =====================================================================
# Modelo BadgeCliente
# =====================================================================

class TestBadgeClienteModel:
    def test_criar_badge(self, app):
        with app.app_context():
            c = _criar_cliente()
            badge = BadgeCliente(
                id_cliente=c.id_cliente,
                codigo="test",
                nome="Teste",
                descricao="Desc",
                icone="🎯",
            )
            db.session.add(badge)
            db.session.commit()
            assert badge.id_badge is not None
            d = badge.to_dict()
            assert d["codigo"] == "test"
            assert d["icone"] == "🎯"

    def test_badge_relationship(self, app):
        with app.app_context():
            c = _criar_cliente()
            badge = BadgeCliente(
                id_cliente=c.id_cliente,
                codigo="rel_test",
                nome="Rel",
                descricao="D",
            )
            db.session.add(badge)
            db.session.commit()
            assert len(c.badges) == 1
            assert c.badges[0].codigo == "rel_test"
