# models.py — Définition des modèles de données (ORM SQLAlchemy)
#
# Ce fichier centralise tous les modèles de la base de données.
# Chaque classe Python correspond à une table SQL.
# SQLAlchemy gère la correspondance objet-relationnel (ORM) :
# on manipule des objets Python sans écrire de SQL manuellement.
#
# Schéma de la base digimarket.db :
#   user ──< order ──< order_item >── product

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Instance globale de SQLAlchemy, partagée entre tous les modèles.
# Elle est liée à l'application Flask dans app.py via db.init_app(app).
db = SQLAlchemy()


class User(db.Model):
    """Représente un utilisateur de la plateforme DigiMarket.

    Un utilisateur peut avoir le rôle 'client' (acheteur) ou 'admin' (gestionnaire).
    Son mot de passe est toujours stocké sous forme de hash (jamais en clair).
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)  # identifiant unique de connexion
    password_hash = db.Column(db.String(256), nullable=False)       # hash bcrypt du mot de passe
    nom = db.Column(db.String(100), nullable=False)                 # nom complet affiché
    role = db.Column(db.String(20), nullable=False, default='client')  # 'client' ou 'admin'
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relation one-to-many : un utilisateur peut passer plusieurs commandes.
    # backref='utilisateur' ajoute un attribut .utilisateur sur chaque Order.
    commandes = db.relationship('Order', backref='utilisateur', lazy=True)

    def set_password(self, password):
        """Hache le mot de passe en clair et le stocke dans password_hash.
        Utilise pbkdf2:sha256 via werkzeug (algorithme sécurisé avec sel aléatoire).
        """
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie qu'un mot de passe en clair correspond au hash stocké.
        Retourne True si le mot de passe est correct, False sinon.
        """
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Sérialise l'utilisateur en dictionnaire JSON-compatible.
        Le password_hash n'est jamais exposé dans la réponse API.
        """
        return {
            'id': self.id,
            'email': self.email,
            'nom': self.nom,
            'role': self.role,
            'date_creation': self.date_creation.isoformat()
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'


class Product(db.Model):
    """Représente un produit disponible à la vente sur DigiMarket."""
    __tablename__ = 'product'

    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)                                # description longue, optionnelle
    categorie = db.Column(db.String(50), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, default=0)               # mis à jour à chaque commande
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    def to_dict(self):
        """Sérialise le produit en dictionnaire JSON-compatible."""
        return {
            'id': self.id,
            'nom': self.nom,
            'description': self.description,
            'categorie': self.categorie,
            'prix': self.prix,
            'quantite_stock': self.quantite_stock
        }

    def __repr__(self):
        return f'<Product {self.nom}>'


class Order(db.Model):
    """Représente une commande passée par un utilisateur.

    Une commande regroupe un ou plusieurs OrderItem (lignes de commande).
    Son statut évolue au fil de la livraison : en_attente → confirmée → expédiée → livrée.
    """
    __tablename__ = 'order'

    id = db.Column(db.Integer, primary_key=True)
    # Clé étrangère vers la table user : chaque commande appartient à un utilisateur.
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_commande = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    adresse_livraison = db.Column(db.String(200), nullable=False)
    # Valeurs possibles : 'en_attente', 'confirmée', 'expédiée', 'livrée', 'annulée'
    statut = db.Column(db.String(20), default='en_attente')

    # Relation one-to-many avec les lignes de commande.
    # cascade='all, delete-orphan' : si la commande est supprimée, ses items le sont aussi.
    items = db.relationship('OrderItem', backref='commande', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        """Sérialise la commande et ses lignes en dictionnaire JSON-compatible."""
        return {
            'id': self.id,
            'utilisateur_id': self.utilisateur_id,
            'date_commande': self.date_commande.isoformat(),
            'adresse_livraison': self.adresse_livraison,
            'statut': self.statut,
            # Chaque item est lui-même sérialisé via OrderItem.to_dict()
            'items': [item.to_dict() for item in self.items]
        }

    def __repr__(self):
        return f'<Order {self.id} ({self.statut})>'


class OrderItem(db.Model):
    """Représente une ligne de commande (un produit dans une commande).

    Stocke le prix unitaire au moment de l'achat, indépendamment
    des variations futures du prix du produit.
    """
    __tablename__ = 'order_item'

    id = db.Column(db.Integer, primary_key=True)
    # Clé étrangère vers la commande parente
    commande_id = db.Column(db.Integer, db.ForeignKey('order.id'), nullable=False)
    # Clé étrangère vers le produit commandé
    produit_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    # Prix figé au moment de la commande (historique des prix)
    prix_unitaire = db.Column(db.Float, nullable=False)

    # Relation many-to-one vers le produit (pour accéder à produit.nom dans to_dict)
    produit = db.relationship('Product', backref='order_items')

    def to_dict(self):
        """Sérialise la ligne de commande en dictionnaire JSON-compatible."""
        return {
            'produit_id': self.produit_id,
            'nom': self.produit.nom,        # nom du produit au moment de la lecture
            'quantite': self.quantite,
            'prix_unitaire': self.prix_unitaire
        }

    def __repr__(self):
        return f'<OrderItem commande={self.commande_id} produit={self.produit_id}>'
