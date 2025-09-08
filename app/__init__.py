from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os  # for environment variables

db = SQLAlchemy()
login_manager = LoginManager()

def create_app():
    app = Flask(__name__)

    # Secret key
    app.config['SECRET_KEY'] = 'vans_secret_key'

    # Database configuration
    # Use environment variable first (Postgres on Render), fallback to local SQLite
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'postgresql://logbok_user:q9R5S6Zp9TVeTsoEmAjagHqun0YSWywz@dpg-d2vjp7fdiees738f3gd0-a/logbok',        # <-- Here you can put your Internal URL on Render
        'sqlite:///logbook.db' # fallback for local dev
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # recommended for SQLAlchemy

    db.init_app(app)
    login_manager.init_app(app)

    # Where to redirect if user is not logged in
    login_manager.login_view = "auth.login"

    # Import and register blueprints
    from .routes import main
    from .auth import auth

    app.register_blueprint(main)
    app.register_blueprint(auth)

    return app

# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    from .models import User
    return User.query.get(int(user_id))
