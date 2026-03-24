from flask import Blueprint, request, jsonify
from models import db, Cart, CartItem, Product
from middlewares import token_required

cart_bp = Blueprint('cart', __name__, url_prefix='/api/cart')


@cart_bp.route('', methods=['GET'])
@token_required
def list_cart():
    cart = Cart.query.first()
    if not cart:
        return jsonify([]), 200

    items = [
        {
            'id': item.product_id,
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity
        }
        for item in cart.items
    ]
    return jsonify(items), 200


@cart_bp.route('', methods=['POST'])
@token_required
def add_to_cart():
    data = request.get_json()
    if not data or 'id' not in data or 'quantity' not in data:
        return jsonify({'error': 'Champs manquants (id, quantity)'}), 400

    product = db.session.get(Product, data['id'])
    if not product:
        return jsonify({'error': 'Produit non trouvé'}), 404

    cart = Cart.query.first()
    if not cart:
        cart = Cart()
        db.session.add(cart)
        db.session.commit()

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=data['id']).first()
    if cart_item:
        cart_item.quantity += int(data['quantity'])
    else:
        cart_item = CartItem(
            cart_id=cart.id,
            product_id=data['id'],
            quantity=int(data['quantity'])
        )
        db.session.add(cart_item)

    db.session.commit()
    return jsonify({}), 201


@cart_bp.route('/<product_id>', methods=['PATCH'])
@token_required
def update_cart_item(product_id):
    data = request.get_json()
    if not data or 'quantity' not in data:
        return jsonify({'error': 'Champ manquant (quantity)'}), 400

    cart = Cart.query.first()
    if not cart:
        return jsonify({'error': 'Panier non trouvé'}), 404

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if not cart_item:
        return jsonify({'error': 'Produit non trouvé dans le panier'}), 404

    cart_item.quantity = int(data['quantity'])
    db.session.commit()
    return jsonify({}), 200


@cart_bp.route('/<product_id>', methods=['DELETE'])
@token_required
def remove_from_cart(product_id):
    cart = Cart.query.first()
    if not cart:
        return jsonify({'error': 'Panier non trouvé'}), 404

    cart_item = CartItem.query.filter_by(cart_id=cart.id, product_id=product_id).first()
    if not cart_item:
        return jsonify({'error': 'Produit non trouvé dans le panier'}), 404

    db.session.delete(cart_item)
    db.session.commit()
    return jsonify({}), 200
