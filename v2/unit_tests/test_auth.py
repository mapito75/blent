# test_auth.py — Tests unitaires pour le blueprint /api/auth
#
# La base de données est entièrement mockée (unittest.mock).
# Seul le client HTTP Flask est réel.

import pytest
import jwt
from unittest.mock import patch, MagicMock
from app import create_app
from models import User

SECRET_KEY = 'ceciestunesecretkey'


@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        yield app.test_client()


def _db_result(user=None):
    """Mock d'un résultat de requête SQLAlchemy (scalaire)."""
    mock = MagicMock()
    mock.scalar_one_or_none.return_value = user
    return mock


def _fake_user(email='jean@example.com', role='client', password_ok=True):
    """Mock d'un objet User retourné par la base."""
    u = MagicMock(spec=User)
    u.id = 1
    u.email = email
    u.role = role
    u.check_password.return_value = password_ok
    u.to_dict.return_value = {
        'id': 1, 'email': email, 'nom': 'Jean', 'role': role,
        'date_creation': '2024-01-01T00:00:00'
    }
    return u


# ---------------------------------------------------------------------------
# POST /api/auth/register
# ---------------------------------------------------------------------------

def _to_dict_safe(self):
    """Remplaçant de User.to_dict() tolérant une date_creation None (commit mocké)."""
    return {
        'id': self.id,
        'email': self.email,
        'nom': self.nom,
        'role': self.role,
        'date_creation': self.date_creation.isoformat() if self.date_creation else None
    }


def _patch_register():
    """Contexte combiné pour tester register : session mockée + db.select + to_dict sûr."""
    return (
        patch('blueprints.auth.db.session'),
        patch('blueprints.auth.db.select'),
        patch.object(User, 'to_dict', _to_dict_safe),
    )


def test_register_ok(client):
    with patch('blueprints.auth.db.session') as mock_session, \
         patch('blueprints.auth.db.select'), \
         patch.object(User, 'to_dict', _to_dict_safe):
        mock_session.execute.return_value = _db_result(None)
        r = client.post('/api/auth/register', json={
            'email': 'alice@example.com',
            'password': 'secret123',
            'nom': 'Alice'
        })
    assert r.status_code == 201
    assert r.get_json()['user']['email'] == 'alice@example.com'
    assert r.get_json()['user']['role'] == 'client'

def test_register_email_normalise_en_minuscules(client):
    with patch('blueprints.auth.db.session') as mock_session, \
         patch('blueprints.auth.db.select'), \
         patch.object(User, 'to_dict', _to_dict_safe):
        mock_session.execute.return_value = _db_result(None)
        client.post('/api/auth/register', json={
            'email': 'ALICE@EXAMPLE.COM',
            'password': 'secret123',
            'nom': 'Alice'
        })
    # Vérifie que l'objet User reçu par session.add() a un email en minuscules
    user_cree = mock_session.add.call_args.args[0]
    assert user_cree.email == 'alice@example.com'

def test_register_role_admin(client):
    with patch('blueprints.auth.db.session') as mock_session, \
         patch('blueprints.auth.db.select'), \
         patch.object(User, 'to_dict', _to_dict_safe):
        mock_session.execute.return_value = _db_result(None)
        r = client.post('/api/auth/register', json={
            'email': 'admin@example.com',
            'password': 'adminpass',
            'nom': 'Admin',
            'role': 'admin'
        })
    assert r.status_code == 201
    user_cree = mock_session.add.call_args.args[0]
    assert user_cree.role == 'admin'

def test_register_role_invalide_devient_client(client):
    with patch('blueprints.auth.db.session') as mock_session, \
         patch('blueprints.auth.db.select'), \
         patch.object(User, 'to_dict', _to_dict_safe):
        mock_session.execute.return_value = _db_result(None)
        r = client.post('/api/auth/register', json={
            'email': 'test@example.com',
            'password': 'secret123',
            'nom': 'Test',
            'role': 'superuser'
        })
    assert r.status_code == 201
    # Le rôle invalide doit être silencieusement remplacé par 'client'
    user_cree = mock_session.add.call_args.args[0]
    assert user_cree.role == 'client'

def test_register_email_deja_utilise(client):
    utilisateur = _fake_user()
    with patch('blueprints.auth.db.session') as mock_session:
        mock_session.execute.return_value = _db_result(utilisateur)
        r = client.post('/api/auth/register', json={
            'email': 'jean@example.com',
            'password': 'secret123',
            'nom': 'Jean'
        })
    assert r.status_code == 409

def test_register_mot_de_passe_trop_court(client):
    r = client.post('/api/auth/register', json={
        'email': 'test@example.com',
        'password': '1234',
        'nom': 'Test'
    })
    assert r.status_code == 400
    assert 'caractères' in r.get_json()['error']

def test_register_champ_manquant(client):
    r = client.post('/api/auth/register', json={
        'email': 'x@x.com',
        'password': 'pass1234'
    })
    assert r.status_code == 400
    assert 'Champs manquants' in r.get_json()['error']

def test_register_sans_corps_json(client):
    r = client.post('/api/auth/register', data='', content_type='application/json')
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# POST /api/auth/login
# ---------------------------------------------------------------------------

def test_login_ok(client):
    utilisateur = _fake_user()
    with patch('blueprints.auth.db.session') as mock_session:
        mock_session.execute.return_value = _db_result(utilisateur)
        r = client.post('/api/auth/login', json={
            'email': 'jean@example.com',
            'password': 'motdepasse123'
        })
    assert r.status_code == 200
    assert 'token' in r.get_json()

def test_login_token_contient_role_et_user_id(client):
    utilisateur = _fake_user()
    with patch('blueprints.auth.db.session') as mock_session:
        mock_session.execute.return_value = _db_result(utilisateur)
        r = client.post('/api/auth/login', json={
            'email': 'jean@example.com',
            'password': 'motdepasse123'
        })
    token = r.get_json()['token']
    payload = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
    assert payload['user_id'] == 1
    assert payload['role'] == 'client'

def test_login_mauvais_mot_de_passe(client):
    utilisateur = _fake_user(password_ok=False)
    with patch('blueprints.auth.db.session') as mock_session:
        mock_session.execute.return_value = _db_result(utilisateur)
        r = client.post('/api/auth/login', json={
            'email': 'jean@example.com',
            'password': 'mauvaismdp'
        })
    assert r.status_code == 401

def test_login_email_inexistant(client):
    with patch('blueprints.auth.db.session') as mock_session:
        mock_session.execute.return_value = _db_result(None)
        r = client.post('/api/auth/login', json={
            'email': 'inconnu@example.com',
            'password': 'nimporte'
        })
    assert r.status_code == 401

def test_login_message_generique(client):
    """Le message d'erreur ne doit pas révéler si l'email existe."""
    with patch('blueprints.auth.db.session') as mock_session:
        mock_session.execute.return_value = _db_result(None)
        r = client.post('/api/auth/login', json={
            'email': 'inconnu@example.com',
            'password': 'nimporte'
        })
    assert r.get_json()['error'] == 'Email ou mot de passe incorrect'

def test_login_champ_manquant(client):
    r = client.post('/api/auth/login', json={'email': 'x@x.com'})
    assert r.status_code == 400
