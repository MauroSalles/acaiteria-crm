"""
Testes dos endpoints de Suporte (Tickets + Mensagens) — Açaiteria CRM
"""
import json


class TestListarTickets:
    def test_listar_tickets_vazio(self, client):
        resp = client.get('/api/suporte/tickets')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['dados'] == []
        assert data['total'] == 0

    def test_listar_tickets_nao_autenticado(self, unauthenticated_client):
        resp = unauthenticated_client.get('/api/suporte/tickets')
        assert resp.status_code == 401

    def test_listar_tickets_com_filtro_status(self, client):
        # Cria ticket para ter dados
        client.post('/api/suporte/tickets', json={
            'assunto': 'Teste filtro',
            'categoria': 'duvida',
            'prioridade': 'normal',
            'mensagem': 'Mensagem inicial do ticket',
        })
        resp = client.get('/api/suporte/tickets?status=aberto')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1
        for t in data['dados']:
            assert t['status'] == 'aberto'

    def test_listar_tickets_paginacao(self, client):
        resp = client.get('/api/suporte/tickets?pagina=1&limite=5')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'pagina' in data
        assert 'limite' in data
        assert 'total_paginas' in data


class TestCriarTicket:
    def test_criar_ticket_sucesso(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Máquina de açaí com defeito',
            'categoria': 'problema',
            'prioridade': 'alta',
            'mensagem': 'A máquina parou de funcionar hoje cedo',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['assunto'] == 'Máquina de açaí com defeito'
        assert data['categoria'] == 'problema'
        assert data['prioridade'] == 'alta'
        assert data['status'] == 'aberto'
        assert data['total_mensagens'] == 1
        assert data['mensagens'][0]['conteudo'] == 'A máquina parou de funcionar hoje cedo'

    def test_criar_ticket_sem_assunto(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': '',
            'categoria': 'duvida',
            'prioridade': 'normal',
            'mensagem': 'Mensagem qualquer aqui',
        })
        assert resp.status_code == 400

    def test_criar_ticket_categoria_invalida(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Teste',
            'categoria': 'invalida',
            'prioridade': 'normal',
            'mensagem': 'Mensagem de teste válida',
        })
        assert resp.status_code == 400

    def test_criar_ticket_prioridade_invalida(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Teste',
            'categoria': 'duvida',
            'prioridade': 'nao_existe',
            'mensagem': 'Mensagem de teste válida',
        })
        assert resp.status_code == 400

    def test_criar_ticket_mensagem_curta(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Teste',
            'categoria': 'duvida',
            'prioridade': 'normal',
            'mensagem': 'abc',  # Menos de 5 chars
        })
        assert resp.status_code == 400

    def test_criar_ticket_nao_autenticado(self, unauthenticated_client):
        resp = unauthenticated_client.post('/api/suporte/tickets', json={
            'assunto': 'Teste',
            'categoria': 'duvida',
            'prioridade': 'normal',
            'mensagem': 'Mensagem de teste válida',
        })
        assert resp.status_code == 401


class TestObterTicket:
    def test_obter_ticket_existente(self, client):
        # Cria ticket
        create_resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Dúvida sobre cardápio',
            'categoria': 'duvida',
            'prioridade': 'baixa',
            'mensagem': 'Como faço para alterar o cardápio?',
        })
        id_ticket = create_resp.get_json()['id_ticket']

        resp = client.get(f'/api/suporte/tickets/{id_ticket}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['id_ticket'] == id_ticket
        assert data['assunto'] == 'Dúvida sobre cardápio'
        assert len(data['mensagens']) == 1

    def test_obter_ticket_inexistente(self, client):
        resp = client.get('/api/suporte/tickets/99999')
        assert resp.status_code == 404

    def test_obter_ticket_nao_autenticado(self, unauthenticated_client):
        resp = unauthenticated_client.get('/api/suporte/tickets/1')
        assert resp.status_code == 401


class TestEnviarMensagem:
    def _criar_ticket(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Ticket para chat',
            'categoria': 'sugestao',
            'prioridade': 'normal',
            'mensagem': 'Primeira mensagem do ticket',
        })
        return resp.get_json()['id_ticket']

    def test_enviar_mensagem_sucesso(self, client):
        id_ticket = self._criar_ticket(client)
        resp = client.post(f'/api/suporte/tickets/{id_ticket}/mensagens', json={
            'conteudo': 'Segunda mensagem respondendo',
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['conteudo'] == 'Segunda mensagem respondendo'
        assert data['id_ticket'] == id_ticket

    def test_enviar_mensagem_vazia(self, client):
        id_ticket = self._criar_ticket(client)
        resp = client.post(f'/api/suporte/tickets/{id_ticket}/mensagens', json={
            'conteudo': '',
        })
        assert resp.status_code == 400

    def test_enviar_mensagem_ticket_inexistente(self, client):
        resp = client.post('/api/suporte/tickets/99999/mensagens', json={
            'conteudo': 'Mensagem para ticket inexistente',
        })
        assert resp.status_code == 404

    def test_admin_responde_muda_status(self, client):
        """Quando admin responde, ticket aberto vai para em_andamento"""
        id_ticket = self._criar_ticket(client)

        # Verifica status inicial
        ticket = client.get(f'/api/suporte/tickets/{id_ticket}').get_json()
        assert ticket['status'] == 'aberto'

        # Admin envia mensagem
        client.post(f'/api/suporte/tickets/{id_ticket}/mensagens', json={
            'conteudo': 'Estamos analisando sua solicitação',
        })

        # Verifica que status mudou
        ticket = client.get(f'/api/suporte/tickets/{id_ticket}').get_json()
        assert ticket['status'] == 'em_andamento'

    def test_enviar_mensagem_ticket_fechado(self, client):
        id_ticket = self._criar_ticket(client)
        # Fecha o ticket
        client.put(f'/api/suporte/tickets/{id_ticket}/status', json={
            'status': 'fechado',
        })
        # Tenta enviar mensagem
        resp = client.post(f'/api/suporte/tickets/{id_ticket}/mensagens', json={
            'conteudo': 'Tentativa em ticket fechado',
        })
        assert resp.status_code == 400

    def test_enviar_mensagem_nao_autenticado(self, unauthenticated_client):
        resp = unauthenticated_client.post('/api/suporte/tickets/1/mensagens', json={
            'conteudo': 'Mensagem não autorizada',
        })
        assert resp.status_code == 401


class TestAtualizarStatusTicket:
    def _criar_ticket(self, client):
        resp = client.post('/api/suporte/tickets', json={
            'assunto': 'Ticket status teste',
            'categoria': 'outro',
            'prioridade': 'normal',
            'mensagem': 'Mensagem para teste de status',
        })
        return resp.get_json()['id_ticket']

    def test_admin_atualiza_status(self, client):
        id_ticket = self._criar_ticket(client)
        resp = client.put(f'/api/suporte/tickets/{id_ticket}/status', json={
            'status': 'resolvido',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'resolvido'

    def test_status_invalido(self, client):
        id_ticket = self._criar_ticket(client)
        resp = client.put(f'/api/suporte/tickets/{id_ticket}/status', json={
            'status': 'inexistente',
        })
        assert resp.status_code == 400

    def test_ticket_inexistente(self, client):
        resp = client.put('/api/suporte/tickets/99999/status', json={
            'status': 'fechado',
        })
        assert resp.status_code == 404

    def test_nao_autenticado(self, unauthenticated_client):
        resp = unauthenticated_client.put('/api/suporte/tickets/1/status', json={
            'status': 'fechado',
        })
        assert resp.status_code == 401

    def test_admin_pode_reabrir(self, client):
        id_ticket = self._criar_ticket(client)
        # Fecha
        client.put(f'/api/suporte/tickets/{id_ticket}/status', json={
            'status': 'fechado',
        })
        # Reabre
        resp = client.put(f'/api/suporte/tickets/{id_ticket}/status', json={
            'status': 'aberto',
        })
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'aberto'

    def test_fluxo_completo_status(self, client):
        """Testa o ciclo completo de vida do ticket"""
        id_ticket = self._criar_ticket(client)

        # aberto → em_andamento
        resp = client.put(f'/api/suporte/tickets/{id_ticket}/status', json={'status': 'em_andamento'})
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'em_andamento'

        # em_andamento → resolvido
        resp = client.put(f'/api/suporte/tickets/{id_ticket}/status', json={'status': 'resolvido'})
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'resolvido'

        # resolvido → fechado
        resp = client.put(f'/api/suporte/tickets/{id_ticket}/status', json={'status': 'fechado'})
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'fechado'


class TestSuportePaginaHTML:
    def test_pagina_suporte_autenticado(self, client):
        resp = client.get('/suporte')
        assert resp.status_code == 200

    def test_pagina_suporte_nao_autenticado(self, unauthenticated_client):
        resp = unauthenticated_client.get('/suporte')
        assert resp.status_code == 302  # Redireciona para login


class TestIAAutoResponder:
    """Testes do endpoint /api/suporte/ia-resposta — Agente IA ML (TF-IDF + Cosine Similarity)."""

    def test_ia_resposta_match_senha(self, client):
        """Pergunta sobre senha deve retornar resposta sobre login."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'esqueci minha senha como faço login',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ia'] is True
        assert data['confianca'] > 0
        assert 'senha' in data['resposta'].lower() or 'login' in data['resposta'].lower()
        assert 'categoria_sugerida' in data
        assert 'metodo' in data
        assert 'similaridade' in data

    def test_ia_resposta_match_venda(self, client):
        """Pergunta sobre vendas deve retornar resposta sobre registro de vendas."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'como posso registrar uma venda nova?',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ia'] is True
        assert data['confianca'] > 0
        assert data['metodo'] == 'tfidf_cosine_similarity'

    def test_ia_resposta_match_lgpd(self, client):
        """Pergunta sobre LGPD deve retornar resposta sobre proteção de dados."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'quero saber sobre lgpd e privacidade dos dados',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['confianca'] > 0
        assert 'lgpd' in data['resposta'].lower() or 'dados' in data['resposta'].lower()

    def test_ia_resposta_sem_match(self, client):
        """Pergunta sem match deve retornar confianca 0 com fallback."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'xyz lorem ipsum blah',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['confianca'] == 0.0
        assert data['ia'] is True
        assert data['metodo'] == 'nenhum_match'

    def test_ia_resposta_mensagem_curta(self, client):
        """Mensagem com menos de 2 chars deve retornar 400."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'a',
        })
        assert resp.status_code == 400

    def test_ia_resposta_mensagem_vazia(self, client):
        """Mensagem vazia deve retornar 400."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': '',
        })
        assert resp.status_code == 400

    def test_ia_resposta_sem_corpo(self, client):
        """Requisição sem JSON deve retornar 400."""
        resp = client.post('/api/suporte/ia-resposta',
                           data='', content_type='application/json')
        assert resp.status_code == 400

    def test_ia_resposta_nao_autenticado(self, unauthenticated_client):
        """Endpoint deve exigir autenticação."""
        resp = unauthenticated_client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'como faço login?',
        })
        assert resp.status_code == 401

    def test_ia_resposta_match_estoque(self, client):
        """Pergunta sobre estoque deve retornar resposta sobre controle de estoque."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'o estoque está acabando preciso repor produtos',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['confianca'] > 0

    def test_ia_resposta_match_fidelidade(self, client):
        """Pergunta sobre fidelidade deve retornar resposta sobre pontos."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'como funciona o programa de fidelidade e pontos?',
        })
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['confianca'] > 0

    def test_ia_retorna_similaridade_numerica(self, client):
        """Campo similaridade deve ser float entre 0 e 1."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'relatório financeiro fechamento de caixa',
        })
        data = resp.get_json()
        assert isinstance(data['similaridade'], float)
        assert 0.0 <= data['similaridade'] <= 1.0

    def test_ia_categoria_sugerida_valida(self, client):
        """Categoria sugerida deve ser um valor válido."""
        resp = client.post('/api/suporte/ia-resposta', json={
            'mensagem': 'erro bug o sistema não funciona travou',
        })
        data = resp.get_json()
        assert data['categoria_sugerida'] in ('duvida', 'problema', 'sugestao', 'outro')
