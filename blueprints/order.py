from flask import Blueprint, request, jsonify
from models import db, Order, OrderItem, Product
from middlewares import token_required, require_json_fields, validate_enum

order_bp = Blueprint('order', __name__, url_prefix='/api/orders')


@order_bp.route('', methods=['GET'])
@token_required
def list_orders():
    commandes = Order.query.filter_by(utilisateur_id=request.current_user_id).all()
    return jsonify([c.to_dict() for c in commandes]), 200


@order_bp.route('/<int:order_id>', methods=['GET'])
@token_required
def get_order(order_id):
    commande = Order.query.filter_by(id=order_id, utilisateur_id=request.current_user_id).first()
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404
    return jsonify(commande.to_dict()), 200


@order_bp.route('', methods=['POST'])
@token_required
@require_json_fields('adresse_livraison', 'items')
def create_order():
    data = request.get_json()

    if not data['items']:
        return jsonify({'error': 'La commande doit contenir au moins un produit'}), 400

    commande = Order(
        utilisateur_id=request.current_user_id,
        adresse_livraison=data['adresse_livraison']
    )
    db.session.add(commande)
    db.session.flush()

    for item in data['items']:
        if 'produit_id' not in item or 'quantite' not in item:
            db.session.rollback()
            return jsonify({'error': 'Chaque item doit avoir produit_id et quantite'}), 400

        produit = db.session.get(Product, item['produit_id'])
        if not produit:
            db.session.rollback()
            return jsonify({'error': f'Produit {item["produit_id"]} non trouvé'}), 404

        if produit.quantite_stock < item['quantite']:
            db.session.rollback()
            return jsonify({'error': f'Stock insuffisant pour {produit.nom}'}), 400

        order_item = OrderItem(
            commande_id=commande.id,
            produit_id=produit.id,
            quantite=item['quantite'],
            prix_unitaire=produit.prix
        )
        produit.quantite_stock -= item['quantite']
        db.session.add(order_item)

    db.session.commit()
    return jsonify(commande.to_dict()), 201


STATUTS_VALIDES = ('en_attente', 'confirmée', 'expédiée', 'livrée', 'annulée')


@order_bp.route('/<int:order_id>/statut', methods=['PATCH'])
@token_required
@require_json_fields('statut')
@validate_enum('statut', STATUTS_VALIDES)
def update_statut(order_id):
    if request.current_user_role != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403

    data = request.get_json()
    commande = db.session.get(Order, order_id)
    if not commande:
        return jsonify({'error': 'Commande non trouvée'}), 404

    commande.statut = data['statut']
    db.session.commit()
    return jsonify(commande.to_dict()), 200
