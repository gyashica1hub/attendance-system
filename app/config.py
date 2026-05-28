import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '..', '.env'))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, '..', 'attendance.db')
    
    # Fix for Render/Railway PostgreSQL URLs
    if SQLALCHEMY_DATABASE_URI and SQLALCHEMY_DATABASE_URI.startswith("postgres://"):
        SQLALCHEMY_DATABASE_URI = SQLALCHEMY_DATABASE_URI.replace("postgres://", "postgresql://", 1)
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Face recognition
    FACE_CONFIDENCE_THRESHOLD = 70
    
    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    
    # Dataset path
    DATASET_PATH = os.environ.get('DATASET_PATH') or os.path.join(basedir, '..', 'dataset')