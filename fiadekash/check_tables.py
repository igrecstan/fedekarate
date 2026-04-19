# check_tables.py
import mysql.connector
from dotenv import load_dotenv
import os

load_dotenv()

conn = mysql.connector.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", 3306)),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "fiadekash")
)

cursor = conn.cursor()

print("=" * 50)
print("VÉRIFICATION DES TABLES")
print("=" * 50)

# Vérifier les roles
cursor.execute("SELECT id, nom, is_super FROM roles")
roles = cursor.fetchall()
print(f"\n📋 ROLES ({len(roles)}):")
for r in roles:
    print(f"   - id:{r[0]}, nom:{r[1]}, is_super:{r[2]}")

# Vérifier les permissions
cursor.execute("SELECT id, nom, slug FROM permissions")
permissions = cursor.fetchall()
print(f"\n📋 PERMISSIONS ({len(permissions)}):")
for p in permissions[:10]:  # Afficher les 10 premières
    print(f"   - id:{p[0]}, nom:{p[1]}, slug:{p[2]}")
if len(permissions) > 10:
    print(f"   ... et {len(permissions)-10} autres")

# Vérifier les role_permissions
cursor.execute("SELECT COUNT(*) FROM role_permissions")
rp_count = cursor.fetchone()[0]
print(f"\n📋 ROLE_PERMISSIONS: {rp_count} associations")

# Vérifier l'utilisateur admin
cursor.execute("""
    SELECT u.id, u.login, u.nom, u.prenom, u.email, u.actif, r.nom as role_nom, r.is_super
    FROM users u
    LEFT JOIN roles r ON u.role_id = r.id
    WHERE u.login = 'admin'
""")
admin = cursor.fetchone()

print(f"\n👤 ADMIN:")
if admin:
    print(f"   - id: {admin[0]}")
    print(f"   - login: {admin[1]}")
    print(f"   - nom: {admin[2]}")
    print(f"   - prenom: {admin[3]}")
    print(f"   - email: {admin[4]}")
    print(f"   - actif: {admin[5]}")
    print(f"   - rôle: {admin[6]}")
    print(f"   - is_super: {admin[7]}")
else:
    print("   ❌ Admin non trouvé ! Exécutez python create_admin.py")

cursor.close()
conn.close()