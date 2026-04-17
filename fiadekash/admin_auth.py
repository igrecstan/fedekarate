# admin_auth.py - Version refactorisée
from flask import Blueprint, request, jsonify, session
from functools import wraps
import hashlib
import secrets
from datetime import datetime, timedelta
import logging
import json
import os

logger = logging.getLogger(__name__)

admin_bp = Blueprint('admin', __name__, url_prefix='/api/admin')

# Configuration
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD_HASH = hashlib.sha256("admin123".encode()).hexdigest()
TOKEN_EXPIRY_HOURS = 24

# Stockage des tokens (à remplacer par Redis/BDD en production)
active_tokens = {}

def admin_required(f):
    """Décorateur pour protéger les routes admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Récupérer le token
        token = None
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
        
        # Vérifier aussi dans les paramètres de requête (pour les GET)
        if not token and request.args.get('token'):
            token = request.args.get('token')
        
        # Vérifier le token
        if not token or token not in active_tokens:
            return jsonify({'success': False, 'message': 'Non authentifié'}), 401
        
        # Vérifier l'expiration
        token_data = active_tokens[token]
        created_at = datetime.fromisoformat(token_data['created_at'])
        if datetime.now() - created_at > timedelta(hours=TOKEN_EXPIRY_HOURS):
            del active_tokens[token]
            return jsonify({'success': False, 'message': 'Session expirée'}), 401
        
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/login', methods=['POST'])
def admin_login():
    """Authentification admin"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'Données invalides'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        logger.info(f"Tentative de connexion admin: {username}")
        
        if not username or not password:
            return jsonify({
                'success': False,
                'message': 'Identifiant et mot de passe requis'
            }), 400
        
        # Vérification des identifiants
        password_hash = hashlib.sha256(password.encode()).hexdigest()
        
        if username == ADMIN_USERNAME and password_hash == ADMIN_PASSWORD_HASH:
            token = secrets.token_hex(32)
            active_tokens[token] = {
                'username': username,
                'created_at': datetime.now().isoformat()
            }
            
            logger.info(f"Connexion admin réussie: {username}")
            
            return jsonify({
                'success': True,
                'token': token,
                'expires_in': TOKEN_EXPIRY_HOURS * 3600,
                'message': 'Connexion réussie'
            })
        else:
            logger.warning(f"Tentative de connexion échouée: {username}")
            return jsonify({
                'success': False,
                'message': 'Identifiant ou mot de passe incorrect'
            }), 401
            
    except Exception as e:
        logger.error(f"Erreur lors de la connexion: {str(e)}")
        return jsonify({'success': False, 'message': 'Erreur interne'}), 500

@admin_bp.route('/verify', methods=['GET'])
@admin_required
def verify_admin():
    """Vérifie si l'admin est connecté"""
    return jsonify({'success': True, 'message': 'Session valide'})

@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    """Déconnexion admin"""
    token = None
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
    
    if token and token in active_tokens:
        del active_tokens[token]
    
    return jsonify({'success': True, 'message': 'Déconnecté'})

# ========== STATISTIQUES (endpoints simulés pour le dashboard) ==========

@admin_bp.route('/clubs/count', methods=['GET'])
@admin_required
def get_clubs_count():
    """Récupère le nombre total de clubs"""
    try:
        # Simulation - à remplacer par une vraie requête BDD
        # from app import get_db_connection
        # conn = get_db_connection()
        # cursor = conn.cursor()
        # cursor.execute("SELECT COUNT(*) FROM clubs")
        # count = cursor.fetchone()[0]
        # conn.close()
        
        # Données simulées
        count = 42
        
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Erreur get_clubs_count: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/licencies/count', methods=['GET'])
@admin_required
def get_licencies_count():
    """Récupère le nombre total de licenciés"""
    try:
        # Simulation
        count = 1247
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Erreur get_licencies_count: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/events/count', methods=['GET'])
@admin_required
def get_events_count():
    """Récupère le nombre d'événements à venir"""
    try:
        # Simulation
        count = 8
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Erreur get_events_count: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/messages/unread/count', methods=['GET'])
@admin_required
def get_unread_messages_count():
    """Récupère le nombre de messages non lus"""
    try:
        # Simulation
        count = 3
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Erreur get_unread_messages_count: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@admin_bp.route('/messages', methods=['GET'])
@admin_required
def get_recent_messages():
    """Récupère les messages récents"""
    try:
        # Simulation
        messages = [
            {
                'id': 1,
                'nom': 'Jean Dupont',
                'email': 'jean@example.com',
                'message': 'Bonjour, je souhaiterais plus d\'informations...',
                'date_creation': datetime.now().isoformat(),
                'read': False
            },
            {
                'id': 2,
                'nom': 'Marie Martin',
                'email': 'marie@example.com',
                'message': 'Félicitations pour votre organisation...',
                'date_creation': (datetime.now() - timedelta(days=1)).isoformat(),
                'read': True
            }
        ]
        
        limit = request.args.get('limit', default=10, type=int)
        return jsonify({'success': True, 'messages': messages[:limit]})
    except Exception as e:
        logger.error(f"Erreur get_recent_messages: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500