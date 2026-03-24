# middlewares.py — Décorateurs réutilisables pour les routes Flask
#
# require_json_fields : vérifie la présence de champs obligatoires dans le corps JSON
# token_required      : vérifie et décode le token JWT depuis l'en-tête Authorization

import jwt
from functools import wraps
from flask import request, jsonify, current_app


def require_json_fields(*fields):
    """Vérifie que le corps JSON contient les champs requis.

    Retourne 400 si le corps n'est pas du JSON valide ou si un champ est absent/null/vide.
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json()
            if not data:
                return jsonify({'error': 'Corps de requête JSON requis'}), 400
            missing = [
                field for field in fields
                if field not in data or data[field] is None or data[field] == ''
            ]
            if missing:
                return jsonify({'error': f'Champs manquants : {", ".join(missing)}'}), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


def token_required(f):
    """Protège une route en exigeant un token JWT valide.

    Lit le token dans l'en-tête Authorization (format "Bearer <token>").
    Injecte dans la requête :
    - request.current_user_id   : id de l'utilisateur connecté
    - request.current_user_role : rôle ('client' ou 'admin')

    Retourne 401 si le token est absent, expiré ou invalide.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token manquant'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            request.current_user_id = payload['user_id']
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Token invalide'}), 401
        return f(*args, **kwargs)
    return decorated
