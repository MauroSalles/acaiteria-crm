"""
Testes extras do módulo financeiro — CRUD, resumo consolidado, categorias.
Complementa test_compras_fornecedores.py com cobertura de lançamentos manuais.
"""


class TestFinanceiroCRUD:
    """CRUD de lançamentos financeiros."""

    RECEITA = {
        'tipo': 'receita',
        'categoria': 'Vendas',
        'descricao': 'Venda balcão',
        'valor': 150.50,
        'data_lancamento': '2025-01-15',
        'forma_pagamento': 'Pix',
        'status': 'Pago',
    }
    DESPESA = {
        'tipo': 'despesa',
        'categoria': 'Fornecedores',
        'descricao': 'Compra polpa',
        'valor': 80.00,
        'data_lancamento': '2025-01-15',
        'forma_pagamento': 'Boleto',
        'status': 'Pago',
    }

    def test_criar_receita(self, client):
        resp = client.post('/api/financeiro', json=self.RECEITA)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['tipo'] == 'receita'
        assert float(data['valor']) == 150.50

    def test_criar_despesa(self, client):
        resp = client.post('/api/financeiro', json=self.DESPESA)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['tipo'] == 'despesa'

    def test_listar_lancamentos(self, client):
        client.post('/api/financeiro', json=self.RECEITA)
        client.post('/api/financeiro', json=self.DESPESA)
        resp = client.get('/api/financeiro')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'lancamentos' in data
        assert len(data['lancamentos']) >= 2
        assert 'resumo' in data

    def test_listar_filtro_tipo(self, client):
        client.post('/api/financeiro', json=self.RECEITA)
        client.post('/api/financeiro', json=self.DESPESA)
        resp = client.get('/api/financeiro?tipo=receita')
        assert resp.status_code == 200
        data = resp.get_json()
        for lanc in data['lancamentos']:
            assert lanc['tipo'] == 'receita'

    def test_listar_filtro_data(self, client):
        client.post('/api/financeiro', json=self.RECEITA)
        resp = client.get(
            '/api/financeiro?data_inicio=2025-01-01&data_fim=2025-12-31'
        )
        assert resp.status_code == 200
        assert len(resp.get_json()['lancamentos']) >= 1

    def test_listar_filtro_busca(self, client):
        client.post('/api/financeiro', json=self.RECEITA)
        resp = client.get('/api/financeiro?busca=balcão')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['lancamentos']) >= 1

    def test_atualizar_lancamento(self, client):
        r = client.post('/api/financeiro', json=self.RECEITA)
        lid = r.get_json()['id_lancamento']
        resp = client.put(f'/api/financeiro/{lid}', json={
            'valor': 200.00,
            'descricao': 'Atualizado',
        })
        assert resp.status_code == 200
        assert float(resp.get_json()['valor']) == 200.00

    def test_atualizar_tipo_invalido(self, client):
        r = client.post('/api/financeiro', json=self.RECEITA)
        lid = r.get_json()['id_lancamento']
        resp = client.put(f'/api/financeiro/{lid}', json={
            'tipo': 'invalido',
        })
        assert resp.status_code == 400

    def test_atualizar_inexistente(self, client):
        resp = client.put('/api/financeiro/99999', json={'valor': 100})
        assert resp.status_code == 404

    def test_excluir_lancamento(self, client):
        r = client.post('/api/financeiro', json=self.RECEITA)
        lid = r.get_json()['id_lancamento']
        resp = client.delete(f'/api/financeiro/{lid}')
        assert resp.status_code == 200
        assert 'excluído' in resp.get_json().get('mensagem', '').lower() or \
               'sucesso' in resp.get_json().get('mensagem', '').lower()

    def test_excluir_inexistente(self, client):
        resp = client.delete('/api/financeiro/99999')
        assert resp.status_code == 404

    def test_paginacao(self, client):
        for i in range(5):
            d = dict(self.RECEITA)
            d['descricao'] = f'Lanc {i}'
            client.post('/api/financeiro', json=d)
        resp = client.get('/api/financeiro?pagina=1&por_pagina=2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['lancamentos']) == 2
        assert data['total'] >= 5
        assert data['total_paginas'] >= 3


class TestResumoFinanceiro:
    """Testa o resumo consolidado (lançamentos + vendas + compras)."""

    def test_resumo_vazio(self, client):
        resp = client.get('/api/financeiro/resumo')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_receitas' in data
        assert 'total_despesas' in data
        assert 'saldo' in data
        assert 'detalhamento' in data

    def test_resumo_com_lancamentos(self, client):
        client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'Vendas',
            'valor': 500, 'data_lancamento': '2025-06-01',
        })
        client.post('/api/financeiro', json={
            'tipo': 'despesa', 'categoria': 'Fornecedores',
            'valor': 200, 'data_lancamento': '2025-06-01',
        })
        resp = client.get('/api/financeiro/resumo')
        data = resp.get_json()
        assert data['detalhamento']['receitas_manual'] == 500.0
        assert data['detalhamento']['despesas_manual'] == 200.0
        assert data['saldo'] == 300.0

    def test_resumo_com_filtro_data(self, client):
        client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'Vendas',
            'valor': 100, 'data_lancamento': '2025-01-15',
        })
        client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'Vendas',
            'valor': 200, 'data_lancamento': '2025-06-15',
        })
        resp = client.get(
            '/api/financeiro/resumo?data_inicio=2025-06-01&data_fim=2025-06-30'
        )
        data = resp.get_json()
        assert data['detalhamento']['receitas_manual'] == 200.0

    def test_resumo_com_venda(self, client):
        """Vendas do sistema aparecem no resumo como receitas."""
        c = client.post('/api/clientes', json={
            'nome': 'Fin Test', 'consentimento_lgpd': True,
        })
        cid = c.get_json()['id_cliente']
        p = client.post('/api/produtos', json={
            'nome_produto': 'Produto Fin', 'preco': 25,
            'categoria': 'Açaí',
        })
        pid = p.get_json()['id_produto']
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 2}],
            'forma_pagamento': 'Pix',
        })
        resp = client.get('/api/financeiro/resumo')
        data = resp.get_json()
        assert data['detalhamento']['receitas_vendas'] == 50.0
        assert data['total_receitas'] == 50.0


class TestCategoriasFinanceiro:
    """Testa endpoint de categorias distintas."""

    def test_categorias_vazio(self, client):
        resp = client.get('/api/financeiro/categorias')
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_categorias_com_dados(self, client):
        client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'Vendas',
            'valor': 100, 'data_lancamento': '2025-01-15',
        })
        client.post('/api/financeiro', json={
            'tipo': 'despesa', 'categoria': 'Fornecedores',
            'valor': 50, 'data_lancamento': '2025-01-15',
        })
        resp = client.get('/api/financeiro/categorias')
        cats = resp.get_json()
        assert 'Vendas' in cats
        assert 'Fornecedores' in cats


class TestFinanceiroSeguranca:
    """Testa autenticação nos endpoints financeiros."""

    def test_listar_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.get('/api/financeiro')
        assert resp.status_code == 401

    def test_criar_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'X', 'valor': 10,
            'data_lancamento': '2025-01-15',
        })
        assert resp.status_code == 401

    def test_resumo_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.get('/api/financeiro/resumo')
        assert resp.status_code == 401

    def test_categorias_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.get('/api/financeiro/categorias')
        assert resp.status_code == 401

    def test_excluir_sem_login(self, unauthenticated_client):
        resp = unauthenticated_client.delete('/api/financeiro/1')
        assert resp.status_code == 401


class TestFinanceiroValidacao:
    """Testa validações de entrada no módulo financeiro."""

    def test_tipo_invalido(self, client):
        resp = client.post('/api/financeiro', json={
            'tipo': 'empréstimo',
            'categoria': 'X', 'valor': 100,
            'data_lancamento': '2025-01-15',
        })
        assert resp.status_code == 400

    def test_valor_negativo(self, client):
        resp = client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'X',
            'valor': -100, 'data_lancamento': '2025-01-15',
        })
        assert resp.status_code == 400

    def test_data_invalida(self, client):
        resp = client.post('/api/financeiro', json={
            'tipo': 'receita', 'categoria': 'X',
            'valor': 100, 'data_lancamento': 'ontem',
        })
        assert resp.status_code == 400

    def test_sem_dados(self, client):
        resp = client.post('/api/financeiro', json={})
        assert resp.status_code == 400

    def test_pagina_financeiro_html(self, client):
        resp = client.get('/financeiro')
        assert resp.status_code == 200
