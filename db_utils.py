import os
import logging
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

logger = logging.getLogger(__name__)

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
        return conn
    except Error as e:
        logger.error(f"Erreur de connexion à la BDD: {e}")
        return None

def update_activity_statuses(conn):
    """Met à jour le statut des clubs et licenciés: actif ou inactif si absent des 2 dernières saisons."""
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT id_saison FROM saison ORDER BY id_saison DESC LIMIT 2")
        saisons = cursor.fetchall()
        if not saisons:
            cursor.close()
            return
            
        saison_ids = [s[0] for s in saisons]
        ids_str = ",".join(map(str, saison_ids))
            
        # Update Clubs - Utilisation d'une requête plus performante
        cursor.execute(f"""
            UPDATE club c
            LEFT JOIN (SELECT DISTINCT List_club FROM clubs_saison WHERE List_saison IN ({ids_str})) active 
            ON c.id_club = active.List_club
            SET c.statut = IF(active.List_club IS NULL, 'inactif', 'actif')
        """)
        
        # Update Athletes (Licenciés)
        cursor.execute(f"""
            UPDATE athletes a
            LEFT JOIN (SELECT DISTINCT list_ath FROM athletes_saison WHERE list_saison IN ({ids_str})) active 
            ON a.id_ath = active.list_ath
            SET a.statut = IF(active.list_ath IS NULL, 'inactif', 'actif')
        """)
            
        conn.commit()
        cursor.close()
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des statuts: {e}")

def get_db_connection():
    """Alias pour get_db() - retourne une connexion MySQL et met à jour les statuts"""
    conn = get_db()
    if conn:
        update_activity_statuses(conn)
    return conn
