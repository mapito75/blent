import jwt
from datetime import datetime, timezone, timedelta
from flask import Blueprint, request, jsonify, current_app
from models import db, User
from middlewares import require_json_fields

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/register', methods=['POST'])
@require_json_fields('email', 'password', 'nom')
def register():
    data = request.get_json()

    if len(data['password']) < 8:
        return jsonify({'error': 'Le mot de passe doit contenir au moins 8 caractères'}), 400

    existing = db.session.execute(
        db.select(User).filter_by(email=data['email'].lower())
    ).scalar_one_or_none()
    if existing:
        return jsonify({'error': 'Cette adresse email est déjà utilisée'}), 409

    role = data.get('role', 'client')
    if role not in ('client', 'admin'):
        role = 'client'

    user = User(
        email=data['email'].lower(),
        nom=data['nom'],
        role=role
    )
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
    data = request.get_json()
    email = data.get('email', '').lower()
    password = data.get('password', '')

    user = db.session.execute(
        db.select(User).filter_by(email=email)
    ).scalar_one_or_none()
    if not user or not user.check_password(password):
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
