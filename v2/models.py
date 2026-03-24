# models.py — Définition des modèles de données (ORM SQLAlchemy)
#
# Ce fichier centralise tous les modèles de la base de données.
# Chaque classe Python correspond à une table SQL existante dans digimarket.db.

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Instance globale de SQLAlchemy, partagée entre tous les modèles.
# Liée à l'application Flask dans app.py via db.init_app(app).
db = SQLAlchemy()


class User(db.Model):
    """Représente un utilisateur de la plateforme DigiMarket.

    Rôles possibles : 'client' (acheteur) ou 'admin' (gestionnaire).
    Le mot de passe est toujours stocké sous forme de hash, jamais en clair.
    """
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='client')
    date_creation = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        """Hache le mot de passe et le stocke dans password_hash."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Vérifie qu'un mot de passe en clair correspond au hash stocké."""
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        """Sérialise l'utilisateur en dictionnaire JSON-compatible (sans password_hash)."""
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
    description = db.Column(db.Text)
    categorie = db.Column(db.String(50), nullable=False)
    prix = db.Column(db.Float, nullable=False)
    quantite_stock = db.Column(db.Integer, default=0)
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
