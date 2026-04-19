import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Base de données
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_USER = os.getenv('DB_USER', 'root')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_NAME = os.getenv('DB_NAME', 'fiadekash')
    
    # JWT
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre-secret-key-tres-securisee-2025')
    JWT_EXPIRATION_HOURS = 24
    
    # Upload
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max
    
    # CORS
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000']