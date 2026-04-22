import logging
from flask import Blueprint, jsonify, request
from db_utils import get_db_connection
from mysql.connector import Error

licencies_bp = Blueprint('licencies_api', __name__, url_prefix='/api/admin')
logger = logging.getLogger(__name__)

@licencies_bp.route('/licencies/count', methods=['GET'])
def get_licencies_count():
    saison_id = request.args.get('saison', type=int)
    logger.info(f"Requête get_licencies_count avec saison_id={saison_id}")
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if saison_id:
            # Utilisation d'une jointure pour être plus robuste
            cursor.execute("""
                SELECT COUNT(DISTINCT a.id_ath) as count 
                FROM athletes a
                INNER JOIN athletes_saison asai ON a.id_ath = asai.list_ath
                WHERE asai.list_saison = %s
            """, (saison_id,))
        else:
            cursor.execute("SELECT COUNT(*) as count FROM athletes")
        result = cursor.fetchone()
        count = result['count'] if result else 0
        logger.info(f"Résultat licencies_count: {count}")
        return jsonify({'success': True, 'count': count})
    except Exception as e:
        logger.error(f"Erreur get_licencies_count: {e}")
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
            SELECT a.*, a.id_ath as id_licencie, a.num_ath as num_licence, 
                   a.tel_ath as contact,
                   c.nom_club, c.id_club as id_club, c.List_sect as secteur,
                   c.identif_club as identif_club,
                   s.nom_secteur as nom_secteur, g.libelle as grade,
                   asai.list_saison as id_saison, asai.assure as assure
            FROM athletes a
            LEFT JOIN club c ON a.list_club = c.id_club
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            LEFT JOIN grade g ON a.list_grade = g.id_grade
            LEFT JOIN athletes_saison asai ON a.id_ath = asai.list_ath
            ORDER BY a.nom_prenoms ASC
        """
        cursor.execute(query)
        licencies = cursor.fetchall()
        # Ajouter un statut par défaut si manquant
        for l in licencies:
            if 'statut' not in l or l['statut'] is None:
                l['statut'] = 'actif'
        return jsonify({'success': True, 'licencies': licencies})
    except Exception as e:
        logger.error(f"Erreur get_all_licencies: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@licencies_bp.route('/licencies/<int:id>', methods=['GET'])
def get_licencie(id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT a.num_ath as num_licence, a.nom_prenoms, a.genre, a.date_nais as date_naissance, 
                   a.lieu_nais, a.tel_ath as contact, a.mail_ath as email, a.prof_ath, 
                   a.person_prevenir, a.tel_person, a.passeport_etabli, a.statut,
                   a.list_club as id_club, a.list_grade as id_grade,
                   c.nom_club, s.id_secteur, s.nom_secteur, g.libelle as grade_libelle
            FROM athletes AS a 
            INNER JOIN club AS c ON a.list_club = c.id_club 
            INNER JOIN secteur AS s ON c.List_sect = s.id_secteur 
            INNER JOIN grade AS g ON a.list_grade = g.id_grade 
            WHERE a.id_ath = %s
        """
        cursor.execute(query, (id,))
        licencie = cursor.fetchone()
        if licencie:
            # Conversion des dates pour JSON
            if licencie.get('date_naissance'):
                licencie['date_naissance'] = licencie['date_naissance'].isoformat()
            return jsonify({'success': True, 'licencie': licencie})
        return jsonify({'success': False, 'message': 'Licencié non trouvé'}), 404
    except Exception as e:
        logger.error(f"Erreur get_licencie: {e}")
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

@licencies_bp.route('/licencies/<int:id>', methods=['PUT'])
def update_licencie(id):
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 1. Mettre à jour la table athletes
        update_query = """
            UPDATE athletes 
            SET nom_prenoms = %s, tel_ath = %s, mail_ath = %s, 
                date_nais = %s, list_club = %s, list_grade = %s, statut = %s
            WHERE id_ath = %s
        """
        full_name = data.get('nom_prenoms', '').strip()
        cursor.execute(update_query, (
            full_name,
            data.get('contact'),
            data.get('email'),
            data.get('date_naissance') or None,
            data.get('id_club'),
            data.get('list_grade'),
            data.get('statut', 'actif'),
            id
        ))
        
        # 2. Mettre à jour ou insérer dans athletes_saison
        if data.get('id_saison'):
            cursor.execute("SELECT id_athsaison FROM athletes_saison WHERE list_ath = %s AND list_saison = %s", (id, data['id_saison']))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE athletes_saison 
                    SET list_club = %s, list_grade = %s, assure = %s
                    WHERE list_ath = %s AND list_saison = %s
                """, (data['id_club'], data['list_grade'], data.get('assure', 0), id, data['id_saison']))
            else:
                cursor.execute("""
                    INSERT INTO athletes_saison (list_ath, list_saison, list_club, list_grade, assure)
                    VALUES (%s, %s, %s, %s, %s)
                """, (id, data['id_saison'], data['id_club'], data['list_grade'], data.get('assure', 0)))
        
        conn.commit()
        return jsonify({'success': True, 'message': 'Licencié mis à jour'})
    except Exception as e:
        logger.error(f"Erreur update_licencie: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@licencies_bp.route('/grades', methods=['GET'])
def get_grades():
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
