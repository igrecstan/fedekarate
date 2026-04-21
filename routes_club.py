import logging
from flask import Blueprint, jsonify, request
from db_utils import get_db_connection
from mysql.connector import Error

club_bp = Blueprint('club_api', __name__, url_prefix='/api/club')
logger = logging.getLogger(__name__)

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
        
        return jsonify({
            "success": True,
            "club_id": club["identif_club"],
            "nom_club": club.get("nom_club"),
            "representant": club.get("representant")
        }), 200
    except Exception as e:
        logger.error(f"Erreur api_club_login: {e}")
        return jsonify({"success": False, "message": str(e)}), 500
    finally:
        if cursor: cursor.close()
        if conn: conn.close()

@club_bp.route("/logout", methods=["POST"])
def api_club_logout():
    return jsonify({"success": True, "message": "Déconnecté."}), 200
