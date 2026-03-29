import requests
import json

BASE = "http://127.0.0.1:5000"

def print_response(label, response):
    print(f"\n[{label}] {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


# --- Authentification (prérequis) ---

requests.post(f"{BASE}/api/auth/register", json={
    "email": "jean@example.com",
    "password": "motdepasse123",
    "nom": "Jean Dupont",
    "role": "client"
})
client_token = requests.post(f"{BASE}/api/auth/login", json={
    "email": "jean@example.com",
    "password": "motdepasse123"
}).json()["token"]

requests.post(f"{BASE}/api/auth/register", json={
    "email": "admin@example.com",
    "password": "adminpass123",
    "nom": "Admin DigiMarket",
    "role": "admin"
})
admin_token = requests.post(f"{BASE}/api/auth/login", json={
    "email": "admin@example.com",
    "password": "adminpass123"
}).json()["token"]


# --- Produits (prérequis) ---

rep = requests.post(f"{BASE}/api/produits",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "nom": "Casque audio",
        "description": "Casque gaming surround 7.1",
        "categorie": "Audio",
        "prix": 59.99,
        "quantite_stock": 20
    }
)
produit1_id = rep.json().get("id")

rep = requests.post(f"{BASE}/api/produits",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "nom": "Tapis de souris XL",
        "description": "Tapis gaming 90x40cm",
        "categorie": "Accessoires",
        "prix": 19.99,
        "quantite_stock": 5
    }
)
produit2_id = rep.json().get("id")


# --- Gestion des commandes ---

# curl -X POST http://127.0.0.1:5000/api/commandes \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <client_token>" \
#   -d '{"adresse_livraison":"12 rue de la Paix, Paris","lignes":[{"product_id":<id>,"quantite":2},{"product_id":<id>,"quantite":1}]}'
rep = requests.post(f"{BASE}/api/commandes",
    headers={"Authorization": f"Bearer {client_token}"},
    json={
        "adresse_livraison": "12 rue de la Paix, 75001 Paris",
        "lignes": [
            {"product_id": produit1_id, "quantite": 2},
            {"product_id": produit2_id, "quantite": 1}
        ]
    }
)
print_response("POST /api/commandes (client)", rep)
commande_id = rep.json().get("id")

# curl -X POST http://127.0.0.1:5000/api/commandes \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <client_token>" \
#   -d '{"adresse_livraison":"...","lignes":[{"product_id":<id>,"quantite":999}]}'
rep = requests.post(f"{BASE}/api/commandes",
    headers={"Authorization": f"Bearer {client_token}"},
    json={
        "adresse_livraison": "12 rue de la Paix, 75001 Paris",
        "lignes": [{"product_id": produit2_id, "quantite": 999}]
    }
)
print_response("POST /api/commandes (stock insuffisant → 400)", rep)

# curl -X POST http://127.0.0.1:5000/api/commandes \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <client_token>" \
#   -d '{"adresse_livraison":"...","lignes":[{"product_id":9999,"quantite":1}]}'
rep = requests.post(f"{BASE}/api/commandes",
    headers={"Authorization": f"Bearer {client_token}"},
    json={
        "adresse_livraison": "12 rue de la Paix, 75001 Paris",
        "lignes": [{"product_id": 9999, "quantite": 1}]
    }
)
print_response("POST /api/commandes (produit inexistant → 404)", rep)

# curl http://127.0.0.1:5000/api/commandes \
#   -H "Authorization: Bearer <client_token>"
rep = requests.get(f"{BASE}/api/commandes",
    headers={"Authorization": f"Bearer {client_token}"}
)
print_response("GET /api/commandes (client → ses commandes)", rep)

# curl http://127.0.0.1:5000/api/commandes \
#   -H "Authorization: Bearer <admin_token>"
rep = requests.get(f"{BASE}/api/commandes",
    headers={"Authorization": f"Bearer {admin_token}"}
)
print_response("GET /api/commandes (admin → toutes)", rep)

# curl http://127.0.0.1:5000/api/commandes/<id> \
#   -H "Authorization: Bearer <client_token>"
rep = requests.get(f"{BASE}/api/commandes/{commande_id}",
    headers={"Authorization": f"Bearer {client_token}"}
)
print_response(f"GET /api/commandes/{commande_id} (client)", rep)

# curl http://127.0.0.1:5000/api/commandes/9999 \
#   -H "Authorization: Bearer <admin_token>"
rep = requests.get(f"{BASE}/api/commandes/9999",
    headers={"Authorization": f"Bearer {admin_token}"}
)
print_response("GET /api/commandes/9999 (404)", rep)

# curl http://127.0.0.1:5000/api/commandes/<id>/lignes \
#   -H "Authorization: Bearer <client_token>"
rep = requests.get(f"{BASE}/api/commandes/{commande_id}/lignes",
    headers={"Authorization": f"Bearer {client_token}"}
)
print_response(f"GET /api/commandes/{commande_id}/lignes (client)", rep)

# curl -X PATCH http://127.0.0.1:5000/api/commandes/<id> \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <client_token>" \
#   -d '{"statut":"validee"}'
rep = requests.patch(f"{BASE}/api/commandes/{commande_id}",
    headers={"Authorization": f"Bearer {client_token}"},
    json={"statut": "validee"}
)
print_response(f"PATCH /api/commandes/{commande_id} (client → 403)", rep)

# curl -X PATCH http://127.0.0.1:5000/api/commandes/<id> \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <admin_token>" \
#   -d '{"statut":"invalide"}'
rep = requests.patch(f"{BASE}/api/commandes/{commande_id}",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"statut": "invalide"}
)
print_response(f"PATCH /api/commandes/{commande_id} (statut invalide → 400)", rep)

# curl -X PATCH http://127.0.0.1:5000/api/commandes/<id> \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <admin_token>" \
#   -d '{"statut":"validee"}'
rep = requests.patch(f"{BASE}/api/commandes/{commande_id}",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"statut": "validee"}
)
print_response(f"PATCH /api/commandes/{commande_id} (admin → validee)", rep)

# curl -X PATCH http://127.0.0.1:5000/api/commandes/<id> \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <admin_token>" \
#   -d '{"statut":"expediee"}'
rep = requests.patch(f"{BASE}/api/commandes/{commande_id}",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"statut": "expediee"}
)
print_response(f"PATCH /api/commandes/{commande_id} (admin → expediee)", rep)
