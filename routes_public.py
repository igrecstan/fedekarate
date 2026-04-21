import logging
from flask import Blueprint, send_from_directory, request, jsonify, abort
from pathlib import Path
from db_utils import get_db_connection

public_bp = Blueprint('public', __name__)
logger = logging.getLogger(__name__)
ROOT = Path(__file__).resolve().parent

@public_bp.route("/")
def index():
    return send_from_directory(ROOT, "index.html")

@public_bp.route("/api/contact", methods=["POST"])
def api_contact():
    data = request.get_json(silent=True) or {}
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO messages (nom, email, message, date_creation) 
                VALUES (%s, %s, %s, NOW())
            """, (data.get('nom', ''), data.get('email', ''), data.get('message', '')))
            conn.commit()
            cursor.close()
            conn.close()
    except Exception as e:
        logger.error(f"Erreur sauvegarde message: {e}")
    
    return jsonify({"ok": True, "message": "Message reçu."})

@public_bp.route("/api/seasons-summary")
def api_seasons_summary():
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            # Compter les clubs par saison
            cursor.execute("""
                SELECT s.id_saison, s.libelle_saison, COUNT(cs.List_club) as club_count
                FROM saison s
                LEFT JOIN clubs_saison cs ON s.id_saison = cs.List_saison
                GROUP BY s.id_saison, s.libelle_saison
                ORDER BY s.id_saison DESC
            """)
            seasons = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "seasons": seasons})
    except Exception as e:
        logger.error(f"Erreur api_seasons_summary: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    return jsonify({"success": False, "message": "Erreur BDD"}), 500

@public_bp.route("/api/clubs")
def api_clubs():
    saison_id = request.args.get('saison', type=int)
    try:
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            query = """
                SELECT c.nom_club, c.identif_club, c.representant, s.nom_secteur as secteur, g.libelle as grade
                FROM club c
                LEFT JOIN secteur s ON c.List_sect = s.id_secteur
                LEFT JOIN grade g ON c.grade = g.id_grade
            """
            
            if saison_id:
                query = """
                    SELECT c.nom_club, c.identif_club, c.representant, s.nom_secteur as secteur, g.libelle as grade
                    FROM clubs_saison cs
                    JOIN club c ON cs.List_club = c.id_club
                    LEFT JOIN secteur s ON cs.List_sect = s.id_secteur
                    LEFT JOIN grade g ON c.grade = g.id_grade
                    WHERE cs.List_saison = %s
                """
                cursor.execute(query, (saison_id,))
            else:
                query += " WHERE c.statut = 'actif'"
                cursor.execute(query)
                
            clubs = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify({"success": True, "clubs": clubs})
    except Exception as e:
        logger.error(f"Erreur api_clubs: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    return jsonify({"success": False, "message": "Erreur BDD"}), 500

@public_bp.route("/<path:filename>")
def site_files(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    filepath = ROOT / filename
    if not filepath.exists() or not filepath.is_file():
        abort(404)
    return send_from_directory(ROOT, filename)
