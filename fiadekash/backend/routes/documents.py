# backend/routes/documents.py
from flask import Blueprint, request, jsonify
from models import DocumentModel
from routes.auth import token_required

documents_bp = Blueprint('documents', __name__)


@documents_bp.route('/api/documents/', methods=['GET', 'OPTIONS'])
@token_required
def get_documents():
    """Récupère tous les documents"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        documents = DocumentModel.get_all()
        return jsonify({
            'success': True,
            'data': documents
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@documents_bp.route('/api/documents/', methods=['POST'])
@token_required
def create_document():
    """Crée un nouveau document"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données requises'}), 400
        
        if not data.get('title') or not data.get('url'):
            return jsonify({'success': False, 'message': 'Titre et URL requis'}), 400
        
        doc_id = DocumentModel.create(data)
        
        return jsonify({
            'success': True,
            'message': 'Document créé avec succès',
            'document_id': doc_id
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@documents_bp.route('/api/documents/<int:doc_id>', methods=['PUT'])
@token_required
def update_document(doc_id):
    """Met à jour un document"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'message': 'Données requises'}), 400
        
        success = DocumentModel.update(doc_id, data)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document mis à jour avec succès'
            })
        else:
            return jsonify({'success': False, 'message': 'Document non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


@documents_bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
@token_required
def delete_document(doc_id):
    """Supprime un document"""
    try:
        success = DocumentModel.delete(doc_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Document supprimé avec succès'
            })
        else:
            return jsonify({'success': False, 'message': 'Document non trouvé'}), 404
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500