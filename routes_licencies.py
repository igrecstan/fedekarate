import logging
from flask import Blueprint, jsonify, request
from db_utils import get_db_connection
from mysql.connector import Error

licencies_bp = Blueprint('licencies_api', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

@licencies_bp.route('/licencies/count', methods=['GET'])
def get_licencies_count():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM athletes")
        result = cursor.fetchone()
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@licencies_bp.route('/licencies/all', methods=['GET'])
def get_all_licencies():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        # Note: La table peut s'appeler 'athletes' ou 'licencies' selon la BDD
        # D'après licencies.js, il attend des colonnes comme nom_prenoms, grade, statut, etc.
        query = """
            SELECT a.*, c.nom_club, s.nom_secteur as secteur
            FROM athletes a
            LEFT JOIN club c ON a.id_club = c.id_club
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            ORDER BY a.created_At DESC
        """
        cursor.execute(query)
        licencies = cursor.fetchall()
        return jsonify({'success': True, 'licencies': licencies})
    except Exception as e:
        logger.error(f"Erreur get_all_licencies: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@licencies_bp.route('/licencies/<int:id>', methods=['DELETE'])
def delete_licencie(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM athletes WHERE id_ath = %s", (id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Licencié supprimé'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@licencies_bp.route('/saisons/licencies', methods=['GET'])
def get_saisons_licencies():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM saison ORDER BY id_saison DESC")
        saisons = cursor.fetchall()
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
