import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def test_db():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST", "localhost"),
            user=os.environ.get("DB_USER", "root"),
            password=os.environ.get("DB_PASSWORD", ""),
            database=os.environ.get("DB_NAME", "fiadekash")
        )
        cursor = conn.cursor(dictionary=True)
        query = """
            SELECT c.*, s.nom_secteur as secteur, COALESCE(g.libelle, c.grade) as grade_name
            FROM club c 
            LEFT JOIN secteur s ON c.List_sect = s.id_secteur 
            LEFT JOIN grade g ON (c.grade REGEXP '^[0-9]+$') AND (c.grade = g.id_grade)
            ORDER BY s.nom_secteur ASC, c.nom_club ASC
        """
        cursor.execute(query)
        clubs = cursor.fetchall()
        print(f"Success! Found {len(clubs)} clubs.")
        if len(clubs) > 0:
            print("First club:", clubs[0]['nom_club'])
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_db()
