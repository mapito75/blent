# test_products.py — Tests unitaires pour le blueprint /api/produits
#
# La base de données est entièrement mockée (unittest.mock).
# Seul le client HTTP Flask est réel.

import pytest
import jwt
from unittest.mock import patch, MagicMock, patch
from app import create_app
from models import Product

SECRET_KEY = 'ceciestunesecretkey'


@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        yield app.test_client()


def make_token(role='admin', user_id=1):
    return jwt.encode({'user_id': user_id, 'role': role}, SECRET_KEY, algorithm='HS256')


def _fake_product(id=1, nom='Clavier', categorie='Périphériques', prix=89.99,
                  quantite_stock=10, description='RGB'):
    """Mock d'un produit retourné par la base."""
    p = MagicMock(spec=Product)
    p.id = id
    p.nom = nom
    p.categorie = categorie
    p.prix = prix
    p.quantite_stock = quantite_stock
    p.description = description
    # to_dict() lit les attributs courants du mock (utile pour vérifier les mises à jour)
    p.to_dict.side_effect = lambda: {
        'id': p.id, 'nom': p.nom, 'categorie': p.categorie,
        'prix': p.prix, 'quantite_stock': p.quantite_stock, 'description': p.description
    }
    return p


def _to_dict_safe(self):
    """Remplaçant de Product.to_dict() sans date_creation (commit mocké)."""
    return {
        'id': self.id,
        'nom': self.nom,
        'description': self.description,
        'categorie': self.categorie,
        'prix': self.prix,
        'quantite_stock': self.quantite_stock,
    }


# ---------------------------------------------------------------------------
# GET /api/produits
# ---------------------------------------------------------------------------

def test_list_products_vide(client):
    with patch('blueprints.products.Product.query') as mock_query:
        mock_query.all.return_value = []
        r = client.get('/api/produits')
    assert r.status_code == 200
    assert r.get_json() == []

def test_list_products_avec_produits(client):
    produit = _fake_product()
    with patch('blueprints.products.Product.query') as mock_query:
        mock_query.all.return_value = [produit]
        r = client.get('/api/produits')
    assert r.status_code == 200
    assert len(r.get_json()) == 1
    assert r.get_json()[0]['nom'] == 'Clavier'

def test_list_products_recherche_avec_resultat(client):
    produit = _fake_product()
    with patch('blueprints.products.Product.query') as mock_query:
        mock_query.filter.return_value.all.return_value = [produit]
        r = client.get('/api/produits?q=clavier')
    assert r.status_code == 200
    assert len(r.get_json()) == 1

def test_list_products_recherche_sans_resultat(client):
    with patch('blueprints.products.Product.query') as mock_query:
        mock_query.filter.return_value.all.return_value = []
        r = client.get('/api/produits?q=inexistant')
    assert r.status_code == 200
    assert r.get_json() == []


# ---------------------------------------------------------------------------
# GET /api/produits/<id>
# ---------------------------------------------------------------------------

def test_get_product_trouve(client):
    produit = _fake_product()
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = produit
        r = client.get('/api/produits/1')
    assert r.status_code == 200
    assert r.get_json()['nom'] == 'Clavier'

def test_get_product_non_trouve(client):
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.get('/api/produits/9999')
    assert r.status_code == 404
    assert 'error' in r.get_json()


# ---------------------------------------------------------------------------
# POST /api/produits
# ---------------------------------------------------------------------------

def test_create_product_ok(client):
    token = make_token(role='admin')
    with patch('blueprints.products.db.session'), \
         patch.object(Product, 'to_dict', _to_dict_safe):
        r = client.post('/api/produits',
                        json={'nom': 'Souris', 'categorie': 'Périphériques', 'prix': 29.99},
                        headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 201
    assert r.get_json()['nom'] == 'Souris'

def test_create_product_quantite_stock_defaut(client):
    token = make_token(role='admin')
    with patch('blueprints.products.db.session'), \
         patch.object(Product, 'to_dict', _to_dict_safe):
        r = client.post('/api/produits',
                        json={'nom': 'Souris', 'categorie': 'Périphériques', 'prix': 29.99},
                        headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 201
    assert r.get_json()['quantite_stock'] == 0

def test_create_product_sans_token(client):
    r = client.post('/api/produits',
                    json={'nom': 'Souris', 'categorie': 'Périphériques', 'prix': 29.99})
    assert r.status_code == 401

def test_create_product_role_client(client):
    token = make_token(role='client')
    r = client.post('/api/produits',
                    json={'nom': 'Souris', 'categorie': 'Périphériques', 'prix': 29.99},
                    headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403

def test_create_product_champ_manquant(client):
    token = make_token(role='admin')
    r = client.post('/api/produits',
                    json={'nom': 'Souris'},
                    headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400
    assert 'Champs manquants' in r.get_json()['error']

def test_create_product_sans_corps_json(client):
    token = make_token(role='admin')
    r = client.post('/api/produits', data='', content_type='application/json',
                    headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# PUT /api/produits/<id>
# ---------------------------------------------------------------------------

def test_update_product_ok(client):
    produit = _fake_product()
    token = make_token(role='admin')
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = produit
        r = client.put('/api/produits/1', json={'prix': 99.99},
                       headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert r.get_json()['prix'] == 99.99

def test_update_product_partiel(client):
    """Seuls les champs fournis doivent être modifiés."""
    produit = _fake_product(nom='Clavier', prix=89.99)
    token = make_token(role='admin')
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = produit
        r = client.put('/api/produits/1', json={'prix': 150.0},
                       headers={'Authorization': f'Bearer {token}'})
    assert r.get_json()['nom'] == 'Clavier'   # inchangé
    assert r.get_json()['prix'] == 150.0       # mis à jour

def test_update_product_sans_token(client):
    r = client.put('/api/produits/1', json={'prix': 99.99})
    assert r.status_code == 401

def test_update_product_role_client(client):
    token = make_token(role='client')
    r = client.put('/api/produits/1', json={'prix': 99.99},
                   headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403

def test_update_product_non_trouve(client):
    token = make_token(role='admin')
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.put('/api/produits/9999', json={'prix': 99.99},
                       headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/produits/<id>
# ---------------------------------------------------------------------------

def test_delete_product_ok(client):
    produit = _fake_product(nom='Clavier')
    token = make_token(role='admin')
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = produit
        r = client.delete('/api/produits/1',
                          headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert 'supprimé' in r.get_json()['message']

def test_delete_product_sans_token(client):
    r = client.delete('/api/produits/1')
    assert r.status_code == 401

def test_delete_product_role_client(client):
    token = make_token(role='client')
    r = client.delete('/api/produits/1',
                      headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403

def test_delete_product_non_trouve(client):
    token = make_token(role='admin')
    with patch('blueprints.products.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.delete('/api/produits/9999',
                          headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 404
