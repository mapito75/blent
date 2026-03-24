# blueprints/order.py — Blueprint de gestion des commandes
#
# Ce module expose les routes REST pour créer et consulter des commandes.
# Toutes les routes sont protégées par @token_required (authentification JWT obligatoire).
#
# Routes disponibles :
#   GET    /api/orders             → liste des commandes de l'utilisateur connecté
#   GET    /api/orders/<id>        → détail d'une commande
#   POST   /api/orders             → créer une nouvelle commande
#   PATCH  /api/orders/<id>/statut → mettre à jour le statut (admin uniquement)

from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem, Product
from middlewares import token_required, require_json_fields, validate_enum

# Préfixe commun à toutes les routes de ce blueprint
order_bp = Blueprint('order', __name__, url_prefix='/api/orders')

# Valeurs autorisées pour le statut d'une commande (cycle de vie)
STATUTS_VALIDES = ('en_attente', 'confirmée', 'expédiée', 'livrée', 'annulée')


@order_bp.route('', methods=['GET'])
@token_required
def list_orders():
    """Retourne toutes les commandes de l'utilisateur connecté.

    L'utilisateur ne voit que ses propres commandes (filtrage par utilisateur_id).

    Retourne :
        200 + liste des commandes (peut être vide)
    """
    # request.current_user_id est injecté par le décorateur @token_required
    commandes = Order.query.filter_by(utilisateur_id=request.current_user_id).all()
    return jsonify([c.to_dict() for c in commandes]), 200


@order_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    """Retourne le détail d'une commande spécifique.

    La commande doit appartenir à l'utilisateur connecté.

    Args:
        order_id (int): identifiant de la commande (dans l'URL)

    Retourne :
        200 + détail de la commande
        404 si la commande n'existe pas ou n'appartient pas à l'utilisateur
    """
    # Double filtre : id ET utilisateur_id pour éviter qu'un utilisateur
    # accède aux commandes d'un autre en devinant l'id
    commande = Order.query.filter_by(id=order_id, utilisateur_id=request.current_user_id).first()
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404
    return jsonify(commande.to_dict()), 200


@order_bp.route('', methods=['POST'])
@token_required
@require_json_fields('adresse_livraison', 'items')
def create_order():
    """Crée une nouvelle commande pour l'utilisateur connecté.

    Corps JSON attendu :
        {
            "adresse_livraison": "12 rue de la Paix, 75001 Paris",
            "items": [
                {"produit_id": 1, "quantite": 2},
                {"produit_id": 3, "quantite": 1}
            ]
        }

    Comportement :
    - Vérifie que chaque produit existe et a assez de stock
    - Déduit la quantité commandée du stock de chaque produit
    - Fixe le prix unitaire au prix actuel du produit (historique des prix)
    - Utilise une transaction : si un item est invalide, toute la commande est annulée (rollback)

    Retourne :
        201 + commande créée avec ses items
        400 si les items sont vides ou mal formés
        404 si un produit n'existe pas
    """
    data = request.get_json()

    # Une commande sans produit n'a pas de sens
    if not data['items']:
        return jsonify({'error': 'La commande doit contenir au moins un produit'}), 400

    # Crée l'entête de la commande sans encore la valider (flush sans commit)
    commande = Order(
        utilisateur_id=request.current_user_id,
        adresse_livraison=data['adresse_livraison']
    )
    db.session.add(commande)
    # flush() envoie le INSERT à la base pour obtenir l'id auto-incrémenté,
    # sans valider la transaction (permet de l'utiliser dans les OrderItem)
    db.session.flush()

    # Traitement de chaque ligne de commande
    for item in data['items']:
        # Validation de la structure de chaque item
        if 'produit_id' not in item or 'quantite' not in item:
            db.session.rollback()  # annule toute la transaction en cas d'erreur
            return jsonify({'error': 'Chaque item doit avoir produit_id et quantite'}), 400

        # Vérifie que le produit existe
        produit = db.session.get(Product, item['produit_id'])
        if not produit:
            db.session.rollback()
            return jsonify({'error': f'Produit {item["produit_id"]} non trouvé'}), 404

        # Vérifie que le stock est suffisant
        if produit.quantite_stock < item['quantite']:
            db.session.rollback()
            return jsonify({'error': f'Stock insuffisant pour {produit.nom}'}), 400

        # Crée la ligne de commande avec le prix actuel du produit
        order_item = OrderItem(
            commande_id=commande.id,
            produit_id=produit.id,
            quantite=item['quantite'],
            prix_unitaire=produit.prix  # prix figé au moment de la commande
        )
        # Décrémente le stock du produit
        produit.quantite_stock -= item['quantite']
        db.session.add(order_item)

    # Valide toute la transaction en une seule fois (atomique)
    db.session.commit()
    return jsonify(commande.to_dict()), 201


@order_bp.route('/<int:order_id>/statut', methods=['PATCH'])
@token_required
@require_json_fields('statut')
@validate_enum('statut', STATUTS_VALIDES)
def update_statut(order_id):
    """Met à jour le statut d'une commande (réservé aux admins).

    Corps JSON attendu :
        {
            "statut": "confirmée"
        }

    Valeurs autorisées : en_attente, confirmée, expédiée, livrée, annulée

    Args:
        order_id (int): identifiant de la commande (dans l'URL)

    Retourne :
        200 + commande mise à jour
        403 si l'utilisateur n'est pas admin
        404 si la commande n'existe pas
    """
    # Seul un admin peut modifier le statut d'une commande
    if request.current_user_role != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403

    data = request.get_json()

    # Recherche la commande sans restriction d'utilisateur (l'admin voit toutes les commandes)
    commande = db.session.get(Order, order_id)
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404

    commande.statut = data['statut']
    db.session.commit()
    return jsonify(commande.to_dict()), 200
