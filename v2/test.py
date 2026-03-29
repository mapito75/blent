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
rep = requests.post(f"{BASE}/api/auth/register", json={
    "email": "jean@example.com",
    "password": "motdepasse123",
    "nom": "Jean Dupont",
    "role": "client"
})
print_response("POST /api/auth/register (client)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"adminpass123","nom":"Admin DigiMarket","role":"admin"}'
rep = requests.post(f"{BASE}/api/auth/register", json={
    "email": "admin@example.com",
    "password": "adminpass123",
    "nom": "Admin DigiMarket",
    "role": "admin"
})
print_response("POST /api/auth/register (admin)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"motdepasse123","nom":"Jean Dupont"}'
rep = requests.post(f"{BASE}/api/auth/register", json={
    "email": "jean@example.com",
    "password": "motdepasse123",
    "nom": "Jean Dupont"
})
print_response("POST /api/auth/register (email déjà utilisé → 409)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"court@example.com","password":"1234","nom":"Test"}'
rep = requests.post(f"{BASE}/api/auth/register", json={
    "email": "court@example.com",
    "password": "1234",
    "nom": "Test"
})
print_response("POST /api/auth/register (mot de passe trop court → 400)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"motdepasse123"}'
rep = requests.post(f"{BASE}/api/auth/login", json={
    "email": "jean@example.com",
    "password": "motdepasse123"
})
print_response("POST /api/auth/login (client)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"mauvaismdp"}'
rep = requests.post(f"{BASE}/api/auth/login", json={
    "email": "jean@example.com",
    "password": "mauvaismdp"
})
print_response("POST /api/auth/login (mauvais mot de passe → 401)", rep)

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"inconnu@example.com","password":"motdepasse123"}'
rep = requests.post(f"{BASE}/api/auth/login", json={
    "email": "inconnu@example.com",
    "password": "motdepasse123"
})
print_response("POST /api/auth/login (email inexistant → 401)", rep)
