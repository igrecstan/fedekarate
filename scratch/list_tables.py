import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "fiadekash")
)

cursor = conn.cursor()
cursor.execute("SHOW TABLES")
tables = cursor.fetchall()
print("Tables in fiadekash:")
for t in tables:
    print(f"- {t[0]}")
cursor.close()
conn.close()
