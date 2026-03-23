"""
Fixture compartilhada para todos os testes — Açaiteria CRM
Cria app Flask com banco SQLite em memória para isolamento total.
"""
import sys
import os
import pytest

# Garantir que o diretório cloud_version esteja no path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Definir DATABASE_URL ANTES de importar o app, para que o app use memória
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'

from backend.app import app as flask_app
from backend.models import db as _db


@pytest.fixture()
def app():
    """Cria instância do app com banco de dados em memória."""
    flask_app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'SQLALCHEMY_ECHO': False,
    })

    with flask_app.app_context():
        _db.drop_all()
        _db.create_all()
        yield flask_app
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def client(app):
    """Cliente HTTP de teste."""
    return app.test_client()


@pytest.fixture()
def db_session(app):
    """Sessão do banco dentro do contexto do app."""
    with app.app_context():
        yield _db.session
