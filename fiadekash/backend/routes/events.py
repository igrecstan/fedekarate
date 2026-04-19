# backend/routes/events.py
from flask import Blueprint, request, jsonify
from models import EventModel
from routes.auth import token_required

events_bp = Blueprint('events', __name__)


@events_bp.route('/api/events/', methods=['GET', 'OPTIONS'])
@token_required
def get_events():
    """Récupère tous les événements"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        events = EventModel.get_all()
        return jsonify({
            'success': True,
            'data': events
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@events_bp.route('/api/events/', methods=['POST'])
@token_required
def create_event():
    """Crée un nouvel événement"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données requises'}), 400
        
        if not data.get('name') or not data.get('date'):
            return jsonify({'success': False, 'message': 'Nom et date requis'}), 400
        
        event_id = EventModel.create(data)
        
        return jsonify({
            'success': True,
            'message': 'Événement créé avec succès',
            'event_id': event_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@events_bp.route('/api/events/<int:event_id>', methods=['PUT'])
@token_required
def update_event(event_id):
    """Met à jour un événement"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données requises'}), 400
        
        success = EventModel.update(event_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Événement mis à jour avec succès'
            })
        else:
            return jsonify({'success': False, 'message': 'Événement non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@events_bp.route('/api/events/<int:event_id>', methods=['DELETE'])
@token_required
def delete_event(event_id):
    """Supprime un événement"""
    try:
        success = EventModel.delete(event_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Événement supprimé avec succès'
            })
        else:
            return jsonify({'success': False, 'message': 'Événement non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500