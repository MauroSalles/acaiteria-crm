"""
Testes da API de Vendas — Açaiteria CRM
Cobertura: criação, listagem, bloqueio LGPD, validação de itens.
"""


def _setup_cliente_e_produto(client, consentimento=True):
    """Cria um cliente e um produto, retorna (id_cliente, id_produto)."""
    rc = client.post('/api/clientes', json={
        'nome': 'Cliente Teste',
        'consentimento_lgpd': consentimento,
        'versao_politica': 'v1.0',
    })
    assert rc.status_code == 201, (
        f'Falha ao criar cliente: {rc.status_code} {rc.data}'
    )
    rp = client.post('/api/produtos', json={
        'nome_produto': 'Açaí 500ml',
        'preco': 18.90,
    })
    assert rp.status_code == 201, (
        f'Falha ao criar produto: {rp.status_code} {rp.data}'
    )
    return rc.get_json()['id_cliente'], rp.get_json()['id_produto']


class TestCriarVenda:
    def test_criar_venda_valida(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 2}],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['id_cliente'] == cid
        assert data['valor_total'] == 37.80  # 18.90 * 2
        assert len(data['itens']) == 1

    def test_venda_com_desconto(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 2}],
            'desconto_percentual': 10.0,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # 18.90 * 2 = 37.80  →  37.80 * 0.90 = 34.02
        assert data['valor_total'] == 34.02

    def test_venda_com_taxa(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Cartão',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
            'taxa': 2.50,
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # 18.90 + 2.50 = 21.40
        assert data['valor_total'] == 21.40

    def test_venda_produto_inativo_rejeitada(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        # Desativar o produto
        client.delete(f'/api/produtos/{pid}')
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
        })
        assert resp.status_code == 400
        assert 'desativado' in resp.get_json()['erro'].lower()

    def test_venda_bloqueada_sem_consentimento_lgpd(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=False)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 1}],
        })
        assert resp.status_code == 400
        assert 'LGPD' in resp.get_json()['erro']

    def test_venda_sem_itens_retorna_400(self, client):
        cid, _ = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [],
        })
        assert resp.status_code == 400

    def test_venda_cliente_inexistente_404(self, client):
        _, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': 9999,
            'itens': [{'id_produto': pid, 'quantidade': 1}],
        })
        assert resp.status_code == 404

    def test_venda_produto_inexistente_404(self, client):
        cid, _ = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': 9999, 'quantidade': 1}],
        })
        assert resp.status_code == 404


class TestListarVendas:
    def test_listar_vendas_vazio(self, client):
        resp = client.get('/api/vendas')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['vendas'] == []
        assert data['total'] == 0

    def test_listar_com_vendas(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 1}],
        })
        resp = client.get('/api/vendas')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['vendas']) == 1
        assert data['total'] == 1

    def test_filtrar_por_forma_pagamento(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Pix',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
        })
        resp = client.get('/api/vendas?forma_pagamento=Pix')
        data = resp.get_json()
        assert data['total'] == 1
        resp2 = client.get('/api/vendas?forma_pagamento=Cartao')
        assert resp2.get_json()['total'] == 0

    def test_obter_venda_por_id(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        rv = client.post('/api/vendas', json={
            'id_cliente': cid,
            'itens': [{'id_produto': pid, 'quantidade': 3}],
        })
        vid = rv.get_json()['id_venda']
        resp = client.get(f'/api/vendas/{vid}')
        assert resp.status_code == 200
        assert resp.get_json()['id_venda'] == vid

    def test_obter_venda_inexistente_404(self, client):
        resp = client.get('/api/vendas/9999')
        assert resp.status_code == 404
