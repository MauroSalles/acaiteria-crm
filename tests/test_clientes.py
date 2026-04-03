"""
Testes da API de Clientes — Açaiteria CRM
Cobertura: CRUD, validação Pydantic, LGPD (consentimento, anonimização, histórico).
"""


# ============================================================
# HELPERS
# ============================================================

def _criar_cliente(client, **overrides):
    """Helper rápido para criar um cliente com dados válidos."""
    payload = {
        'nome': 'Maria Silva',
        'telefone': '12999990000',
        'email': 'maria@email.com',
        'consentimento_lgpd': True,
        'versao_politica': 'v1.0',
    }
    payload.update(overrides)
    return client.post('/api/clientes', json=payload)


# ============================================================
# TESTES — LISTAR CLIENTES
# ============================================================

class TestListarClientes:
    def test_lista_vazia(self, client):
        resp = client.get('/api/clientes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['clientes'] == []
        assert data['total'] == 0

    def test_lista_com_clientes(self, client):
        _criar_cliente(client, nome='Ana')
        _criar_cliente(client, nome='Bruno', email='bruno@e.com')
        resp = client.get('/api/clientes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data['clientes']) == 2
        nomes = {c['nome'] for c in data['clientes']}
        assert 'Ana' in nomes
        assert 'Bruno' in nomes


# ============================================================
# TESTES — CRIAR CLIENTE
# ============================================================

class TestCriarCliente:
    def test_criar_com_dados_validos(self, client):
        resp = _criar_cliente(client)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nome'] == 'Maria Silva'
        assert data['consentimento_lgpd'] is True

    def test_criar_sem_nome_retorna_400(self, client):
        resp = client.post('/api/clientes', json={
            'nome': '',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 400

    def test_criar_com_email_invalido_retorna_400(self, client):
        resp = client.post('/api/clientes', json={
            'nome': 'Teste',
            'email': 'nao-e-email',
            'consentimento_lgpd': True,
        })
        assert resp.status_code == 400

    def test_criar_sem_consentimento(self, client):
        resp = _criar_cliente(client, consentimento_lgpd=False)
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['consentimento_lgpd'] is False


# ============================================================
# TESTES — OBTER / ATUALIZAR / DELETAR CLIENTE
# ============================================================

class TestCrudCliente:
    def test_obter_cliente_existente(self, client):
        r = _criar_cliente(client)
        cid = r.get_json()['id_cliente']
        resp = client.get(f'/api/clientes/{cid}')
        assert resp.status_code == 200
        assert resp.get_json()['nome'] == 'Maria Silva'

    def test_obter_cliente_inexistente_404(self, client):
        resp = client.get('/api/clientes/9999')
        assert resp.status_code == 404

    def test_atualizar_cliente(self, client):
        r = _criar_cliente(client)
        cid = r.get_json()['id_cliente']
        resp = client.put(
            f'/api/clientes/{cid}', json={'nome': 'Maria Atualizada'})
        assert resp.status_code == 200
        assert resp.get_json()['nome'] == 'Maria Atualizada'

    def test_deletar_anonimiza_cliente(self, client):
        r = _criar_cliente(client)
        cid = r.get_json()['id_cliente']
        resp = client.delete(f'/api/clientes/{cid}')
        assert resp.status_code == 200

        # Verificar anonimização: não aparece mais na lista
        lista = client.get('/api/clientes').get_json()['clientes']
        assert all(c['id_cliente'] != cid for c in lista)


# ============================================================
# TESTES — LGPD (CONSENTIMENTO E HISTÓRICO)
# ============================================================

class TestLGPD:
    def test_conceder_consentimento(self, client):
        r = _criar_cliente(client, consentimento_lgpd=False)
        cid = r.get_json()['id_cliente']
        resp = client.put(f'/api/clientes/{cid}/consentimento', json={
            'consentimento_lgpd': True,
            'versao_politica': 'v1.0',
        })
        assert resp.status_code == 200
        assert resp.get_json()['cliente']['consentimento_lgpd'] is True

    def test_revogar_consentimento(self, client):
        r = _criar_cliente(client, consentimento_lgpd=True)
        cid = r.get_json()['id_cliente']
        resp = client.put(f'/api/clientes/{cid}/consentimento', json={
            'consentimento_lgpd': False,
            'versao_politica': 'v1.0',
        })
        assert resp.status_code == 200
        assert resp.get_json()['cliente']['consentimento_lgpd'] is False

    def test_historico_consentimento(self, client):
        r = _criar_cliente(client, consentimento_lgpd=True)
        cid = r.get_json()['id_cliente']

        # Revogar
        client.put(f'/api/clientes/{cid}/consentimento', json={
            'consentimento_lgpd': False,
            'versao_politica': 'v1.0',
        })

        resp = client.get(f'/api/clientes/{cid}/consentimento/historico')
        assert resp.status_code == 200
        hist = resp.get_json()['historico']
        # Deve ter ao menos 2 entradas: concessão inicial + revogação
        assert len(hist) >= 2
        acoes = [h['acao'] for h in hist]
        assert 'concedeu' in acoes
        assert 'revogou' in acoes

    def test_historico_cliente_inexistente_404(self, client):
        resp = client.get('/api/clientes/9999/consentimento/historico')
        assert resp.status_code == 404
