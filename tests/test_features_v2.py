"""
Testes das features v2 — 2FA, Combos, Indicações, Assinaturas,
Webhooks, Upload de Foto, Agendamento, Multi-Loja, NFC-e,
Cursor Pagination, API Versioning, OpenAPI, Email, Painel Cliente.
"""
from decimal import Decimal
import pyotp

from backend.models import (
    db, Cliente, Produto, Venda, ItemVenda,
)


# =====================================================================
# Helpers
# =====================================================================

def _cliente(consentimento=True):
    c = Cliente(
        nome="Cliente V2", email="v2@email.com", telefone="11999990000",
        consentimento_lgpd=consentimento, ativo=True, pontos_fidelidade=0,
    )
    db.session.add(c)
    db.session.commit()
    return c


def _produto(nome="Açaí 500ml", preco=15.0, estoque=100):
    p = Produto(
        nome_produto=nome, preco=Decimal(str(preco)),
        categoria="Açaí", ativo=True,
        estoque_atual=estoque, estoque_minimo=5,
    )
    db.session.add(p)
    db.session.commit()
    return p


def _venda(cliente, produto, qtd=1, valor=None):
    v = Venda(
        id_cliente=cliente.id_cliente,
        forma_pagamento="PIX", status_pagamento="Concluído",
        status_pedido="Entregue",
        valor_total=valor or Decimal(str(produto.preco * qtd)),
    )
    item = ItemVenda(
        id_produto=produto.id_produto, quantidade=qtd,
        preco_unitario=produto.preco, subtotal=produto.preco * qtd,
    )
    v.itens.append(item)
    db.session.add(v)
    db.session.commit()
    return v


def _cliente_session(test_client, cliente_id):
    """Client HTTP autenticado como cliente (painel do cliente)."""
    with test_client.session_transaction() as sess:
        sess["autenticado"] = True
        sess["cliente_id"] = cliente_id


# =====================================================================
# API VERSION
# =====================================================================

class TestAPIVersion:
    def test_version(self, client):
        r = client.get("/api/version")
        assert r.status_code == 200
        d = r.get_json()
        assert "version" in d
        assert "prefix" in d

    def test_version_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/version")
        assert r.status_code == 200


# =====================================================================
# OPENAPI EXPORT
# =====================================================================

class TestOpenAPI:
    def test_openapi_json(self, client):
        r = client.get("/api/openapi.json")
        assert r.status_code == 200
        d = r.get_json()
        assert "swagger" in d or "openapi" in d
        assert "paths" in d

    def test_openapi_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/openapi.json")
        assert r.status_code == 200


# =====================================================================
# CURSOR PAGINATION
# =====================================================================

class TestCursorPagination:
    def test_cursor_vazio(self, client):
        r = client.get("/api/vendas/cursor")
        assert r.status_code == 200
        d = r.get_json()
        assert d["vendas"] == []
        assert d["has_next"] is False

    def test_cursor_com_dados(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            for _ in range(5):
                _venda(c, p)
        r = client.get("/api/vendas/cursor?limit=3")
        d = r.get_json()
        assert len(d["vendas"]) == 3
        assert d["has_next"] is True
        assert d["next_cursor"] is not None

    def test_cursor_segunda_pagina(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            for _ in range(5):
                _venda(c, p)
        r1 = client.get("/api/vendas/cursor?limit=3")
        d1 = r1.get_json()
        cursor = d1["next_cursor"]
        r2 = client.get(f"/api/vendas/cursor?after_id={cursor}&limit=3")
        d2 = r2.get_json()
        assert len(d2["vendas"]) == 2
        assert d2["has_next"] is False

    def test_cursor_filtro_status(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            _venda(c, p)
        r = client.get("/api/vendas/cursor?status=Concluído")
        d = r.get_json()
        assert len(d["vendas"]) >= 1

    def test_cursor_requer_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/vendas/cursor")
        assert r.status_code in (401, 302)


# =====================================================================
# 2FA (TWO-FACTOR AUTHENTICATION)
# =====================================================================

class TestTwoFactor:
    def test_2fa_setup(self, client, app):
        r = client.post("/api/2fa/setup")
        assert r.status_code == 200
        d = r.get_json()
        assert "secret" in d
        assert "uri" in d

    def test_2fa_verify_e_ativar(self, client, app):
        r1 = client.post("/api/2fa/setup")
        secret = r1.get_json()["secret"]
        codigo = pyotp.TOTP(secret).now()
        r2 = client.post(
            "/api/2fa/verify",
            json={"codigo": codigo},
        )
        assert r2.status_code == 200
        assert "ativado" in r2.get_json()["mensagem"].lower()

    def test_2fa_verify_codigo_invalido(self, client, app):
        client.post("/api/2fa/setup")
        r = client.post(
            "/api/2fa/verify",
            json={"codigo": "000000"},
        )
        assert r.status_code == 400

    def test_2fa_status_inativo(self, client):
        r = client.get("/api/2fa/status")
        assert r.status_code == 200
        d = r.get_json()
        assert d["ativo"] is False

    def test_2fa_status_ativo(self, client, app):
        r1 = client.post("/api/2fa/setup")
        secret = r1.get_json()["secret"]
        codigo = pyotp.TOTP(secret).now()
        client.post("/api/2fa/verify", json={"codigo": codigo})
        r = client.get("/api/2fa/status")
        assert r.get_json()["ativo"] is True

    def test_2fa_disable(self, client, app):
        r1 = client.post("/api/2fa/setup")
        secret = r1.get_json()["secret"]
        codigo = pyotp.TOTP(secret).now()
        client.post("/api/2fa/verify", json={"codigo": codigo})
        r = client.post("/api/2fa/disable")
        assert r.status_code == 200
        status = client.get("/api/2fa/status").get_json()
        assert status["ativo"] is False

    def test_2fa_requer_auth(self, unauthenticated_client):
        r = unauthenticated_client.post("/api/2fa/setup")
        assert r.status_code in (401, 302)


# =====================================================================
# UPLOAD DE FOTO DO PRODUTO
# =====================================================================

class TestFotoProduto:
    def test_upload_foto_url(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        r = client.post(
            f"/api/produtos/{pid}/foto",
            json={"foto_url": "https://example.com/foto.jpg"},
        )
        assert r.status_code == 200
        assert "mensagem" in r.get_json()

    def test_upload_foto_base64(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        r = client.post(
            f"/api/produtos/{pid}/foto",
            json={"foto_url": "data:image/png;base64,iVBORw0KGgo="},
        )
        assert r.status_code == 200

    def test_upload_foto_url_invalida(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        r = client.post(
            f"/api/produtos/{pid}/foto",
            json={"foto_url": "ftp://invalid.com/foto.jpg"},
        )
        assert r.status_code == 400

    def test_upload_foto_produto_inexistente(self, client):
        r = client.post(
            "/api/produtos/99999/foto",
            json={"foto_url": "https://example.com/foto.jpg"},
        )
        assert r.status_code == 404

    def test_upload_foto_requer_admin(self, app):
        test_client = app.test_client()
        with test_client.session_transaction() as sess:
            sess["autenticado"] = True
            sess["usuario_id"] = 1
            sess["papel"] = "operador"
        r = test_client.post(
            "/api/produtos/1/foto",
            json={"foto_url": "https://example.com/foto.jpg"},
        )
        assert r.status_code in (403, 401)


# =====================================================================
# WEBHOOKS
# =====================================================================

class TestWebhooks:
    def test_criar_webhook(self, client):
        r = client.post("/api/webhooks", json={
            "evento": "venda_criada",
            "url": "https://example.com/hook",
        })
        assert r.status_code == 201
        d = r.get_json()
        assert d["evento"] == "venda_criada"
        assert "id_webhook" in d

    def test_listar_webhooks(self, client):
        client.post("/api/webhooks", json={
            "evento": "cliente_novo",
            "url": "https://example.com/hook",
        })
        r = client.get("/api/webhooks")
        assert r.status_code == 200
        assert len(r.get_json()) >= 1

    def test_deletar_webhook(self, client):
        r1 = client.post("/api/webhooks", json={
            "evento": "venda_criada",
            "url": "https://example.com/hook",
        })
        wid = r1.get_json()["id_webhook"]
        r = client.delete(f"/api/webhooks/{wid}")
        assert r.status_code == 200

    def test_webhook_evento_invalido(self, client):
        r = client.post("/api/webhooks", json={
            "evento": "evento_invalido",
            "url": "https://example.com/hook",
        })
        assert r.status_code == 400

    def test_webhook_url_nao_https(self, client):
        r = client.post("/api/webhooks", json={
            "evento": "venda_criada",
            "url": "http://inseguro.com/hook",
        })
        assert r.status_code == 400

    def test_webhook_requer_admin(self, app):
        tc = app.test_client()
        with tc.session_transaction() as sess:
            sess["autenticado"] = True
            sess["usuario_id"] = 1
            sess["papel"] = "operador"
        r = tc.get("/api/webhooks")
        assert r.status_code in (403, 401)


# =====================================================================
# COMBOS / KITS
# =====================================================================

class TestCombos:
    def test_criar_combo(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        r = client.post("/api/combos", json={
            "nome": "Combo Família",
            "descricao": "2 açaís",
            "preco_combo": 25.0,
            "itens": [{"id_produto": pid, "quantidade": 2}],
        })
        assert r.status_code == 201
        d = r.get_json()
        assert d["nome"] == "Combo Família"
        assert len(d["itens"]) == 1

    def test_listar_combos(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        client.post("/api/combos", json={
            "nome": "Combo A", "preco_combo": 20.0,
            "itens": [{"id_produto": pid, "quantidade": 1}],
        })
        r = client.get("/api/combos")
        assert r.status_code == 200
        assert len(r.get_json()) >= 1

    def test_atualizar_combo(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        r1 = client.post("/api/combos", json={
            "nome": "Combo B", "preco_combo": 20.0,
            "itens": [{"id_produto": pid, "quantidade": 1}],
        })
        cid = r1.get_json()["id_combo"]
        r = client.put(f"/api/combos/{cid}", json={
            "nome": "Combo B Atualizado",
            "preco_combo": 22.0,
        })
        assert r.status_code == 200
        assert r.get_json()["nome"] == "Combo B Atualizado"

    def test_desativar_combo(self, client, app):
        with app.app_context():
            p = _produto()
            pid = p.id_produto
        r1 = client.post("/api/combos", json={
            "nome": "Combo C", "preco_combo": 20.0,
            "itens": [{"id_produto": pid, "quantidade": 1}],
        })
        cid = r1.get_json()["id_combo"]
        r = client.delete(f"/api/combos/{cid}")
        assert r.status_code == 200

    def test_combo_economia(self, client, app):
        with app.app_context():
            p = _produto(preco=15.0)
            pid = p.id_produto
        r = client.post("/api/combos", json={
            "nome": "Combo Eco", "preco_combo": 25.0,
            "itens": [{"id_produto": pid, "quantidade": 2}],
        })
        d = r.get_json()
        assert d["economia"] == 5.0

    def test_combo_sem_itens(self, client):
        r = client.post("/api/combos", json={
            "nome": "Combo Vazio", "preco_combo": 10.0,
            "itens": [],
        })
        assert r.status_code == 400


# =====================================================================
# INDICAÇÕES (REFERRAL)
# =====================================================================

class TestIndicacoes:
    def test_gerar_codigo_indicacao(self, client, app):
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        r = client.get(f"/api/indicacoes/codigo/{cid}")
        assert r.status_code == 200
        d = r.get_json()
        assert "codigo" in d
        assert len(d["codigo"]) > 0

    def test_validar_indicacao(self, client, app):
        with app.app_context():
            c1 = _cliente()
            c2 = Cliente(
                nome="Indicado", email="ind@email.com",
                telefone="11888880000", consentimento_lgpd=True,
                ativo=True, pontos_fidelidade=0,
            )
            db.session.add(c2)
            db.session.commit()
            cid1, cid2 = c1.id_cliente, c2.id_cliente
        r1 = client.get(f"/api/indicacoes/codigo/{cid1}")
        codigo = r1.get_json()["codigo"]
        r2 = client.post("/api/indicacoes/validar", json={
            "codigo": codigo,
            "id_cliente_indicado": cid2,
        })
        assert r2.status_code == 200
        d = r2.get_json()
        assert d["indicador_pontos"] == 50
        assert d["indicado_pontos"] == 50

    def test_indicacao_duplicada(self, client, app):
        with app.app_context():
            c1 = _cliente()
            c2 = Cliente(
                nome="Indicado2", email="ind2@email.com",
                telefone="11777770000", consentimento_lgpd=True,
                ativo=True, pontos_fidelidade=0,
            )
            db.session.add(c2)
            db.session.commit()
            cid1, cid2 = c1.id_cliente, c2.id_cliente
        r1 = client.get(f"/api/indicacoes/codigo/{cid1}")
        codigo = r1.get_json()["codigo"]
        client.post("/api/indicacoes/validar", json={
            "codigo": codigo, "id_cliente_indicado": cid2,
        })
        r3 = client.post("/api/indicacoes/validar", json={
            "codigo": codigo, "id_cliente_indicado": cid2,
        })
        assert r3.status_code == 400

    def test_indicacao_mesmo_cliente(self, client, app):
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        r1 = client.get(f"/api/indicacoes/codigo/{cid}")
        codigo = r1.get_json()["codigo"]
        r = client.post("/api/indicacoes/validar", json={
            "codigo": codigo, "id_cliente_indicado": cid,
        })
        assert r.status_code == 400

    def test_listar_indicacoes(self, client):
        r = client.get("/api/indicacoes")
        assert r.status_code == 200
        assert isinstance(r.get_json(), list)

    def test_codigo_invalido(self, client):
        r = client.post("/api/indicacoes/validar", json={
            "codigo": "INEXISTENTE", "id_cliente_indicado": 999,
        })
        assert r.status_code == 404


# =====================================================================
# AGENDAMENTO
# =====================================================================

class TestAgendamento:
    def test_agendar_venda(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            v = _venda(c, p)
            vid = v.id_venda
        r = client.put(f"/api/vendas/{vid}/agendar", json={
            "data_agendamento": "2099-12-31T14:30:00",
        })
        assert r.status_code == 200
        d = r.get_json()
        assert "data_agendamento" in d

    def test_agendar_sem_data(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            v = _venda(c, p)
            vid = v.id_venda
        r = client.put(f"/api/vendas/{vid}/agendar", json={})
        assert r.status_code == 400

    def test_agendar_venda_inexistente(self, client):
        r = client.put("/api/vendas/99999/agendar", json={
            "data_agendamento": "2099-12-31T14:30:00",
        })
        assert r.status_code == 404

    def test_listar_agendamentos(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            v = _venda(c, p)
            vid = v.id_venda
        client.put(f"/api/vendas/{vid}/agendar", json={
            "data_agendamento": "2099-12-31T14:30:00",
        })
        r = client.get("/api/agendamentos")
        assert r.status_code == 200
        assert len(r.get_json()) >= 1

    def test_agendamento_requer_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/agendamentos")
        assert r.status_code in (401, 302)


# =====================================================================
# ASSINATURAS / PLANOS MENSAIS
# =====================================================================

class TestAssinaturas:
    def test_criar_plano(self, client):
        r = client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano Açaí 10",
            "descricao": "10 açaís por mês",
            "preco_mensal": 89.90,
            "limite_usos": 10,
        })
        assert r.status_code == 201
        d = r.get_json()
        assert d["nome_plano"] == "Plano Açaí 10"
        assert d["limite_usos"] == 10

    def test_listar_planos(self, client):
        client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano X", "preco_mensal": 50.0,
            "limite_usos": 5,
        })
        r = client.get("/api/assinaturas/planos")
        assert r.status_code == 200
        assert len(r.get_json()) >= 1

    def test_assinar_plano(self, client, app):
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        r1 = client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano Teste", "preco_mensal": 50.0,
            "limite_usos": 5,
        })
        id_ass = r1.get_json()["id_assinatura"]
        r = client.post("/api/assinaturas/assinar", json={
            "id_assinatura": id_ass, "id_cliente": cid,
        })
        assert r.status_code == 201
        d = r.get_json()
        assert d["status"] == "ativa"

    def test_usar_assinatura(self, client, app):
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        r1 = client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano Uso", "preco_mensal": 50.0,
            "limite_usos": 3,
        })
        id_ass = r1.get_json()["id_assinatura"]
        r2 = client.post("/api/assinaturas/assinar", json={
            "id_assinatura": id_ass, "id_cliente": cid,
        })
        acid = r2.get_json()["id"]
        r = client.post(f"/api/assinaturas/{acid}/usar")
        assert r.status_code == 200
        d = r.get_json()
        assert d["usos_restantes"] == 2

    def test_usar_assinatura_esgotada(self, client, app):
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        r1 = client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano Mini", "preco_mensal": 30.0,
            "limite_usos": 1,
        })
        id_ass = r1.get_json()["id_assinatura"]
        r2 = client.post("/api/assinaturas/assinar", json={
            "id_assinatura": id_ass, "id_cliente": cid,
        })
        acid = r2.get_json()["id"]
        client.post(f"/api/assinaturas/{acid}/usar")
        r = client.post(f"/api/assinaturas/{acid}/usar")
        assert r.status_code == 400

    def test_assinaturas_do_cliente(self, client, app):
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        r1 = client.post("/api/assinaturas/planos", json={
            "nome_plano": "Plano List", "preco_mensal": 50.0,
            "limite_usos": 5,
        })
        id_ass = r1.get_json()["id_assinatura"]
        client.post("/api/assinaturas/assinar", json={
            "id_assinatura": id_ass, "id_cliente": cid,
        })
        r = client.get(f"/api/clientes/{cid}/assinaturas")
        assert r.status_code == 200
        assert len(r.get_json()) >= 1


# =====================================================================
# EMAIL NOTIFICATION
# =====================================================================

class TestEmailNotificacao:
    def test_enviar_email_simulado(self, client):
        r = client.post("/api/notificacoes/email", json={
            "email": "destino@email.com",
            "assunto": "Promoção Açaí",
            "corpo": "<p>20% OFF!</p>",
        })
        assert r.status_code == 200
        d = r.get_json()
        assert d["destinatario"] == "destino@email.com"

    def test_email_invalido(self, client):
        r = client.post("/api/notificacoes/email", json={
            "email": "invalido",
            "assunto": "Teste",
            "corpo": "corpo",
        })
        assert r.status_code == 400

    def test_email_campos_faltando(self, client):
        r = client.post("/api/notificacoes/email", json={
            "email": "ok@email.com",
        })
        assert r.status_code == 400

    def test_email_requer_admin(self, app):
        tc = app.test_client()
        with tc.session_transaction() as sess:
            sess["autenticado"] = True
            sess["usuario_id"] = 1
            sess["papel"] = "operador"
        r = tc.post("/api/notificacoes/email", json={
            "email": "a@b.com", "assunto": "X", "corpo": "Y",
        })
        assert r.status_code in (403, 401)


# =====================================================================
# NFC-e (CUPOM FISCAL PDF)
# =====================================================================

class TestNFCe:
    def test_gerar_nfce(self, client, app):
        with app.app_context():
            c = _cliente()
            p = _produto()
            v = _venda(c, p)
            vid = v.id_venda
        r = client.get(f"/api/vendas/{vid}/nfce")
        assert r.status_code == 200
        assert r.content_type == "application/pdf"
        assert len(r.data) > 100

    def test_nfce_venda_inexistente(self, client):
        r = client.get("/api/vendas/99999/nfce")
        assert r.status_code == 404

    def test_nfce_requer_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/vendas/1/nfce")
        assert r.status_code in (401, 302)


# =====================================================================
# PAINEL DO CLIENTE (FAVORITOS + REORDENAR)
# =====================================================================

class TestPainelCliente:
    def test_favoritos(self, app):
        tc = app.test_client()
        with app.app_context():
            c = _cliente()
            p = _produto()
            _venda(c, p, qtd=3)
            cid = c.id_cliente
        _cliente_session(tc, cid)
        r = tc.get("/api/cliente/favoritos")
        assert r.status_code == 200
        fav = r.get_json()
        assert len(fav) >= 1
        assert fav[0]["total_comprado"] == 3

    def test_favoritos_sem_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/cliente/favoritos")
        assert r.status_code == 401

    def test_reordenar(self, app):
        tc = app.test_client()
        with app.app_context():
            c = _cliente()
            p = _produto()
            v = _venda(c, p, qtd=2)
            cid, vid = c.id_cliente, v.id_venda
        _cliente_session(tc, cid)
        r = tc.post(f"/api/cliente/reordenar/{vid}")
        assert r.status_code == 201
        d = r.get_json()
        assert "venda" in d

    def test_reordenar_venda_inexistente(self, app):
        tc = app.test_client()
        with app.app_context():
            c = _cliente()
            cid = c.id_cliente
        _cliente_session(tc, cid)
        r = tc.post("/api/cliente/reordenar/99999")
        assert r.status_code == 404

    def test_reordenar_sem_lgpd(self, app):
        tc = app.test_client()
        with app.app_context():
            c = _cliente(consentimento=False)
            p = _produto()
            v = _venda(c, p)
            cid, vid = c.id_cliente, v.id_venda
        _cliente_session(tc, cid)
        r = tc.post(f"/api/cliente/reordenar/{vid}")
        assert r.status_code == 403


# =====================================================================
# MULTI-LOJA
# =====================================================================

class TestMultiLoja:
    def test_criar_loja(self, client):
        r = client.post("/api/lojas", json={
            "nome": "Unidade Centro",
            "endereco": "Rua Principal, 100",
            "telefone": "1133334444",
            "cnpj": "12.345.678/0001-01",
        })
        assert r.status_code == 201
        d = r.get_json()
        assert d["nome"] == "Unidade Centro"

    def test_listar_lojas(self, client):
        client.post("/api/lojas", json={
            "nome": "Unidade 1", "endereco": "End 1",
        })
        r = client.get("/api/lojas")
        assert r.status_code == 200
        assert len(r.get_json()) >= 1

    def test_atualizar_loja(self, client):
        r1 = client.post("/api/lojas", json={
            "nome": "Loja A", "endereco": "End A",
        })
        lid = r1.get_json()["id_loja"]
        r = client.put(f"/api/lojas/{lid}", json={
            "nome": "Loja A Atualizada",
        })
        assert r.status_code == 200
        assert r.get_json()["nome"] == "Loja A Atualizada"

    def test_desativar_loja(self, client):
        r1 = client.post("/api/lojas", json={
            "nome": "Loja B", "endereco": "End B",
        })
        lid = r1.get_json()["id_loja"]
        r = client.delete(f"/api/lojas/{lid}")
        assert r.status_code == 200

    def test_loja_requer_admin_para_criar(self, app):
        tc = app.test_client()
        with tc.session_transaction() as sess:
            sess["autenticado"] = True
            sess["usuario_id"] = 1
            sess["papel"] = "operador"
        r = tc.post("/api/lojas", json={
            "nome": "Loja Op", "endereco": "End",
        })
        assert r.status_code in (403, 401)

    def test_loja_listar_requer_auth(self, unauthenticated_client):
        r = unauthenticated_client.get("/api/lojas")
        assert r.status_code in (401, 302)
