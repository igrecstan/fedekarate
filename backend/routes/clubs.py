# backend/routes/clubs.py
from flask import Blueprint, request, jsonify
from models import ClubModel
from functools import wraps
import jwt
from config import Config

clubs_bp = Blueprint('clubs', __name__)

def token_required(f):
    """Décorateur pour vérifier le token JWT"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        if not token:
            return jsonify({'success': False, 'message': 'Token manquant'}), 401
        
        try:
            jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token expiré'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Token invalide'}), 401
        
        return f(*args, **kwargs)
    return decorated


@clubs_bp.route('/api/clubs/', methods=['GET', 'OPTIONS'])
@token_required
def get_clubs():
    """Récupère tous les clubs"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        
        offset = (page - 1) * per_page
        
        clubs = ClubModel.get_all(limit=per_page, offset=offset)
        total = ClubModel.count()
        
        return jsonify({
            'success': True,
            'data': clubs,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': (total + per_page - 1) // per_page
            }
        })
    except Exception as e:
        print(f"❌ Erreur get_clubs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@clubs_bp.route('/api/clubs/', methods=['POST'])
@token_required
def create_club():
    """Crée un nouveau club"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données requises'}), 400
        
        # Validation basique
        if not data.get('nom du club') or not data.get('nom et prenoms'):
            return jsonify({'success': False, 'message': 'Nom du club et responsable requis'}), 400
        
        club_id = ClubModel.create(data)
        
        return jsonify({
            'success': True,
            'message': 'Club créé avec succès',
            'club_id': club_id
        })
    except Exception as e:
        print(f"❌ Erreur create_club: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@clubs_bp.route('/api/clubs/<int:club_id>', methods=['GET'])
@token_required
def get_club(club_id):
    """Récupère un club spécifique"""
    try:
        club = ClubModel.get_by_id(club_id)
        
        if not club:
            return jsonify({'success': False, 'message': 'Club non trouvé'}), 404
        
        return jsonify({
            'success': True,
            'data': club
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@clubs_bp.route('/api/clubs/<int:club_id>', methods=['PUT'])
@token_required
def update_club(club_id):
    """Met à jour un club"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données requises'}), 400
        
        success = ClubModel.update(club_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Club mis à jour avec succès'
            })
        else:
            return jsonify({'success': False, 'message': 'Club non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@clubs_bp.route('/api/clubs/<int:club_id>', methods=['DELETE'])
@token_required
def delete_club(club_id):
    """Supprime un club"""
    try:
        success = ClubModel.delete(club_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Club supprimé avec succès'
            })
        else:
            return jsonify({'success': False, 'message': 'Club non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500