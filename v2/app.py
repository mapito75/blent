# app.py — Point d'entrée de l'application Flask
#
# Utilise le pattern "Application Factory" : create_app() instancie et configure Flask,
# ce qui facilite les tests et évite les imports circulaires.

import os
from flask import Flask
from models import db


def create_app():
    """Crée et configure l'application Flask.

    1. Configure la base SQLite et la clé secrète JWT
    2. Initialise SQLAlchemy
    3. Crée les tables manquantes
    4. Enregistre les blueprints

    Returns:
        Flask: l'instance configurée
    """
    app = Flask(__name__)

    # Flask place le fichier dans instance/ par défaut avec sqlite:/// (chemin relatif)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///digimarket.db'
    app.json.ensure_ascii = False  # Retourne les accents en UTF-8 plutôt qu'en \uXXXX
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'ceciestunesecretkey')

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from blueprints.auth import auth_bp
    from blueprints.products import products_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
