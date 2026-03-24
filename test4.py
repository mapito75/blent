import requests
import json

def print_response(response):
    print(f"Status: {response.status_code}")
    print("Response:", json.dumps(response.json(), indent=2))


rep = requests.post("http://127.0.0.1:5000/api/auth/register", json={ "email": "jean@example.com", "password": "motdepasse123",
  "nom": "Jean Dupont", "role": "client" }
)


rep = requests.post("http://127.0.0.1:5000/api/auth/login", json={ "email": "jean@example.com", "password": "motdepasse123" })
my_token = json.loads(rep.content)["token"]
print(rep.status_code, json.loads(rep.content))
print("my_token", my_token)

