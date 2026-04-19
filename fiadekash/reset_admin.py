"""
Script utilitaire — Créer / réinitialiser le mot de passe admin
Lancer : python reset_admin.py
"""
import os
import bcrypt
import mysql.connector

# ── Paramètres BDD ─────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = int(os.getenv("DB_PORT", 3306))
DB_USER     = os.getenv("DB_USER",     "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")        # mot de passe MySQL root
DB_NAME     = os.getenv("DB_NAME",     "fiadekash")

# ── Nouveaux identifiants admin ────────────────────────────
ADMIN_LOGIN    = "admin"
ADMIN_PASSWORD = "fiadekash2025"   # ← changez ici si besoin

def main():
    print("=== FI-ADEKASH — Reset mot de passe admin ===\n")

    # Connexion MySQL
    try:
        db = mysql.connector.connect(
            host=DB_HOST, port=DB_PORT,
            user=DB_USER, password=DB_PASSWORD,
            database=DB_NAME, charset="utf8mb4"
        )
        print("✅ Connexion MySQL OK")
    except mysql.connector.Error as e:
        print(f"❌ Erreur connexion MySQL : {e}")
        print("\nVérifiez DB_USER / DB_PASSWORD dans ce fichier.")
        return

    # Générer le hash bcrypt
    password_hash = bcrypt.hashpw(ADMIN_PASSWORD.encode(), bcrypt.gensalt()).decode()
    print(f"✅ Hash généré pour '{ADMIN_PASSWORD}'")

    cur = db.cursor(dictionary=True)

    # Vérifier si l'admin existe
    cur.execute("SELECT id FROM users WHERE login = %s", (ADMIN_LOGIN,))
    existing = cur.fetchone()

    if existing:
        # Mettre à jour
        cur.execute(
            "UPDATE users SET password_hash = %s WHERE login = %s",
            (password_hash, ADMIN_LOGIN)
        )
        db.commit()
        print(f"✅ Mot de passe mis à jour pour '{ADMIN_LOGIN}'")
    else:
        # Créer l'admin s'il n'existe pas
        cur.execute(
            """INSERT INTO users (nom, prenom, email, login, password_hash, role_id)
               VALUES (%s, %s, %s, %s, %s, 1)""",
            ("ADEKASH", "Admin", "admin@fi-adekash.ci", ADMIN_LOGIN, password_hash)
        )
        db.commit()
        print(f"✅ Admin '{ADMIN_LOGIN}' créé avec succès")

    cur.close()
    db.close()
    print(f"\n🎉 Vous pouvez maintenant vous connecter avec :")
    print(f"   Login    : {ADMIN_LOGIN}")
    print(f"   Password : {ADMIN_PASSWORD}")

if __name__ == "__main__":
    main()
