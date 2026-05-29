# app/__init__.py
from flask import Flask
from app.routes.auth import auth_bp as auth_bp
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

# ⚠️ Yeh global instances sirf EK BAAR create hone chahiye
db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()


def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Config load karo
    from app.config import config
    app.config.from_object(config[config_name])
    
    # ⚠️ Yeh init_app calls MUST hain
    db.init_app(app)           # <-- Check karo yeh hai!
    login_manager.init_app(app)
    migrate.init_app(app, db)  # <-- Check karo yeh hai!
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # Blueprints register karo
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.attendance import attendance_bp
    from app.routes.reports import reports_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Upload folder create karo
    import os
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'dataset'), exist_ok=True)
    
    # ⚠️ Database tables create karo app context ke andar
    with app.app_context():
        db.create_all()
    
    return app