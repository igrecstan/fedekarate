import mysql.connector
from db_utils import get_db_connection

def check_athlete():
    conn = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM athletes WHERE id_ath = 924")
        athlete = cursor.fetchone()
        print(f"Athlete 924: {athlete}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        if conn: conn.close()

if __name__ == "__main__":
    check_athlete()
