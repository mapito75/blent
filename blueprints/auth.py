# blueprints/auth.py — Blueprint d'authentification
#
# Ce module gère l'inscription et la connexion des utilisateurs.
# Il expose deux routes sous le préfixe /api/auth :
#   POST /api/auth/register  → créer un compte
#   POST /api/auth/login     → se connecter et obtenir un token JWT
#
# Le token JWT retourné par /login doit être envoyé dans les requêtes suivantes
# via l'en-tête : Authorization: Bearer <token>

import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from models import db, User
from middlewares import require_json_fields

# Création du blueprint avec un préfixe d'URL commun à toutes ses routes
auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@require_json_fields('email', 'password', 'nom')
def register():
    """Crée un nouveau compte utilisateur.

    Corps JSON attendu :
        {
            "email": "jean@example.com",
            "password": "motdepasse123",
            "nom": "Jean Dupont",
            "role": "client"  (optionnel, défaut: "client")
        }

    Retourne :
        201 + données utilisateur si le compte est créé
        400 si champs manquants ou mot de passe trop court
        409 si l'email est déjà utilisé
    """
    data = request.get_json()

    # Le mot de passe doit contenir au moins 8 caractères pour une sécurité minimale
    if len(data['password']) < 8:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caractères'}), 400

    # Vérifie l'unicité de l'email (insensible à la casse, stocké en minuscules)
    existing = db.session.execute(
        db.select(User).filter_by(email=data['email'].lower())
    ).scalar_one_or_none()
    if existing:
        return jsonify({'error': 'Cette adresse email est déjà utilisée'}), 409

    # Le rôle 'admin' peut être demandé explicitement, sinon 'client' par défaut.
    # Toute valeur invalide est silencieusement remplacée par 'client'.
    role = data.get('role', 'client')
    if role not in ('client', 'admin'):
        role = 'client'

    user = User(
        email=data['email'].lower(),
        nom=data['nom'],
        role=role
    )
    # set_password hache le mot de passe avant de le stocker
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'Compte créé avec succès',
        'user': user.to_dict()
    }), 201


@auth_bp.route('/login', methods=['POST'])
@require_json_fields('email', 'password')
def login():
    """Authentifie un utilisateur et retourne un token JWT.

    Corps JSON attendu :
        {
            "email": "jean@example.com",
            "password": "motdepasse123"
        }

    Retourne :
        200 + token JWT (valable 24h) si les identifiants sont corrects
        401 si l'email ou le mot de passe est incorrect

    Le token retourné contient (encodé) :
        - user_id : identifiant de l'utilisateur
        - role    : 'client' ou 'admin'
        - exp     : timestamp d'expiration (24h)
    """
    data = request.get_json()
    email = data.get('email', '').lower()
    password = data.get('password', '')

    # Recherche l'utilisateur par email (insensible à la casse)
    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    # Message volontairement générique pour ne pas révéler si l'email existe ou non
    if not user or not user.check_password(password):
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

    # Construction du payload JWT avec une expiration de 24 heures
    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    # Signature du token avec la clé secrète de l'application (algorithme HMAC-SHA256)
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Connexion réussie',
        'token': token,
        'user': user.to_dict()
    }), 200
