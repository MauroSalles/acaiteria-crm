"""
Testes da API de Produtos — Açaiteria CRM
"""


def _criar_produto(client, **overrides):
    payload = {
        'nome_produto': 'Açaí 500ml',
        'categoria': 'Açaí',
        'descricao': 'Açaí batido 500ml com granola',
        'preco': 18.90,
    }
    payload.update(overrides)
    return client.post('/api/produtos', json=payload)


class TestListarProdutos:
    def test_lista_vazia(self, client):
        resp = client.get('/api/produtos')
        assert resp.status_code == 200
        assert resp.get_json() == []

    def test_lista_com_produtos(self, client):
        _criar_produto(client, nome_produto='Açaí 300ml')
        _criar_produto(client, nome_produto='Açaí 700ml')
        resp = client.get('/api/produtos')
        assert resp.status_code == 200
        assert len(resp.get_json()) == 2


class TestCriarProduto:
    def test_criar_produto_valido(self, client):
        resp = _criar_produto(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nome_produto'] == 'Açaí 500ml'
        assert data['preco'] == 18.90

    def test_criar_produto_sem_nome_retorna_400(self, client):
        resp = client.post('/api/produtos', json={'preco': 10.0})
        assert resp.status_code == 400

    def test_criar_produto_sem_preco_retorna_400(self, client):
        resp = client.post('/api/produtos', json={'nome_produto': 'Teste'})
        assert resp.status_code == 400
