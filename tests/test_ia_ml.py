"""
Testes para endpoints de IA/ML — Açaiteria CRM
Cobre: chatbot TF-IDF, recomendações, segmentação RFM,
       tendências, feedback loop, stats.
"""
import pytest
from backend.models import db, Cliente, Produto, Venda, ItemVenda


# ── helpers ──────────────────────────────────────────────────────────


def _criar_cliente(nome="Maria", telefone="11999990001",
                   email="maria@test.com", lgpd=True):
    c = Cliente(
        nome=nome, telefone=telefone, email=email,
        consentimento_lgpd=lgpd, ativo=True, pontos_fidelidade=0,
    )
    if lgpd:
        from datetime import datetime, timezone
        c.data_consentimento = datetime.now(timezone.utc)
    db.session.add(c)
    db.session.flush()
    return c


def _criar_produto(nome="Açaí 500ml", preco=15.0, cat="Açaí"):
    p = Produto(
        nome_produto=nome, categoria=cat, preco=preco,
        estoque_atual=100, estoque_minimo=5, ativo=True,
    )
    db.session.add(p)
    db.session.flush()
    return p


def _criar_venda(cliente, itens):
    """itens = [(produto, qtd), ...]"""
    total = sum(float(p.preco) * q for p, q in itens)
    v = Venda(
        id_cliente=cliente.id_cliente,
        valor_total=total,
        forma_pagamento="Pix",
        status_pagamento="Concluído",
    )
    db.session.add(v)
    db.session.flush()
    for p, q in itens:
        iv = ItemVenda(
            id_venda=v.id_venda, id_produto=p.id_produto,
            quantidade=q, preco_unitario=float(p.preco),
            subtotal=float(p.preco) * q,
        )
        db.session.add(iv)
    db.session.commit()
    return v


# ── Chatbot TF-IDF ──────────────────────────────────────────────────


class TestIAChatbot:
    def test_ia_resposta_senha(self, client):
        r = client.post("/api/suporte/ia-resposta",
                        json={"mensagem": "esqueci minha senha"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["ia"] is True
        assert data["confianca"] > 0
        assert "senha" in data["resposta"].lower() or "login" in data["resposta"].lower()

    def test_ia_resposta_venda(self, client):
        r = client.post("/api/suporte/ia-resposta",
                        json={"mensagem": "como registrar uma venda"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["confianca"] > 0
        assert data["metodo"] == "tfidf_cosine_similarity"

    def test_ia_resposta_curta(self, client):
        r = client.post("/api/suporte/ia-resposta",
                        json={"mensagem": "a"})
        assert r.status_code == 400

    def test_ia_resposta_sem_match(self, client):
        r = client.post("/api/suporte/ia-resposta",
                        json={"mensagem": "xyzabc123 nada relevante"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["confianca"] == 0 or data["metodo"] == "nenhum_match"

    def test_ia_resposta_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.post("/api/suporte/ia-resposta",
                                        json={"mensagem": "senha"})
        assert r.status_code == 401


# ── Recomendações ────────────────────────────────────────────────────


class TestIARecomendacoes:
    def test_recomendacao_cold_start(self, client, app):
        """Cliente sem compras → recebe recomendações por popularidade."""
        with app.app_context():
            c = _criar_cliente()
            p1 = _criar_produto("Açaí 1L", 20.0)
            # Criar outra cliente com compras para gerar popularidade
            c2 = _criar_cliente("João", "11999990002", "joao@test.com")
            _criar_venda(c2, [(p1, 3)])

            r = client.get(f"/api/ia/recomendacoes/{c.id_cliente}")
            assert r.status_code == 200
            data = r.get_json()
            assert data["metodo"] == "popularidade_cold_start"
            assert len(data["recomendacoes"]) >= 1

    def test_recomendacao_collaborative(self, client, app):
        """Clientes com histórico → collaborative filtering."""
        with app.app_context():
            p1 = _criar_produto("Açaí 500ml", 15.0)
            p2 = _criar_produto("Açaí 1L", 20.0)
            p3 = _criar_produto("Sorvete", 12.0)

            c1 = _criar_cliente("Ana", "11900000001", "ana@t.com")
            c2 = _criar_cliente("Bia", "11900000002", "bia@t.com")
            c3 = _criar_cliente("Cris", "11900000003", "cris@t.com")

            # Ana compra p1 e p2
            _criar_venda(c1, [(p1, 2), (p2, 1)])
            # Bia compra p1, p2 e p3 (similar a Ana, mas tem p3 extra)
            _criar_venda(c2, [(p1, 3), (p2, 2), (p3, 1)])
            # Cris compra p3
            _criar_venda(c3, [(p3, 5)])

            r = client.get(f"/api/ia/recomendacoes/{c1.id_cliente}")
            assert r.status_code == 200
            data = r.get_json()
            assert "recomendacoes" in data

    def test_recomendacao_cliente_inexistente(self, client):
        r = client.get("/api/ia/recomendacoes/99999")
        assert r.status_code == 404

    def test_recomendacao_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/ia/recomendacoes/1")
        assert r.status_code == 401


# ── Segmentação RFM ─────────────────────────────────────────────────


class TestIASegmentacao:
    def test_segmentacao_vazia(self, client, app):
        """Sem clientes com vendas → lista vazia."""
        with app.app_context():
            r = client.get("/api/ia/segmentacao")
            assert r.status_code == 200
            data = r.get_json()
            assert data["total_clientes"] == 0
            assert data["metodo"] == "rfm_analysis"

    def test_segmentacao_com_dados(self, client, app):
        """Clientes com vendas → gera segmentação."""
        with app.app_context():
            p = _criar_produto()
            c1 = _criar_cliente("Ana", "11900000001", "ana@t.com")
            c2 = _criar_cliente("Bia", "11900000002", "bia@t.com")
            _criar_venda(c1, [(p, 5)])
            _criar_venda(c1, [(p, 3)])
            _criar_venda(c2, [(p, 1)])

            r = client.get("/api/ia/segmentacao")
            assert r.status_code == 200
            data = r.get_json()
            assert data["total_clientes"] == 2
            assert len(data["segmentacao"]) == 2
            assert "resumo" in data
            # Cada item deve ter campos RFM
            item = data["segmentacao"][0]
            assert "recency" in item
            assert "frequency" in item
            assert "monetary" in item
            assert "segmento" in item

    def test_segmentacao_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/ia/segmentacao")
        assert r.status_code == 401


# ── Tendências ───────────────────────────────────────────────────────


class TestIATendencias:
    def test_tendencias_sem_dados(self, client, app):
        with app.app_context():
            r = client.get("/api/ia/tendencias")
            assert r.status_code == 200
            data = r.get_json()
            assert data["total_vendas"] == 0
            assert data["metodo"] == "regressao_linear_simples"

    def test_tendencias_com_vendas(self, client, app):
        with app.app_context():
            p = _criar_produto()
            c = _criar_cliente()
            _criar_venda(c, [(p, 2)])
            _criar_venda(c, [(p, 3)])

            r = client.get("/api/ia/tendencias?dias=30")
            assert r.status_code == 200
            data = r.get_json()
            assert data["total_vendas"] == 2
            assert "receita_total" in data
            assert "tendencia" in data
            assert "regressao" in data

    def test_tendencias_parametro_dias(self, client, app):
        r = client.get("/api/ia/tendencias?dias=7")
        assert r.status_code == 200
        data = r.get_json()
        assert data["periodo_dias"] == 7

    def test_tendencias_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/ia/tendencias")
        assert r.status_code == 401


# ── Feedback Loop ────────────────────────────────────────────────────


class TestIAFeedback:
    def test_feedback_positivo(self, client):
        r = client.post("/api/suporte/ia-feedback",
                        json={"util": True, "pergunta": "como vender"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["registrado"] is True
        assert data["stats"]["positivo"] >= 1

    def test_feedback_negativo(self, client):
        r = client.post("/api/suporte/ia-feedback",
                        json={"util": False, "pergunta": "nada"})
        assert r.status_code == 200
        data = r.get_json()
        assert data["registrado"] is True

    def test_feedback_sem_campo_util(self, client):
        r = client.post("/api/suporte/ia-feedback",
                        json={"pergunta": "teste"})
        assert r.status_code == 400

    def test_feedback_campo_invalido(self, client):
        r = client.post("/api/suporte/ia-feedback",
                        json={"util": "sim"})
        assert r.status_code == 400

    def test_feedback_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.post("/api/suporte/ia-feedback",
                                        json={"util": True})
        assert r.status_code == 401


# ── Stats ────────────────────────────────────────────────────────────


class TestIAStats:
    def test_stats_retorna_info(self, client):
        r = client.get("/api/ia/stats")
        assert r.status_code == 200
        data = r.get_json()
        assert data["engine"]["tipo"] == "TF-IDF + Cosine Similarity"
        assert data["engine"]["documentos_treinados"] == 12
        assert len(data["modulos"]) == 5

    def test_stats_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/ia/stats")
        assert r.status_code == 401


# ── PIX QR Code ──────────────────────────────────────────────────────


class TestPixQRCode:
    def test_pix_qrcode_com_valor(self, client):
        r = client.get("/api/pix/qrcode?valor=25.50&txid=Pedido1")
        assert r.status_code == 200
        data = r.get_json()
        assert "payload" in data
        assert data["valor"] == 25.50
        # Payload deve ser BRCode EMV válido: começa com 00 02 01
        assert data["payload"].startswith("000201")
        # Deve conter br.gov.bcb.pix
        assert "br.gov.bcb.pix" in data["payload"]
        # Deve terminar com CRC16 (4 hex chars)
        assert len(data["payload"]) > 20

    def test_pix_qrcode_sem_valor(self, client):
        r = client.get("/api/pix/qrcode")
        assert r.status_code == 200
        data = r.get_json()
        assert data["valor"] == 0
        assert data["payload"].startswith("000201")

    def test_pix_qrcode_valor_negativo(self, client):
        r = client.get("/api/pix/qrcode?valor=-10")
        assert r.status_code == 400

    def test_pix_qrcode_sem_auth(self, unauthenticated_client):
        """PIX endpoint deve ser público (sem autenticação)."""
        r = unauthenticated_client.get("/api/pix/qrcode?valor=10")
        assert r.status_code == 200

    def test_pix_qrcode_chave_presente(self, client):
        r = client.get("/api/pix/qrcode?valor=15")
        data = r.get_json()
        assert "@" in data["chave"]  # É email


# ── Checkout LGPD ────────────────────────────────────────────────────


class TestCheckoutLGPD:
    def test_checkout_bloqueado_sem_lgpd(self, client, app):
        """Checkout deve ser bloqueado se cliente não tem consentimento LGPD."""
        with app.app_context():
            c = _criar_cliente("Sem LGPD", "11900000099",
                               "semlgpd@t.com", lgpd=False)
            p = _criar_produto()
            db.session.commit()

            # Simular login do cliente
            with client.session_transaction() as sess:
                sess["cliente_id"] = c.id_cliente
                sess["cliente_nome"] = c.nome

            r = client.post("/api/cliente/carrinho/checkout", json={
                "itens": [{"id_produto": p.id_produto, "quantidade": 1}],
                "forma_pagamento": "Pix",
            })
            assert r.status_code == 403
            assert "LGPD" in r.get_json()["erro"]
