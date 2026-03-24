import requests
import json

BASE = "http://127.0.0.1:5000"

def print_response(label, response):
    print(f"\n[{label}] {response.status_code}")
    print(json.dumps(response.json(), indent=2, ensure_ascii=False))


# --- Authentification ---

# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"motdepasse123","nom":"Jean Dupont","role":"client"}'
requests.post(f"{BASE}/api/auth/register", json={
    "email": "jean@example.com",
    "password": "motdepasse123",
    "nom": "Jean Dupont",
    "role": "client"
})

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"motdepasse123"}'
rep = requests.post(f"{BASE}/api/auth/login", json={
    "email": "jean@example.com",
    "password": "motdepasse123"
})
client_token = rep.json()["token"]
print_response("POST /api/auth/login (client)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"adminpass123","nom":"Admin DigiMarket","role":"admin"}'
requests.post(f"{BASE}/api/auth/register", json={
    "email": "admin@example.com",
    "password": "adminpass123",
    "nom": "Admin DigiMarket",
    "role": "admin"
})

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"adminpass123"}'
rep = requests.post(f"{BASE}/api/auth/login", json={
    "email": "admin@example.com",
    "password": "adminpass123"
})
admin_token = rep.json()["token"]
print_response("POST /api/auth/login (admin)", rep)


# --- Catalogue produits ---

# curl http://127.0.0.1:5000/api/produits
rep = requests.get(f"{BASE}/api/produits")
print_response("GET /api/produits (liste vide)", rep)

# curl -X POST http://127.0.0.1:5000/api/produits \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <admin_token>" \
#   -d '{"nom":"Clavier mécanique","description":"Clavier gaming RGB","categorie":"Périphériques","prix":89.99,"quantite_stock":50}'
rep = requests.post(f"{BASE}/api/produits",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "nom": "Clavier mécanique",
        "description": "Clavier gaming RGB",
        "categorie": "Périphériques",
        "prix": 89.99,
        "quantite_stock": 50
    }
)
print_response("POST /api/produits (admin)", rep)
product_id = rep.json().get("id")

# curl -X POST http://127.0.0.1:5000/api/produits \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <admin_token>" \
#   -d '{"nom":"Souris sans fil","description":"Souris ergonomique 1600 DPI","categorie":"Périphériques","prix":34.99,"quantite_stock":100}'
rep = requests.post(f"{BASE}/api/produits",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={
        "nom": "Souris sans fil",
        "description": "Souris ergonomique 1600 DPI",
        "categorie": "Périphériques",
        "prix": 34.99,
        "quantite_stock": 100
    }
)
print_response("POST /api/produits (2ème produit)", rep)

# curl http://127.0.0.1:5000/api/produits
rep = requests.get(f"{BASE}/api/produits")
print_response("GET /api/produits (liste complète)", rep)

# curl "http://127.0.0.1:5000/api/produits?q=clavier"
rep = requests.get(f"{BASE}/api/produits", params={"q": "clavier"})
print_response("GET /api/produits?q=clavier", rep)

# curl "http://127.0.0.1:5000/api/produits?q=xxxxinexistant"
rep = requests.get(f"{BASE}/api/produits", params={"q": "xxxxinexistant"})
print_response("GET /api/produits?q=xxxxinexistant (aucun résultat)", rep)

# curl http://127.0.0.1:5000/api/produits/<id>
rep = requests.get(f"{BASE}/api/produits/{product_id}")
print_response(f"GET /api/produits/{product_id}", rep)

# curl http://127.0.0.1:5000/api/produits/9999
rep = requests.get(f"{BASE}/api/produits/9999")
print_response("GET /api/produits/9999 (404)", rep)

# curl -X PUT http://127.0.0.1:5000/api/produits/<id> \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <admin_token>" \
#   -d '{"prix":79.99,"quantite_stock":45}'
rep = requests.put(f"{BASE}/api/produits/{product_id}",
    headers={"Authorization": f"Bearer {admin_token}"},
    json={"prix": 79.99, "quantite_stock": 45}
)
print_response(f"PUT /api/produits/{product_id} (admin)", rep)

# curl -X POST http://127.0.0.1:5000/api/produits \
#   -H "Content-Type: application/json" \
#   -H "Authorization: Bearer <client_token>" \
#   -d '{"nom":"Hack","categorie":"Test","prix":1.0}'
rep = requests.post(f"{BASE}/api/produits",
    headers={"Authorization": f"Bearer {client_token}"},
    json={"nom": "Hack", "categorie": "Test", "prix": 1.0}
)
print_response("POST /api/produits (client → 403)", rep)

# curl -X DELETE http://127.0.0.1:5000/api/produits/<id> \
#   -H "Authorization: Bearer <admin_token>"
rep = requests.delete(f"{BASE}/api/produits/{product_id}",
    headers={"Authorization": f"Bearer {admin_token}"}
)
print_response(f"DELETE /api/produits/{product_id} (admin)", rep)
