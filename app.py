import os
import jwt
from datetime import datetime, timezone, timedelta
from functools import wraps

from flask import Flask, request, jsonify
from models import db, User

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basic_store.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

db.init_app(app)

with app.app_context():
    db.create_all()


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token manquant'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.current_user_id = payload['user_id']
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user_role != 'admin':
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        return f(*args, **kwargs)
    return decorated


# POST /api/auth/register
@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Corps de requête JSON requis'}), 400

    required_fields = ['email', 'password', 'first_name', 'last_name']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({'error': f'Champs manquants : {", ".join(missing)}'}), 400

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
        first_name=data['first_name'],
        last_name=data['last_name'],
        role=role
    )
    user.set_password(data['password'])
    db.session.add(user)
    db.session.commit()

    return jsonify({
        'message': 'Compte créé avec succès',
        'user': user.to_dict()
    }), 201


# POST /api/auth/login
@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Corps de requête JSON requis'}), 400

    email = data.get('email', '').lower()
    password = data.get('password', '')
    if not email or not password:
        return jsonify({'error': 'Email et mot de passe requis'}), 400

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
    token = jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

    return jsonify({
        'message': 'Connexion réussie',
        'token': token,
        'user': user.to_dict()
    }), 200


if __name__ == '__main__':
    app.run(debug=True)
