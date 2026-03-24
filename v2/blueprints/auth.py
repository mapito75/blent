# blueprints/auth.py — Blueprint d'authentification
#
# Routes exposées sous /api/auth :
#   POST /api/auth/register  → créer un compte utilisateur
#   POST /api/auth/login     → s'authentifier et obtenir un token JWT

import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from models import db, User
from middlewares import require_json_fields

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
            "role": "client"   (optionnel, défaut : "client")
        }

    Retourne :
        201 + données utilisateur si le compte est créé
        400 si le mot de passe est trop court
        409 si l'email est déjà utilisé
    """
    data = request.get_json()

    if len(data['password']) < 8:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caractères'}), 400

    email = data['email'].lower()

    existing = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()
    if existing:
        return jsonify({'error': 'Cette adresse email est déjà utilisée'}), 409

    # Toute valeur de rôle invalide est remplacée silencieusement par 'client'
    role = data.get('role', 'client')
    if role not in ('client', 'admin'):
        role = 'client'

    user = User(email=email, nom=data['nom'], role=role)
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
    """Authentifie un utilisateur et retourne un token JWT valable 24h.

    Corps JSON attendu :
        {
            "email": "jean@example.com",
            "password": "motdepasse123"
        }

    Retourne :
        200 + token JWT si les identifiants sont corrects
        401 si l'email ou le mot de passe est incorrect

    Le token contient : user_id, role, exp (expiration à 24h).
    À envoyer dans les requêtes suivantes via : Authorization: Bearer <token>
    """
    data = request.get_json()
    email = data['email'].lower()

    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()

    # Message générique pour ne pas révéler si l'email existe en base
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Email ou mot de passe incorrect'}), 401

    payload = {
        'user_id': user.id,
        'role': user.role,
        'exp': datetime.now(timezone.utc) + timedelta(hours=24)
    }
    token = jwt.encode(payload, current_app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Connexion réussie',
        'token': token,
        'user': user.to_dict()
    }), 200
