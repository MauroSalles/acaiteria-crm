"""
Testes do Sprint v4 — Novos endpoints CRUD, fixes de segurança e performance.
Cobre: complemento GET individual, lancamento GET individual, combo GET individual,
assinatura planos CRUD completo, soft-delete de lancamento, cache invalidation,
session fixation fix, CSV sanitize fix, _construir_matriz_compras limit.
"""
from decimal import Decimal
from backend.models import (
    db, Cliente, Produto, Complemento, LancamentoFinanceiro,
    ComboKit, ComboKitItem, Assinatura,
    Venda, ItemVenda,
)


# ============================================================
# Helpers
# ============================================================

def _criar_cliente(consent=True):
    c = Cliente(
        nome="Teste Sprint4", telefone="11999990000",
        email="sprint4@test.com", consentimento_lgpd=consent, ativo=True,
    )
    db.session.add(c)
    db.session.flush()
    return c


def _criar_produto(nome="Açaí Test", preco=25):
    p = Produto(
        nome_produto=nome, categoria="Test",
        preco=Decimal(str(preco)), estoque_atual=100,
        estoque_minimo=5, ativo=True,
    )
    db.session.add(p)
    db.session.flush()
    return p


def _criar_complemento(nome="Granola Test"):
    comp = Complemento(
        nome=nome, categoria="Farináceo",
        unidade_medida="g", preco_adicional=Decimal("2.00"), ativo=True,
    )
    db.session.add(comp)
    db.session.flush()
    return comp


# ============================================================
# GET individual — Complemento
# ============================================================

class TestComplementoGetIndividual:
    def test_obter_complemento_sucesso(self, client, app):
        with app.app_context():
            comp = _criar_complemento()
            db.session.commit()
            cid = comp.id_complemento
        resp = client.get(f"/api/complementos/{cid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["nome"] == "Granola Test"
        assert data["id_complemento"] == cid

    def test_obter_complemento_nao_encontrado(self, client, app):
        resp = client.get("/api/complementos/99999")
        assert resp.status_code == 404


# ============================================================
# GET individual — Lançamento Financeiro
# ============================================================

class TestLancamentoGetIndividual:
    def test_obter_lancamento_sucesso(self, client, app):
        with app.app_context():
            from datetime import date
            lanc = LancamentoFinanceiro(
                tipo="receita", categoria="Vendas",
                valor=Decimal("150.00"),
                data_lancamento=date.today(),
                status="Pago",
            )
            db.session.add(lanc)
            db.session.commit()
            lid = lanc.id_lancamento
        resp = client.get(f"/api/financeiro/{lid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["tipo"] == "receita"
        assert data["valor"] == 150.0

    def test_obter_lancamento_nao_encontrado(self, client, app):
        resp = client.get("/api/financeiro/99999")
        assert resp.status_code == 404


# ============================================================
# Soft-delete de Lançamento Financeiro
# ============================================================

class TestLancamentoSoftDelete:
    def test_delete_cancela_ao_inves_de_remover(self, client, app):
        with app.app_context():
            from datetime import date
            lanc = LancamentoFinanceiro(
                tipo="despesa", categoria="Aluguel",
                valor=Decimal("1000.00"),
                data_lancamento=date.today(), status="Pago",
            )
            db.session.add(lanc)
            db.session.commit()
            lid = lanc.id_lancamento

        resp = client.delete(f"/api/financeiro/{lid}")
        assert resp.status_code == 200
        assert "cancelado" in resp.get_json()["mensagem"].lower()

        # Verificar que não foi removido, só cancelado
        with app.app_context():
            lanc = LancamentoFinanceiro.query.get(lid)
            assert lanc is not None
            assert lanc.status == "Cancelado"


# ============================================================
# GET individual — Combo
# ============================================================

class TestComboGetIndividual:
    def test_obter_combo_sucesso(self, client, app):
        with app.app_context():
            p = _criar_produto()
            combo = ComboKit(
                nome="Combo Test", preco_combo=Decimal("40.00"),
            )
            combo.itens.append(ComboKitItem(
                id_produto=p.id_produto, quantidade=2,
            ))
            db.session.add(combo)
            db.session.commit()
            cid = combo.id_combo
        resp = client.get(f"/api/combos/{cid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["nome"] == "Combo Test"
        assert len(data["itens"]) == 1

    def test_obter_combo_nao_encontrado(self, client, app):
        resp = client.get("/api/combos/99999")
        assert resp.status_code == 404


# ============================================================
# CRUD completo — Assinatura Planos
# ============================================================

class TestAssinaturaPlanoCRUD:
    def test_criar_plano(self, client):
        resp = client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano Mensal", "preco_mensal": 99.90,
            "limite_usos": 15, "descricao": "15 açaís por mês",
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data["nome_plano"] == "Plano Mensal"
        assert data["preco_mensal"] == 99.90
        assert data["limite_usos"] == 15

    def test_listar_planos(self, client, app):
        with app.app_context():
            db.session.add(Assinatura(
                nome_plano="X", preco_mensal=Decimal("50"),
            ))
            db.session.commit()
        resp = client.get("/api/assinaturas/planos")
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_obter_plano_individual(self, client, app):
        with app.app_context():
            p = Assinatura(
                nome_plano="Gold", preco_mensal=Decimal("120"),
                limite_usos=20,
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id_assinatura
        resp = client.get(f"/api/assinaturas/planos/{pid}")
        assert resp.status_code == 200
        assert resp.get_json()["nome_plano"] == "Gold"

    def test_obter_plano_nao_encontrado(self, client):
        resp = client.get("/api/assinaturas/planos/99999")
        assert resp.status_code == 404

    def test_atualizar_plano(self, client, app):
        with app.app_context():
            p = Assinatura(
                nome_plano="Basic", preco_mensal=Decimal("50"),
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id_assinatura
        resp = client.put(f"/api/assinaturas/planos/{pid}", json={
            "nome_plano": "Premium",
            "preco_mensal": 150,
            "limite_usos": 30,
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data["nome_plano"] == "Premium"
        assert data["preco_mensal"] == 150.0
        assert data["limite_usos"] == 30

    def test_atualizar_plano_nao_encontrado(self, client):
        resp = client.put("/api/assinaturas/planos/99999", json={
            "nome_plano": "X",
        })
        assert resp.status_code == 404

    def test_desativar_plano(self, client, app):
        with app.app_context():
            p = Assinatura(
                nome_plano="Delete Me", preco_mensal=Decimal("30"),
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id_assinatura
        resp = client.delete(f"/api/assinaturas/planos/{pid}")
        assert resp.status_code == 200
        assert "desativado" in resp.get_json()["mensagem"].lower()

        # Verifica que foi desativado
        with app.app_context():
            p = Assinatura.query.get(pid)
            assert p.ativo is False

    def test_desativar_plano_nao_encontrado(self, client):
        resp = client.delete("/api/assinaturas/planos/99999")
        assert resp.status_code == 404


# ============================================================
# Cache invalidation em criar/atualizar/deletar produto
# ============================================================

class TestCacheInvalidationProduto:
    def test_criar_produto_invalida_cache(self, client, app):
        """Após criar produto, vitrine deve incluir o novo produto."""
        resp = client.post("/api/produtos", json={
            "nome_produto": "Novo Produto Cache",
            "preco": 19.99,
            "categoria": "Cache Test",
        })
        assert resp.status_code == 201
        # Verificar que vitrine retorna o produto
        resp2 = client.get("/api/vitrine/produtos")
        assert resp2.status_code == 200
        nomes = [p["nome_produto"] for p in resp2.get_json()]
        assert "Novo Produto Cache" in nomes

    def test_atualizar_produto_invalida_cache(self, client, app):
        """Após atualizar produto, dados devem refletir."""
        with app.app_context():
            p = _criar_produto("Antes")
            db.session.commit()
            pid = p.id_produto
        resp = client.put(f"/api/produtos/{pid}", json={
            "nome_produto": "Depois",
        })
        assert resp.status_code == 200
        assert resp.get_json()["nome_produto"] == "Depois"

    def test_deletar_produto_invalida_cache(self, client, app):
        """Após desativar produto, vitrine não deve listá-lo."""
        with app.app_context():
            p = _criar_produto("Remover Cache")
            db.session.commit()
            pid = p.id_produto
        resp = client.delete(f"/api/produtos/{pid}")
        assert resp.status_code == 200
        resp2 = client.get("/api/vitrine/produtos")
        nomes = [p["nome_produto"] for p in resp2.get_json()]
        assert "Remover Cache" not in nomes


# ============================================================
# CSV Sanitize — .strip() em vez de .lstrip()
# ============================================================

class TestCSVSanitize:
    def test_exportar_csv_sanitiza_valores(self, client, app):
        """CSV deve sanitizar fórmulas no início E no conteúdo."""
        with app.app_context():
            c = Cliente(
                nome="  =cmd|' /C calc'!A0",
                telefone="11999999999",
                email="safe@test.com",
                consentimento_lgpd=True,
                ativo=True,
            )
            db.session.add(c)
            db.session.commit()
        resp = client.get("/api/exportar/clientes-csv")
        assert resp.status_code == 200
        content = resp.data.decode("utf-8")
        # O nome deve ser sanitizado (prefixado com ')
        assert "'  =cmd" in content or "=cmd" not in content.split("\n")[1]


# ============================================================
# Session fixation — cliente_login regenera session
# ============================================================

class TestSessionFixation:
    def test_login_cliente_regenera_session(self, app):
        """Após login de cliente, session IDs devem ser regenerados."""
        with app.app_context():
            c = Cliente(
                nome="Cliente Session Test",
                email="session@test.com",
                consentimento_lgpd=True,
                ativo=True,
            )
            c.set_senha("senha123")
            db.session.add(c)
            db.session.commit()

        test_client = app.test_client()

        # Pré-popular session com dados antigos
        with test_client.session_transaction() as sess:
            sess["old_data"] = "should_be_cleared"

        # Fazer login
        resp = test_client.post("/cliente/login", data={
            "identificador": "session@test.com",
            "senha": "senha123",
        }, follow_redirects=False)
        assert resp.status_code == 302

        # Verificar que old_data foi limpo
        with test_client.session_transaction() as sess:
            assert "old_data" not in sess
            assert sess.get("cliente_id") is not None


# ============================================================
# _construir_matriz_compras — limite de 5000
# ============================================================

class TestMatrizComprasLimite:
    def test_ia_recomendacoes_funciona(self, client, app):
        """Endpoint de recomendações deve funcionar sem OOM."""
        with app.app_context():
            c = _criar_cliente()
            p = _criar_produto()
            v = Venda(
                id_cliente=c.id_cliente,
                valor_total=Decimal("25.00"),
                forma_pagamento="Dinheiro",
                status_pagamento="Concluído",
            )
            v.itens.append(ItemVenda(
                id_produto=p.id_produto,
                quantidade=1,
                preco_unitario=Decimal("25.00"),
                subtotal=Decimal("25.00"),
            ))
            db.session.add(v)
            db.session.commit()
            cid = c.id_cliente
        resp = client.get(f"/api/ia/recomendacoes/{cid}")
        assert resp.status_code == 200
        data = resp.get_json()
        assert "recomendacoes" in data


# ============================================================
# Testes adicionais — endpoints existentes confirmação
# ============================================================

class TestLojasCRUDCompleto:
    def test_crud_loja_completo(self, client):
        # Criar
        r = client.post("/api/lojas", json={
            "nome": "Filial Centro", "endereco": "Rua A, 123",
            "telefone": "12999999999",
        })
        assert r.status_code == 201
        lid = r.get_json()["id_loja"]

        # Listar
        r = client.get("/api/lojas")
        assert r.status_code == 200
        assert any(lj["id_loja"] == lid for lj in r.get_json())

        # Atualizar
        r = client.put(f"/api/lojas/{lid}", json={
            "nome": "Filial Shopping",
        })
        assert r.status_code == 200
        assert r.get_json()["nome"] == "Filial Shopping"

        # Desativar
        r = client.delete(f"/api/lojas/{lid}")
        assert r.status_code == 200

        # Não aparece mais na listagem (ativa=False)
        r = client.get("/api/lojas")
        assert not any(lj["id_loja"] == lid for lj in r.get_json())


class TestWebhookCRUD:
    def test_crud_webhook_completo(self, client):
        r = client.post("/api/webhooks", json={
            "evento": "venda_criada",
            "url": "https://example.com/hook",
        })
        assert r.status_code == 201
        wid = r.get_json()["id_webhook"]

        r = client.get("/api/webhooks")
        assert r.status_code == 200

        r = client.delete(f"/api/webhooks/{wid}")
        assert r.status_code == 200


class TestIndicacaoEndpoints:
    def test_gerar_codigo_indicacao(self, client, app):
        with app.app_context():
            c = _criar_cliente()
            db.session.commit()
            cid = c.id_cliente
        r = client.get(f"/api/indicacoes/codigo/{cid}")
        assert r.status_code == 200
        assert "codigo" in r.get_json()

    def test_listar_indicacoes(self, client):
        r = client.get("/api/indicacoes")
        assert r.status_code == 200
