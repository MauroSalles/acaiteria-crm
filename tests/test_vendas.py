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


def _setup_complemento(client, nome='Granola', preco=2.50, categoria='Extra'):
    """Cria um complemento e retorna id_complemento."""
    rc = client.post('/api/complementos', json={
        'nome': nome,
        'preco_adicional': preco,
        'categoria': categoria,
        'unidade_medida': 'porção',
    })
    assert rc.status_code == 201, (
        f'Falha ao criar complemento: {rc.status_code} {rc.data}'
    )
    return rc.get_json()['id_complemento']


class TestVendaComComplementos:
    """Testes de vendas com complementos/toppings."""

    def test_venda_com_complementos(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        comp1 = _setup_complemento(client, 'Granola', 2.50)
        comp2 = _setup_complemento(client, 'Leite Condensado', 3.00)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{
                'id_produto': pid,
                'quantidade': 1,
                'complementos': [comp1, comp2],
            }],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # 18.90 + 2.50 + 3.00 = 24.40
        assert data['valor_total'] == 24.40
        assert len(data['itens'][0]['complementos']) == 2

    def test_venda_sem_complementos_continua_funcionando(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['valor_total'] == 18.90
        assert data['itens'][0]['complementos'] == []

    def test_venda_complemento_multiplicado_por_quantidade(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        comp = _setup_complemento(client, 'Nutella', 5.00)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{
                'id_produto': pid,
                'quantidade': 3,
                'complementos': [comp],
            }],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # (18.90 + 5.00) * 3 = 71.70
        assert data['valor_total'] == 71.70

    def test_complemento_inativo_ignorado(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        comp = _setup_complemento(client, 'Amendoim', 1.50)
        # Desativar complemento
        client.delete(f'/api/complementos/{comp}')
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{
                'id_produto': pid,
                'quantidade': 1,
                'complementos': [comp],
            }],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # Complemento inativo ignorado: preço = só do produto
        assert data['valor_total'] == 18.90
        assert len(data['itens'][0]['complementos']) == 0

    def test_complemento_inexistente_ignorado(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{
                'id_produto': pid,
                'quantidade': 1,
                'complementos': [9999],
            }],
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['valor_total'] == 18.90
        assert data['itens'][0]['complementos'] == []


def _setup_cupom(client, codigo='PROMO10', tipo='percentual', valor=10,
                 usos_maximos=100, valor_minimo=0):
    """Cria um cupom de desconto e retorna o código."""
    rc = client.post('/api/cupons', json={
        'codigo': codigo,
        'tipo_desconto': tipo,
        'valor_desconto': valor,
        'usos_maximos': usos_maximos,
        'valor_minimo_pedido': valor_minimo,
    })
    assert rc.status_code == 201, (
        f'Falha ao criar cupom: {rc.status_code} {rc.data}'
    )
    return rc.get_json()['codigo']


class TestVendaComCupom:
    """Testes de vendas com cupom de desconto."""

    def test_venda_com_cupom_percentual(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        _setup_cupom(client, 'DESC10', 'percentual', 10)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 2}],
            'cupom_codigo': 'DESC10',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # 18.90 * 2 = 37.80 → 37.80 - 10% = 34.02
        assert data['valor_total'] == 34.02

    def test_venda_com_cupom_fixo(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        _setup_cupom(client, 'FIXO5', 'fixo', 5)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
            'cupom_codigo': 'FIXO5',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # 18.90 - 5.00 = 13.90
        assert data['valor_total'] == 13.90

    def test_venda_cupom_fixo_nao_fica_negativo(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        _setup_cupom(client, 'MEGA', 'fixo', 9999)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
            'cupom_codigo': 'MEGA',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['valor_total'] == 0.00

    def test_venda_cupom_invalido_ignorado(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
            'cupom_codigo': 'INEXISTENTE',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # Cupom não encontrado → sem desconto
        assert data['valor_total'] == 18.90

    def test_venda_cupom_incrementa_usos(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        _setup_cupom(client, 'USO1', 'percentual', 5, usos_maximos=10)
        client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 1}],
            'cupom_codigo': 'USO1',
        })
        # Verificar que usos_atuais incrementou
        resp = client.get('/api/cupons')
        assert resp.status_code == 200
        data = resp.get_json()
        cupons = data.get('cupons', data) if isinstance(data, dict) else data
        cupom = [c for c in cupons if c['codigo'] == 'USO1'][0]
        assert cupom['usos_realizados'] == 1

    def test_venda_cupom_com_desconto_percentual_combinado(self, client):
        cid, pid = _setup_cliente_e_produto(client, consentimento=True)
        _setup_cupom(client, 'COMBO', 'percentual', 10)
        resp = client.post('/api/vendas', json={
            'id_cliente': cid,
            'forma_pagamento': 'Dinheiro',
            'itens': [{'id_produto': pid, 'quantidade': 2}],
            'desconto_percentual': 10.0,
            'cupom_codigo': 'COMBO',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # 18.90 * 2 = 37.80
        # desconto_percentual 10% = 3.78
        # cupom 10% = 3.78
        # total = 37.80 - 7.56 = 30.24
        assert data['valor_total'] == 30.24
