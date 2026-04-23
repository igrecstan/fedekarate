import logging
import datetime
import bcrypt
from flask import Blueprint, jsonify, request, session
from db_utils import get_db_connection, update_activity_statuses
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
    saison_id = request.args.get('saison', type=int)
    logger.info(f"Requête get_clubs_count avec saison_id={saison_id}")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if saison_id:
            # On vérifie dans clubs_saison avec jointure pour être sûr
            cursor.execute("""
                SELECT COUNT(DISTINCT cs.List_club) as count 
                FROM clubs_saison cs
                WHERE cs.List_saison = %s
            """, (saison_id,))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM club")
        result = cursor.fetchone()
        count = result['count'] if result else 0
        logger.info(f"Résultat clubs_count: {count}")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Erreur get_clubs_count: {e}")
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
            SELECT c.*, s.nom_secteur as secteur, COALESCE(g.libelle, c.grade) as grade_name
            FROM club c 
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            LEFT JOIN grade g ON (c.grade REGEXP '^[0-9]+$') AND (c.grade = g.id_grade)
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
    saison_id = request.args.get('saison_id', type=int)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if saison_id:
            # Secteurs ayant des clubs affiliés à cette saison
            query = """
                SELECT DISTINCT s.* FROM secteur s
                JOIN club c ON s.id_secteur = c.List_sect
                JOIN clubs_saison cs ON c.id_club = cs.List_club
                WHERE cs.List_saison = %s
                ORDER BY s.nom_secteur ASC
            """
            cursor.execute(query, (saison_id,))
        else:
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
    saison_id = request.args.get('saison_id', type=int)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        if saison_id:
            # Uniquement les clubs affiliés à cette saison
            query = """
                SELECT c.*, s.nom_secteur as secteur
                FROM club c 
                JOIN clubs_saison cs ON c.id_club = cs.List_club
                LEFT JOIN secteur s ON c.List_sect = s.id_secteur 
                WHERE cs.List_saison = %s
                ORDER BY s.nom_secteur ASC, c.nom_club ASC
            """
            cursor.execute(query, (saison_id,))
        else:
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

@admin_bp.route('/saisons/clubs', methods=['GET'])
def get_saisons_clubs():
    """Saisons ayant des clubs affiliés"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT DISTINCT s.id_saison, s.libelle_saison 
            FROM saison s 
            INNER JOIN clubs_saison cs ON s.id_saison = cs.List_saison 
            ORDER BY s.libelle_saison DESC
        """
        cursor.execute(query)
        saisons = cursor.fetchall()
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/saisons', methods=['GET'])
def get_all_saisons():
    """Toutes les saisons"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY libelle_saison DESC")
        saisons = cursor.fetchall()
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/secteurs/saison/<int:saison_id>', methods=['GET'])
def get_secteurs_saison(saison_id):
    """Secteurs ayant des clubs affiliés pour une saison donnée"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT DISTINCT sect.id_secteur, sect.nom_secteur 
            FROM secteur sect 
            INNER JOIN clubs_saison cs ON sect.id_secteur = cs.List_sect 
            WHERE cs.List_saison = %s 
            ORDER BY sect.nom_secteur ASC
        """
        cursor.execute(query, (saison_id,))
        secteurs = cursor.fetchall()
        return jsonify({'success': True, 'secteurs': secteurs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/clubs-saison', methods=['GET'])
def get_clubs_saison():
    """Liste des clubs pour une saison et optionnellement un secteur"""
    saison_id = request.args.get('saison', type=int)
    secteur_id = request.args.get('secteur', type=int)
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT c.*, s.nom_secteur as secteur, cs.created_At as date_affiliation, COALESCE(g.libelle, c.grade) as grade_name
            FROM clubs_saison cs 
            JOIN club c ON cs.List_club = c.id_club 
            JOIN secteur s ON cs.List_sect = s.id_secteur 
            LEFT JOIN grade g ON (c.grade REGEXP '^[0-9]+$') AND (c.grade = g.id_grade)
            WHERE 1=1
        """
        params = []
        if saison_id:
            query += " AND cs.List_saison = %s"
            params.append(saison_id)
        if secteur_id:
            query += " AND cs.List_sect = %s"
            params.append(secteur_id)
            
        query += " ORDER BY s.nom_secteur ASC, c.nom_club ASC"
        
        cursor.execute(query, params)
        clubs = cursor.fetchall()
        return jsonify({'success': True, 'clubs': clubs})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/grades', methods=['GET'])
def get_grades():
    """Récupère tous les grades pour les athlètes"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_grade, libelle FROM grade ORDER BY id_grade ASC")
        grades = cursor.fetchall()
        return jsonify({'success': True, 'grades': grades})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/grades/club', methods=['GET'])
def get_grades_club():
    """Récupère les grades pour les clubs (id_grade > 14)"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_grade, libelle FROM grade WHERE id_grade > 14 ORDER BY id_grade ASC")
        grades = cursor.fetchall()
        return jsonify({'success': True, 'grades': grades})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/clubs/last-identif', methods=['GET'])
def get_last_club_identif():
    """Récupère le dernier identifiant club pour calcul du suivant"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT identif_club FROM club ORDER BY id_club DESC LIMIT 1")
        result = cursor.fetchone()
        return jsonify({'success': True, 'last_identif': result['identif_club'] if result else None})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/clubs/<int:club_id>', methods=['DELETE'])
def delete_club(club_id):
    """Supprime un club et ses affiliations"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Supprimer d'abord les affiliations
        cursor.execute("DELETE FROM clubs_saison WHERE List_club = %s", (club_id,))
        
        # Supprimer le club
        cursor.execute("DELETE FROM club WHERE id_club = %s", (club_id,))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Club supprimé avec succès'})
    except Exception as e:
        if conn: conn.rollback()
        logger.error(f"Erreur suppression club {club_id}: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/clubs', methods=['POST'])
def create_club():
    """Crée un nouveau club"""
    data = request.get_json(silent=True) or {}
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Colonnes: List_sect, nom_club, identif_club, representant, grade, contact, whatapp, email, Num_declaration, statut, created_At, update_At
        query = """
            INSERT INTO club (List_sect, nom_club, identif_club, representant, grade, contact, whatapp, email, Num_declaration, statut, created_At, update_At)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, 'actif', CURDATE(), NOW())
        """
        params = (
            data.get('List_sect'),
            data.get('nom_club'),
            data.get('identif_club'),
            data.get('representant'),
            data.get('grade'),
            data.get('contact'),
            data.get('whatsapp'),
            data.get('email'),
            data.get('Num_declaration')
        )
        
        cursor.execute(query, params)
        club_id = cursor.lastrowid
        
        # Affilier automatiquement à la saison en cours si disponible
        cursor.execute("SELECT id_saison FROM saison ORDER BY id_saison DESC LIMIT 1")
        saison = cursor.fetchone()
        if saison:
            cursor.execute("""
                INSERT INTO clubs_saison (List_saison, List_club, List_sect, created_At)
                VALUES (%s, %s, %s, CURDATE())
            """, (saison[0], club_id, data.get('List_sect')))
            
        conn.commit()
        return jsonify({'success': True, 'id': club_id})
    except Exception as e:
        if conn: conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/settings', methods=['GET'])
def get_settings():
    """Récupère tous les paramètres de configuration"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM configuration")
        settings = cursor.fetchall()
        return jsonify({'success': True, 'settings': settings})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/settings/<string:key>', methods=['PUT'])
def update_setting(key):
    """Met à jour un paramètre spécifique"""
    data = request.get_json(silent=True) or {}
    value = data.get('value')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE configuration SET valeur_config = %s WHERE cle_config = %s", (value, key))
        conn.commit()
        return jsonify({'success': True, 'message': 'Paramètre mis à jour'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@admin_bp.route('/stats/sectorielles', methods=['GET'])
def get_stats_sectorielles():
    """Statistiques par secteur pour une saison donnée"""
    saison_id = request.args.get('saison_id', type=int)
    if not saison_id:
        return jsonify({'success': False, 'message': 'saison_id requis'}), 400
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer l'année de la saison
        cursor.execute("SELECT libelle_saison FROM saison WHERE id_saison = %s", (saison_id,))
        saison = cursor.fetchone()
        if not saison:
            return jsonify({'success': False, 'message': 'Saison non trouvée'}), 404
            
        annee = saison['libelle_saison']
        
        # Requête complexe pour tout calculer en un coup ou presque
        # On itère sur les secteurs
        query = """
            SELECT 
                s.id_secteur, 
                s.nom_secteur as secteur,
                (SELECT COUNT(*) FROM club c WHERE c.List_sect = s.id_secteur AND YEAR(c.created_At) = %s) as nouveau_club,
                (SELECT COUNT(*) FROM clubs_saison cs WHERE cs.List_sect = s.id_secteur AND cs.List_saison = %s) as total_club,
                (SELECT COUNT(*) FROM athletes a JOIN club c ON a.list_club = c.id_club WHERE c.List_sect = s.id_secteur AND YEAR(a.created_at) = %s) as nouveau_licencie,
                (SELECT COUNT(*) FROM athletes_saison asai JOIN club c ON asai.list_club = c.id_club WHERE c.List_sect = s.id_secteur AND asai.list_saison = %s) as total_licencie,
                (SELECT COUNT(*) FROM athletes_saison asai JOIN club c ON asai.list_club = c.id_club WHERE c.List_sect = s.id_secteur AND asai.list_saison = %s AND asai.list_grade >= 16) as total_ceinture_noire,
                (SELECT COUNT(*) FROM athletes_saison asai JOIN club c ON asai.list_club = c.id_club WHERE c.List_sect = s.id_secteur AND asai.list_saison = %s AND (asai.assure = 1 OR asai.assure = b'1')) as total_assure
            FROM secteur s
            ORDER BY s.nom_secteur ASC
        """
        cursor.execute(query, (annee, saison_id, annee, saison_id, saison_id, saison_id))
        sectoriel = cursor.fetchall()
        
        # Calculer le total global
        totals = {
            'secteur': '📌 Tous secteurs',
            'nouveau_club': sum(row['nouveau_club'] for row in sectoriel),
            'total_club': sum(row['total_club'] for row in sectoriel),
            'nouveau_licencie': sum(row['nouveau_licencie'] for row in sectoriel),
            'total_licencie': sum(row['total_licencie'] for row in sectoriel),
            'total_ceinture_noire': sum(row['total_ceinture_noire'] for row in sectoriel),
            'total_assure': sum(row['total_assure'] for row in sectoriel)
        }
        
        return jsonify({
            'success': True, 
            'sectoriel': sectoriel,
            'totalRow': totals
        })
    except Exception as e:
        logger.error(f"Erreur get_stats_sectorielles: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

