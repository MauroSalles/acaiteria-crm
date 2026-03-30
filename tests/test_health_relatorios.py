"""
Testes do Health Check, Relatórios e Autenticação — Açaiteria CRM
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

    def test_relatorio_por_data(self, client):
        resp = client.get('/api/relatorios/por-data?data=2026-01-01')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'total_vendas' in data
        assert 'faturamento_total' in data
        assert 'por_forma_pagamento' in data


class TestRelatorioClientesFrequentes:
    def test_clientes_frequentes_vazio(self, client):
        resp = client.get('/api/relatorios/clientes-frequentes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['dados'] == []
        assert data['total'] == 0
        assert data['pagina'] == 1


class TestRelatorioProdutosRanking:
    def test_produtos_ranking_vazio(self, client):
        resp = client.get('/api/relatorios/produtos-ranking')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['dados'] == []
        assert data['total'] == 0
        assert data['pagina'] == 1


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

    def test_pagina_usuarios_admin(self, client):
        resp = client.get('/usuarios')
        assert resp.status_code == 200
        assert b'Usu' in resp.data

    def test_pagina_404(self, client):
        resp = client.get('/rota-inexistente')
        assert resp.status_code == 404


class TestAutenticacao:
    def test_login_page_carrega(self, unauthenticated_client):
        resp = unauthenticated_client.get('/login')
        assert resp.status_code == 200
        assert b'email' in resp.data or b'Email' in resp.data

    def test_rota_protegida_redireciona_sem_auth(self, unauthenticated_client):
        resp = unauthenticated_client.get('/')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']

    def test_login_com_credenciais_corretas(self, unauthenticated_client):
        resp = unauthenticated_client.post('/login', data={
            'email': 'admin@teste.com', 'senha': 'admin123'
        })
        assert resp.status_code == 302
        assert '/' in resp.headers['Location']

    def test_login_com_credenciais_erradas(self, unauthenticated_client):
        resp = unauthenticated_client.post('/login', data={
            'email': 'admin@teste.com', 'senha': 'errado'
        })
        assert resp.status_code == 200
        assert 'incorreto' in resp.data.decode('utf-8').lower()

    def test_logout(self, client):
        resp = client.get('/logout')
        assert resp.status_code == 302
        assert '/login' in resp.headers['Location']


class TestUsuariosAPI:
    def test_listar_usuarios(self, client):
        resp = client.get('/api/usuarios')
        assert resp.status_code == 200
        data = resp.get_json()
        assert len(data) >= 1
        assert data[0]['email'] == 'admin@teste.com'

    def test_criar_usuario(self, client):
        resp = client.post('/api/usuarios', json={
            'nome': 'Operador Teste',
            'email': 'operador@teste.com',
            'senha': 'op123456',
            'papel': 'operador'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['nome'] == 'Operador Teste'
        assert data['papel'] == 'operador'

    def test_criar_usuario_email_duplicado(self, client):
        resp = client.post('/api/usuarios', json={
            'nome': 'Dup', 'email': 'admin@teste.com',
            'senha': 'abcd1234', 'papel': 'operador'
        })
        assert resp.status_code == 409

    def test_atualizar_usuario(self, client):
        # Criar primeiro
        resp = client.post('/api/usuarios', json={
            'nome': 'Edit Test', 'email': 'edit@teste.com',
            'senha': 'abcd1234', 'papel': 'operador'
        })
        uid = resp.get_json()['id_usuario']
        # Atualizar
        resp = client.put(f'/api/usuarios/{uid}', json={'nome': 'Editado'})
        assert resp.status_code == 200
        assert resp.get_json()['nome'] == 'Editado'

    def test_desativar_usuario(self, client):
        resp = client.post('/api/usuarios', json={
            'nome': 'Del Test', 'email': 'del@teste.com',
            'senha': 'abcd1234', 'papel': 'operador'
        })
        uid = resp.get_json()['id_usuario']
        resp = client.delete(f'/api/usuarios/{uid}')
        assert resp.status_code == 200
        assert 'desativado' in resp.get_json()['mensagem'].lower()

    def test_nao_pode_desativar_proprio_usuario(self, client):
        resp = client.delete('/api/usuarios/1')
        assert resp.status_code == 400

    def test_usuario_me(self, client):
        resp = client.get('/api/me')
        assert resp.status_code == 200
        assert resp.get_json()['email'] == 'admin@teste.com'


class TestExportCSV:
    def test_exportar_csv_vazio(self, client):
        resp = client.get('/api/exportar/clientes-csv')
        assert resp.status_code == 200
        assert 'text/csv' in resp.content_type
