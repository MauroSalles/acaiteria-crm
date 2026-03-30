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


class TestCancelamentoVenda:
    """Testa o cancelamento/estorno de vendas (somente admin)."""

    def _criar_venda(self, client):
        """Helper: cria cliente + produto + venda, retorna (id_venda, id_cliente, id_produto)."""
        rc = client.post('/api/clientes', json={
            'nome': 'Cancelar Teste', 'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        cid = rc.get_json()['id_cliente']
        rp = client.post('/api/produtos', json={
            'nome_produto': 'Açaí Cancel', 'preco': 20.0,
            'estoque_atual': 10, 'estoque_minimo': 2,
        })
        pid = rp.get_json()['id_produto']
        rv = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Pix',
            'itens': [{'id_produto': pid, 'quantidade': 3}],
        })
        vid = rv.get_json()['id_venda']
        return vid, cid, pid

    def test_cancelar_venda_sucesso(self, client):
        vid, cid, pid = self._criar_venda(client)

        # Estoque deve ser 7 (10 - 3)
        assert client.get(f'/api/produtos/{pid}').get_json()['estoque_atual'] == 7

        resp = client.post(f'/api/vendas/{vid}/cancelar', json={
            'motivo': 'Cliente desistiu da compra',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['estoque_restaurado'] is True
        assert data['pontos_removidos'] == 60  # 3 x 20 = 60

        # Estoque restaurado para 10
        assert client.get(f'/api/produtos/{pid}').get_json()['estoque_atual'] == 10

        # Venda marcada como cancelada
        venda = client.get(f'/api/vendas/{vid}').get_json()
        assert venda['status_pagamento'] == 'Cancelado'

    def test_cancelar_venda_sem_motivo(self, client):
        vid, _, _ = self._criar_venda(client)
        resp = client.post(f'/api/vendas/{vid}/cancelar', json={})
        assert resp.status_code == 400
        assert 'motivo' in resp.get_json()['erro'].lower()

    def test_cancelar_venda_duplicada(self, client):
        vid, _, _ = self._criar_venda(client)
        client.post(f'/api/vendas/{vid}/cancelar', json={'motivo': 'Primeira vez'})
        resp = client.post(f'/api/vendas/{vid}/cancelar', json={'motivo': 'Segunda vez'})
        assert resp.status_code == 400
        assert 'já foi cancelada' in resp.get_json()['erro']

    def test_cancelar_venda_inexistente(self, client):
        resp = client.post('/api/vendas/9999/cancelar', json={'motivo': 'Teste'})
        assert resp.status_code == 404

    def test_cancelar_venda_requer_admin(self, client):
        vid, _, _ = self._criar_venda(client)
        with client.session_transaction() as sess:
            sess['papel'] = 'operador'
        resp = client.post(f'/api/vendas/{vid}/cancelar', json={'motivo': 'Teste'})
        assert resp.status_code == 403

    def test_cancelar_remove_pontos_fidelidade(self, client):
        vid, cid, _ = self._criar_venda(client)
        # Após venda de R$60, deve ter 60 pontos
        pontos_antes = client.get(f'/api/clientes/{cid}/pontos').get_json()['pontos']
        assert pontos_antes == 60

        client.post(f'/api/vendas/{vid}/cancelar', json={'motivo': 'Estorno'})
        pontos_depois = client.get(f'/api/clientes/{cid}/pontos').get_json()['pontos']
        assert pontos_depois == 0


class TestSegurancaRotas:
    """Testa que rotas protegidas exigem autenticação."""

    def test_editar_cliente_sem_login(self, app):
        c = app.test_client()
        resp = c.put('/api/clientes/1', json={'nome': 'Hacker'})
        assert resp.status_code == 401

    def test_deletar_cliente_sem_login(self, app):
        c = app.test_client()
        resp = c.delete('/api/clientes/1')
        assert resp.status_code == 401

    def test_listar_vendas_sem_login(self, app):
        c = app.test_client()
        resp = c.get('/api/vendas')
        assert resp.status_code == 401

    def test_criar_venda_sem_login(self, app):
        c = app.test_client()
        resp = c.post('/api/vendas', json={})
        assert resp.status_code == 401

    def test_listar_produtos_sem_login(self, app):
        c = app.test_client()
        resp = c.get('/api/produtos')
        assert resp.status_code == 401

    def test_dashboard_sem_login(self, app):
        c = app.test_client()
        resp = c.get('/api/dashboard/graficos')
        assert resp.status_code == 401

    def test_exportar_csv_sem_login(self, app):
        c = app.test_client()
        resp = c.get('/api/exportar/clientes-csv')
        assert resp.status_code == 401


class TestEdicaoCliente:
    """Testa a edição de clientes com validação aprimorada."""

    def _criar_cliente(self, client, nome='Edit Test', telefone=None, email=None):
        resp = client.post('/api/clientes', json={
            'nome': nome, 'telefone': telefone, 'email': email,
            'consentimento_lgpd': True, 'versao_politica': 'v1.0',
        })
        return resp.get_json()['id_cliente']

    def test_editar_nome(self, client):
        cid = self._criar_cliente(client)
        resp = client.put(f'/api/clientes/{cid}', json={'nome': 'Nome Editado'})
        assert resp.status_code == 200
        assert resp.get_json()['nome'] == 'Nome Editado'

    def test_editar_email_duplicado(self, client):
        c1 = self._criar_cliente(client, nome='C1', email='unico@teste.com')
        c2 = self._criar_cliente(client, nome='C2', email='outro@teste.com')
        resp = client.put(f'/api/clientes/{c2}', json={'email': 'unico@teste.com'})
        assert resp.status_code == 409
        assert 'E-mail' in resp.get_json()['erro']

    def test_editar_telefone_duplicado(self, client):
        c1 = self._criar_cliente(client, nome='T1', telefone='(12) 91111-0001')
        c2 = self._criar_cliente(client, nome='T2', telefone='(12) 92222-0002')
        resp = client.put(f'/api/clientes/{c2}', json={'telefone': '(12) 91111-0001'})
        assert resp.status_code == 409
        assert 'Telefone' in resp.get_json()['erro']

    def test_editar_nome_curto(self, client):
        cid = self._criar_cliente(client)
        resp = client.put(f'/api/clientes/{cid}', json={'nome': 'A'})
        assert resp.status_code == 400

    def test_editar_cliente_anonimizado(self, client):
        cid = self._criar_cliente(client)
        client.delete(f'/api/clientes/{cid}')
        resp = client.put(f'/api/clientes/{cid}', json={'nome': 'Fantasma'})
        assert resp.status_code == 400
        assert 'anonimizado' in resp.get_json()['erro']

    def test_editar_email_invalido(self, client):
        cid = self._criar_cliente(client)
        resp = client.put(f'/api/clientes/{cid}', json={'email': 'sem-arroba'})
        assert resp.status_code == 400
        assert 'inválido' in resp.get_json()['erro']

    def test_editar_manter_mesmo_email(self, client):
        """Editar outro campo não deve conflitar com o próprio email."""
        cid = self._criar_cliente(client, nome='Meu', email='meu@teste.com')
        resp = client.put(f'/api/clientes/{cid}', json={
            'nome': 'Meu Editado', 'email': 'meu@teste.com'
        })
        assert resp.status_code == 200
        assert resp.get_json()['nome'] == 'Meu Editado'


class TestRegistroLoginPage:
    """Testa o fluxo de auto-cadastro via página de login (Registre-se)."""

    def test_login_contem_registre_se(self, app):
        """Página de login contém o formulário Registre-se."""
        c = app.test_client()
        resp = c.get('/login')
        html = resp.data.decode()
        assert resp.status_code == 200
        assert 'Cadastre-se' in html
        assert 'reg-form' in html
        assert 'flipToRegister' in html

    def test_login_contem_lgpd(self, app):
        """Formulário de registro tem checkbox LGPD."""
        c = app.test_client()
        resp = c.get('/login')
        html = resp.data.decode()
        assert 'reg-lgpd' in html
        assert 'Política de Privacidade' in html

    def test_login_contem_steps(self, app):
        """Formulário de registro tem indicador multi-step."""
        c = app.test_client()
        resp = c.get('/login')
        html = resp.data.decode()
        assert 'step-1' in html
        assert 'step-2' in html
        assert 'step-3' in html
        assert 'step-dot' in html

    def test_registro_via_api_totem_sucesso(self, app):
        """Registro na página de login usa a mesma API do totem."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Cliente Login Page',
            'telefone': '(12) 97777-0001',
            'email': 'loginreg@teste.com',
            'consentimento_lgpd': True,
            'versao_politica': 'v1.0',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nome'] == 'Cliente Login Page'
        assert data['pontos_fidelidade'] == 10

    def test_registro_apenas_nome_e_lgpd(self, app):
        """Registro mínimo: só nome + consentimento (sem telefone/email)."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Só Nome',
            'consentimento_lgpd': True,
            'versao_politica': 'v1.0',
        })
        assert resp.status_code == 201
        assert resp.get_json()['pontos_fidelidade'] == 10

    def test_registro_com_observacoes(self, app):
        """Registro com campo de preferências preenchido."""
        c = app.test_client()
        resp = c.post('/api/totem/cadastro', json={
            'nome': 'Preferência Teste',
            'observacoes': 'Gosto de açaí com granola e banana',
            'consentimento_lgpd': True,
            'versao_politica': 'v1.0',
        })
        assert resp.status_code == 201

    def test_login_form_post_ainda_funciona(self, app):
        """Login por POST continua funcionando normalmente."""
        c = app.test_client()
        resp = c.post('/login', data={
            'email': 'invalido@naoexiste.com',
            'senha': 'senhaerrada',
        })
        assert resp.status_code == 200
        assert 'incorretos' in resp.data.decode()


class TestOfflinePage:
    """Testes da página offline PWA."""

    def test_offline_page_sem_auth(self, unauthenticated_client):
        """Página offline deve ser acessível sem autenticação."""
        resp = unauthenticated_client.get('/offline')
        assert resp.status_code == 200

    def test_offline_page_com_auth(self, client):
        """Página offline também funciona autenticado."""
        resp = client.get('/offline')
        assert resp.status_code == 200


class TestSenhaMinima:
    """Testes de segurança — senha mínima de 8 caracteres."""

    def test_criar_usuario_senha_curta(self, client):
        """Senha com menos de 8 chars deve ser rejeitada."""
        resp = client.post('/api/usuarios', json={
            'nome': 'Teste Senha',
            'email': 'senhacurta@teste.com',
            'senha': 'abc123',
            'papel': 'operador',
        })
        assert resp.status_code == 400

    def test_criar_usuario_senha_exata_8(self, client):
        """Senha com exatamente 8 chars deve ser aceita."""
        resp = client.post('/api/usuarios', json={
            'nome': 'Teste Senha OK',
            'email': 'senha8@teste.com',
            'senha': '12345678',
            'papel': 'operador',
        })
        assert resp.status_code == 201

    def test_atualizar_senha_curta(self, client):
        """Atualizar para senha curta deve falhar."""
        # Cria usuario com senha válida
        resp = client.post('/api/usuarios', json={
            'nome': 'Update Senha',
            'email': 'upsenha@teste.com',
            'senha': 'senhavalida123',
            'papel': 'operador',
        })
        uid = resp.get_json()['id_usuario']
        # Tenta atualizar com senha curta
        resp = client.put(f'/api/usuarios/{uid}', json={
            'senha': 'abc',
        })
        assert resp.status_code == 400
