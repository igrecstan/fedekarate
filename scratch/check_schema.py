
import mysql.connector
from db_utils import get_db_connection

conn = get_db_connection()
cursor = conn.cursor()

tables = ['saison', 'club', 'athletes', 'clubs_saison', 'athletes_saison', 'secteur', 'grade']

for table in tables:
    print(f"\n--- Structure of {table} ---")
    try:
        cursor.execute(f"DESCRIBE {table}")
        for row in cursor.fetchall():
            print(row)
    except Exception as e:
        print(f"Error describing {table}: {e}")

cursor.close()
conn.close()
