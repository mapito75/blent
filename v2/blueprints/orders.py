# blueprints/orders.py — Blueprint de gestion des commandes
#
# Routes exposées sous /api/commandes :
#   GET    /api/commandes              → liste des commandes (admin : toutes, client : les siennes)
#   GET    /api/commandes/<id>         → détail d'une commande
#   POST   /api/commandes              → créer une commande (clients uniquement)
#   PATCH  /api/commandes/<id>         → modifier le statut (admin uniquement)
#   GET    /api/commandes/<id>/lignes  → lignes d'une commande

from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem, Product
from middlewares import token_required, require_json_fields

orders_bp = Blueprint('orders', __name__, url_prefix='/api/commandes')


@orders_bp.route('', methods=['GET'])
@token_required
def list_commandes():
    """Retourne la liste des commandes.

    - Admin : toutes les commandes de la plateforme.
    - Client : uniquement ses propres commandes.

    Retourne :
        200 + liste des commandes
    """
    if request.current_user_role == 'admin':
        commandes = Order.query.all()
    else:
        commandes = Order.query.filter_by(utilisateur_id=request.current_user_id).all()

    return jsonify([c.to_dict() for c in commandes]), 200


@orders_bp.route('/<int:commande_id>', methods=['GET'])
@token_required
def get_commande(commande_id):
    """Retourne le détail d'une commande spécifique.

    - Admin : peut consulter n'importe quelle commande.
    - Client : ne peut consulter que ses propres commandes.

    Retourne :
        200 + données de la commande
        403 si le client tente d'accéder à la commande d'un autre
        404 si la commande n'existe pas
    """
    commande = db.session.get(Order, commande_id)
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404

    if request.current_user_role != 'admin' and commande.utilisateur_id != request.current_user_id:
        return jsonify({'error': 'Accès non autorisé'}), 403

    return jsonify(commande.to_dict()), 200


@orders_bp.route('', methods=['POST'])
@token_required
@require_json_fields('lignes', 'adresse_livraison')
def create_commande():
    """Crée une nouvelle commande pour le client connecté.

    Corps JSON attendu :
        {
            "adresse_livraison": "12 rue de la Paix, Paris",
            "lignes": [
                {"product_id": 1, "quantite": 2},
                {"product_id": 3, "quantite": 1}
            ]
        }

    Vérifie la disponibilité en stock de chaque produit avant de valider.
    Déduit automatiquement les quantités du stock après validation.

    Retourne :
        201 + données de la commande créée
        400 si les lignes sont vides ou mal formées
        400 si un produit est en rupture de stock
        404 si un produit n'existe pas
    """
    data = request.get_json()
    lignes = data['lignes']

    if not isinstance(lignes, list) or len(lignes) == 0:
        return jsonify({'error': 'La commande doit contenir au moins une ligne'}), 400

    # Vérification de chaque ligne et récupération des produits
    produits_commandes = []
    for ligne in lignes:
        product_id = ligne.get('product_id')
        quantite = ligne.get('quantite')

        if not product_id or not quantite or quantite <= 0:
            return jsonify({'error': 'Chaque ligne doit avoir un product_id et une quantite > 0'}), 400

        produit = db.session.get(Product, product_id)
        if not produit:
            return jsonify({'error': f'Produit {product_id} non trouvé'}), 404

        if produit.quantite_stock < quantite:
            return jsonify({
                'error': f'Stock insuffisant pour "{produit.nom}" '
                         f'(disponible : {produit.quantite_stock}, demandé : {quantite})'
            }), 400

        produits_commandes.append((produit, quantite))

    # Création de la commande
    commande = Order(
        utilisateur_id=request.current_user_id,
        adresse_livraison=data['adresse_livraison'],
        statut='en_attente'
    )
    db.session.add(commande)
    db.session.flush()  # génère commande.id avant de créer les lignes

    # Création des lignes et mise à jour du stock
    for produit, quantite in produits_commandes:
        ligne = OrderItem(
            commande_id=commande.id,
            produit_id=produit.id,
            quantite=quantite,
            prix_unitaire=produit.prix
        )
        db.session.add(ligne)
        produit.quantite_stock -= quantite

    db.session.commit()
    return jsonify(commande.to_dict()), 201


@orders_bp.route('/<int:commande_id>', methods=['PATCH'])
@token_required
def update_statut(commande_id):
    """Modifie le statut d'une commande (admin uniquement).

    Corps JSON attendu :
        {"statut": "validee"}

    Statuts acceptés : en_attente, validee, expediee, annulee.

    Retourne :
        200 + commande mise à jour
        400 si le statut est invalide
        403 si l'utilisateur n'est pas admin
        404 si la commande n'existe pas
    """
    if request.current_user_role != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403

    commande = db.session.get(Order, commande_id)
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404

    data = request.get_json() or {}
    nouveau_statut = data.get('statut')

    if not nouveau_statut or nouveau_statut not in Order.STATUTS:
        return jsonify({
            'error': f'Statut invalide. Valeurs acceptées : {", ".join(Order.STATUTS)}'
        }), 400

    commande.statut = nouveau_statut
    db.session.commit()
    return jsonify(commande.to_dict()), 200


@orders_bp.route('/<int:commande_id>/lignes', methods=['GET'])
@token_required
def get_lignes(commande_id):
    """Retourne les lignes d'une commande spécifique.

    - Admin : peut consulter n'importe quelle commande.
    - Client : ne peut consulter que ses propres commandes.

    Retourne :
        200 + liste des lignes de commande
        403 si le client tente d'accéder à la commande d'un autre
        404 si la commande n'existe pas
    """
    commande = db.session.get(Order, commande_id)
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404

    if request.current_user_role != 'admin' and commande.utilisateur_id != request.current_user_id:
        return jsonify({'error': 'Accès non autorisé'}), 403

    return jsonify([l.to_dict() for l in commande.lignes]), 200
