import os
from flask import Flask
from models import db


def create_app():
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///basic_store.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

    db.init_app(app)

    with app.app_context():
        db.create_all()

    from blueprints.auth import auth_bp
    from blueprints.cart import cart_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(cart_bp)

    return app


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
