# backend/routes/auth.py
from flask import Blueprint, request, jsonify
import jwt
from datetime import datetime, timedelta
from config import Config
from functools import wraps

auth_bp = Blueprint('auth', __name__)

def token_required(f):
    """Décorateur pour vérifier le token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token manquant'}), 401
        
        try:
            payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
            request.user = payload
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token invalide'}), 401
        
        return f(*args, **kwargs)
    return decorated


@auth_bp.route('/api/auth/login', methods=['POST', 'OPTIONS'])
def login():
    """Authentification admin"""
    print("📥 Route auth/login appelée")
    
    # Gérer la requête OPTIONS pour CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Données JSON requises'}), 400
        
        username = data.get('username')
        password = data.get('password')
        
        print(f"👤 Tentative de connexion: {username}")
        
        # Vérification simple pour le développement
        if username == 'admin' and password == 'admin123':
            token = jwt.encode(
                {
                    'username': username,
                    'exp': datetime.utcnow() + timedelta(hours=Config.JWT_EXPIRATION_HOURS)
                },
                Config.SECRET_KEY,
                algorithm='HS256'
            )
            print("✅ Login réussi")
            return jsonify({
                'success': True,
                'token': token,
                'user': {'username': username, 'role': 'admin'}
            })
        
        print("❌ Identifiants invalides")
        return jsonify({'success': False, 'message': 'Identifiants invalides'}), 401
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@auth_bp.route('/api/auth/verify', methods=['GET'])
def verify_token():
    """Vérifie la validité du token"""
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    
    if not token:
        return jsonify({'success': False, 'message': 'Token manquant'}), 401
    
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        return jsonify({'success': True, 'user': payload})
    except jwt.ExpiredSignatureError:
        return jsonify({'success': False, 'message': 'Token expiré'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'success': False, 'message': 'Token invalide'}), 401