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

@public_bp.route("/<path:filename>")
def site_files(filename):
    if '..' in filename or filename.startswith('/'):
        abort(404)
    filepath = ROOT / filename
    if not filepath.exists() or not filepath.is_file():
        abort(404)
    return send_from_directory(ROOT, filename)
