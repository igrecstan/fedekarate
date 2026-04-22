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
                   a.lieu_nais, a.nation, a.tel_ath as contact, a.mail_ath as email, a.prof_ath, 
                   a.person_prevenir, a.tel_person, a.passeport_etabli, a.statut,
                   a.list_club as id_club, a.list_grade as id_grade,
                   c.nom_club, s.id_secteur, s.nom_secteur, g.libelle as grade_libelle,
                   as_s.assure
            FROM athletes AS a 
            LEFT JOIN club AS c ON a.list_club = c.id_club 
            LEFT JOIN secteur AS s ON c.List_sect = s.id_secteur 
            LEFT JOIN grade AS g ON a.list_grade = g.id_grade 
            LEFT JOIN athletes_saison AS as_s ON a.id_ath = as_s.list_ath AND as_s.list_saison = 5
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

@licencies_bp.route('/licencies/next-number', methods=['GET'])
def get_next_licence_number():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        from datetime import datetime
        now = datetime.now()
        month = now.strftime('%m')
        year = now.strftime('%y')
        
        cursor.execute("SELECT num_ath FROM athletes WHERE num_ath REGEXP '^[0-9]{8}$' ORDER BY id_ath DESC LIMIT 1")
        last_num = cursor.fetchone()
        
        if last_num and last_num[0]:
            try:
                last_serial = int(last_num[0][-4:])
                new_serial = last_serial + 1
            except:
                new_serial = 1000
        else:
            new_serial = 1000
            
        num_licence = f"{month}{year}{new_serial:04d}"
        return jsonify({'success': True, 'next_number': num_licence})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@licencies_bp.route('/licencies', methods=['POST'])
def create_licencie():
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Données manquantes'}), 400
        
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Générer le numéro de licence (même logique que next-number pour cohérence)
        from datetime import datetime
        now = datetime.now()
        month = now.strftime('%m')
        year = now.strftime('%y')
        
        cursor.execute("SELECT num_ath FROM athletes WHERE num_ath REGEXP '^[0-9]{8}$' ORDER BY id_ath DESC LIMIT 1")
        last_num = cursor.fetchone()
        
        # On refait le calcul pour éviter les doublons si deux personnes créent en même temps
        if last_num and last_num['num_ath']:
            try:
                last_serial = int(last_num['num_ath'][-4:])
                new_serial = last_serial + 1
            except:
                new_serial = 1000
        else:
            new_serial = 1000
            
        num_licence = f"{month}{year}{new_serial:04d}"
        
        # 2. Identifier la saison courante (année en cours)
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        # 3. Insérer dans la table athletes
        insert_query = """
            INSERT INTO athletes (
                nom_prenoms, tel_ath, mail_ath, date_nais, 
                list_club, list_grade, num_ath, statut,
                genre, lieu_nais, nation, prof_ath, person_prevenir, tel_person, passeport_etabli,
                created_at, update_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """
        cursor.execute(insert_query, (
            data.get('nom_prenoms', '').strip().upper(),
            data.get('contact', '').strip().upper(),
            data.get('email', '').strip(),
            data.get('date_naissance') or None,
            data.get('id_club'),
            data.get('list_grade'),
            num_licence,
            'actif',
            data.get('genre'),
            data.get('lieu_nais', '').strip().upper(),
            data.get('nation', '').strip().upper(),
            data.get('prof_ath', '').strip().upper(),
            data.get('person_prevenir', '').strip().upper(),
            data.get('tel_person', '').strip().upper(),
            int(data.get('passeport_etabli', 0))
        ))
        
        new_id = cursor.lastrowid
        
        # 4. Affiliation automatique à la saison identifiée
        assure_val = int(data.get('assure', 0))
        cursor.execute("""
            INSERT INTO athletes_saison (list_ath, list_saison, list_club, list_grade, assure, created_at, update_at)
            VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
        """, (new_id, saison_id, data['id_club'], data['list_grade'], assure_val))
            
        conn.commit()
        return jsonify({'success': True, 'message': 'Licencié créé et affilié avec succès', 'id': new_id, 'num_licence': num_licence})
    except Exception as e:
        logger.error(f"Erreur create_licencie: {e}")
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
                date_nais = %s, list_club = %s, list_grade = %s,
                genre = %s, lieu_nais = %s, nation = %s, prof_ath = %s, 
                person_prevenir = %s, tel_person = %s, passeport_etabli = %s,
                update_at = NOW()
            WHERE id_ath = %s
        """
        full_name = data.get('nom_prenoms', '').strip().upper()
        contact = data.get('contact', '').strip().upper()
        cursor.execute(update_query, (
            full_name,
            contact,
            data.get('email', '').strip(),
            data.get('date_naissance') or None,
            data.get('id_club'),
            data.get('list_grade'),
            data.get('genre'),
            data.get('lieu_nais', '').strip().upper(),
            data.get('nation', '').strip().upper(),
            data.get('prof_ath', '').strip().upper(),
            data.get('person_prevenir', '').strip().upper(),
            data.get('tel_person', '').strip().upper(),
            int(data.get('passeport_etabli', 0)),
            id
        ))
        
        # 2. Mettre à jour ou insérer dans athletes_saison
        if data.get('id_saison'):
            assure_val = int(data.get('assure', 0))
            cursor.execute("SELECT id_athsaison FROM athletes_saison WHERE list_ath = %s AND list_saison = %s", (id, data['id_saison']))
            exists = cursor.fetchone()
            if exists:
                cursor.execute("""
                    UPDATE athletes_saison 
                    SET list_club = %s, list_grade = %s, assure = %s, update_at = NOW()
                    WHERE list_ath = %s AND list_saison = %s
                """, (data['id_club'], data['list_grade'], assure_val, id, data['id_saison']))
            else:
                cursor.execute("""
                    INSERT INTO athletes_saison (list_ath, list_saison, list_club, list_grade, assure, created_at, update_at)
                    VALUES (%s, %s, %s, %s, %s, NOW(), NOW())
                """, (id, data['id_saison'], data['id_club'], data['list_grade'], assure_val))
        
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
    exclude_ath = request.args.get('exclude_athlete_id', type=int)
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        if exclude_ath:
            query = """
                SELECT * FROM saison 
                WHERE id_saison NOT IN (
                    SELECT list_saison FROM athletes_saison WHERE list_ath = %s
                )
                ORDER BY id_saison DESC
            """
            cursor.execute(query, (exclude_ath,))
        else:
            cursor.execute("SELECT * FROM saison ORDER BY id_saison DESC")
        saisons = cursor.fetchall()
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
