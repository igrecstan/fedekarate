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
cursor.execute("DESCRIBE athletes")
columns = cursor.fetchall()
print("Columns in athletes:")
for c in columns:
    print(f"- {c[0]}")
cursor.close()
conn.close()
