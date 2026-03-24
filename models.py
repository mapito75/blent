from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

# Initialisation de l'extension SQLAlchemy
db = SQLAlchemy()

# Définition des modèles
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    role = db.Column(db.String(10), nullable=False, default='client')  # 'client' ou 'admin'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'role': self.role,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<User {self.email} ({self.role})>'

class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.String(10), primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, default=0)
    
    def __repr__(self):
        return f'<Product {self.name}>'

class Cart(db.Model):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relation avec les éléments du panier
    items = db.relationship('CartItem', backref='cart', lazy=True, cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Cart {self.id}>'

class CartItem(db.Model):
    __tablename__ = 'cart_items'
    
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'), nullable=False)
    product_id = db.Column(db.String(10), db.ForeignKey('products.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    
    # Relation avec le produit
    product = db.relationship('Product', backref='cart_items')
    
    def __repr__(self):
        return f'<CartItem {self.id}, Product: {self.product_id}, Qty: {self.quantity}>'