# middlewares.py — Décorateurs réutilisables pour les routes Flask
#
# Un décorateur est une fonction qui enveloppe une autre fonction pour lui ajouter
# un comportement avant ou après son exécution, sans modifier son code.
# Ici, les décorateurs interceptent les requêtes HTTP pour valider les données
# et vérifier l'authentification avant d'appeler la fonction de la route.
#
# Exemple d'utilisation :
#   @token_required
#   @require_json_fields('email', 'password')
#   def ma_route():
#       ...

import jwt
from functools import wraps
from flask import request, jsonify, current_app


def require_json_fields(*fields):
    """Décorateur-fabrique : vérifie que le corps JSON contient les champs requis.

    Retourne une erreur 400 si :
    - le corps de la requête n'est pas du JSON valide
    - un des champs listés est absent, null, ou est une chaîne vide

    Note : une liste vide [] est considérée comme présente (pas une chaîne vide),
    ce qui permet de différencier "champ absent" de "liste vide" (ex: items=[]).

    Args:
        *fields: noms des champs obligatoires à vérifier dans le JSON

    Exemple :
        @require_json_fields('email', 'password')
        def login(): ...
    """
    def decorator(f):
        @wraps(f)  # préserve le nom et la docstring de la fonction décorée
        def decorated(*args, **kwargs):
            data = request.get_json()
            # Vérifie que le Content-Type est bien application/json et que le corps est parseable
            if not data:
                return jsonify({'error': 'Corps de requête JSON requis'}), 400
            # Liste des champs absents, null ou vides (chaîne vide uniquement, pas liste vide)
            missing = [field for field in fields if field not in data or data[field] is None or data[field] == '']
            if missing:
                return jsonify({'error': f'Champs manquants : {", ".join(missing)}'}), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


def validate_enum(field, allowed_values):
    """Décorateur-fabrique : vérifie que la valeur d'un champ fait partie d'une liste autorisée.

    Retourne une erreur 400 si le champ est présent mais contient une valeur non autorisée.
    Si le champ est absent, ce décorateur ne fait rien (utiliser require_json_fields en complément).

    Args:
        field (str): nom du champ à valider
        allowed_values (tuple|list): valeurs autorisées

    Exemple :
        STATUTS = ('en_attente', 'confirmée', 'livrée')

        @require_json_fields('statut')
        @validate_enum('statut', STATUTS)
        def update_statut(): ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            data = request.get_json() or {}
            value = data.get(field)
            # On ne valide que si le champ est présent (require_json_fields gère l'absence)
            if value is not None and value not in allowed_values:
                return jsonify({
                    'error': f'Valeur invalide pour "{field}". Valeurs acceptées : {", ".join(allowed_values)}'
                }), 400
            return f(*args, **kwargs)
        return decorated
    return decorator


def token_required(f):
    """Décorateur : protège une route en exigeant un token JWT valide.

    Lit le token dans l'en-tête Authorization (format "Bearer <token>").
    Si le token est valide, injecte l'identité de l'utilisateur dans la requête :
    - request.current_user_id  : id de l'utilisateur connecté
    - request.current_user_role: rôle ('client' ou 'admin')

    Retourne :
    - 401 si le token est absent, expiré ou invalide
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        # Le format attendu est "Bearer <token>" (avec un espace)
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Token manquant'}), 401
        token = auth_header.split(' ', 1)[1]
        try:
            # Décode et vérifie la signature du token avec la clé secrète de l'app
            payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
            # Stocke les infos utilisateur dans l'objet request (accessible dans la route)
            request.current_user_id = payload['user_id']
            request.current_user_role = payload['role']
        except jwt.ExpiredSignatureError:
            # Le token a dépassé sa date d'expiration (champ 'exp' du payload)
            return jsonify({'error': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            # La signature ne correspond pas ou le token est malformé
            return jsonify({'error': 'Token invalide'}), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """Décorateur : protège une route en exigeant un token JWT valide ET le rôle 'admin'.

    Combine token_required (authentification) et la vérification du rôle (autorisation).
    Retourne 403 si l'utilisateur est authentifié mais n'est pas admin.
    """
    @wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if request.current_user_role != 'admin':
            return jsonify({'error': 'Accès réservé aux administrateurs'}), 403
        return f(*args, **kwargs)
    return decorated
