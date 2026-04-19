import re
from datetime import datetime
import mysql.connector
from mysql.connector import Error

def convert_date(date_str):
    dt = datetime.strptime(date_str.strip(), '%d/%m/%Y')
    return dt.strftime('%Y-%m-%d')

# Lecture du fichier
with open('donnees.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

updates = []
for line in lines:
    line = line.strip()
    if not line:
        continue
    parts = re.split(r'[\t\s]+', line)
    if len(parts) >= 2:
        date_raw = parts[0]
        id_raw = parts[1]
        if id_raw.isdigit():
            updates.append((int(id_raw), convert_date(date_raw)))

print(f"{len(updates)} lignes à mettre à jour")

# Connexion à la BDD
try:
    conn = mysql.connector.connect(
        host='localhost',
        user='root',
        password='',
        database='fiadekash'
    )


    cursor = conn.cursor()
    
    # Exécution par lots de 150
    batch_size = 150
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        print(f"Traitement du lot {i//batch_size + 1}...")
        
        for id_val, date_val in batch:
            sql = "UPDATE athletes_saison SET created_at = %s WHERE id_athsaison = %s"
            cursor.execute(sql, (date_val, id_val))
        
        conn.commit()
        print(f"  ✅ Lot {i//batch_size + 1} terminé")
    
    cursor.close()
    conn.close()
    print("✅ Mise à jour terminée")
    
except Error as e:
    print(f"❌ Erreur: {e}")