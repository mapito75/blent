import requests
import json

def print_response(response):
    print(f"Status: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))


# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"motdepasse123","nom":"Jean Dupont","role":"client"}'
rep = requests.post("http://127.0.0.1:5000/api/auth/register", json={
    "email": "jean@example.com",
    "password": "motdepasse123",
    "nom": "Jean Dupont",
    "role": "client"
})

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"jean@example.com","password":"motdepasse123"}'
rep = requests.post("http://127.0.0.1:5000/api/auth/login", json={
    "email": "jean@example.com",
    "password": "motdepasse123"
})
my_token = json.loads(rep.content)["token"]
print(rep.status_code, json.loads(rep.content))
print("my_token (client)", my_token)


# curl -X POST http://127.0.0.1:5000/api/auth/register \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"adminpass123","nom":"Admin DigiMarket","role":"admin"}'
rep = requests.post("http://127.0.0.1:5000/api/auth/register", json={
    "email": "admin@example.com",
    "password": "adminpass123",
    "nom": "Admin DigiMarket",
    "role": "admin"
})

# curl -X POST http://127.0.0.1:5000/api/auth/login \
#   -H "Content-Type: application/json" \
#   -d '{"email":"admin@example.com","password":"adminpass123"}'
rep = requests.post("http://127.0.0.1:5000/api/auth/login", json={
    "email": "admin@example.com",
    "password": "adminpass123"
})
admin_token = json.loads(rep.content)["token"]
print(rep.status_code, json.loads(rep.content))
print("my_token (admin)", admin_token)

