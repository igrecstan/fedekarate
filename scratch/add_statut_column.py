from db_utils import get_db
import logging

def add_status_column():
    conn = get_db()
    if not conn:
        print("Erreur de connexion")
        return
    try:
        cursor = conn.cursor()
        cursor.execute("ALTER TABLE athletes ADD COLUMN statut VARCHAR(10) DEFAULT 'actif'")
        conn.commit()
        print("Colonne statut ajoutée avec succès")
    except Exception as e:
        print(f"Erreur: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_status_column()
