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

# IMPORTANT: NE PAS importer le blueprint admin car il crée des conflits
# On commente l'import du blueprint admin
# try:
#     from admin_auth import admin_bp
#     app.register_blueprint(admin_bp)
#     logger.info("Blueprint admin chargé avec succès")
# except ImportError as e:
#     logger.warning(f"admin_auth.py non trouvé, blueprint admin non chargé: {e}")

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
        
        # Vérifier d'abord si la table users existe
        cursor.execute("SHOW TABLES LIKE 'users'")
        if not cursor.fetchone():
            logger.error("Table users non trouvée")
            return jsonify({'success': False, 'message': 'Configuration BDD incomplète'}), 500
        
        # Récupérer l'utilisateur
        cursor.execute("""
            SELECT id, login, password_hash, nom, prenom, email, role_id, actif
            FROM users 
            WHERE login = %s
        """, (login,))
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Utilisateur non trouvé: {login}")
            return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        # Vérifier si le compte est actif
        if user.get('actif') == 0:
            logger.warning(f"Compte inactif: {login}")
            return jsonify({'success': False, 'message': 'Compte désactivé'}), 401
        
        # Vérifier le mot de passe
        password_hash = user.get('password_hash', '')
        if not password_hash:
            logger.error(f"Mot de passe non trouvé pour: {login}")
            return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        # Vérifier avec bcrypt
        try:
            if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                logger.warning(f"Mot de passe incorrect pour: {login}")
                return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        except Exception as bcrypt_error:
            logger.error(f"Erreur bcrypt: {bcrypt_error}")
            # Peut-être que le mot de passe n'est pas hashé avec bcrypt
            # Comparaison directe en texte clair (pour migration)
            if password != password_hash:
                return jsonify({'success': False, 'message': 'Identifiant ou mot de passe incorrect'}), 401
        
        # Mettre à jour la dernière connexion
        try:
            cursor.execute("UPDATE users SET derniere_cnx = NOW() WHERE id = %s", (user['id'],))
            conn.commit()
        except:
            pass
        
        # Déterminer le rôle
        role_name = 'Administrateur'
        role_id = user.get('role_id')
        if role_id == 1:
            role_name = 'Super Admin'
        elif role_id == 2:
            role_name = 'Administrateur'
        elif role_id == 3:
            role_name = 'Modérateur'
        
        # Stocker en session
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

# Routes pour les pages admin
@app.get("/admin/admin-login.html")
def admin_login_page():
    """Page de connexion admin"""
    return send_from_directory(ROOT, "admin/admin-login.html")

@app.get("/admin/admin-dashboard.html")
def admin_dashboard_page():
    """Page dashboard admin"""
    return send_from_directory(ROOT, "admin/admin-dashboard.html")

@app.get("/admin/dashboard.html")
def admin_dashboard_redirect():
    """Redirection vers admin-dashboard.html"""
    return send_from_directory(ROOT, "admin/admin-dashboard.html")

@app.get("/admin/clubs.html")
def admin_clubs_page():
    """Page de gestion des clubs (liste)"""
    return send_from_directory(ROOT, "admin/clubs.html")

@app.get("/admin/clubs-saison.html")
def admin_clubs_saison_page():
    """Page des clubs par saison"""
    return send_from_directory(ROOT, "admin/clubs-saison.html")

@app.get("/admin/clubs-new.html")
def admin_clubs_new_page():
    """Page de création d'un nouveau club"""
    return send_from_directory(ROOT, "admin/clubs-new.html")

@app.get("/admin/evenements.html")
def admin_evenements_page():
    """Page de gestion des événements"""
    return send_from_directory(ROOT, "admin/evenements.html")

@app.get("/admin/documents.html")
def admin_documents_page():
    """Page de gestion des documents"""
    return send_from_directory(ROOT, "admin/documents.html")

@app.get("/admin/messages.html")
def admin_messages_page():
    """Page de gestion des messages"""
    return send_from_directory(ROOT, "admin/messages.html")

@app.get("/admin/utilisateurs.html")
def admin_utilisateurs_page():
    """Page de gestion des utilisateurs"""
    return send_from_directory(ROOT, "admin/utilisateurs.html")

@app.get("/admin/sidebar.html")
def admin_sidebar():
    """Sidebar pour l'administration"""
    return send_from_directory(ROOT, "admin/sidebar.html")

# Route pour les fichiers CSS
@app.get("/admin/css/<path:filename>")
def admin_css(filename):
    """Sert les fichiers CSS de l'administration"""
    filepath = ROOT / "admin" / "css" / filename
    if not filepath.exists() or not filepath.is_file():
        abort(404)
    return send_from_directory(ROOT / "admin" / "css", filename)

# Route générique pour les autres fichiers statiques
@app.get("/<path:filename>")
def site_files(filename):
    """Sert les fichiers statiques"""
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
    """Réception du formulaire contact"""
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
    """Vérifie l'identifiant club dans la table `club` de la BDD"""
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
    """Déconnexion"""
    if request.method == "OPTIONS":
        return "", 204
    return jsonify({"success": True, "message": "Déconnexion effectuée."}), 200

# ============================================================
# ROUTES API - CLUBS (ADMIN) avec jointure secteur
# ============================================================

@app.route('/api/admin/clubs/count', methods=['GET'])
def get_clubs_count():
    """Retourne le nombre total de clubs"""
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

# ... (le reste de votre code reste identique jusqu'à la fin)



@app.route('/api/admin/clubs', methods=['GET'])
def get_clubs():
    """Récupère la liste des clubs avec pagination, recherche et jointure secteur"""
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
        
        # Requête avec jointure sur la table secteur
        query = """
            SELECT 
                c.id_club,
                c.identif_club,
                c.nom_club,
                c.representant,
                c.contact,
                c.grade,
                c.List_sect,
                s.nom_secteur as secteur,
                c.Num_declaration,
                c.created_At,
                c.update_At
            FROM club c
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur
        """
        
        params = []
        
        # Ajouter la recherche si présente
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
        
        # Ajouter la pagination (sauf si limit est très grand pour récupérer tout)
        if limit != 9999:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        clubs = cursor.fetchall()
        
        # Compter le total pour la pagination
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
    """Récupère un club par son ID avec jointure secteur"""
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
    """Récupère le dernier identifiant de club pour générer le suivant"""
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
    """Crée un nouveau club"""
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
            # C'est un nom, chercher l'id
            cursor.execute("SELECT id_secteur FROM secteur WHERE nom_secteur = %s", (list_sect,))
            result = cursor.fetchone()
            if result:
                list_sect = result[0]
            else:
                list_sect = None
        
        cursor.execute("""
            INSERT INTO club (
                identif_club,
                nom_club,
                representant,
                grade,
                contact,
                List_sect,
                Num_declaration,
                created_At,
                update_At
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, CURDATE(), NOW())
        """, (
            data.get('identif_club'),
            data.get('nom_club'),
            data.get('representant'),
            data.get('grade'),
            data.get('contact'),
            list_sect,
            data.get('Num_declaration')
        ))
        conn.commit()
        
        return jsonify({'success': True, 'id': cursor.lastrowid, 'message': 'Club créé avec succès'})
    except Exception as e:
        logger.error(f"Erreur create_club: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


@app.route('/api/admin/clubs/<int:club_id>', methods=['PUT'])
def update_club(club_id):
    """Met à jour un club"""
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
        
        cursor.execute("""
            UPDATE club SET
                identif_club = %s,
                nom_club = %s,
                representant = %s,
                grade = %s,
                contact = %s,
                List_sect = %s,
                Num_declaration = %s,
                update_At = NOW()
            WHERE id_club = %s
        """, (
            data.get('identif_club'),
            data.get('nom_club'),
            data.get('representant'),
            data.get('grade'),
            data.get('contact'),
            list_sect,
            data.get('Num_declaration'),
            club_id
        ))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Club mis à jour avec succès'})
    except Exception as e:
        logger.error(f"Erreur update_club: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

@app.route('/api/admin/clubs/<int:club_id>', methods=['DELETE'])
def delete_club(club_id):
    """Supprime un club"""
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
    """Bascule le statut d'un club (actif <-> inactif) - NE SUPPRIME PAS LE CLUB"""
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


@app.route('/api/admin/secteurs', methods=['GET'])
def get_secteurs():
    """Récupère la liste des secteurs"""
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


@app.route('/api/admin/grades', methods=['GET'])
def get_grades():
    """Récupère les grades"""
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
# ROUTES API - LICENCIES
# ============================================================

@app.route('/api/admin/licencies/count', methods=['GET'])
def get_licencies_count():
    """Retourne le nombre total de licenciés"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT COUNT(*) as count FROM licencie")
        result = cursor.fetchone()
        
        return jsonify({'success': True, 'count': result['count'] if result else 0})
    except Exception as e:
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
    """Retourne le nombre total d'événements"""
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
    """Récupère la liste des événements"""
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
    """Crée un nouvel événement"""
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
    """Met à jour un événement"""
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
    """Supprime un événement"""
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
    """Récupère un événement par son ID"""
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
    """Retourne le nombre de messages non lus"""
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
    """Récupère la liste des messages"""
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
    """Marque un message comme lu"""
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
    """Supprime un message"""
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
# ROUTES API - SAISONS ET CLUBS PAR SAISON
# ============================================================

@app.route('/api/admin/saisons', methods=['GET'])
def get_saisons():
    """Récupère la liste des saisons"""
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id_saison, libelle_saison FROM saison ORDER BY libelle_saison DESC")
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
# ROUTES ADMIN - GESTION DES UTILISATEURS (table users)
# ============================================================

@app.route('/api/admin/users', methods=['GET'])
def get_users():
    """Récupère la liste des utilisateurs"""
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
    """Crée un nouvel utilisateur"""
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor()
        
        # Vérifier si le login existe déjà
        cursor.execute("SELECT id FROM users WHERE login = %s", (data.get('login'),))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Ce login existe déjà'}), 409
        
        # Vérifier si l'email existe déjà
        if data.get('email'):
            cursor.execute("SELECT id FROM users WHERE email = %s", (data.get('email'),))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Cet email existe déjà'}), 409
        
        # Hacher le mot de passe
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
    """Met à jour un utilisateur"""
    data = request.get_json()
    conn = None
    cursor = None
    try:
        conn = get_db()
        if not conn:
            return jsonify({'success': False, 'message': 'Erreur de connexion BDD'}), 500
        
        cursor = conn.cursor()
        
        # Vérifier si le login existe déjà pour un autre utilisateur
        cursor.execute("SELECT id FROM users WHERE login = %s AND id != %s", (data.get('login'), user_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Ce login existe déjà'}), 409
        
        # Vérifier si l'email existe déjà pour un autre utilisateur
        if data.get('email'):
            cursor.execute("SELECT id FROM users WHERE email = %s AND id != %s", (data.get('email'), user_id))
            if cursor.fetchone():
                return jsonify({'success': False, 'message': 'Cet email existe déjà'}), 409
        
        # Construction dynamique de la requête
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
    """Supprime un utilisateur"""
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
    """Réinitialise le mot de passe d'un utilisateur"""
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
    print("=" * 50)
    app.run(host="127.0.0.1", port=5000, debug=True)