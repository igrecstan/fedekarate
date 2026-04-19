# create_admin.py
import bcrypt
import mysql.connector
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()

def create_admin():
    conn = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", 3306)),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "fiadekash")
    )
    cursor = conn.cursor()
    
    # 1. Créer les permissions de base
    permissions = [
        ('admin_access', 'admin.access', 'Accès à l\'administration'),
        ('clubs_view', 'clubs.view', 'Voir les clubs'),
        ('clubs_create', 'clubs.create', 'Créer des clubs'),
        ('clubs_edit', 'clubs.edit', 'Modifier les clubs'),
        ('clubs_delete', 'clubs.delete', 'Supprimer les clubs'),
        ('users_view', 'users.view', 'Voir les utilisateurs'),
        ('users_create', 'users.create', 'Créer des utilisateurs'),
        ('users_edit', 'users.edit', 'Modifier les utilisateurs'),
        ('users_delete', 'users.delete', 'Supprimer les utilisateurs'),
        ('events_view', 'events.view', 'Voir les événements'),
        ('events_create', 'events.create', 'Créer des événements'),
        ('events_edit', 'events.edit', 'Modifier les événements'),
        ('events_delete', 'events.delete', 'Supprimer les événements'),
        ('documents_view', 'documents.view', 'Voir les documents'),
        ('documents_upload', 'documents.upload', 'Uploader des documents'),
        ('documents_delete', 'documents.delete', 'Supprimer des documents'),
        ('messages_view', 'messages.view', 'Voir les messages'),
        ('messages_delete', 'messages.delete', 'Supprimer des messages'),
    ]
    
    permission_ids = {}
    for nom, slug, desc in permissions:
        cursor.execute("""
            INSERT INTO permissions (nom, slug, description) 
            VALUES (%s, %s, %s)
            ON DUPLICATE KEY UPDATE nom = VALUES(nom)
        """, (nom, slug, desc))
        
        cursor.execute("SELECT id FROM permissions WHERE slug = %s", (slug,))
        perm = cursor.fetchone()
        if perm:
            permission_ids[slug] = perm[0]
    
    print(f"✓ {len(permissions)} permissions créées/vérifiées")
    
    # 2. Créer le rôle admin (avec is_super = 1)
    cursor.execute("SELECT id FROM roles WHERE nom = 'admin'")
    role = cursor.fetchone()
    
    if not role:
        cursor.execute("""
            INSERT INTO roles (nom, description, is_super, created_at, updated_at) 
            VALUES ('admin', 'Administrateur avec tous les droits', 1, NOW(), NOW())
        """)
        conn.commit()
        role_id = cursor.lastrowid
        print("✓ Rôle 'admin' créé (super admin)")
    else:
        role_id = role[0]
        # Mettre à jour is_super = 1
        cursor.execute("""
            UPDATE roles SET is_super = 1, updated_at = NOW() 
            WHERE id = %s
        """, (role_id,))
        conn.commit()
        print("✓ Rôle 'admin' existant (mis à jour super admin)")
    
    # 3. Attribuer toutes les permissions au rôle admin
    for slug, perm_id in permission_ids.items():
        cursor.execute("""
            INSERT IGNORE INTO role_permissions (role_id, permission_id) 
            VALUES (%s, %s)
        """, (role_id, perm_id))
    conn.commit()
    print(f"✓ {len(permission_ids)} permissions attribuées au rôle admin")
    
    # 4. Hasher le mot de passe
    password = "fiadekash2025"
    hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    # 5. Créer ou mettre à jour l'utilisateur admin
    cursor.execute("""
        SELECT id FROM users WHERE login = 'admin'
    """)
    existing_user = cursor.fetchone()
    
    if existing_user:
        cursor.execute("""
            UPDATE users 
            SET nom = %s, prenom = %s, email = %s, password_hash = %s, 
                role_id = %s, actif = 1, updated_at = NOW()
            WHERE login = 'admin'
        """, ("Administrateur", "Super", "admin@fiadekash.com", hashed.decode('utf-8'), role_id))
        print("✓ Utilisateur admin mis à jour")
    else:
        cursor.execute("""
            INSERT INTO users (nom, prenom, email, login, password_hash, role_id, actif, created_at, updated_at) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
        """, ("Administrateur", "Super", "admin@fiadekash.com", "admin", hashed.decode('utf-8'), role_id, 1))
        print("✓ Utilisateur admin créé")
    
    conn.commit()
    
    print("\n" + "=" * 50)
    print("✓ Admin créé/mis à jour avec succès !")
    print("=" * 50)
    print(f"  Login    : admin")
    print(f"  Password : {password}")
    print(f"  Email    : admin@fiadekash.com")
    print(f"  Nom      : Administrateur")
    print(f"  Prénom   : Super")
    print(f"  Rôle     : admin (super admin)")
    print(f"  Permissions : {len(permission_ids)} permissions")
    print("=" * 50)
    
    cursor.close()
    conn.close()

if __name__ == "__main__":
    create_admin()