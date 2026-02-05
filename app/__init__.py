from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from getpass import getpass

from config import Config

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'
csrf = CSRFProtect()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from app.routes.auth import auth_bp
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')

    with app.app_context():
        db.create_all()

    @app.cli.command('create-admin')
    def create_admin():
        """Create an admin user."""
        from app.models import User

        username = input('Admin username: ')
        email = input('Admin email: ')
        password = getpass('Admin password: ')
        confirm_password = getpass('Confirm password: ')

        if password != confirm_password:
            print('Passwords do not match!')
            return

        existing_user = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing_user:
            print('User with that username or email already exists!')
            return

        admin = User(username=username, email=email, is_admin=True)
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()

        print(f'Admin user "{username}" created successfully!')

    @app.cli.command('seed-articles')
    def seed_articles():
        """Seed the database with sample articles."""
        import json
        import os
        from app.models import Article

        # Check if articles already exist
        if Article.query.count() > 0:
            print(f'Database already has {Article.query.count()} articles. Skipping seed.')
            return

        # Load sample articles
        sample_path = os.path.join(os.path.dirname(os.path.dirname(__file__)),
                                   'sample_data', 'sample_articles.json')

        if not os.path.exists(sample_path):
            print(f'Sample file not found at {sample_path}')
            return

        with open(sample_path, 'r') as f:
            articles = json.load(f)

        for a in articles:
            article = Article(
                title=a['title'],
                source=a.get('source', ''),
                url=a.get('url', ''),
                full_text=a['full_text']
            )
            db.session.add(article)

        db.session.commit()
        print(f'Successfully added {len(articles)} articles!')

    return app
