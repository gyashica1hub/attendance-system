import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_class='app.config.Config'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please login to access this page.'
    login_manager.login_message_category = 'warning'
    
    # Register blueprints
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.attendance import bp as attendance_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.api import bp as api_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    
    # Create upload folders
    os.makedirs(os.path.join(app.root_path, '..', 'dataset'), exist_ok=True)
    
    # Create tables (first time only - better use flask db upgrade)
    # with app.app_context():
    #     db.create_all()
    
    return app

@login_manager.user_loader
def load_user(user_id):
    from app.models import Teacher
    return Teacher.query.get(int(user_id))