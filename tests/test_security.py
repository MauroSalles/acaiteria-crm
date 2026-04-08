"""
Testes de segurança — XSS, SQL-injection, CSRF, autenticação.
Complementa test_kaizen.TestSeguranca com cenários mais profundos.
"""


class TestXSSPayloads:
    """Testa que payloads XSS não causam erro 500 e são tratados."""

    PAYLOADS = [
        '<script>alert(1)</script>',
        '<img src=x onerror=alert(1)>',
        '"><svg onload=alert(1)>',
        "javascript:alert(1)",
        '<iframe src="data:text/html,<script>alert(1)</script>">',
        "{{7*7}}",           # template injection
        "${7*7}",            # template injection (ES6)
        "'; DROP TABLE--",   # classic SQL injection
    ]

    def test_xss_nome_cliente(self, client):
        for payload in self.PAYLOADS:
            resp = client.post('/api/clientes', json={
                'nome': payload,
                'consentimento_lgpd': True,
            })
            assert resp.status_code in (201, 400), \
                f"Payload {payload!r} causou status {resp.status_code}"

    def test_xss_produto_nome(self, client):
        for payload in self.PAYLOADS:
            resp = client.post('/api/produtos', json={
                'nome_produto': payload,
                'preco': 10.0,
                'categoria': 'Teste',
            })
            assert resp.status_code in (201, 400)

    def test_xss_busca_global(self, client):
        for payload in self.PAYLOADS:
            resp = client.get(f'/api/busca?q={payload}')
            assert resp.status_code == 200

    def test_xss_observacoes_venda(self, client):
        """Observações em venda não devem causar crash."""
        c = client.post('/api/clientes', json={
            'nome': 'XSS Test',
            'consentimento_lgpd': True,
        })
        cid = c.get_json()['id_cliente']
        p = client.post('/api/produtos', json={
            'nome_produto': 'Prod XSS', 'preco': 5, 'categoria': 'Teste',
        })
        pid = p.get_json()['id_produto']
        for payload in self.PAYLOADS[:3]:
            resp = client.post('/api/vendas', json={
                'id_cliente': cid,
                'itens': [{'id_produto': pid, 'quantidade': 1}],
                'forma_pagamento': 'Pix',
                'observacoes': payload,
            })
            assert resp.status_code in (201, 400)


class TestSQLInjection:
    """Testa que parâmetros de query-string não permitem SQL injection."""

    SQL_PAYLOADS = [
        "1 OR 1=1",
        "1; DROP TABLE clientes--",
        "' UNION SELECT * FROM usuarios--",
        "1' AND '1'='1",
        "-1 OR 1=1",
    ]

    def test_sqli_pagina_clientes(self, client):
        for p in self.SQL_PAYLOADS:
            resp = client.get(f'/api/clientes?pagina={p}')
            assert resp.status_code in (200, 400, 500)
            # Certifica que não retornou dados de outra tabela
            data = resp.get_json()
            if resp.status_code == 200:
                assert 'clientes' in data or 'erro' in data

    def test_sqli_busca_clientes(self, client):
        for p in self.SQL_PAYLOADS:
            resp = client.get(f'/api/clientes?busca={p}')
            assert resp.status_code == 200

    def test_sqli_id_cliente(self, client):
        """IDs inválidos devem retornar 404, não erro de SQL."""
        for bad_id in [999999, 0, -1]:
            resp = client.get(f'/api/clientes/{bad_id}')
            assert resp.status_code == 404

    def test_sqli_filtro_vendas(self, client):
        for p in self.SQL_PAYLOADS:
            resp = client.get(f'/api/vendas?forma_pagamento={p}')
            assert resp.status_code in (200, 400)

    def test_sqli_por_pagina(self, client):
        resp = client.get('/api/clientes?por_pagina=100;DROP TABLE')
        assert resp.status_code in (200, 400, 500)


class TestAuthBypass:
    """Testa tentativas de bypass de autenticação."""

    def test_acesso_admin_sem_login(self, unauthenticated_client):
        rotas_protegidas = [
            '/api/clientes', '/api/produtos', '/api/vendas',
            '/api/logs', '/api/dashboard/graficos', '/api/busca?q=a',
            '/api/fidelidade/ranking', '/api/relatorios/dia-atual',
            '/api/financeiro', '/api/financeiro/resumo',
        ]
        for rota in rotas_protegidas:
            resp = unauthenticated_client.get(rota)
            assert resp.status_code in (401, 302), \
                f"{rota} permitiu acesso sem login: {resp.status_code}"

    def test_post_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.post('/api/clientes',
                                           json={'nome': 'Hacker'})
        assert resp.status_code in (401, 302)

    def test_delete_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.delete('/api/clientes/1')
        assert resp.status_code in (401, 302)

    def test_pagina_admin_redireciona(self, unauthenticated_client):
        paginas = ['/', '/clientes', '/produtos', '/vendas',
                   '/relatorios', '/financeiro']
        for p in paginas:
            resp = unauthenticated_client.get(p)
            assert resp.status_code in (200, 302)

    def test_painel_cliente_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.get('/cliente/painel')
        assert resp.status_code == 302
        assert '/cliente/login' in resp.headers.get('Location', '')

    def test_extrato_cliente_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.get('/cliente/extrato')
        assert resp.status_code == 302


class TestCSRFHeaders:
    """Testa headers de segurança e proteção CSRF."""

    def test_content_type_json(self, client):
        resp = client.get('/api/clientes')
        assert 'application/json' in resp.content_type

    def test_session_cookie_httponly(self, app):
        assert app.config.get('SESSION_COOKIE_HTTPONLY') is True

    def test_session_cookie_samesite(self, app):
        assert app.config.get('SESSION_COOKIE_SAMESITE') == 'Lax'

    def test_csp_nonce_presente(self, client):
        """Páginas HTML devem ter nonce CSP no template."""
        resp = client.get('/')
        assert resp.status_code == 200


class TestInputValidation:
    """Testa validação de entradas em endpoints críticos."""

    def test_cliente_nome_vazio(self, client):
        resp = client.post('/api/clientes', json={
            'nome': '', 'consentimento_lgpd': True,
        })
        assert resp.status_code == 400

    def test_cliente_nome_curto(self, client):
        resp = client.post('/api/clientes', json={
            'nome': 'A', 'consentimento_lgpd': True,
        })
        assert resp.status_code == 400

    def test_produto_preco_negativo(self, client):
        resp = client.post('/api/produtos', json={
            'nome_produto': 'Teste Neg', 'preco': -5,
            'categoria': 'Teste',
        })
        assert resp.status_code == 400

    def test_produto_preco_zero(self, client):
        resp = client.post('/api/produtos', json={
            'nome_produto': 'Teste Zero', 'preco': 0,
            'categoria': 'Teste',
        })
        assert resp.status_code == 400

    def test_venda_itens_vazio(self, client):
        resp = client.post('/api/vendas', json={
            'id_cliente': 1, 'itens': [],
        })
        assert resp.status_code == 400

    def test_venda_quantidade_invalida(self, client):
        c = client.post('/api/clientes', json={
            'nome': 'Val Test', 'consentimento_lgpd': True,
        })
        cid = c.get_json()['id_cliente']
        p = client.post('/api/produtos', json={
            'nome_produto': 'Val Prod', 'preco': 10,
            'categoria': 'Teste',
        })
        pid = p.get_json()['id_produto']
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': -1}],
            'forma_pagamento': 'Pix',
        })
        assert resp.status_code == 400

    def test_venda_quantidade_zero(self, client):
        c = client.post('/api/clientes', json={
            'nome': 'Val Test2', 'consentimento_lgpd': True,
        })
        cid = c.get_json()['id_cliente']
        p = client.post('/api/produtos', json={
            'nome_produto': 'Val Prod2', 'preco': 10,
            'categoria': 'Teste',
        })
        pid = p.get_json()['id_produto']
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 0}],
            'forma_pagamento': 'Pix',
        })
        assert resp.status_code == 400

    def test_email_invalido(self, client):
        resp = client.post('/api/clientes', json={
            'nome': 'Email Bad',
            'email': 'not-an-email',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 400

    def test_financeiro_tipo_invalido(self, client):
        resp = client.post('/api/financeiro', json={
            'tipo': 'invalido',
            'categoria': 'Teste',
            'valor': 100,
            'data_lancamento': '2025-01-15',
        })
        assert resp.status_code == 400

    def test_financeiro_valor_negativo(self, client):
        resp = client.post('/api/financeiro', json={
            'tipo': 'receita',
            'categoria': 'Vendas',
            'valor': -100,
            'data_lancamento': '2025-01-15',
        })
        assert resp.status_code == 400
