"""
Testes do portal do cliente — login, cadastro, painel, extrato, logout.
"""
from backend.models import db, Cliente


def _criar_cliente_com_senha(app, nome='Portal Test', email='portal@test.com',
                             telefone='11999990001', senha='Teste123!'):
    """Helper: cria cliente com senha no banco."""
    with app.app_context():
        c = Cliente(
            nome=nome,
            email=email,
            telefone=telefone,
            consentimento_lgpd=True,
            ativo=True,
        )
        c.set_senha(senha)
        db.session.add(c)
        db.session.commit()
        return c.id_cliente


class TestClienteLoginPage:
    """Testa a página e fluxo de login do cliente."""

    def test_get_login_page(self, app):
        c = app.test_client()
        resp = c.get('/cliente/login')
        assert resp.status_code == 200
        assert b'login' in resp.data.lower() or b'Login' in resp.data

    def test_login_campos_vazios(self, app):
        c = app.test_client()
        resp = c.post('/cliente/login', data={
            'identificador': '', 'senha': '',
        })
        assert resp.status_code == 200
        assert 'Preencha' in resp.data.decode()

    def test_login_credenciais_incorretas(self, app):
        _criar_cliente_com_senha(app)
        c = app.test_client()
        resp = c.post('/cliente/login', data={
            'identificador': 'portal@test.com',
            'senha': 'SenhaErrada1',
        })
        assert resp.status_code == 200
        assert 'incorretas' in resp.data.decode().lower() or \
               'incorreta' in resp.data.decode().lower()

    def test_login_sucesso_email(self, app):
        _criar_cliente_com_senha(app)
        c = app.test_client()
        resp = c.post('/cliente/login', data={
            'identificador': 'portal@test.com',
            'senha': 'Teste123!',
        }, follow_redirects=False)
        assert resp.status_code == 302
        assert '/cliente/painel' in resp.headers.get('Location', '')

    def test_login_sucesso_telefone(self, app):
        _criar_cliente_com_senha(app, email='tel@test.com',
                                 telefone='11888880001')
        c = app.test_client()
        resp = c.post('/cliente/login', data={
            'identificador': '11888880001',
            'senha': 'Teste123!',
        }, follow_redirects=False)
        assert resp.status_code == 302

    def test_login_cliente_inativo(self, app):
        cid = _criar_cliente_com_senha(app, email='inativo@test.com',
                                       telefone='11777770001')
        with app.app_context():
            cli = db.session.get(Cliente, cid)
            cli.ativo = False
            db.session.commit()
        c = app.test_client()
        resp = c.post('/cliente/login', data={
            'identificador': 'inativo@test.com',
            'senha': 'Teste123!',
        })
        assert resp.status_code == 200


class TestClienteCadastroPage:
    """Testa o auto-cadastro de clientes com senha."""

    def test_get_cadastro_page(self, app):
        c = app.test_client()
        resp = c.get('/cliente/cadastro')
        assert resp.status_code == 200

    def test_cadastro_nome_curto(self, app):
        c = app.test_client()
        resp = c.post('/cliente/cadastro', data={
            'nome': 'A', 'email': 'c@c.com',
            'senha': 'Teste123!', 'consentimento_lgpd': 'on',
        })
        assert resp.status_code == 200
        assert '2 caracteres' in resp.data.decode()

    def test_cadastro_senha_fraca(self, app):
        c = app.test_client()
        resp = c.post('/cliente/cadastro', data={
            'nome': 'Teste Fraca', 'email': 'fraca@t.com',
            'senha': 'abc', 'consentimento_lgpd': 'on',
        })
        assert resp.status_code == 200
        assert 'senha' in resp.data.decode().lower()

    def test_cadastro_sem_consentimento(self, app):
        c = app.test_client()
        resp = c.post('/cliente/cadastro', data={
            'nome': 'Sem LGPD', 'email': 'lgpd@t.com',
            'senha': 'Teste123!',
        })
        assert resp.status_code == 200
        assert 'LGPD' in resp.data.decode() or \
               'consentimento' in resp.data.decode().lower()

    def test_cadastro_sucesso(self, app):
        c = app.test_client()
        resp = c.post('/cliente/cadastro', data={
            'nome': 'Cliente Novo',
            'email': 'novo@test.com',
            'telefone': '11666660001',
            'senha': 'Teste123!',
            'consentimento_lgpd': 'on',
        }, follow_redirects=False)
        # Sucesso redireciona para login ou painel
        assert resp.status_code in (200, 302)

    def test_cadastro_email_duplicado(self, app):
        _criar_cliente_com_senha(app, email='dup@test.com',
                                 telefone='11555550001')
        c = app.test_client()
        resp = c.post('/cliente/cadastro', data={
            'nome': 'Dup Test', 'email': 'dup@test.com',
            'telefone': '11555550002', 'senha': 'Teste123!',
            'consentimento_lgpd': 'on',
        })
        assert resp.status_code == 200
        assert 'cadastrado' in resp.data.decode().lower()


class TestClientePainel:
    """Testa o painel do cliente logado."""

    def _login(self, app, email='painel@test.com'):
        cid = _criar_cliente_com_senha(app, email=email,
                                       telefone='11444440001')
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['cliente_id'] = cid
            sess['cliente_nome'] = 'Portal Test'
            sess['tipo_usuario'] = 'cliente'
        return c, cid

    def test_painel_acesso(self, app):
        c, _ = self._login(app)
        resp = c.get('/cliente/painel')
        assert resp.status_code == 200
        assert b'Portal Test' in resp.data or b'painel' in resp.data.lower()

    def test_painel_sem_login_redireciona(self, app):
        c = app.test_client()
        resp = c.get('/cliente/painel')
        assert resp.status_code == 302
        assert '/cliente/login' in resp.headers.get('Location', '')

    def test_painel_cliente_inativo(self, app):
        cid = _criar_cliente_com_senha(app, email='paineloff@test.com',
                                       telefone='11333330001')
        with app.app_context():
            cli = db.session.get(Cliente, cid)
            cli.ativo = False
            db.session.commit()
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['cliente_id'] = cid
        resp = c.get('/cliente/painel')
        assert resp.status_code == 302


class TestClienteExtrato:
    """Testa a página de extrato do cliente."""

    def test_extrato_acesso(self, app):
        cid = _criar_cliente_com_senha(app, email='ext@test.com',
                                       telefone='11222220001')
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['cliente_id'] = cid
            sess['cliente_nome'] = 'Portal Test'
        resp = c.get('/cliente/extrato')
        assert resp.status_code == 200

    def test_extrato_sem_login(self, app):
        c = app.test_client()
        resp = c.get('/cliente/extrato')
        assert resp.status_code == 302

    def test_badges_api(self, app):
        cid = _criar_cliente_com_senha(app, email='badge@test.com',
                                       telefone='11111110001')
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['autenticado'] = True
            sess['usuario_id'] = 1
            sess['papel'] = 'admin'
        resp = c.get(f'/api/clientes/{cid}/badges')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'badges' in data


class TestClienteLogout:
    """Testa o logout do cliente."""

    def test_logout_redireciona(self, app):
        cid = _criar_cliente_com_senha(app, email='logout@test.com',
                                       telefone='11000000001')
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['cliente_id'] = cid
            sess['tipo_usuario'] = 'cliente'
        resp = c.get('/cliente/logout', follow_redirects=False)
        assert resp.status_code == 302
        assert '/vitrine' in resp.headers.get('Location', '')

    def test_logout_limpa_sessao(self, app):
        cid = _criar_cliente_com_senha(app, email='logout2@test.com',
                                       telefone='11000000002')
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['cliente_id'] = cid
            sess['tipo_usuario'] = 'cliente'
        c.get('/cliente/logout')
        with c.session_transaction() as sess:
            assert 'cliente_id' not in sess


class TestCheckoutCliente:
    """Testa o fluxo de checkout do carrinho do cliente."""

    def _setup(self, app):
        cid = _criar_cliente_com_senha(app, email='cart@test.com',
                                       telefone='11000000003')
        c = app.test_client()
        with c.session_transaction() as sess:
            sess['cliente_id'] = cid
        # Criar produto pelo admin
        admin = app.test_client()
        with admin.session_transaction() as sess:
            sess['autenticado'] = True
            sess['usuario_id'] = 1
            sess['papel'] = 'admin'
        p = admin.post('/api/produtos', json={
            'nome_produto': 'Açaí Checkout', 'preco': 15,
            'categoria': 'Açaí',
        })
        pid = p.get_json()['id_produto']
        return c, cid, pid

    def test_checkout_carrinho_vazio(self, app):
        c, _, _ = self._setup(app)
        resp = c.post('/api/cliente/carrinho/checkout', json={
            'itens': [],
        })
        assert resp.status_code == 400

    def test_checkout_sem_login(self, app):
        anon = app.test_client()
        resp = anon.post('/api/cliente/carrinho/checkout', json={
            'itens': [{'id_produto': 1, 'quantidade': 1}],
        })
        assert resp.status_code == 302

    def test_checkout_sucesso(self, app):
        c, cid, pid = self._setup(app)
        resp = c.post('/api/cliente/carrinho/checkout', json={
            'itens': [{'id_produto': pid, 'quantidade': 2}],
            'forma_pagamento': 'Pix',
        })
        assert resp.status_code in (200, 201)

    def test_checkout_forma_invalida(self, app):
        c, cid, pid = self._setup(app)
        resp = c.post('/api/cliente/carrinho/checkout', json={
            'itens': [{'id_produto': pid, 'quantidade': 1}],
            'forma_pagamento': 'Bitcoin',
        })
        assert resp.status_code == 400
