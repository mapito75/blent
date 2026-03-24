import jwt
from functools import wraps
from flask import request, jsonify, current_app


def require_json_fields(*fields):
    """Vérifie que le corps JSON contient les champs requis."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Corps de requête JSON requis'}), 400
            missing = [field for field in fields if field not in data or data[field] is None or data[field] == '']
            if missing:
                return jsonify({'error': f'Champs manquants : {", ".join(missing)}'}), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_enum(field, allowed_values):
    """Vérifie que la valeur d'un champ fait partie des valeurs autorisées."""
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json() or {}
            value = data.get(field)
            if value is not None and value not in allowed_values:
                return jsonify({
                    'error': f'Valeur invalide pour "{field}". Valeurs acceptées : {", ".join(allowed_values)}'
                }), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


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
