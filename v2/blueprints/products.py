# blueprints/products.py — Blueprint du catalogue produits
#
# Routes exposées sous /api/produits :
#   GET    /api/produits          → liste tous les produits (public, supporte ?q= pour la recherche)
#   GET    /api/produits/<id>     → détail d'un produit (public)
#   POST   /api/produits          → créer un produit (admin uniquement)
#   PUT    /api/produits/<id>     → modifier un produit (admin uniquement)
#   DELETE /api/produits/<id>     → supprimer un produit (admin uniquement)

from flask import Blueprint, request, jsonify
from models import db, Product
from middlewares import token_required, require_json_fields

products_bp = Blueprint('products', __name__, url_prefix='/api/produits')


@products_bp.route('', methods=['GET'])
def list_products():
    """Retourne la liste de tous les produits.

    Paramètre de requête optionnel :
        ?q=<terme>  → filtre par nom, description ou catégorie (insensible à la casse)

    Retourne :
        200 + liste des produits (peut être vide)
    """
    q = request.args.get('q', '').strip()
    if q:
        # Recherche dans nom, description et catégorie via LIKE (insensible à la casse)
        pattern = f'%{q}%'
        produits = Product.query.filter(
            db.or_(
                Product.nom.ilike(pattern),
                Product.description.ilike(pattern),
                Product.categorie.ilike(pattern)
            )
        ).all()
    else:
        produits = Product.query.all()

    return jsonify([p.to_dict() for p in produits]), 200


@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Retourne le détail d'un produit spécifique.

    Retourne :
        200 + données du produit
        404 si le produit n'existe pas
    """
    produit = db.session.get(Product, product_id)
    if not produit:
        return jsonify({'error': 'Produit non trouvé'}), 404
    return jsonify(produit.to_dict()), 200


@products_bp.route('', methods=['POST'])
@token_required
@require_json_fields('nom', 'categorie', 'prix')
def create_product():
    """Crée un nouveau produit dans le catalogue (admin uniquement).

    Corps JSON attendu :
        {
            "nom": "Clavier mécanique",
            "description": "Clavier gaming RGB",   (optionnel)
            "categorie": "Périphériques",
            "prix": 89.99,
            "quantite_stock": 50                    (optionnel, défaut : 0)
        }

    Retourne :
        201 + données du produit créé
        403 si l'utilisateur n'est pas admin
    """
    if request.current_user_role != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403

    data = request.get_json()

    produit = Product(
        nom=data['nom'],
        description=data.get('description'),
        categorie=data['categorie'],
        prix=data['prix'],
        quantite_stock=data.get('quantite_stock', 0)
    )
    db.session.add(produit)
    db.session.commit()

    return jsonify(produit.to_dict()), 201


@products_bp.route('/<int:product_id>', methods=['PUT'])
@token_required
def update_product(product_id):
    """Modifie un produit existant (admin uniquement).

    Tous les champs sont optionnels : seuls les champs fournis sont mis à jour.

    Corps JSON (au moins un champ) :
        {
            "nom": "Nouveau nom",
            "description": "...",
            "categorie": "...",
            "prix": 99.99,
            "quantite_stock": 30
        }

    Retourne :
        200 + données du produit mis à jour
        403 si l'utilisateur n'est pas admin
        404 si le produit n'existe pas
    """
    if request.current_user_role != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403

    produit = db.session.get(Product, product_id)
    if not produit:
        return jsonify({'error': 'Produit non trouvé'}), 404

    data = request.get_json() or {}

    # Mise à jour partielle : seuls les champs présents dans le JSON sont modifiés
    if 'nom' in data:
        produit.nom = data['nom']
    if 'description' in data:
        produit.description = data['description']
    if 'categorie' in data:
        produit.categorie = data['categorie']
    if 'prix' in data:
        produit.prix = data['prix']
    if 'quantite_stock' in data:
        produit.quantite_stock = data['quantite_stock']

    db.session.commit()
    return jsonify(produit.to_dict()), 200


@products_bp.route('/<int:product_id>', methods=['DELETE'])
@token_required
def delete_product(product_id):
    """Supprime un produit du catalogue (admin uniquement).

    Retourne :
        200 + message de confirmation
        403 si l'utilisateur n'est pas admin
        404 si le produit n'existe pas
    """
    if request.current_user_role != 'admin':
        return jsonify({'error': 'Accès réservé aux administrateurs'}), 403

    produit = db.session.get(Product, product_id)
    if not produit:
        return jsonify({'error': 'Produit non trouvé'}), 404

    db.session.delete(produit)
    db.session.commit()
    return jsonify({'message': f'Produit "{produit.nom}" supprimé'}), 200
