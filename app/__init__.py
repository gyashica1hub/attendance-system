from flask import Flask, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate

db = SQLAlchemy()
login_manager = LoginManager()
migrate = Migrate()

def create_app(config_name='default'):
    app = Flask(__name__)
    
    # Config load karo
    from app.config import config
    app.config.from_object(config[config_name])
    
    # Extensions init
    db.init_app(app)
    login_manager.init_app(app)
    migrate.init_app(app, db)
    
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'
    
    # User loader
    @login_manager.user_loader
    def load_user(user_id):
        from app.models import Teacher
        return Teacher.query.get(int(user_id))
    
    # Blueprints register
    from app.routes.auth import bp as auth_bp
    from app.routes.dashboard import bp as dashboard_bp
    from app.routes.attendance import bp as attendance_bp
    from app.routes.reports import bp as reports_bp
    from app.routes.api import bp as api_bp
    from app.routes.admin import bp as admin_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(attendance_bp, url_prefix='/attendance')
    app.register_blueprint(reports_bp, url_prefix='/reports')
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    
    # Home route
    @app.route('/')
    def home():
        from flask_login import current_user
        if current_user.is_authenticated:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # Upload folders
    import os
    os.makedirs(app.config.get('UPLOAD_FOLDER', 'dataset'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'uploads', 'students'), exist_ok=True)
    os.makedirs(os.path.join(app.root_path, 'static', 'img'), exist_ok=True)
    
    # ✅ Create tables - uncommented!
    with app.app_context():
        db.create_all()
    
    return app