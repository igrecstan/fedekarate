import os
import logging
from flask import Flask
from routes_admin import admin_bp
from routes_club import club_bp
from routes_public import public_bp
from routes_licencies import licencies_bp

# Configuration logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "fiadekash-secret-key-2024-secure")

# Enregistrement des Blueprints
app.register_blueprint(admin_bp)
app.register_blueprint(club_bp)
app.register_blueprint(licencies_bp)
app.register_blueprint(public_bp) # À enregistrer en dernier car il gère les fichiers statiques par défaut

@app.after_request
def _cors_api_dev(response):
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS, GET, PUT, DELETE"
    return response

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)