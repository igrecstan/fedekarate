import logging
from flask import Blueprint, jsonify, request
from db_utils import get_db_connection
from mysql.connector import Error

club_bp = Blueprint('club_api', __name__, url_prefix='/api/club')
logger = logging.getLogger(__name__)

def get_config_value(key, default):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT valeur_config FROM configuration WHERE cle_config = %s", (key,))
        row = cursor.fetchone()
        return row['valeur_config'] if row else default
    except:
        return default
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/athlete/<int:athlete_id>", methods=["GET"])
def get_athlete_info(athlete_id):
    """Récupère le nom et prénom d'un athlète"""
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT nom_prenoms FROM athletes WHERE id_ath = %s", (athlete_id,))
        athlete = cursor.fetchone()
        if athlete:
            return jsonify({"success": True, "nom_prenoms": athlete['nom_prenoms']})
        return jsonify({"success": False, "message": "Athlète non trouvé"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/login", methods=["POST", "OPTIONS"])
def api_club_login():
    if request.method == "OPTIONS":
        return "", 204
    
    data = request.get_json(silent=True) or {}
    club_id = str(data.get("club_id") or "").strip().upper()
    
    if not club_id:
        return jsonify({"success": False, "message": "Identifiant manquant."}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM club WHERE identif_club = %s LIMIT 1"
        cursor.execute(query, (club_id,))
        club = cursor.fetchone()
        
        if not club:
            return jsonify({"success": False, "message": "Identifiant non reconnu."}), 401
        
        # 2. Vérifier si le club est affilié pour la saison en cours
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5

        cursor.execute("SELECT * FROM clubs_saison WHERE List_club = %s AND List_saison = %s", (club['id_club'], saison_id))
        affiliation = cursor.fetchone()
        est_actif = affiliation is not None

        return jsonify({
            "success": True,
            "id_club_reel": club["id_club"],
            "club_id": club["identif_club"],
            "nom_club": club.get("nom_club"),
            "representant": club.get("representant"),
            "est_actif": est_actif
        }), 200
    except Exception as e:
        logger.error(f"Erreur api_club_login: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/config", methods=["GET"])
def get_club_config():
    """Récupère les paramètres publics pour le club"""
    montant_ath = get_config_value('tarif_affiliation', 5000)
    montant_club = get_config_value('tarif_affiliation_club', 10000)
    return jsonify({
        "success": True, 
        "tarif_affiliation": int(montant_ath),
        "tarif_affiliation_club": int(montant_club)
    })

@club_bp.route("/logout", methods=["POST"])
def api_club_logout():
    return jsonify({"success": True, "message": "Déconnecté."}), 200

@club_bp.route("/<club_id>/stats", methods=["GET"])
def get_club_stats(club_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtenir l'ID interne du club
        cursor.execute("SELECT id_club FROM club WHERE identif_club = %s LIMIT 1", (club_id,))
        club = cursor.fetchone()
        
        if not club:
            cursor.execute("SELECT id_club FROM club WHERE id_club = %s LIMIT 1", (club_id,))
            club = cursor.fetchone()
            
        if not club:
            return jsonify({"success": False, "message": "Club non trouvé"}), 404
        
        id_club = club['id_club']
        
        # 2. Identifier la saison courante (même logique que dans admin)
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        # 3. Compter les licenciés AFFILIÉS à la saison en cours
        query = """
            SELECT COUNT(DISTINCT list_ath) as count 
            FROM athletes_saison 
            WHERE list_club = %s AND list_saison = %s
        """
        cursor.execute(query, (id_club, saison_id))
        licencies_count = cursor.fetchone()['count']
        
        # 4. Compter les compétitions (placeholder)
        competitions_count = 0
        
        # 5. Compter les documents (placeholder)
        documents_count = 0
        
        return jsonify({
            "success": True,
            "licencies": licencies_count,
            "competitions": competitions_count,
            "documents": documents_count,
            "saison_id": saison_id
        })
    except Exception as e:
        logger.error(f"Erreur get_club_stats: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/<club_id>/licencies", methods=["GET"])
def get_club_licencies(club_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtenir l'ID interne du club
        cursor.execute("SELECT id_club FROM club WHERE identif_club = %s LIMIT 1", (club_id,))
        club = cursor.fetchone()
        
        if not club:
            cursor.execute("SELECT id_club FROM club WHERE id_club = %s LIMIT 1", (club_id,))
            club = cursor.fetchone()
            
        if not club:
            return jsonify({"success": False, "message": "Club non trouvé"}), 404
        
        id_club = club['id_club']
        
        # 2. Identifier la saison courante
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        # 3. Récupérer TOUS les athlètes du club
        # On fait une jointure gauche pour savoir s'ils sont affiliés à la saison en cours
        query = """
            SELECT a.id_ath as id_licencie, a.num_ath as num_licence, a.nom_prenoms, 
                   a.genre, a.date_nais as date_naissance, a.tel_ath as contact,
                   a.statut, g.libelle as grade,
                   (SELECT COUNT(*) FROM athletes_saison asai 
                    WHERE asai.list_ath = a.id_ath AND asai.list_saison = %s) as est_affilie
            FROM athletes a
            LEFT JOIN grade g ON a.list_grade = g.id_grade
            WHERE a.list_club = %s
            ORDER BY a.nom_prenoms ASC
        """
        cursor.execute(query, (saison_id, id_club))
        licencies = cursor.fetchall()
        
        # Adapter le format pour le frontend
        for l in licencies:
            if l.get('date_naissance'):
                l['date_naissance'] = l['date_naissance'].isoformat()
            parts = l.get('nom_prenoms', '').split(' ', 1)
            l['nom'] = parts[0]
            l['prenom'] = parts[1] if len(parts) > 1 else ''
            
        return jsonify({
            "success": True, 
            "licencies": licencies, 
            "saison_id": saison_id,
            "current_year": current_year
        })
    except Exception as e:
        logger.error(f"Erreur get_club_licencies: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/<club_id>/competitions", methods=["GET"])
def get_club_competitions(club_id):
    # Pour l'instant, retourne une liste vide en attendant la création de la table
    return jsonify({"success": True, "competitions": []})

@club_bp.route("/<club_id>/licencies/<int:licencie_id>/affilier", methods=["POST"])
def affilier_licencie(club_id, licencie_id):
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtenir l'ID interne du club
        cursor.execute("SELECT id_club FROM club WHERE identif_club = %s LIMIT 1", (club_id,))
        club = cursor.fetchone()
        if not club:
            return jsonify({"success": False, "message": "Club non trouvé"}), 404
        id_club = club['id_club']
        
        # 2. Identifier la saison courante
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        # 3. Vérifier si l'athlète appartient bien au club
        cursor.execute("SELECT list_grade FROM athletes WHERE id_ath = %s AND list_club = %s", (licencie_id, id_club))
        athlete = cursor.fetchone()
        if not athlete:
            return jsonify({"success": False, "message": "Athlète non trouvé ou n'appartient pas à votre club"}), 404
        
        # 4. Vérifier si déjà affilié
        cursor.execute("SELECT id_athsaison FROM athletes_saison WHERE list_ath = %s AND list_saison = %s", (licencie_id, saison_id))
        if cursor.fetchone():
            return jsonify({"success": False, "message": "Déjà affilié pour cette saison"}), 400
            
        # 5. Créer l'affiliation (En attente de paiement)
        montant = int(get_config_value('tarif_affiliation', 5000))
        cursor.execute("""
            INSERT INTO athletes_saison (list_ath, list_saison, list_club, list_grade, assure, statut_paiement, montant_paye, created_at, update_at)
            VALUES (%s, %s, %s, %s, 1, 'en_attente', %s, NOW(), NOW())
        """, (licencie_id, saison_id, id_club, athlete['list_grade'], montant))
        
        conn.commit()
        return jsonify({"success": True, "message": "Affiliation réussie"})
    except Exception as e:
        logger.error(f"Erreur affilier_licencie: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/<club_id>/licencie", methods=["POST"])
def create_club_athlete(club_id):
    data = request.get_json(silent=True) or {}
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Obtenir l'ID interne du club
        cursor.execute("SELECT id_club FROM club WHERE identif_club = %s LIMIT 1", (club_id,))
        club = cursor.fetchone()
        if not club:
            return jsonify({"success": False, "message": "Club non trouvé"}), 404
        id_club = club['id_club']
        
        # 2. Générer le numéro de licence (Matricule)
        from datetime import datetime
        now = datetime.now()
        month = now.strftime('%m')
        year = now.strftime('%y')
        
        cursor.execute("SELECT num_ath FROM athletes WHERE num_ath REGEXP '^[0-9]{8}$' ORDER BY id_ath DESC LIMIT 1")
        last_num = cursor.fetchone()
        
        if last_num and last_num['num_ath']:
            try:
                last_serial = int(last_num['num_ath'][-4:])
                new_serial = last_serial + 1
            except:
                new_serial = 1000
        else:
            new_serial = 1000
            
        num_licence = f"{month}{year}{new_serial:04d}"
        
        # 3. Insérer l'athlète
        cursor.execute("""
            INSERT INTO athletes (
                nom_prenoms, date_nais, lieu_nais, nation, genre, 
                list_club, list_grade, tel_ath, mail_ath, prof_ath,
                person_prevenir, tel_person, passeport_etabli, num_ath,
                created_at, update_at
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            data.get('nom_prenoms'),
            data.get('date_naissance'),
            data.get('lieu_nais'),
            data.get('nation'),
            data.get('genre', 'M'),
            id_club,
            data.get('list_grade', 1),
            data.get('contact'),
            data.get('email'),
            data.get('prof_ath'),
            data.get('person_prevenir'),
            data.get('tel_person'),
            data.get('passeport_etabli', 0),
            num_licence
        ))
        athlete_id = cursor.lastrowid
        
        # 3. Affilier automatiquement à la saison en cours (Statut: en_attente de paiement)
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        montant = int(get_config_value('tarif_affiliation', 5000))
        
        cursor.execute("""
            INSERT INTO athletes_saison (list_ath, list_saison, list_club, list_grade, assure, statut_paiement, montant_paye, created_at, update_at)
            VALUES (%s, %s, %s, %s, %s, 'en_attente', %s, NOW(), NOW())
        """, (athlete_id, saison_id, id_club, data.get('list_grade', 1), data.get('assure', 0), montant))
        
        conn.commit()
        return jsonify({"success": True, "message": "Athlète créé et affilié avec succès", "id": athlete_id})
    except Exception as e:
        logger.error(f"Erreur create_club_athlete: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/grades", methods=["GET"])
def get_grades():
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_grade, libelle FROM grade ORDER BY id_grade ASC")
        grades = cursor.fetchall()
        return jsonify({"success": True, "grades": grades})
    except Exception as e:
        logger.error(f"Erreur get_grades: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/<club_id>/payment/simulate", methods=["POST"])
def simulate_payment(club_id):
    data = request.get_json(silent=True) or {}
    athlete_id = data.get('athlete_id')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Identifier la saison courante
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        # 2. Mettre à jour le statut de paiement
        import uuid
        ref = f"SIM-{uuid.uuid4().hex[:8].upper()}"
        
        cursor.execute("""
            UPDATE athletes_saison 
            SET statut_paiement = 'valide', reference_paiement = %s, update_at = NOW()
            WHERE list_ath = %s AND list_saison = %s
        """, (ref, athlete_id, saison_id))
        
        conn.commit()
        return jsonify({"success": True, "message": "Paiement validé (simulation)", "reference": ref})
    except Exception as e:
        logger.error(f"Erreur simulate_payment: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/payment/simulate-club", methods=["POST"])
def simulate_club_payment():
    data = request.get_json(silent=True) or {}
    id_club = data.get('id_club')
    conn = None
    cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # 1. Identifier la saison courante
        from datetime import datetime
        current_year = datetime.now().year
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison LIKE %s OR id_saison = 5 LIMIT 1", (f"%{current_year}%",))
        saison_row = cursor.fetchone()
        saison_id = saison_row['id_saison'] if saison_row else 5
        
        # 2. Récupérer les infos du club
        cursor.execute("SELECT List_sect FROM club WHERE id_club = %s", (id_club,))
        club = cursor.fetchone()
        if not club:
            return jsonify({"success": False, "message": "Club non trouvé"}), 404
            
        # 3. Créer l'affiliation club (si elle n'existe pas déjà)
        cursor.execute("SELECT * FROM clubs_saison WHERE List_club = %s AND List_saison = %s", (id_club, saison_id))
        if not cursor.fetchone():
            cursor.execute("""
                INSERT INTO clubs_saison (List_saison, List_club, List_sect, created_At)
                VALUES (%s, %s, %s, CURDATE())
            """, (saison_id, id_club, club['List_sect']))
        
        conn.commit()
        return jsonify({"success": True, "message": "Affiliation club validée"})
    except Exception as e:
        logger.error(f"Erreur simulate_club_payment: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()
