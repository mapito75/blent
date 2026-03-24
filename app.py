# app.py — Point d'entrée de l'application Flask
#
# Ce fichier utilise le pattern "Application Factory" : au lieu de créer
# l'application Flask directement au niveau du module (ce qui rendrait les
# tests difficiles et créerait des problèmes d'importation circulaire),
# on encapsule la création dans une fonction create_app().
# Cela permet d'instancier plusieurs configurations différentes (dev, test, prod).

import os
from flask import Flask
from models import db


def create_app():
    """Crée et configure l'application Flask.

    Étapes :
    1. Instancie Flask
    2. Configure la base de données SQLite et la clé secrète JWT
    3. Initialise SQLAlchemy avec l'app
    4. Crée les tables si elles n'existent pas
    5. Enregistre les blueprints (auth, order)

    Returns:
        app (Flask): l'instance de l'application configurée
    """
    app = Flask(__name__)

    # URI de connexion à la base de données SQLite.
    # Le fichier digimarket.db sera créé dans le dossier instance/ automatiquement par Flask.
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digimarket.db'

    # Désactive le suivi des modifications des objets SQLAlchemy (améliore les performances).
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Clé secrète utilisée pour signer les tokens JWT.
    # En production, cette valeur doit être définie via la variable d'environnement SECRET_KEY
    # et ne jamais être codée en dur dans le code source.
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ceciestunesecretkey')

    # Lie SQLAlchemy à l'instance Flask (injecte la config de l'app dans l'extension).
    db.init_app(app)

    # Le contexte applicatif est nécessaire pour toute opération sur la base de données
    # en dehors d'une requête HTTP. db.create_all() crée les tables définies dans models.py
    # si elles n'existent pas encore.
    with app.app_context():
        db.create_all()

    # Import différé des blueprints pour éviter les imports circulaires
    # (les blueprints importent eux-mêmes `db` depuis models.py).
    from blueprints.auth import auth_bp
    from blueprints.order import order_bp

    # Enregistrement des blueprints : chaque blueprint apporte ses propres routes
    # avec son préfixe d'URL défini dans le fichier blueprint correspondant.
    app.register_blueprint(auth_bp)   # routes /api/auth/*
    app.register_blueprint(order_bp)  # routes /api/orders/*

    return app


# Ce bloc n'est exécuté que si le fichier est lancé directement (python app.py),
# pas lorsqu'il est importé comme module (ex: par les tests).
if __name__ == '__main__':
    app = create_app()
    # debug=True active le rechargement automatique et les messages d'erreur détaillés.
    # Ne jamais utiliser debug=True en production.
    app.run(debug=True)
