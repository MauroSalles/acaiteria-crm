"""
Testes End-to-End — Açaiteria CRM
Fluxos completos que exercitam múltiplas funcionalidades integradas.
"""


class TestFluxoCompletoVenda:
    """Fluxo: criar cliente → criar produto com estoque → vender → conferir estoque."""

    def test_venda_desconta_estoque(self, client):
        # 1. Criar cliente com consentimento
        rc = client.post('/api/clientes', json={
            'nome': 'Maria E2E',
            'consentimento_lgpd': True,
            'versao_politica': 'v1.0',
        })
        assert rc.status_code == 201
        cid = rc.get_json()['id_cliente']

        # 2. Criar produto com estoque controlado
        rp = client.post('/api/produtos', json={
            'nome_produto': 'Açaí 700ml',
            'preco': 25.90,
            'categoria': 'Açaí',
            'estoque_atual': 10,
            'estoque_minimo': 3,
        })
        assert rp.status_code == 201
        pid = rp.get_json()['id_produto']
        assert rp.get_json()['estoque_atual'] == 10

        # 3. Registrar venda com 4 unidades
        rv = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Pix',
            'itens': [{'id_produto': pid, 'quantidade': 4}],
        })
        assert rv.status_code == 201

        # 4. Verificar estoque descontou para 6
        rget = client.get(f'/api/produtos/{pid}')
        assert rget.status_code == 200
        assert rget.get_json()['estoque_atual'] == 6

    def test_venda_bloqueada_estoque_insuficiente(self, client):
        rc = client.post('/api/clientes', json={
            'nome': 'João E2E', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        cid = rc.get_json()['id_cliente']

        rp = client.post('/api/produtos', json={
            'nome_produto': 'Suco Natural',
            'preco': 12.00,
            'estoque_atual': 2,
            'estoque_minimo': 1,
        })
        pid = rp.get_json()['id_produto']

        # Tentar vender 5, mas só tem 2
        rv = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 5}],
        })
        assert rv.status_code == 400
        assert 'Estoque insuficiente' in rv.get_json()['erro']


class TestEstoqueBaixo:
    """Testa o endpoint de produtos com estoque abaixo do mínimo."""

    def test_produto_estoque_baixo(self, client):
        # Produto com estoque abaixo do mínimo
        client.post('/api/produtos', json={
            'nome_produto': 'Granola',
            'preco': 5.00,
            'estoque_atual': 2,
            'estoque_minimo': 5,
        })
        # Produto OK - sem controle de estoque
        client.post('/api/produtos', json={
            'nome_produto': 'Mel',
            'preco': 3.00,
        })

        resp = client.get('/api/produtos/estoque-baixo')
        assert resp.status_code == 200
        baixos = resp.get_json()
        nomes = [p['nome_produto'] for p in baixos]
        assert 'Granola' in nomes
        assert 'Mel' not in nomes  # estoque 0 e minimo 0 → controle inativo


class TestAuditLog:
    """Testa o registro e consulta do histórico de ações."""

    def test_log_criacao_cliente(self, client):
        client.post('/api/clientes', json={
            'nome': 'Log Test', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        resp = client.get('/api/logs?entidade=cliente&acao=criar')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1
        assert any('Log Test' in (l.get('detalhes') or '') for l in data['logs'])

    def test_log_criacao_produto(self, client):
        client.post('/api/produtos', json={
            'nome_produto': 'Produto Log', 'preco': 10.0,
        })
        resp = client.get('/api/logs?entidade=produto&acao=criar')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1

    def test_log_criacao_venda(self, client):
        rc = client.post('/api/clientes', json={
            'nome': 'Venda Log', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        rp = client.post('/api/produtos', json={
            'nome_produto': 'Açaí Log', 'preco': 15.0,
        })
        client.post('/api/vendas', json={
            'id_cliente': rc.get_json()['id_cliente'],
            'itens': [{'id_produto': rp.get_json()['id_produto'], 'quantidade': 1}],
        })
        resp = client.get('/api/logs?entidade=venda&acao=criar')
        assert resp.status_code == 200
        assert resp.get_json()['total'] >= 1

    def test_log_paginacao(self, client):
        # Criar vários clientes para gerar logs
        for i in range(5):
            client.post('/api/clientes', json={
                'nome': f'Pag {i}', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
            })
        resp = client.get('/api/logs?por_pagina=2&pagina=1')
        data = resp.get_json()
        assert len(data['logs']) == 2
        assert data['total'] >= 5
        assert data['total_paginas'] >= 3

    def test_log_requer_admin(self, client, app):
        """Operador não pode ver logs."""
        with client.session_transaction() as sess:
            sess['papel'] = 'operador'
        resp = client.get('/api/logs')
        assert resp.status_code == 403


class TestDashboardGraficos:
    """Testa o endpoint de dados dos gráficos."""

    def test_graficos_sem_dados(self, client):
        resp = client.get('/api/dashboard/graficos')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'vendas_por_dia' in data
        assert 'por_forma_pagamento' in data
        assert 'top_produtos' in data

    def test_graficos_com_venda(self, client):
        rc = client.post('/api/clientes', json={
            'nome': 'Graf Teste', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        rp = client.post('/api/produtos', json={
            'nome_produto': 'Açaí Graf', 'preco': 20.0,
        })
        client.post('/api/vendas', json={
            'id_cliente': rc.get_json()['id_cliente'],
            'forma_pagamento': 'Pix',
            'itens': [{'id_produto': rp.get_json()['id_produto'], 'quantidade': 3}],
        })
        resp = client.get('/api/dashboard/graficos')
        data = resp.get_json()
        # Deve ter pelo menos uma forma de pagamento
        assert len(data['por_forma_pagamento']) >= 1
        assert data['por_forma_pagamento'][0]['forma'] == 'Pix'


class TestFiltrosAvancados:
    """Testa filtros avançados de vendas e produtos."""

    def _setup(self, client):
        rc = client.post('/api/clientes', json={
            'nome': 'Filtro Teste', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        rp = client.post('/api/produtos', json={
            'nome_produto': 'Açaí Filtro', 'preco': 18.0, 'categoria': 'Açaí',
        })
        return rc.get_json()['id_cliente'], rp.get_json()['id_produto']

    def test_filtro_produto_por_busca(self, client):
        client.post('/api/produtos', json={
            'nome_produto': 'Tapioca Especial', 'preco': 8.0, 'categoria': 'Complementos',
        })
        client.post('/api/produtos', json={
            'nome_produto': 'Açaí Premium', 'preco': 30.0, 'categoria': 'Açaí',
        })
        resp = client.get('/api/produtos?busca=tapioca')
        prods = resp.get_json()
        assert len(prods) == 1
        assert prods[0]['nome_produto'] == 'Tapioca Especial'

    def test_filtro_produto_por_categoria(self, client):
        client.post('/api/produtos', json={
            'nome_produto': 'Mel Puro', 'preco': 6.0, 'categoria': 'Complementos',
        })
        client.post('/api/produtos', json={
            'nome_produto': 'Açaí Trad', 'preco': 15.0, 'categoria': 'Açaí',
        })
        resp = client.get('/api/produtos?categoria=Complementos')
        prods = resp.get_json()
        assert all(p['categoria'] == 'Complementos' for p in prods)

    def test_vendas_paginacao(self, client):
        cid, pid = self._setup(client)
        # Criar 3 vendas
        for _ in range(3):
            client.post('/api/vendas', json={
                'id_cliente': cid,
                'itens': [{'id_produto': pid, 'quantidade': 1}],
            })
        resp = client.get('/api/vendas?por_pagina=2&pagina=1')
        data = resp.get_json()
        assert len(data['vendas']) == 2
        assert data['total'] == 3
        assert data['total_paginas'] == 2


class TestPaginasHTML:
    """Testa que todas as páginas HTML respondem 200 (autenticado como admin)."""

    def test_pagina_dashboard(self, client):
        assert client.get('/').status_code == 200

    def test_pagina_clientes(self, client):
        assert client.get('/clientes').status_code == 200

    def test_pagina_produtos(self, client):
        assert client.get('/produtos').status_code == 200

    def test_pagina_nova_venda(self, client):
        assert client.get('/nova-venda').status_code == 200

    def test_pagina_relatorios(self, client):
        assert client.get('/relatorios').status_code == 200

    def test_pagina_fechamento(self, client):
        assert client.get('/fechamento').status_code == 200

    def test_pagina_usuarios(self, client):
        assert client.get('/usuarios').status_code == 200

    def test_pagina_historico(self, client):
        assert client.get('/historico').status_code == 200

    def test_pagina_lgpd(self, client):
        assert client.get('/politica-privacidade').status_code == 200

    def test_login_nao_autenticado(self, app):
        """Login acessível sem autenticação."""
        c = app.test_client()
        assert c.get('/login').status_code == 200

    def test_redirect_sem_login(self, app):
        """Redireciona para login quando não autenticado."""
        c = app.test_client()
        resp = c.get('/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']


class TestFidelidade:
    """Testa o programa de fidelidade (pontos por compra, consulta, resgate)."""

    def _criar_cliente_e_produto(self, client):
        rc = client.post('/api/clientes', json={
            'nome': 'Fiel Teste', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        assert rc.status_code == 201
        rp = client.post('/api/produtos', json={
            'nome_produto': 'Açaí Fidelidade', 'preco': 25.00,
        })
        assert rp.status_code == 201
        return rc.get_json()['id_cliente'], rp.get_json()['id_produto']

    def test_pontos_acumulados_apos_venda(self, client):
        cid, pid = self._criar_cliente_e_produto(client)
        rv = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 4}],  # 4 x 25 = R$100
        })
        assert rv.status_code == 201
        data = rv.get_json()
        assert data['pontos_ganhos'] == 100
        assert data['pontos_total'] == 100

    def test_consultar_pontos(self, client):
        cid, pid = self._criar_cliente_e_produto(client)
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 2}],  # 2 x 25 = R$50
        })
        resp = client.get(f'/api/clientes/{cid}/pontos')
        assert resp.status_code == 200
        assert resp.get_json()['pontos'] == 50

    def test_resgatar_pontos(self, client):
        cid, pid = self._criar_cliente_e_produto(client)
        # Criar vendas para acumular 200 pontos
        for _ in range(2):
            client.post('/api/vendas', json={
                'id_cliente': cid,
                'itens': [{'id_produto': pid, 'quantidade': 4}],  # 100 cada
            })

        resp = client.post(f'/api/clientes/{cid}/pontos/resgatar', json={'pontos': 200})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['pontos_resgatados'] == 200
        assert data['desconto_gerado'] == 10.0  # 200/100 * 5 = R$10
        assert data['pontos_restantes'] == 0

    def test_resgatar_insuficiente(self, client):
        cid, pid = self._criar_cliente_e_produto(client)
        resp = client.post(f'/api/clientes/{cid}/pontos/resgatar', json={'pontos': 500})
        assert resp.status_code == 400

    def test_resgatar_minimo_100(self, client):
        cid, pid = self._criar_cliente_e_produto(client)
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 2}],  # 50 pontos
        })
        resp = client.post(f'/api/clientes/{cid}/pontos/resgatar', json={'pontos': 50})
        assert resp.status_code == 400
        assert 'Mínimo' in resp.get_json()['erro']

    def test_ranking_fidelidade(self, client):
        cid, pid = self._criar_cliente_e_produto(client)
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 4}],
        })
        resp = client.get('/api/fidelidade/ranking')
        assert resp.status_code == 200
        ranking = resp.get_json()
        assert len(ranking) >= 1
        assert ranking[0]['pontos'] > 0


class TestTotemAutoCadastro:
    """Testa o fluxo de auto-cadastro público via totem."""

    def test_pagina_totem_publica(self, app):
        """Totem acessível SEM autenticação."""
        c = app.test_client()
        resp = c.get('/totem')
        assert resp.status_code == 200
        assert 'Combina' in resp.data.decode()

    def test_cadastro_totem_sucesso(self, app):
        """Auto-cadastro com dados válidos e consentimento."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Cliente Totem',
            'telefone': '(12) 99999-0001',
            'email': 'totem@teste.com',
            'consentimento_lgpd': True,
            'versao_politica': 'v1.0',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nome'] == 'Cliente Totem'
        assert data['pontos_fidelidade'] == 10  # bônus de boas-vindas
        assert data['id_cliente'] > 0

    def test_cadastro_totem_sem_nome(self, app):
        """Rejeita cadastro sem nome."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 400
        assert 'Nome' in resp.get_json()['erro']

    def test_cadastro_totem_sem_consentimento(self, app):
        """Rejeita cadastro sem aceite LGPD."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Sem LGPD',
            'consentimento_lgpd': False,
        })
        assert resp.status_code == 400
        assert 'Consentimento' in resp.get_json()['erro']

    def test_cadastro_totem_email_duplicado(self, app):
        """Rejeita cadastro com email já existente."""
        c = app.test_client()
        c.post('/api/totem/cadastro', json={
            'nome': 'Primeiro',
            'email': 'dup@teste.com',
            'consentimento_lgpd': True,
        })
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Segundo',
            'email': 'dup@teste.com',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 409
        assert 'cadastrado' in resp.get_json()['erro']

    def test_cadastro_totem_telefone_duplicado(self, app):
        """Rejeita cadastro com telefone já existente."""
        c = app.test_client()
        c.post('/api/totem/cadastro', json={
            'nome': 'Primeiro Tel',
            'telefone': '(12) 98888-0001',
            'consentimento_lgpd': True,
        })
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Segundo Tel',
            'telefone': '(12) 98888-0001',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 409

    def test_cadastro_totem_email_invalido(self, app):
        """Rejeita e-mail inválido."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Email Ruim',
            'email': 'sem-arroba',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 400

    def test_cadastro_totem_somente_nome(self, app):
        """Cadastro mínimo: apenas nome + consentimento."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Minimalista',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 201
        assert resp.get_json()['pontos_fidelidade'] == 10

    def test_cliente_totem_visivel_no_sistema(self, client, app):
        """Cliente cadastrado pelo totem aparece na lista de clientes."""
        c = app.test_client()
        c.post('/api/totem/cadastro', json={
            'nome': 'Visivel No CRM',
            'telefone': '(12) 97777-0001',
            'consentimento_lgpd': True,
        })
        # Buscar via API autenticada
        resp = client.get('/api/clientes?busca=Visivel')
        assert resp.status_code == 200
        clientes = resp.get_json()['clientes']
        assert any(c['nome'] == 'Visivel No CRM' for c in clientes)

