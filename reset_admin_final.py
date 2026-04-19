import mysql.connector
import bcrypt
import os
from dotenv import load_dotenv

load_dotenv()

conn = mysql.connector.connect(
    host=os.environ.get("DB_HOST", "localhost"),
    port=int(os.environ.get("DB_PORT", 3306)),
    user=os.environ.get("DB_USER", "root"),
    password=os.environ.get("DB_PASSWORD", ""),
    database=os.environ.get("DB_NAME", "fiadekash"),
)

cursor = conn.cursor()

# Vérifier la structure de la table users
cursor.execute("SHOW TABLES LIKE 'users'")
if not cursor.fetchone():
    print("❌ La table 'users' n'existe pas!")
    print("   Veuillez d'abord créer la table users avec la commande SQL appropriée.")
    exit(1)

# Vérifier les colonnes
cursor.execute("DESCRIBE users")
columns = [col[0] for col in cursor.fetchall()]
print(f"Colonnes trouvées: {columns}")

if 'password_hash' not in columns:
    print("❌ La colonne 'password_hash' n'existe pas!")
    print("   Ajoutez-la avec: ALTER TABLE users ADD COLUMN password_hash VARCHAR(255);")
    exit(1)

# Créer ou mettre à jour l'admin
password = "fiadekash2025"
hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
hashed_str = hashed.decode('utf-8')

# Vérifier si l'admin existe
cursor.execute("SELECT id FROM users WHERE login = 'admin'")
admin = cursor.fetchone()

if admin:
    cursor.execute("UPDATE users SET password_hash = %s, actif = 1 WHERE login = 'admin'", (hashed_str,))
    print(f"✅ Admin mis à jour avec mot de passe: {password}")
else:
    # Vérifier quelles colonnes sont disponibles
    insert_fields = ['login', 'password_hash', 'actif']
    insert_values = ['admin', hashed_str, 1]
    
    if 'nom' in columns:
        insert_fields.append('nom')
        insert_values.append('Administrateur')
    if 'prenom' in columns:
        insert_fields.append('prenom')
        insert_values.append('Admin')
    if 'role_id' in columns:
        insert_fields.append('role_id')
        insert_values.append(1)
    if 'created_at' in columns:
        insert_fields.append('created_at')
        insert_values.append('NOW()')
    
    query = f"INSERT INTO users ({', '.join(insert_fields)}) VALUES ({', '.join(['%s'] * len(insert_values))})"
    # Remplacer 'NOW()' par la fonction SQL
    if 'created_at' in columns:
        query = query.replace("'NOW()'", "NOW()")
    
    cursor.execute(query, insert_values)
    print(f"✅ Admin créé avec mot de passe: {password}")

conn.commit()
cursor.close()
conn.close()

print("\n🎉 Vous pouvez maintenant vous connecter avec :")
print("   Login    : admin")
print(f"   Password : {password}")
print("\n👉 Redémarrez le serveur Flask puis connectez-vous")