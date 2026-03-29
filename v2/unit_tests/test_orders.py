# test_orders.py — Tests unitaires pour le blueprint /api/commandes
#
# La base de données est entièrement mockée (unittest.mock).
# Seul le client HTTP Flask est réel.

import pytest
import jwt
from unittest.mock import patch, MagicMock
from app import create_app
from models import Order, OrderItem, Product

SECRET_KEY = 'ceciestunesecretkey'


@pytest.fixture
def client():
    app = create_app({'TESTING': True, 'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:'})
    with app.app_context():
        yield app.test_client()


def make_token(role='client', user_id=1):
    return jwt.encode({'user_id': user_id, 'role': role}, SECRET_KEY, algorithm='HS256')


def _fake_order(id=1, utilisateur_id=1, adresse='12 rue de la Paix', statut='en_attente', lignes=None):
    """Mock d'une commande retournée par la base."""
    o = MagicMock(spec=Order)
    o.id = id
    o.utilisateur_id = utilisateur_id
    o.adresse_livraison = adresse
    o.statut = statut
    o.lignes = lignes or []
    o.to_dict.side_effect = lambda: {
        'id': o.id,
        'utilisateur_id': o.utilisateur_id,
        'adresse_livraison': o.adresse_livraison,
        'statut': o.statut,
        'date_commande': None
    }
    return o


def _fake_product(id=1, nom='Clavier', prix=89.99, stock=10):
    """Mock d'un produit retourné par la base."""
    p = MagicMock(spec=Product)
    p.id = id
    p.nom = nom
    p.prix = prix
    p.quantite_stock = stock
    return p


def _fake_order_item(commande_id=1, produit_id=1, quantite=2, prix_unitaire=89.99):
    """Mock d'une ligne de commande."""
    i = MagicMock(spec=OrderItem)
    i.commande_id = commande_id
    i.produit_id = produit_id
    i.quantite = quantite
    i.prix_unitaire = prix_unitaire
    i.to_dict.return_value = {
        'id': 1, 'commande_id': commande_id, 'produit_id': produit_id,
        'quantite': quantite, 'prix_unitaire': prix_unitaire
    }
    return i


def _to_dict_safe_order(self):
    """Remplaçant de Order.to_dict() sans date_commande (commit mocké)."""
    return {
        'id': self.id,
        'utilisateur_id': self.utilisateur_id,
        'adresse_livraison': self.adresse_livraison,
        'statut': self.statut,
        'date_commande': None
    }


# ---------------------------------------------------------------------------
# GET /api/commandes
# ---------------------------------------------------------------------------

def test_list_commandes_admin_voit_tout(client):
    commandes = [_fake_order(id=1, utilisateur_id=1), _fake_order(id=2, utilisateur_id=2)]
    token = make_token(role='admin')
    with patch('blueprints.orders.Order.query') as mock_query:
        mock_query.all.return_value = commandes
        r = client.get('/api/commandes', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert len(r.get_json()) == 2

def test_list_commandes_client_voit_ses_commandes(client):
    commande = _fake_order(utilisateur_id=1)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.Order.query') as mock_query:
        mock_query.filter_by.return_value.all.return_value = [commande]
        r = client.get('/api/commandes', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert len(r.get_json()) == 1

def test_list_commandes_sans_token(client):
    r = client.get('/api/commandes')
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# GET /api/commandes/<id>
# ---------------------------------------------------------------------------

def test_get_commande_admin(client):
    commande = _fake_order(id=1, utilisateur_id=2)
    token = make_token(role='admin', user_id=99)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.get('/api/commandes/1', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200

def test_get_commande_client_sa_commande(client):
    commande = _fake_order(id=1, utilisateur_id=1)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.get('/api/commandes/1', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200

def test_get_commande_client_commande_autre(client):
    commande = _fake_order(id=1, utilisateur_id=2)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.get('/api/commandes/1', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403

def test_get_commande_non_trouvee(client):
    token = make_token(role='admin')
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.get('/api/commandes/9999', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/commandes
# ---------------------------------------------------------------------------

def test_create_commande_ok(client):
    produit = _fake_product(id=1, stock=10)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session, \
         patch.object(Order, 'to_dict', _to_dict_safe_order):
        mock_session.get.return_value = produit
        r = client.post('/api/commandes',
                        json={'adresse_livraison': '12 rue de la Paix', 'lignes': [{'product_id': 1, 'quantite': 2}]},
                        headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 201
    assert r.get_json()['statut'] == 'en_attente'

def test_create_commande_deduit_stock(client):
    produit = _fake_product(id=1, stock=10)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session, \
         patch.object(Order, 'to_dict', _to_dict_safe_order):
        mock_session.get.return_value = produit
        client.post('/api/commandes',
                    json={'adresse_livraison': '12 rue de la Paix', 'lignes': [{'product_id': 1, 'quantite': 3}]},
                    headers={'Authorization': f'Bearer {token}'})
    assert produit.quantite_stock == 7  # 10 - 3

def test_create_commande_stock_insuffisant(client):
    produit = _fake_product(id=1, stock=1)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = produit
        r = client.post('/api/commandes',
                        json={'adresse_livraison': '12 rue de la Paix', 'lignes': [{'product_id': 1, 'quantite': 5}]},
                        headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400
    assert 'insuffisant' in r.get_json()['error']

def test_create_commande_produit_inexistant(client):
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.post('/api/commandes',
                        json={'adresse_livraison': '12 rue de la Paix', 'lignes': [{'product_id': 999, 'quantite': 1}]},
                        headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 404

def test_create_commande_lignes_vides(client):
    token = make_token(role='client', user_id=1)
    r = client.post('/api/commandes',
                    json={'adresse_livraison': '12 rue de la Paix', 'lignes': []},
                    headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400

def test_create_commande_champ_manquant(client):
    token = make_token(role='client', user_id=1)
    r = client.post('/api/commandes',
                    json={'adresse_livraison': '12 rue de la Paix'},
                    headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400
    assert 'Champs manquants' in r.get_json()['error']

def test_create_commande_sans_token(client):
    r = client.post('/api/commandes',
                    json={'adresse_livraison': '12 rue de la Paix', 'lignes': [{'product_id': 1, 'quantite': 1}]})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# PATCH /api/commandes/<id>
# ---------------------------------------------------------------------------

def test_update_statut_ok(client):
    commande = _fake_order(statut='en_attente')
    token = make_token(role='admin')
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.patch('/api/commandes/1', json={'statut': 'validee'},
                         headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert commande.statut == 'validee'

def test_update_statut_invalide(client):
    commande = _fake_order()
    token = make_token(role='admin')
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.patch('/api/commandes/1', json={'statut': 'inconnu'},
                         headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 400
    assert 'Statut invalide' in r.get_json()['error']

def test_update_statut_role_client(client):
    token = make_token(role='client')
    r = client.patch('/api/commandes/1', json={'statut': 'validee'},
                     headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403

def test_update_statut_sans_token(client):
    r = client.patch('/api/commandes/1', json={'statut': 'validee'})
    assert r.status_code == 401

def test_update_statut_commande_non_trouvee(client):
    token = make_token(role='admin')
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.patch('/api/commandes/9999', json={'statut': 'validee'},
                         headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /api/commandes/<id>/lignes
# ---------------------------------------------------------------------------

def test_get_lignes_admin(client):
    ligne = _fake_order_item()
    commande = _fake_order(utilisateur_id=2, lignes=[ligne])
    token = make_token(role='admin', user_id=99)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.get('/api/commandes/1/lignes', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200
    assert len(r.get_json()) == 1

def test_get_lignes_client_sa_commande(client):
    ligne = _fake_order_item()
    commande = _fake_order(utilisateur_id=1, lignes=[ligne])
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.get('/api/commandes/1/lignes', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 200

def test_get_lignes_client_commande_autre(client):
    commande = _fake_order(utilisateur_id=2)
    token = make_token(role='client', user_id=1)
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = commande
        r = client.get('/api/commandes/1/lignes', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 403

def test_get_lignes_commande_non_trouvee(client):
    token = make_token(role='admin')
    with patch('blueprints.orders.db.session') as mock_session:
        mock_session.get.return_value = None
        r = client.get('/api/commandes/9999/lignes', headers={'Authorization': f'Bearer {token}'})
    assert r.status_code == 404
