# backend/routes/messages.py
from flask import Blueprint, request, jsonify
from routes.auth import token_required

messages_bp = Blueprint('messages', __name__)

# Données temporaires pour les messages
_messages = [
    {'id': 1, 'name': 'Abidjan Karaté Club', 'email': 'contact@akc.ci', 'date': '2025-04-10', 'message': 'Bonjour, nous souhaitons obtenir des informations sur la procédure d\'adhésion à la fédération...', 'read': False},
    {'id': 2, 'name': 'Marie Touré', 'email': 'm.toure@gmail.com', 'date': '2025-04-09', 'message': 'Nous aimerions organiser un stage interclubs à Bouaké en juin. Est-ce possible ?', 'read': False},
    {'id': 3, 'name': 'Paul Bamba', 'email': 'p.bamba@yahoo.fr', 'date': '2025-04-08', 'message': 'Demande de renouvellement de licence pour notre club de Yamoussoukro.', 'read': False},
]
_next_id = 4


@messages_bp.route('/api/messages/', methods=['GET', 'OPTIONS'])
@token_required
def get_messages():
    """Récupère tous les messages"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        return jsonify({
            'success': True,
            'data': _messages
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/api/messages/<int:msg_id>', methods=['PUT'])
@token_required
def update_message(msg_id):
    """Met à jour un message (marquer comme lu)"""
    try:
        data = request.get_json()
        
        for msg in _messages:
            if msg['id'] == msg_id:
                msg.update(data)
                return jsonify({
                    'success': True,
                    'message': 'Message mis à jour avec succès'
                })
        
        return jsonify({'success': False, 'message': 'Message non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@messages_bp.route('/api/messages/<int:msg_id>', methods=['DELETE'])
@token_required
def delete_message(msg_id):
    """Supprime un message"""
    try:
        global _messages
        _messages = [msg for msg in _messages if msg['id'] != msg_id]
        return jsonify({
            'success': True,
            'message': 'Message supprimé avec succès'
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500