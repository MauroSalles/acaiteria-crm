"""
Fixture compartilhada para todos os testes — Açaiteria CRM
Cria app Flask com banco SQLite em memória para isolamento total.
"""
import sys
import os
import pytest
from sqlalchemy.pool import StaticPool

# Garantir que o diretório cloud_version esteja no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Definir DATABASE_URL ANTES de importar o app, para que o app use memória
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from backend.app import app as flask_app, limiter
from backend.models import db as _db, Usuario


@pytest.fixture()
def app():
    """Cria instância do app com banco de dados em memória."""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ENGINE_OPTIONS': {
            'connect_args': {'check_same_thread': False},
            'poolclass': StaticPool,
        },
        'SQLALCHEMY_ECHO': False,
    })
    limiter.enabled = False

    with flask_app.app_context():
        _db.drop_all()
        _db.create_all()
        # Criar admin de teste
        admin = Usuario(nome='Admin Teste', email='admin@teste.com', papel='admin')
        admin.set_senha('admin123')
        _db.session.add(admin)
        _db.session.commit()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Cliente HTTP de teste — já autenticado como admin."""
    test_client = app.test_client()
    with test_client.session_transaction() as sess:
        sess['autenticado'] = True
        sess['usuario_id'] = 1
        sess['usuario_nome'] = 'Admin Teste'
        sess['papel'] = 'admin'
    return test_client


@pytest.fixture()
def unauthenticated_client(app):
    """Cliente HTTP de teste — SEM autenticação."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Sessão do banco dentro do contexto do app."""
    with app.app_context():
        yield _db.session
