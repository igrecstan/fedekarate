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
            
        saison_ids = tuple(s[0] for s in saisons)
        if len(saison_ids) == 1:
            ids_str = f"({saison_ids[0]})"
        else:
            ids_str = str(saison_ids)
            
        # Update Clubs
        cursor.execute(f"UPDATE club SET statut = 'inactif' WHERE id_club NOT IN (SELECT List_club FROM clubs_saison WHERE List_saison IN {ids_str})")
        cursor.execute(f"UPDATE club SET statut = 'actif' WHERE id_club IN (SELECT List_club FROM clubs_saison WHERE List_saison IN {ids_str})")
        
        # Update Athletes (Licenciés)
        cursor.execute(f"UPDATE athletes SET statut = 'inactif' WHERE id_ath NOT IN (SELECT list_ath FROM athletes_saison WHERE list_saison IN {ids_str})")
        cursor.execute(f"UPDATE athletes SET statut = 'actif' WHERE id_ath IN (SELECT list_ath FROM athletes_saison WHERE list_saison IN {ids_str})")
            
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
