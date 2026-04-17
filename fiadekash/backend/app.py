# backend/app.py
import os
import sys
from flask import Flask, send_from_directory, jsonify, request
from flask_cors import CORS

# Ajouter le dossier courant au path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from routes.auth import auth_bp
from routes.clubs import clubs_bp
from routes.events import events_bp
from routes.documents import documents_bp
from routes.messages import messages_bp

app = Flask(__name__)
app.config.from_object(Config)

# Configuration CORS
CORS(app, origins='*', supports_credentials=True)

# Enregistrement des blueprints
app.register_blueprint(auth_bp)
app.register_blueprint(clubs_bp)
app.register_blueprint(events_bp)
app.register_blueprint(documents_bp)
app.register_blueprint(messages_bp)

# Servir les fichiers uploadés
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(Config.UPLOAD_FOLDER, filename)

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'API FI-ADEKASH en ligne'})

@app.route('/test', methods=['GET'])
def test():
    return jsonify({'message': 'Le serveur fonctionne correctement!'})

@app.route('/routes', methods=['GET'])
def list_routes():
    """Liste toutes les routes disponibles"""
    routes = []
    for rule in app.url_map.iter_rules():
        methods = ','.join(sorted(rule.methods - {'HEAD', 'OPTIONS'}))
        routes.append({
            'endpoint': rule.endpoint,
            'methods': methods,
            'url': str(rule)
        })
    return jsonify({
        'routes': routes,
        'total': len(routes)
    })

if __name__ == '__main__':
    # Créer les dossiers nécessaires
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    
    print("=" * 60)
    print("🚀 Démarrage du serveur API FI-ADEKASH")
    print("=" * 60)
    print(f"📍 URL: http://localhost:5000")
    print(f"📁 Uploads: {Config.UPLOAD_FOLDER}")
    print("=" * 60)
    print("\nRoutes disponibles:")
    
    app.run(host='0.0.0.0', port=5000, debug=True)