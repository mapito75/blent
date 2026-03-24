import jwt
from functools import wraps
from flask import request, jsonify, current_app


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token manquant'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
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
