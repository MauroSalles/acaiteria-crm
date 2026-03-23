"""
Testes do Health Check e Relatórios — Açaiteria CRM
"""


class TestHealth:
    def test_health_endpoint(self, client):
        resp = client.get('/api/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'
        assert data['service'] == 'acaiteria-crm'
        assert 'timestamp' in data


class TestRelatorioDia:
    def test_relatorio_dia_atual(self, client):
        resp = client.get('/api/relatorios/dia-atual')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_vendas' in data
        assert 'faturamento_total' in data
        assert 'ticket_medio' in data
        assert 'por_forma_pagamento' in data


class TestRelatorioClientesFrequentes:
    def test_clientes_frequentes_vazio(self, client):
        resp = client.get('/api/relatorios/clientes-frequentes')
        assert resp.status_code == 200
        assert resp.get_json() == []


class TestRelatorioProdutosRanking:
    def test_produtos_ranking_vazio(self, client):
        resp = client.get('/api/relatorios/produtos-ranking')
        assert resp.status_code == 200
        assert resp.get_json() == []


class TestPaginasHTML:
    def test_pagina_index(self, client):
        resp = client.get('/')
        assert resp.status_code == 200
        assert b'Dashboard' in resp.data

    def test_pagina_cadastro_cliente(self, client):
        resp = client.get('/cadastro-cliente')
        assert resp.status_code == 200
        assert b'Cadastro' in resp.data

    def test_pagina_nova_venda(self, client):
        resp = client.get('/nova-venda')
        assert resp.status_code == 200
        assert b'Venda' in resp.data

    def test_pagina_clientes(self, client):
        resp = client.get('/clientes')
        assert resp.status_code == 200
        assert b'Clientes' in resp.data

    def test_pagina_relatorios(self, client):
        resp = client.get('/relatorios')
        assert resp.status_code == 200

    def test_pagina_fechamento(self, client):
        resp = client.get('/fechamento')
        assert resp.status_code == 200

    def test_pagina_produtos(self, client):
        resp = client.get('/produtos')
        assert resp.status_code == 200
        assert b'Produtos' in resp.data

    def test_pagina_politica_privacidade(self, client):
        resp = client.get('/politica-privacidade')
        assert resp.status_code == 200
        assert b'LGPD' in resp.data

    def test_pagina_404(self, client):
        resp = client.get('/rota-inexistente')
        assert resp.status_code == 404


class TestExportCSV:
    def test_exportar_csv_vazio(self, client):
        resp = client.get('/api/exportar/clientes-csv')
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type
