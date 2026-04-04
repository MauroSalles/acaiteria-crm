"""
Testes para endpoints de IA/ML — Açaiteria CRM
Cobre: chatbot TF-IDF, recomendações, segmentação RFM,
       tendências, feedback loop, stats.
"""
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
        assert "senha" in data["resposta"].lower(
        ) or "login" in data["resposta"].lower()

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
        """PIX endpoint requer autenticação."""
        r = unauthenticated_client.get("/api/pix/qrcode?valor=10")
        assert r.status_code == 401

    def test_pix_qrcode_chave_presente(self, client):
        r = client.get("/api/pix/qrcode?valor=15")
        data = r.get_json()
        assert data["chave"]  # chave configurada via env


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


class TestCheckoutEstoque:
    """Checkout deve validar estoque disponível."""

    def test_checkout_estoque_insuficiente(self, client, app):
        with app.app_context():
            c = _criar_cliente(
                "Comprador", "11900000100", "comprador@t.com"
            )
            p = _criar_produto("Açaí Limitado", 15.0)
            p.estoque_atual = 2
            p.estoque_minimo = 1
            db.session.commit()

            with client.session_transaction() as sess:
                sess["cliente_id"] = c.id_cliente
                sess["cliente_nome"] = c.nome

            r = client.post(
                "/api/cliente/carrinho/checkout",
                json={
                    "itens": [
                        {
                            "id_produto": p.id_produto,
                            "quantidade": 10,
                        }
                    ],
                    "forma_pagamento": "Pix",
                },
            )
            assert r.status_code == 400
            assert "Estoque" in r.get_json()["erro"]

    def test_checkout_desconta_estoque(self, client, app):
        with app.app_context():
            c = _criar_cliente(
                "Comprador2", "11900000101", "compra2@t.com"
            )
            p = _criar_produto("Açaí Estoque", 10.0)
            p.estoque_atual = 5
            p.estoque_minimo = 1
            db.session.commit()
            pid = p.id_produto

            with client.session_transaction() as sess:
                sess["cliente_id"] = c.id_cliente
                sess["cliente_nome"] = c.nome

            r = client.post(
                "/api/cliente/carrinho/checkout",
                json={
                    "itens": [
                        {
                            "id_produto": pid,
                            "quantidade": 2,
                        }
                    ],
                    "forma_pagamento": "Pix",
                },
            )
            assert r.status_code == 201

            prod = db.session.get(Produto, pid)
            assert prod.estoque_atual == 3


# ── Testes de Complementos ───────────────────────────────────────────


class TestComplementos:
    """CRUD de complementos (admin)."""

    def test_criar_complemento(self, client, app):
        with app.app_context():
            r = client.post("/api/complementos", json={
                "nome": "Granola",
                "categoria": "Farináceo",
                "unidade_medida": "g",
                "preco_adicional": 2.50,
            })
            assert r.status_code == 201
            data = r.get_json()
            assert data["nome"] == "Granola"
            assert data["categoria"] == "Farináceo"
            assert data["preco_adicional"] == 2.50

    def test_criar_complemento_sem_nome(self, client, app):
        with app.app_context():
            r = client.post("/api/complementos", json={
                "categoria": "Fruta"
            })
            assert r.status_code == 400

    def test_listar_complementos(self, client, app):
        with app.app_context():
            from backend.models import Complemento
            from decimal import Decimal
            db.session.add(Complemento(
                nome="Leite Condensado", categoria="Calda",
                unidade_medida="ml", preco_adicional=Decimal("3.00"),
            ))
            db.session.commit()
            r = client.get("/api/complementos")
            assert r.status_code == 200
            data = r.get_json()
            assert len(data) >= 1
            assert data[0]["nome"] == "Leite Condensado"

    def test_atualizar_complemento(self, client, app):
        with app.app_context():
            from backend.models import Complemento
            from decimal import Decimal
            comp = Complemento(
                nome="Morango", categoria="Fruta",
                unidade_medida="g", preco_adicional=Decimal("2.00"),
            )
            db.session.add(comp)
            db.session.commit()
            cid = comp.id_complemento

            r = client.put(f"/api/complementos/{cid}", json={
                "preco_adicional": 3.50
            })
            assert r.status_code == 200
            assert r.get_json()["preco_adicional"] == 3.50

    def test_deletar_complemento(self, client, app):
        with app.app_context():
            from backend.models import Complemento
            comp = Complemento(nome="Paçoca", categoria="Farináceo")
            db.session.add(comp)
            db.session.commit()
            cid = comp.id_complemento

            r = client.delete(f"/api/complementos/{cid}")
            assert r.status_code == 200
            # Verificar soft delete
            assert db.session.get(Complemento, cid).ativo is False

    def test_vitrine_complementos_publico(self, unauthenticated_client, app):
        with app.app_context():
            from backend.models import Complemento
            db.session.add(Complemento(
                nome="Banana", categoria="Fruta", ativo=True
            ))
            db.session.add(Complemento(
                nome="Inativo", categoria="X", ativo=False
            ))
            db.session.commit()
            r = unauthenticated_client.get("/api/vitrine/complementos")
            assert r.status_code == 200
            nomes = [c["nome"] for c in r.get_json()]
            assert "Banana" in nomes
            assert "Inativo" not in nomes


# ── Testes de Produto com Volume ─────────────────────────────────────


class TestProdutoVolume:
    """Verifica campo volume no CRUD de produtos."""

    def test_criar_produto_com_volume(self, client, app):
        with app.app_context():
            r = client.post("/api/produtos", json={
                "nome_produto": "Açaí Premium",
                "preco": 19.90,
                "categoria": "Açaí",
                "volume": "10L",
            })
            assert r.status_code == 201
            assert r.get_json()["volume"] == "10L"

    def test_atualizar_volume(self, client, app):
        with app.app_context():
            p = Produto(
                nome_produto="Sorvete X", preco=12.00,
                categoria="Sorvete", volume="5L",
                estoque_atual=1, estoque_minimo=1, ativo=True,
            )
            db.session.add(p)
            db.session.commit()
            pid = p.id_produto

            r = client.put(f"/api/produtos/{pid}", json={
                "volume": "10L"
            })
            assert r.status_code == 200
            assert r.get_json()["volume"] == "10L"

    def test_vitrine_retorna_volume(self, unauthenticated_client, app):
        with app.app_context():
            db.session.add(Produto(
                nome_produto="Pitaya", preco=14.90,
                categoria="Sorvete", volume="10L",
                estoque_atual=1, estoque_minimo=1, ativo=True,
            ))
            db.session.commit()
            r = unauthenticated_client.get("/api/vitrine/produtos")
            assert r.status_code == 200
            ps = r.get_json()
            pitaya = [x for x in ps if x["nome_produto"] == "Pitaya"]
            assert len(pitaya) == 1
            assert pitaya[0]["volume"] == "10L"


# ── Teste Seed de Produtos ───────────────────────────────────────────


class TestSeedProdutos:
    """Verifica se o seed de produtos funciona corretamente."""

    def test_seed_cria_catalogo(self, app):
        with app.app_context():
            from backend.app import _seed_produtos
            # Limpar tabela
            Produto.query.delete()
            db.session.commit()
            _seed_produtos()
            total = Produto.query.count()
            assert total == 39  # 15 açaís + 24 sorvetes
            acais = Produto.query.filter_by(categoria="Açaí").count()
            assert acais == 15
            sorvetes = Produto.query.filter_by(categoria="Sorvete").count()
            assert sorvetes == 24

    def test_seed_substitui_dados_teste(self, app):
        with app.app_context():
            from backend.app import _seed_produtos
            # Se tem produto antigo sem o catálogo real, seed adiciona
            # sem deletar (preserva FKs de vendas existentes)
            Produto.query.delete()
            db.session.commit()
            db.session.add(Produto(
                nome_produto="Teste", preco=1.0,
                estoque_atual=0, estoque_minimo=0, ativo=True,
            ))
            db.session.commit()
            assert Produto.query.count() == 1
            _seed_produtos()  # adiciona catálogo real
            # 1 existente (Teste) + 39 novos = 40
            assert Produto.query.count() == 40
            acais = Produto.query.filter_by(categoria="Açaí").count()
            assert acais == 15

    def test_seed_nao_duplica_catalogo_real(self, app):
        with app.app_context():
            from backend.app import _seed_produtos
            # Se já tem >= 10 produtos, seed não roda
            Produto.query.delete()
            db.session.commit()
            _seed_produtos()
            assert Produto.query.count() == 39
            _seed_produtos()  # não deve duplicar
            assert Produto.query.count() == 39

    def test_seed_estoque_minimo_tradicional(self, app):
        with app.app_context():
            from backend.app import _seed_produtos
            Produto.query.delete()
            db.session.commit()
            _seed_produtos()
            trad = Produto.query.filter_by(
                nome_produto="Açaí Tradicional").first()
            assert trad is not None
            assert trad.estoque_minimo == 3
            assert trad.volume == "10L"
