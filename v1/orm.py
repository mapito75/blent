import os

from sqlalchemy import create_engine, Column, Integer, String, Float, Text, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash

# Création d'une connexion à la base de données SQLite
# Le prefix "sqlite:///" indique qu'on utilise SQLite et qu'il s'agit d'un chemin absolu
engine = create_engine('sqlite:///basic_store.db', echo=False)

# Déclaration de la base qui servira à créer les modèles
Base = declarative_base()

# Définition des modèles
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    role = Column(String(10), nullable=False, default='client')
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User(email='{self.email}', role='{self.role}')>"

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    stock = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<Product(id='{self.id}', name='{self.name}', price='{self.price}')>"

# Création des tables dans la base de données
Base.metadata.create_all(engine)

# Création d'une session pour interagir avec la base de données
Session = sessionmaker(bind=engine)
session = Session()

def add_sample_products():
    # Créer quelques produits
    products = [
        Product(id='prod001', name='Azus TUF F15', description='PC Portable Gamer', price=899, stock=10),
        Product(id='prod002', name='UGreen Souris sans fil', description='Souris ergonomique', price=49.99, stock=20),
        Product(id='prod003', name='Logitech Clavier mécanique', description='Clavier pour gaming', price=129, stock=15)
    ]
    
    # Ajouter les produits à la session
    session.add_all(products)
    
    # Commit pour sauvegarder les changements dans la base de données
    session.commit()
    print("Produits ajoutés avec succès!")

def read_products():
    # Récupérer tous les produits
    all_products = session.query(Product).all()
    print("\nTous les produits:")
    for product in all_products:
        print(product)
    
    # Récupérer un produit spécifique
    specific_product = session.query(Product).filter_by(id='prod001').first()
    print("\nProduit spécifique:")
    print(specific_product)
    
    # Requête avec filtre sur le prix
    expensive_products = session.query(Product).filter(Product.price > 100).all()
    print("\nProduits chers (>100€):")
    for product in expensive_products:
        print(product)

def update_product():
    # Récupérer le produit à mettre à jour
    product = session.query(Product).filter_by(id='prod002').first()
    
    if product:
        # Mettre à jour les attributs
        product.price = 39.99
        product.stock = 25
        
        # Commit pour sauvegarder les changements
        session.commit()
        print("\nProduit mis à jour:")
        print(product)
    else:
        print("\nProduit non trouvé!")

def delete_product():
    # Récupérer le produit à supprimer
    product = session.query(Product).filter_by(id='prod003').first()
    
    if product:
        # Supprimer le produit
        session.delete(product)
        
        # Commit pour sauvegarder les changements
        session.commit()
        print("\nProduit supprimé!")
    else:
        print("\nProduit non trouvé!")

add_sample_products()
read_products()
update_product()
delete_product()

print("\nProduits après opérations:")
for product in session.query(Product).all():
    print(product)

session.close()
engine.dispose()