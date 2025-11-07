from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()
mail = Mail()


def create_app():
    app = Flask(__name__)

    # Core config
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///college_delivery.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mail config (override via environment in production)
    app.config.setdefault('MAIL_SERVER', os.environ.get('MAIL_SERVER', 'localhost'))
    app.config.setdefault('MAIL_PORT', int(os.environ.get('MAIL_PORT', 25)))
    app.config.setdefault('MAIL_USE_TLS', os.environ.get('MAIL_USE_TLS', 'false').lower() == 'true')
    app.config.setdefault('MAIL_USE_SSL', os.environ.get('MAIL_USE_SSL', 'false').lower() == 'true')
    app.config.setdefault('MAIL_USERNAME', os.environ.get('MAIL_USERNAME'))
    app.config.setdefault('MAIL_PASSWORD', os.environ.get('MAIL_PASSWORD'))
    app.config.setdefault('MAIL_DEFAULT_SENDER', os.environ.get('MAIL_DEFAULT_SENDER', 'no-reply@example.com'))

    # Init extensions
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    mail.init_app(app)

    # Register blueprints
    from .routes import bp as main_bp
    app.register_blueprint(main_bp)

    # Create DB tables on first run
    with app.app_context():
        db.create_all()

    return app
