# DigiMarket API

API REST pour une boutique en ligne de matériel informatique, développée avec Flask et SQLAlchemy.

---

## Stack technique

| Composant | Technologie |
|---|---|
| Langage | Python 3.13 |
| Framework | Flask |
| ORM | SQLAlchemy (Flask-SQLAlchemy) |
| Base de données | SQLite |
| Authentification | JWT (PyJWT) |
| Hachage des mots de passe | Werkzeug (PBKDF2-SHA256) |

---

## Installation

```bash
# Cloner le dépôt et se placer dans le dossier du projet
cd v2

# Installer les dépendances
pip install -r requirements.txt
```

---

## Démarrage du serveur

```bash
cd v2
flask run --debug
```

Le serveur démarre sur `http://127.0.0.1:5000`.

---

## Structure du projet

```
v2/
├── app.py                  # Factory Flask (create_app)
├── models.py               # Modèles SQLAlchemy (User, Product, Order, OrderItem)
├── middlewares.py          # Décorateurs réutilisables (token_required, require_json_fields)
├── requirements.txt        # Dépendances Python
├── blueprints/
│   ├── auth.py             # Routes /api/auth
│   ├── products.py         # Routes /api/produits
│   └── orders.py           # Routes /api/commandes
├── unit_tests/
│   ├── test_auth.py        # Tests unitaires auth (14 tests)
│   ├── test_products.py    # Tests unitaires produits (21 tests)
│   └── test_orders.py      # Tests unitaires commandes (23 tests)
├── test.py                 # Tests end-to-end auth
├── test_products.py        # Tests end-to-end produits
├── test_orders.py          # Tests end-to-end commandes
└── instance/
    └── digimarket.db       # Base SQLite (générée automatiquement)
```

---

## Base de données

La base SQLite est créée automatiquement au premier démarrage dans `instance/digimarket.db`.

| Table | Description |
|---|---|
| `user` | Utilisateurs (clients et admins) |
| `product` | Catalogue produits |
| `order` | Commandes |
| `order_item` | Lignes de commande |

---

## Documentation de l'API

### Authentification

Toutes les routes protégées nécessitent un token JWT dans le header :
```
Authorization: Bearer <token>
```

Le token est obtenu via `POST /api/auth/login` et est valable **24h**.

---

### Routes /api/auth

#### `POST /api/auth/register` — Créer un compte

```bash
curl -X POST http://127.0.0.1:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"jean@example.com","password":"motdepasse123","nom":"Jean Dupont","role":"client"}'
```

| Champ | Type | Requis | Description |
|---|---|---|---|
| `email` | string | oui | Adresse email unique |
| `password` | string | oui | Minimum 8 caractères |
| `nom` | string | oui | Nom complet |
| `role` | string | non | `client` (défaut) ou `admin` |

| Code | Cas |
|---|---|
| 201 | Compte créé |
| 400 | Champ manquant ou mot de passe trop court |
| 409 | Email déjà utilisé |

---

#### `POST /api/auth/login` — Se connecter

```bash
curl -X POST http://127.0.0.1:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"jean@example.com","password":"motdepasse123"}'
```

| Code | Cas |
|---|---|
| 200 | Connexion réussie — retourne `token`, `user` |
| 400 | Champ manquant |
| 401 | Email ou mot de passe incorrect |

---

### Routes /api/produits

#### `GET /api/produits` — Lister les produits

```bash
curl http://127.0.0.1:5000/api/produits
curl "http://127.0.0.1:5000/api/produits?q=clavier"
```

Paramètre optionnel `?q=` : recherche insensible à la casse dans le nom, la description et la catégorie.

| Code | Cas |
|---|---|
| 200 | Liste des produits (peut être vide) |

---

#### `GET /api/produits/<id>` — Détail d'un produit

```bash
curl http://127.0.0.1:5000/api/produits/1
```

| Code | Cas |
|---|---|
| 200 | Fiche produit |
| 404 | Produit non trouvé |

---

#### `POST /api/produits` — Créer un produit *(admin)*

```bash
curl -X POST http://127.0.0.1:5000/api/produits \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"nom":"Clavier mécanique","categorie":"Périphériques","prix":89.99,"quantite_stock":50}'
```

| Champ | Type | Requis |
|---|---|---|
| `nom` | string | oui |
| `categorie` | string | oui |
| `prix` | float | oui |
| `description` | string | non |
| `quantite_stock` | integer | non (défaut : 0) |

| Code | Cas |
|---|---|
| 201 | Produit créé |
| 400 | Champ manquant |
| 401 | Token absent ou invalide |
| 403 | Rôle insuffisant |

---

#### `PUT /api/produits/<id>` — Modifier un produit *(admin)*

```bash
curl -X PUT http://127.0.0.1:5000/api/produits/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"prix":79.99,"quantite_stock":45}'
```

Mise à jour partielle : seuls les champs fournis sont modifiés.

| Code | Cas |
|---|---|
| 200 | Produit mis à jour |
| 401 | Token absent ou invalide |
| 403 | Rôle insuffisant |
| 404 | Produit non trouvé |

---

#### `DELETE /api/produits/<id>` — Supprimer un produit *(admin)*

```bash
curl -X DELETE http://127.0.0.1:5000/api/produits/1 \
  -H "Authorization: Bearer <token>"
```

| Code | Cas |
|---|---|
| 200 | Produit supprimé |
| 401 | Token absent ou invalide |
| 403 | Rôle insuffisant |
| 404 | Produit non trouvé |

---

### Routes /api/commandes

#### `GET /api/commandes` — Lister les commandes

```bash
curl http://127.0.0.1:5000/api/commandes \
  -H "Authorization: Bearer <token>"
```

- **Admin** : retourne toutes les commandes de la plateforme.
- **Client** : retourne uniquement ses propres commandes.

| Code | Cas |
|---|---|
| 200 | Liste des commandes |
| 401 | Token absent ou invalide |

---

#### `GET /api/commandes/<id>` — Détail d'une commande

```bash
curl http://127.0.0.1:5000/api/commandes/1 \
  -H "Authorization: Bearer <token>"
```

| Code | Cas |
|---|---|
| 200 | Données de la commande |
| 401 | Token absent ou invalide |
| 403 | Commande appartenant à un autre utilisateur |
| 404 | Commande non trouvée |

---

#### `POST /api/commandes` — Créer une commande

```bash
curl -X POST http://127.0.0.1:5000/api/commandes \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "adresse_livraison": "12 rue de la Paix, 75001 Paris",
    "lignes": [
      {"product_id": 1, "quantite": 2},
      {"product_id": 3, "quantite": 1}
    ]
  }'
```

Vérifie la disponibilité en stock de chaque produit et déduit automatiquement les quantités après validation.

| Code | Cas |
|---|---|
| 201 | Commande créée (statut `en_attente`) |
| 400 | Lignes vides, données invalides ou stock insuffisant |
| 401 | Token absent ou invalide |
| 404 | Produit inexistant |

---

#### `PATCH /api/commandes/<id>` — Modifier le statut *(admin)*

```bash
curl -X PATCH http://127.0.0.1:5000/api/commandes/1 \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"statut":"validee"}'
```

Statuts acceptés : `en_attente`, `validee`, `expediee`, `annulee`.

| Code | Cas |
|---|---|
| 200 | Statut mis à jour |
| 400 | Statut invalide |
| 401 | Token absent ou invalide |
| 403 | Rôle insuffisant |
| 404 | Commande non trouvée |

---

#### `GET /api/commandes/<id>/lignes` — Lignes d'une commande

```bash
curl http://127.0.0.1:5000/api/commandes/1/lignes \
  -H "Authorization: Bearer <token>"
```

| Code | Cas |
|---|---|
| 200 | Liste des lignes de commande |
| 401 | Token absent ou invalide |
| 403 | Commande appartenant à un autre utilisateur |
| 404 | Commande non trouvée |

---

## Tests

### Tests unitaires

Les tests unitaires utilisent `pytest` avec des mocks (`unittest.mock`) — aucune base de données réelle n'est sollicitée.

```bash
cd v2
python -m pytest unit_tests/ -v
```

| Fichier | Routes testées | Nombre de tests |
|---|---|---|
| `unit_tests/test_auth.py` | `/api/auth` | 14 |
| `unit_tests/test_products.py` | `/api/produits` | 21 |
| `unit_tests/test_orders.py` | `/api/commandes` | 23 |

**Total : 58 tests**

---

### Tests end-to-end

Les tests end-to-end s'exécutent contre le serveur Flask en cours d'exécution.

```bash
# 1. Démarrer le serveur dans un terminal
cd v2
flask run --debug

# 2. Dans un autre terminal, lancer les tests
python test.py           # routes auth
python test_products.py  # routes produits
python test_orders.py    # routes commandes
```

Chaque fichier est indépendant : il gère sa propre authentification et peut être exécuté seul.
