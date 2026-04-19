"""
Point d'entrée Python pour FI-ADEKASH.
"""

import os
import logging
import datetime
import bcrypt
from pathlib import Path
from dotenv import load_dotenv

from flask import Flask, abort, jsonify, request, send_from_directory, session
from werkzeug.utils import safe_join
import mysql.connector
from mysql.connector import Error

# Charger les variables d'environnement
load_dotenv()

# Configuration logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent

app = Flask(__name__)

# === SECRET KEY ===
app.secret_key = os.environ.get("SECRET_KEY", "fiadekash-secret-key-2024-very-long-and-secure")
# =================

logger.info("Mode: Utilisation des routes d'authentification directes dans app.py")

@app.after_request
def _cors_api_dev(response):
    """Permet d'appeler /api/* depuis le frontend"""
    if request.path.startswith("/api/"):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET, PUT, DELETE"
    return response

def get_db():
    """Retourne une connexion MySQL depuis les variables d'environnement."""
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            port=int(os.environ.get("DB_PORT", 3306)),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "fiadekash"),
            charset="utf8mb4",
            use_unicode=True,
        )
        logger.info("Connexion BDD réussie")
        return conn
    except Error as e:
        logger.error(f"Erreur de connexion à la BDD: {e}")
        return None

def get_db_connection():
    """Alias pour get_db() - retourne une connexion MySQL"""
    return get_db()

# ============================================================
# ADMIN AUTHENTICATION - ROUTES DIRECTES
# ============================================================

@app.route('/api/admin/login', methods=['POST', 'OPTIONS'])
def admin_login():
    """Authentification admin"""
    if request.method == 'OPTIONS':
        return '', 204
    
    data = request.get_json(silent=True) or {}
    login = data.get('login', '').strip()
    password = data.get('password', '')
    
    logger.info(f"Tentative de connexion admin: {login}")
    
    if not login or not password:
        return jsonify({'success': False, 'message': 'Identifiant et mot de passe requis'}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            logger.error("Table users non trouvée")
            return jsonify({'success': False, 'message': 'Configuration BDD incomplète'}), 500
        
        cursor.execute("""
            SELECT id, login, password_hash, nom, prenom, email, role_id, actif
            FROM users 
            WHERE login = %s
        """, (login,))
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Utilisateur non trouvé: {login}")
            return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        if user.get('actif') == 0:
            logger.warning(f"Compte inactif: {login}")
            return jsonify({'success': False, 'message': 'Compte désactivé'}), 401
        
        password_hash = user.get('password_hash', '')
        if not password_hash:
            logger.error(f"Mot de passe non trouvé pour: {login}")
            return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                logger.warning(f"Mot de passe incorrect pour: {login}")
                return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        except Exception as bcrypt_error:
            logger.error(f"Erreur bcrypt: {bcrypt_error}")
            if password != password_hash:
                return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        try:
            cursor.execute("UPDATE users SET derniere_cnx = NOW() WHERE id = %s", (user['id'],))
            conn.commit()
        except:
            pass
        
        role_name = 'Administrateur'
        role_id = user.get('role_id')
        if role_id == 1:
            role_name = 'Super Admin'
        elif role_id == 2:
            role_name = 'Administrateur'
        elif role_id == 3:
            role_name = 'Modérateur'
        
        session['admin_id'] = user['id']
        session['admin_login'] = user['login']
        session['admin_logged_in'] = True
        
        logger.info(f"Connexion admin réussie: {login}")
        
        return jsonify({
            'success': True,
            'token': f"admin_token_{user['id']}_{int(datetime.datetime.now().timestamp())}",
            'user': {
                'id': user['id'],
                'login': user['login'],
                'nom': user.get('nom', ''),
                'prenom': user.get('prenom', ''),
                'email': user.get('email', ''),
                'role': role_name
            }
        })
    except Error as db_err:
        logger.error(f"Erreur MySQL admin_login: {db_err}")
        return jsonify({'success': False, 'message': f'Erreur base de données: {str(db_err)}'}), 500
    except Exception as e:
        logger.error(f"Erreur admin_login: {e}")
        return jsonify({'success': False, 'message': f'Erreur serveur: {str(e)}'}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/verify', methods=['GET', 'POST', 'OPTIONS'])
def admin_verify():
    """Vérifie si l'admin est connecté"""
    if request.method == 'OPTIONS':
        return '', 204
    
    if session.get('admin_logged_in'):
        return jsonify({'success': True, 'message': 'Session valide'})
    
    auth_header = request.headers.get('Authorization', '')
    if auth_header and auth_header.startswith('Bearer '):
        token = auth_header[7:]
        if token and token.startswith('admin_token_'):
            return jsonify({'success': True, 'message': 'Token valide'})
    
    return jsonify({'success': False, 'message': 'Non authentifié'}), 401

@app.route('/api/admin/logout', methods=['POST', 'OPTIONS'])
def admin_logout():
    """Déconnexion admin"""
    if request.method == 'OPTIONS':
        return '', 204
    
    session.clear()
    return jsonify({'success': True, 'message': 'Déconnecté'})

@app.route('/api/admin/check-session', methods=['GET'])
def admin_check_session():
    """Vérifie l'état de la session admin"""
    if session.get('admin_logged_in'):
        return jsonify({
            'success': True,
            'logged_in': True,
            'user': {
                'id': session.get('admin_id'),
                'login': session.get('admin_login')
            }
        })
    return jsonify({'success': True, 'logged_in': False})

# ============================================================
# ROUTES PAGES STATIQUES
# ============================================================

@app.get("/")
def index():
    return send_from_directory(ROOT, "index.html")

@app.get("/admin/admin-login.html")
def admin_login_page():
    return send_from_directory(ROOT, "admin/admin-login.html")

@app.get("/admin/admin-dashboard.html")
def admin_dashboard_page():
    return send_from_directory(ROOT, "admin/admin-dashboard.html")

@app.get("/admin/dashboard.html")
def admin_dashboard_redirect():
    return send_from_directory(ROOT, "admin/admin-dashboard.html")

@app.get("/admin/clubs.html")
def admin_clubs_page():
    return send_from_directory(ROOT, "admin/clubs.html")

@app.get("/admin/clubs-saison.html")
def admin_clubs_saison_page():
    return send_from_directory(ROOT, "admin/clubs-saison.html")

@app.get("/admin/clubs-new.html")
def admin_clubs_new_page():
    return send_from_directory(ROOT, "admin/clubs-new.html")

@app.get("/admin/licencies-club.html")
def admin_licencies_club_page():
    return send_from_directory(ROOT, "admin/licencies-club.html")

@app.get("/admin/licencies-new.html")
def admin_licencies_new_page():
    return send_from_directory(ROOT, "admin/licencies-new.html")

@app.get("/admin/evenements.html")
def admin_evenements_page():
    return send_from_directory(ROOT, "admin/evenements.html")

@app.get("/admin/documents.html")
def admin_documents_page():
    return send_from_directory(ROOT, "admin/documents.html")

@app.get("/admin/messages.html")
def admin_messages_page():
    return send_from_directory(ROOT, "admin/messages.html")

@app.get("/admin/statistiques.html")
def admin_statistiques_page():
    return send_from_directory(ROOT, "admin/statistiques.html")

@app.get("/admin/utilisateurs.html")
def admin_utilisateurs_page():
    return send_from_directory(ROOT, "admin/utilisateurs.html")

@app.get("/admin/sidebar.html")
def admin_sidebar():
    return send_from_directory(ROOT, "admin/sidebar.html")

@app.get("/admin/css/<path:filename>")
def admin_css(filename):
    filepath = ROOT / "admin" / "css" / filename
    if not filepath.exists() or not filepath.is_file():
        abort(404)
    return send_from_directory(ROOT / "admin" / "css", filename)

@app.get("/<path:filename>")
def site_files(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    
    filepath = ROOT / filename
    if not filepath.exists() or not filepath.is_file():
        abort(404)
    
    return send_from_directory(ROOT, filename)

# ============================================================
# ROUTES API - CONTACT
# ============================================================

@app.post("/api/contact")
def api_contact():
    data = request.get_json(silent=True) or {}
    logger.info(f"Formulaire contact reçu: {data}")
    
    try:
        conn = get_db()
        if conn:
            cursor = conn.cursor()
            cursor.execute("SHOW TABLES LIKE 'messages'")
            if cursor.fetchone():
                cursor.execute("""
                    INSERT INTO messages (nom, email, message, date_creation) 
                    VALUES (%s, %s, %s, NOW())
                """, (data.get('nom', ''), data.get('email', ''), data.get('message', '')))
                conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Erreur sauvegarde message: {e}")
    
    return jsonify({
        "ok": True,
        "message": "Message reçu, nous vous répondrons dans les meilleurs délais.",
        "received_keys": list(data.keys()) if data else [],
    })

# ============================================================
# ROUTES API - CLUB (Espace club)
# ============================================================

@app.route("/api/club/login", methods=["POST", "OPTIONS"])
def api_club_login():
    if request.method == "OPTIONS":
        return "", 204
    
    data = request.get_json(silent=True) or {}
    logger.info(f"Requête login reçue: {data}")
    
    club_id = data.get("club_id") or data.get("clubId") or ""
    club_id = str(club_id).strip().upper()
    
    if not club_id:
        logger.warning("Identifiant manquant")
        return jsonify({
            "success": False,
            "message": "Veuillez renseigner l'identifiant du club."
        }), 400
    
    conn = None
    cursor = None
    
    try:
        conn = get_db()
        if not conn:
            logger.error("Impossible de se connecter à la BDD")
            return jsonify({
                "success": False,
                "message": "Erreur de connexion à la base de données."
            }), 500
        
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SHOW TABLES LIKE 'club'")
        table_exists = cursor.fetchone()
        if not table_exists:
            logger.error("La table 'club' n'existe pas dans la base de données")
            return jsonify({
                "success": False,
                "message": "Configuration de la base de données incomplète."
            }), 500
        
        query = """
            SELECT id_club, identif_club, nom_club, representant, contact, email, whatapp
            FROM club
            WHERE identif_club = %s
            LIMIT 1
        """
        cursor.execute(query, (club_id,))
        club = cursor.fetchone()
        
        if not club:
            logger.warning(f"Identifiant non trouvé: {club_id}")
            return jsonify({
                "success": False,
                "message": "Identifiant non reconnu. Contactez le secrétariat."
            }), 401
        
        return jsonify({
            "success": True,
            "club_id": club["identif_club"],
            "nom_club": club.get("nom_club", club_id),
            "representant": club.get("representant"),
            "contact": club.get("contact"),
            "email": club.get("email"),
            "whatsapp": club.get("whatapp"),
        }), 200
        
    except Error as db_err:
        logger.error(f"Erreur MySQL: {db_err}")
        return jsonify({
            "success": False,
            "message": f"Erreur base de données: {str(db_err)}"
        }), 500
    except Exception as e:
        logger.error(f"Erreur inattendue: {e}")
        return jsonify({
            "success": False,
            "message": f"Erreur serveur: {str(e)}"
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route("/api/club/logout", methods=["POST", "OPTIONS"])
def api_club_logout():
    if request.method == "OPTIONS":
        return "", 204
    return jsonify({"success": True, "message": "Déconnexion effectuée."}), 200

# ============================================================
# ROUTES API - CLUBS (ADMIN)
# ============================================================

@app.route('/api/admin/clubs/count', methods=['GET'])
def get_clubs_count():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM club")
        result = cursor.fetchone()
        
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs', methods=['GET'])
def get_clubs():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    search = request.args.get('search', '')
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                c.id_club,
                c.identif_club,
                c.nom_club,
                c.representant,
                c.contact,
                c.grade,
                c.List_sect,
                c.statut,
                s.nom_secteur as secteur,
                c.Num_declaration,
                c.created_At,
                c.update_At
            FROM club c
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
        """
        
        params = []
        
        if search:
            query += """ 
                WHERE c.nom_club LIKE %s 
                OR c.identif_club LIKE %s 
                OR c.representant LIKE %s
                OR c.contact LIKE %s
            """
            search_param = f'%{search}%'
            params = [search_param, search_param, search_param, search_param]
        
        query += " ORDER BY s.nom_secteur ASC, c.nom_club ASC"
        
        if limit != 9999:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        clubs = cursor.fetchall()
        
        if search:
            cursor.execute("""
                SELECT COUNT(*) as total FROM club c
                WHERE c.nom_club LIKE %s 
                OR c.identif_club LIKE %s 
                OR c.representant LIKE %s
                OR c.contact LIKE %s
            """, (search_param, search_param, search_param, search_param))
        else:
            cursor.execute("SELECT COUNT(*) as total FROM club")
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
        return jsonify({
            'success': True,
            'clubs': clubs,
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': (total + limit - 1) // limit if total > 0 else 1
        })
    except Exception as e:
        logger.error(f"Erreur get_clubs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs/<int:club_id>', methods=['GET'])
def get_club_by_id(club_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                c.id_club,
                c.identif_club,
                c.nom_club,
                c.representant,
                c.grade,
                c.contact,
                c.List_sect,
                c.statut,
                s.nom_secteur as secteur,
                c.Num_declaration,
                c.created_At,
                c.update_At
            FROM club c
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            WHERE c.id_club = %s
        """, (club_id,))
        club = cursor.fetchone()
        
        if not club:
            return jsonify({'success': False, 'message': 'Club non trouvé'}), 404
        
        return jsonify({'success': True, 'club': club})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs/last-identif', methods=['GET'])
def get_last_club_identif():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT identif_club 
            FROM club 
            WHERE identif_club IS NOT NULL AND identif_club != ''
            ORDER BY id_club DESC 
            LIMIT 1
        """)
        result = cursor.fetchone()
        
        last_identif = result['identif_club'] if result else None
        
        return jsonify({
            'success': True,
            'last_identif': last_identif
        })
    except Exception as e:
        logger.error(f"Erreur get_last_club_identif: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs', methods=['POST'])
def create_club():
    """Crée un nouveau club et ajoute l'entrée dans clubs_saison"""
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        
        # Récupérer l'id_secteur à partir du nom du secteur si nécessaire
        list_sect = data.get('List_sect')
        if list_sect and isinstance(list_sect, str) and not list_sect.isdigit():
            cursor.execute("SELECT id_secteur FROM secteur WHERE nom_secteur = %s", (list_sect,))
            result = cursor.fetchone()
            if result:
                list_sect = result[0]
            else:
                list_sect = None
        
        statut = data.get('statut', 'actif')
        identif_club = data.get('identif_club')
        
        # 1. Insérer dans la table club
        cursor.execute("""
            INSERT INTO club (
                identif_club,
                nom_club,
                representant,
                grade,
                contact,
                List_sect,
                Num_declaration,
                statut,
                created_At,
                update_At
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, CURDATE(), NOW())
        """, (
            identif_club,
            data.get('nom_club'),
            data.get('representant'),
            data.get('grade'),
            data.get('contact'),
            list_sect,
            data.get('Num_declaration'),
            statut
        ))
        
        club_id = cursor.lastrowid
        
        # 2. Déterminer la saison en cours (année entière)
        current_year = datetime.datetime.now().year
        
        # 3. Vérifier si la saison existe dans la table saison
        cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison = %s", (str(current_year),))
        saison = cursor.fetchone()
        
        if saison:
            id_saison = saison[0]
        else:
            cursor.execute("INSERT INTO saison (libelle_saison) VALUES (%s)", (str(current_year),))
            id_saison = cursor.lastrowid
        
        # 4. Insérer dans clubs_saison
        cursor.execute("""
            INSERT INTO clubs_saison (
                List_saison,
                List_club,
                List_sect,
                created_At,
                update_At
            ) VALUES (%s, %s, %s, CURDATE(), NOW())
        """, (
            id_saison,
            club_id,
            list_sect
        ))
        
        conn.commit()
        
        return jsonify({'success': True, 'id': club_id, 'identif_club': identif_club, 'message': 'Club créé avec succès'})
    except Exception as e:
        logger.error(f"Erreur create_club: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs/<int:club_id>', methods=['DELETE'])
def delete_club(club_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM club WHERE id_club = %s", (club_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Club supprimé avec succès'})
    except Exception as e:
        logger.error(f"Erreur delete_club: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs/<int:club_id>/toggle-status', methods=['PATCH'])
def toggle_club_status(club_id):
    data = request.get_json()
    new_status = data.get('statut')
    
    if new_status not in ['actif', 'inactif']:
        return jsonify({'success': False, 'message': 'Statut invalide'}), 400
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("UPDATE club SET statut = %s, update_At = NOW() WHERE id_club = %s", 
                       (new_status, club_id))
        conn.commit()
        
        action = "activé" if new_status == 'actif' else "désactivé"
        return jsonify({'success': True, 'message': f'Club {action} avec succès'})
    except Exception as e:
        logger.error(f"Erreur toggle_club_status: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs/all', methods=['GET'])
def get_all_clubs():
    """Récupère TOUS les clubs avec la liste de leurs saisons d'inscription"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        query_clubs = """
            SELECT 
                c.id_club,
                c.identif_club,
                c.nom_club,
                c.representant,
                c.contact,
                c.grade,
                c.List_sect,
                c.Num_declaration,
                c.statut,
                c.created_At,
                c.update_At,
                s.nom_secteur as secteur
            FROM club c
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            ORDER BY c.id_club DESC
        """
        cursor.execute(query_clubs)
        clubs = cursor.fetchall()
        
        for club in clubs:
            cursor.execute("""
                SELECT cs.List_saison as id_saison, sa.libelle_saison
                FROM clubs_saison cs
                LEFT JOIN saison sa ON cs.List_saison = sa.id_saison
                WHERE cs.List_club = %s
                ORDER BY cs.created_At DESC
            """, (club['id_club'],))
            club['saisons'] = cursor.fetchall()
            club['id_saison'] = club['saisons'][0]['id_saison'] if club['saisons'] else None
        
        logger.info(f"Nombre total de clubs UNIQUES récupérés: {len(clubs)}")
        
        return jsonify({
            'success': True,
            'clubs': clubs
        })
    except Exception as e:
        logger.error(f"Erreur get_all_clubs: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des clubs: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - SECTEURS
# ============================================================

@app.route('/api/admin/secteurs', methods=['GET'])
def get_secteurs():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_secteur, nom_secteur FROM secteur ORDER BY nom_secteur ASC")
        secteurs = cursor.fetchall()
        
        return jsonify({'success': True, 'secteurs': secteurs})
    except Exception as e:
        logger.error(f"Erreur get_secteurs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - GRADES
# ============================================================


@app.route('/api/admin/grades', methods=['GET'])
def get_grades():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_grade, designation FROM grade ORDER BY id_grade ASC")
        grades = cursor.fetchall()
        
        return jsonify({'success': True, 'grades': grades})
    except Exception as e:
        logger.error(f"Erreur get_grades: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - ATHLETES (LICENCIES)
# ============================================================

@app.route('/api/admin/licencies/count', methods=['GET'])
def get_licencies_count():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM athletes")
        result = cursor.fetchone()
        
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/licencies/all', methods=['GET'])
def get_all_licencies():
    """Récupère TOUS les athlètes (licenciés) avec leurs informations"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                a.id_ath as id_licencie,
                a.`list_club` as id_club,
                a.`list_grade` as id_grade,
                a.`num_ath` as num_licence,
                a.`nom_prenoms`, 
                a.`genre`,
                a.`date_nais` as date_naissance,
                a.`lieu_nais` as lieu_naissance,
                a.`nation`,
                a.`tel_ath` as contact,
                a.`mail_ath` as email,
                a.`prof_ath`,
                a.`person_prevenir`,
                a.`tel_person` as contact_pers,
                a.`passeport_etabli`,
                a.created_At,
                a.update_At, 
                c.nom_club,
                c.identif_club,
                s.nom_secteur as secteur,
                g.libelle as grade
            FROM athletes a
            LEFT JOIN club c ON a.list_club = c.id_club
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            LEFT JOIN grade g ON a.list_grade = g.id_grade
            ORDER BY a.created_At DESC
        """
        cursor.execute(query)
        athletes = cursor.fetchall()
        
        # Pour chaque athlète, récupérer la liste des saisons
        for athlete in athletes:
            try:
                cursor.execute("""
                    SELECT 
                        asa.List_saison as id_saison, 
                        sa.libelle_saison
                    FROM athletes_saison asa
                    LEFT JOIN saison sa ON asa.List_saison = sa.id_saison
                    WHERE asa.List_athlete = %s
                    ORDER BY asa.created_At DESC
                """, (athlete['id_licencie'],))
                athlete['saisons'] = cursor.fetchall()
                athlete['id_saison'] = athlete['saisons'][0]['id_saison'] if athlete['saisons'] else None
            except Exception as e:
                logger.warning(f"Erreur récupération saisons pour athlete {athlete['id_licencie']}: {e}")
                athlete['saisons'] = []
                athlete['id_saison'] = None
        
        logger.info(f"Nombre total d'athlètes récupérés: {len(athletes)}")
        
        return jsonify({
            'success': True,
            'licencies': athletes
        })
    except Exception as e:
        logger.error(f"Erreur get_all_licencies: {e}")
        return jsonify({
            'success': False,
            'message': f'Erreur lors du chargement des licenciés: {str(e)}'
        }), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/licencies', methods=['GET'])
def get_licencies():
    """Récupère les athlètes avec pagination et filtres"""
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 20, type=int)
    offset = (page - 1) * limit
    search = request.args.get('search', '')
    club_id = request.args.get('club_id', '')
    secteur_id = request.args.get('secteur_id', '')
    statut = request.args.get('statut', '')
    
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        query = """
            SELECT 
                a.id_ath as id_licencie,
                a.`list_club` as id_club,
                a.`list_grade` as id_grade,
                a.`num_ath` as num_licence,
                a.`nom_prenoms`, 
                a.`genre`,
                a.`date_nais` as date_naissance,
                a.`lieu_nais` as lieu_naissance,
                a.`nation`,
                a.`tel_ath` as contact,
                a.`mail_ath` as email,
                a.`prof_ath`,
                a.`person_prevenir`,
                a.`tel_person` as contact_pers,
                a.`passeport_etabli`,
                a.created_At,
                a.update_At,
                c.nom_club,
                c.identif_club,
                s.nom_secteur as secteur
            FROM athletes a
            LEFT JOIN club c ON a.list_club = c.id_club
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            WHERE 1=1
        """
        
        params = []
        
        if search:
            query += " AND (a.nom_prenoms LIKE %s OR a.num_ath LIKE %s)"
            search_param = f'%{search}%'
            params.extend([search_param, search_param])
        
        if club_id:
            query += " AND a.list_club = %s"
            params.append(club_id)
        
        if secteur_id:
            query += " AND c.List_sect = %s"
            params.append(secteur_id)
        
        if statut:
            query += " AND a.statut = %s"
            params.append(statut)
        
        query += " ORDER BY a.created_At DESC"
        
        if limit != 9999:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        athletes = cursor.fetchall()
        
        # Compter le total
        count_query = """
            SELECT COUNT(*) as total FROM athletes a WHERE 1=1
        """
        count_params = []
        if search:
            count_query += " AND (a.nom_prenoms LIKE %s OR a.num_ath LIKE %s)"
            count_params.extend([search_param, search_param])
        if club_id:
            count_query += " AND a.list_club = %s"
            count_params.append(club_id)
        if secteur_id:
            count_query += " AND c.List_sect = %s"
            count_params.append(secteur_id)
        if statut:
            count_query += " AND a.statut = %s"
            count_params.append(statut)
        
        cursor.execute(count_query, count_params)
        total_result = cursor.fetchone()
        total = total_result['total'] if total_result else 0
        
        return jsonify({
            'success': True,
            'licencies': athletes,
            'total': total,
            'page': page,
            'limit': limit,
            'totalPages': (total + limit - 1) // limit if total > 0 else 1
        })
    except Exception as e:
        logger.error(f"Erreur get_licencies: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/licencies/<int:licencie_id>', methods=['GET'])
def get_licencie_by_id(licencie_id):
    """Récupère un athlète par son ID"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT 
                a.id_ath as id_licencie,
                a.`list_club` as id_club,
                a.`list_grade`as id_grade,
                a.`num_ath` as num_licence,
                a.`nom_prenoms`, 
                a.`genre`,
                a.`date_nais` as date_naissance,
                a.`lieu_nais` as lieu_naissance,
                a.`nation`,
                a.`tel_ath` as contact,
                a.`mail_ath` as email,
                a.`prof_ath`,
                a.`person_prevenir`,
                a.`tel_person` as contact_pers,
                a.`passeport_etabli`,
                a.created_At,
                a.update_At,
                c.nom_club,
                c.identif_club,
                s.nom_secteur as secteur
            FROM athletes a
            LEFT JOIN club c ON a.list_club = c.id_club
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
            WHERE a.id_ath = %s
        """, (licencie_id,))
        athlete = cursor.fetchone()
        
        if not athlete:
            return jsonify({'success': False, 'message': 'Licencié non trouvé'}), 404
        
        # Récupérer les saisons
        cursor.execute("""
            SELECT asa.List_saison as id_saison, sa.libelle_saison
            FROM athletes_saison asa
            LEFT JOIN saison sa ON asa.List_saison = sa.id_saison
            WHERE asa.List_athlete = %s
            ORDER BY asa.created_At DESC
        """, (licencie_id,))
        athlete['saisons'] = cursor.fetchall()
        
        # Extraire nom et prénom depuis nom_prenoms
        nom_prenoms = athlete.get('nom_prenoms', '')
        if nom_prenoms:
            parts = nom_prenoms.split(' ', 1)
            athlete['nom'] = parts[0] if parts else ''
            athlete['prenom'] = parts[1] if len(parts) > 1 else ''
        else:
            athlete['nom'] = ''
            athlete['prenom'] = ''
        
        return jsonify({'success': True, 'licencie': athlete})
    except Exception as e:
        logger.error(f"Erreur get_licencie_by_id: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/licencies', methods=['POST'])
def create_licencie():
    """Crée un nouvel athlète et ajoute l'entrée dans athletes_saison"""
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        
        # Générer un numéro de licence si non fourni
        num_licence = data.get('num_licence')
        if not num_licence:
            current_year = datetime.datetime.now().year
            cursor.execute("SELECT COUNT(*) as count FROM athletes")
            count = cursor.fetchone()[0]
            num_licence = f"LIC-{current_year}-{count + 1:04d}"
        
        # Construire nom_prenoms à partir de nom et prenom
        nom = data.get('nom', '').upper()
        prenom = data.get('prenom', '')
        nom_prenoms = f"{nom} {prenom}".strip()
        
        statut = data.get('statut', 'en_attente')
        id_club = data.get('id_club')
        id_secteur = data.get('id_secteur')
        list_grade = data.get('grade')
        
        # 1. Insérer dans la table athletes
        cursor.execute("""
            INSERT INTO athletes (
                num_ath,
                list_club,
                list_grade,
                nom_prenoms,
                genre,
                date_nais,
                lieu_nais,
                nation,
                tel_ath,
                mail_ath,
                prof_ath,
                person_prevenir,
                tel_person,
                passeport_etabli,
                statut,
                created_At,
                update_At
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, (
            num_licence,
            id_club,
            list_grade,
            nom_prenoms,
            data.get('genre', ''),
            data.get('date_naissance'),
            data.get('lieu_naissance', ''),
            data.get('nation', 'CI'),
            data.get('contact'),
            data.get('email', ''),
            data.get('prof_ath', ''),
            data.get('person_prevenir', ''),
            data.get('contact_pers', ''),
            data.get('passeport_etabli', ''),
            statut
        ))
        
        athlete_id = cursor.lastrowid
        
        # 2. Déterminer la saison
        id_saison = data.get('id_saison')
        if not id_saison:
            current_year = datetime.datetime.now().year
            cursor.execute("SELECT id_saison FROM saison WHERE libelle_saison = %s", (str(current_year),))
            saison = cursor.fetchone()
            if saison:
                id_saison = saison[0]
            else:
                cursor.execute("INSERT INTO saison (libelle_saison) VALUES (%s)", (str(current_year),))
                id_saison = cursor.lastrowid
        
        # 3. Insérer dans athletes_saison
        cursor.execute("""
            INSERT INTO athletes_saison (
                List_saison,
                List_athlete,
                List_club,
                List_sect,
                created_At,
                update_At
            ) VALUES (%s, %s, %s, %s, NOW(), NOW())
        """, (
            id_saison,
            athlete_id,
            id_club,
            id_secteur
        ))
        
        conn.commit()
        
        return jsonify({
            'success': True,
            'id': athlete_id,
            'num_licence': num_licence,
            'message': 'Licencié créé avec succès'
        })
    except Exception as e:
        logger.error(f"Erreur create_licencie: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/licencies/<int:licencie_id>', methods=['PUT'])
def update_licencie(licencie_id):
    """Met à jour un athlète"""
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        
        updates = []
        params = []
        
        # Mappage des champs frontend -> colonnes BDD
        field_mapping = {
            'num_licence': 'num_ath',
            'id_club': 'list_club',
            'grade': 'list_grade',
            'contact': 'tel_ath',
            'email': 'mail_ath',
            'date_naissance': 'date_nais',
            'lieu_naissance': 'lieu_nais',
            'statut': 'statut',
            'genre': 'genre',
            'nation': 'nation',
            'prof_ath': 'prof_ath',
            'person_prevenir': 'person_prevenir',
            'contact_pers': 'tel_person',
            'passeport_etabli': 'passeport_etabli'
        }
        
        # Gestion spéciale de nom_prenoms
        if 'nom' in data or 'prenom' in data:
            nom = data.get('nom', '').upper()
            prenom = data.get('prenom', '')
            nom_prenoms = f"{nom} {prenom}".strip()
            updates.append("nom_prenoms = %s")
            params.append(nom_prenoms)
        
        for field, db_column in field_mapping.items():
            if field in data and data[field] is not None:
                updates.append(f"{db_column} = %s")
                params.append(data[field])
        
        if updates:
            updates.append("update_At = NOW()")
            params.append(licencie_id)
            query = f"UPDATE athletes SET {', '.join(updates)} WHERE id_ath = %s"
            cursor.execute(query, params)
        
        # Mettre à jour la saison si nécessaire
        if 'id_saison' in data and data['id_saison']:
            cursor.execute("""
                SELECT id FROM athletes_saison WHERE List_athlete = %s
            """, (licencie_id,))
            existing = cursor.fetchone()
            
            if existing:
                cursor.execute("""
                    UPDATE athletes_saison 
                    SET List_saison = %s, update_At = NOW()
                    WHERE List_athlete = %s
                """, (data['id_saison'], licencie_id))
            else:
                # Récupérer le club et secteur pour l'insertion
                cursor.execute("SELECT list_club FROM athletes WHERE id_ath = %s", (licencie_id,))
                athlete = cursor.fetchone()
                if athlete:
                    cursor.execute("""
                        INSERT INTO athletes_saison (
                            List_saison, List_athlete, List_club, created_At, update_At
                        ) VALUES (%s, %s, %s, NOW(), NOW())
                    """, (data['id_saison'], licencie_id, athlete[0]))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Licencié modifié avec succès'})
    except Exception as e:
        logger.error(f"Erreur update_licencie: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/licencies/<int:licencie_id>', methods=['DELETE'])
def delete_licencie(licencie_id):
    """Supprime un athlète"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        
        # Supprimer d'abord les associations dans athletes_saison
        cursor.execute("DELETE FROM athletes_saison WHERE List_athlete = %s", (licencie_id,))
        
        # Puis supprimer l'athlète
        cursor.execute("DELETE FROM athletes WHERE id_ath = %s", (licencie_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Licencié supprimé avec succès'})
    except Exception as e:
        logger.error(f"Erreur delete_licencie: {e}")
        if conn:
            conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - SAISONS
# ============================================================

# ============================================================
# ROUTES API - SAISONS POUR CLUBS
# ============================================================

@app.route('/api/admin/saisons/clubs', methods=['GET'])
def get_saisons_clubs():
    """Récupère les saisons disponibles pour les clubs"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer les saisons depuis clubs_saison
        query = """
            SELECT DISTINCT 
                s.id_saison,
                s.libelle_saison
            FROM clubs_saison cs
            INNER JOIN saison s ON s.id_saison = cs.List_saison
            ORDER BY s.id_saison DESC
        """
        cursor.execute(query)
        saisons = cursor.fetchall()
        
        # Fallback: toutes les saisons si aucune dans clubs_saison
        if not saisons:
            cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY id_saison DESC")
            saisons = cursor.fetchall()
        
        # Fallback: créer des saisons par défaut
        if not saisons:
            cursor.execute("INSERT INTO saison (libelle_saison) VALUES ('2024'), ('2025')")
            conn.commit()
            cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY id_saison DESC")
            saisons = cursor.fetchall()
        
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        logger.error(f"Erreur get_saisons_clubs: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# ROUTES API - SAISONS POUR ATHLETES (LICENCIES)
# ============================================================

@app.route('/api/admin/saisons/licencies', methods=['GET'])
def get_saisons_licencies():
    """Récupère les saisons disponibles pour les licenciés"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Récupérer les saisons depuis athletes_saison
        query = """
            SELECT DISTINCT 
                s.id_saison,
                s.libelle_saison
            FROM athletes_saison asa
            INNER JOIN saison s ON s.id_saison = asa.list_saison
            ORDER BY s.id_saison DESC
        """
        cursor.execute(query)
        saisons = cursor.fetchall()
        
        # Fallback: toutes les saisons si aucune dans athletes_saison
        if not saisons:
            cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY id_saison DESC")
            saisons = cursor.fetchall()
        
        # Fallback: créer des saisons par défaut
        if not saisons:
            cursor.execute("INSERT INTO saison (libelle_saison) VALUES ('2024'), ('2025')")
            conn.commit()
            cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY id_saison DESC")
            saisons = cursor.fetchall()
        
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        logger.error(f"Erreur get_saisons_licencies: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ============================================================
# ROUTES API - SAISONS GENERIQUE (POUR COMPATIBILITE)
# ============================================================

@app.route('/api/admin/saisons', methods=['GET'])
def get_saisons():
    """Route générique - retourne toutes les saisons"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY id_saison DESC")
        saisons = cursor.fetchall()
        
        return jsonify({'success': True, 'saisons': saisons})
    except Exception as e:
        logger.error(f"Erreur get_saisons: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - EVENTS (COMPETITIONS)
# ============================================================

@app.route('/api/admin/events/count', methods=['GET'])
def get_events_count():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM competition")
        result = cursor.fetchone()
        
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/events', methods=['GET'])
def get_events():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM competition ORDER BY date ASC")
        events = cursor.fetchall()
        
        return jsonify({'success': True, 'events': events, 'data': events})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/events', methods=['POST'])
def create_event():
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO competition (name, date, location, type, description)
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data.get('name'), data.get('date'), data.get('location'),
            data.get('type'), data.get('description')
        ))
        conn.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE competition SET
                name = %s, date = %s, location = %s, type = %s, description = %s
            WHERE id = %s
        """, (
            data.get('name'), data.get('date'), data.get('location'),
            data.get('type'), data.get('description'), event_id
        ))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM competition WHERE id = %s", (event_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM competition WHERE id = %s", (event_id,))
        event = cursor.fetchone()
        
        if not event:
            return jsonify({'success': False, 'message': 'Événement non trouvé'}), 404
        
        return jsonify({'success': True, 'event': event, 'data': event})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - MESSAGES
# ============================================================

@app.route('/api/admin/messages/unread/count', methods=['GET'])
def get_unread_messages_count():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM messages WHERE lu = 0")
        result = cursor.fetchone()
        
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/messages', methods=['GET'])
def get_messages():
    limit = request.args.get('limit', type=int)
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        query = "SELECT * FROM messages ORDER BY date_creation DESC"
        if limit:
            query += f" LIMIT {limit}"
        cursor.execute(query)
        messages = cursor.fetchall()
        
        return jsonify({'success': True, 'messages': messages, 'data': messages})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/messages/<int:msg_id>/read', methods=['PUT'])
def mark_message_read(msg_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("UPDATE messages SET lu = 1 WHERE id = %s", (msg_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/messages/<int:msg_id>', methods=['DELETE'])
def delete_message(msg_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM messages WHERE id = %s", (msg_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES ADMIN - GESTION DES UTILISATEURS
# ============================================================

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, login, nom, prenom, email, role_id, actif, derniere_cnx, created_at, created_by
            FROM users
            ORDER BY id ASC
        """)
        users = cursor.fetchall()
        
        return jsonify({'success': True, 'users': users})
    except Exception as e:
        logger.error(f"Erreur get_users: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/users', methods=['POST'])
def create_user():
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE login = %s", (data.get('login'),))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Ce login existe déjà'}), 409
        
        if data.get('email'):
            cursor.execute("SELECT id FROM users WHERE email = %s", (data.get('email'),))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Cet email existe déjà'}), 409
        
        password = data.get('password', '')
        if not password:
            password = 'default123'
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        cursor.execute("""
            INSERT INTO users (login, password_hash, nom, prenom, email, role_id, actif, created_at, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), %s)
        """, (
            data.get('login'),
            hashed_password.decode('utf-8'),
            data.get('nom'),
            data.get('prenom'),
            data.get('email'),
            data.get('role_id', 2),
            data.get('actif', 1),
            session.get('user_id', 1)
        ))
        conn.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid})
    except Exception as e:
        logger.error(f"Erreur create_user: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor()
        
        cursor.execute("SELECT id FROM users WHERE login = %s AND id != %s", (data.get('login'), user_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Ce login existe déjà'}), 409
        
        if data.get('email'):
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (data.get('email'), user_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Cet email existe déjà'}), 409
        
        updates = []
        params = []
        
        updates.append("login = %s")
        params.append(data.get('login'))
        
        updates.append("nom = %s")
        params.append(data.get('nom'))
        
        updates.append("prenom = %s")
        params.append(data.get('prenom'))
        
        updates.append("email = %s")
        params.append(data.get('email'))
        
        updates.append("role_id = %s")
        params.append(data.get('role_id'))
        
        updates.append("actif = %s")
        params.append(data.get('actif'))
        
        if data.get('password'):
            hashed = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())
            updates.append("password_hash = %s")
            params.append(hashed.decode('utf-8'))
        
        updates.append("updated_at = NOW()")
        
        params.append(user_id)
        query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
        cursor.execute(query, params)
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erreur update_user: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erreur delete_user: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/users/<int:user_id>/reset-password', methods=['PUT'])
def reset_user_password(user_id):
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        new_password = data.get('password')
        if not new_password:
            return jsonify({'success': False, 'message': 'Mot de passe requis'}), 400
        
        hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt())
        
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET password_hash = %s, token_reset = NULL, token_reset_exp = NULL WHERE id = %s", 
                       (hashed_password.decode('utf-8'), user_id))
        conn.commit()
        
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Erreur reset_user_password: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# ROUTES API - STATISTIQUES
# ============================================================

@app.route('/api/admin/stats/dashboard', methods=['GET'])
def get_dashboard_stats():
    """Récupère les statistiques pour le tableau de bord"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        
        # Nombre de clubs
        cursor.execute("SELECT COUNT(*) as count FROM club")
        clubs_count = cursor.fetchone()['count']
        
        # Nombre d'athlètes
        cursor.execute("SELECT COUNT(*) as count FROM athletes")
        athletes_count = cursor.fetchone()['count']
        
        # Nombre d'événements
        cursor.execute("SELECT COUNT(*) as count FROM competition")
        events_count = cursor.fetchone()['count']
        
        # Nombre de messages non lus
        cursor.execute("SELECT COUNT(*) as count FROM messages WHERE lu = 0")
        unread_messages = cursor.fetchone()['count']
        
        # Nombre d'utilisateurs actifs
        cursor.execute("SELECT COUNT(*) as count FROM users WHERE actif = 1")
        active_users = cursor.fetchone()['count']
        
        # Clubs par secteur
        cursor.execute("""
            SELECT s.nom_secteur, COUNT(c.id_club) as count
            FROM secteur s
            LEFT JOIN club c ON c.List_sect = s.id_secteur
            GROUP BY s.id_secteur
            ORDER BY count DESC
        """)
        clubs_by_sector = cursor.fetchall()
        
        # Athlètes par statut
        cursor.execute("""
            SELECT statut, COUNT(*) as count
            FROM athletes
            GROUP BY statut
        """)
        athletes_by_status = cursor.fetchall()
        
        return jsonify({
            'success': True,
            'stats': {
                'clubs': clubs_count,
                'athletes': athletes_count,
                'events': events_count,
                'unread_messages': unread_messages,
                'active_users': active_users,
                'clubs_by_sector': clubs_by_sector,
                'athletes_by_status': athletes_by_status
            }
        })
    except Exception as e:
        logger.error(f"Erreur get_dashboard_stats: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

# ============================================================
# DÉMARRAGE DU SERVEUR
# ============================================================

if __name__ == "__main__":
    print("=" * 50)
    print("Serveur FI-ADEKASH démarré")
    print("=" * 50)
    print("Site public : http://127.0.0.1:5000")
    print("Espace admin: http://127.0.0.1:5000/admin/admin-login.html")
    print("")
    print("Pages admin disponibles:")
    print("  - Dashboard: http://127.0.0.1:5000/admin/admin-dashboard.html")
    print("  - Liste des clubs: http://127.0.0.1:5000/admin/clubs.html")
    print("  - Clubs par saison: http://127.0.0.1:5000/admin/clubs-saison.html")
    print("  - Nouveau club: http://127.0.0.1:5000/admin/clubs-new.html")
    print("  - Licenciés par club: http://127.0.0.1:5000/admin/licencies-club.html")
    print("  - Nouveau licencié: http://127.0.0.1:5000/admin/licencies-new.html")
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=True)