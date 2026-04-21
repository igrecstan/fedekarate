import logging
import datetime
import bcrypt
from flask import Blueprint, jsonify, request, session
from db_utils import get_db_connection
from mysql.connector import Error

admin_bp = Blueprint('admin_api', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

@admin_bp.route('/login', methods=['POST', 'OPTIONS'])
def admin_login():
    """Authentification admin"""
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json(silent=True) or {}
    login = data.get('login', '').strip()
    password = data.get('password', '')
    
    if not login or not password:
        return jsonify({'success': False, 'message': 'Identifiant et mot de passe requis'}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, login, password_hash, nom, prenom, email, role_id, actif
            FROM users 
            WHERE login = %s
        """, (login,))
        user = cursor.fetchone()
        
        if not user or user.get('actif') == 0:
            return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        password_hash = user.get('password_hash', '')
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        except Exception:
            # Fallback for plain text if needed (though not recommended)
            if password != password_hash:
                return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        cursor.execute("UPDATE users SET derniere_cnx = NOW() WHERE id = %s", (user['id'],))
        conn.commit()
        
        session['admin_id'] = user['id']
        session['admin_login'] = user['login']
        session['admin_logged_in'] = True
        
        return jsonify({
            'success': True,
            'token': f"admin_token_{user['id']}_{int(datetime.datetime.now().timestamp())}",
            'user': {
                'id': user['id'],
                'login': user['login'],
                'nom': user.get('nom', ''),
                'prenom': user.get('prenom', ''),
                'email': user.get('email', ''),
                'role': 'Administrateur' # Simplified for now
            }
        })
    except Exception as e:
        logger.error(f"Erreur admin_login: {e}")
        return jsonify({'success': False, 'message': f'Erreur serveur: {str(e)}'}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/verify', methods=['GET', 'POST'])
def admin_verify():
    if session.get('admin_logged_in'):
        return jsonify({'success': True, 'message': 'Session valide'})
    return jsonify({'success': False, 'message': 'Non authentifié'}), 401

@admin_bp.route('/logout', methods=['POST'])
def admin_logout():
    session.clear()
    return jsonify({'success': True, 'message': 'Déconnecté'})

@admin_bp.route('/clubs/count', methods=['GET'])
def get_clubs_count():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM club")
        result = cursor.fetchone()
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/clubs', methods=['GET'])
def get_clubs():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    search = request.args.get('search', '')
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        update_activity_statuses(conn)
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT c.*, s.nom_secteur as secteur 
            FROM club c 
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
        """
        params = []
        if search:
            query += " WHERE c.nom_club LIKE %s OR c.identif_club LIKE %s OR c.representant LIKE %s"
            search_param = f'%{search}%'
            params = [search_param, search_param, search_param]
        
        query += " ORDER BY s.nom_secteur ASC, c.nom_club ASC LIMIT %s OFFSET %s"
        params.extend([limit, offset])
        
        cursor.execute(query, params)
        clubs = cursor.fetchall()
        
        return jsonify({'success': True, 'clubs': clubs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/secteurs', methods=['GET'])
def get_secteurs():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM secteur ORDER BY nom_secteur ASC")
        secteurs = cursor.fetchall()
        return jsonify({'success': True, 'secteurs': secteurs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/clubs/all', methods=['GET'])
def get_all_clubs():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, s.nom_secteur as secteur 
            FROM club c 
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur 
            ORDER BY s.nom_secteur ASC, c.nom_club ASC
        """
        cursor.execute(query)
        clubs = cursor.fetchall()
        return jsonify({'success': True, 'clubs': clubs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
