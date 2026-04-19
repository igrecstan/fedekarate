import csv
import mysql.connector
from datetime import datetime
import os

# Configuration de la base de données
db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',  # Laissez vide pour XAMPP
    'database': 'fiadekash'
}

def convert_date(date_str):
    """Convertit une date au format DD/MM/YYYY en YYYY-MM-DD"""
    if not date_str or date_str == '00-00-00':
        return None
    
    try:
        # Format: 19/02/2022
        if '/' in date_str:
            day, month, year = date_str.split('/')
            return f"{year}-{month}-{day}"
        # Format: 19-02-2022
        elif '-' in date_str:
            day, month, year = date_str.split('-')
            return f"{year}-{month}-{day}"
    except:
        pass
    return None

def create_table(cursor):
    """Crée la table clubs_saison si elle n'existe pas"""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS `clubs_saison` (
      `id_clubSaison` int(11) NOT NULL AUTO_INCREMENT,
      `List_saison` int(11) DEFAULT NULL,
      `List_club` int(11) DEFAULT NULL,
      `List_sect` int(11) DEFAULT NULL,
      `created_At` date DEFAULT NULL,
      `update_At` datetime NOT NULL DEFAULT current_timestamp(),
      PRIMARY KEY (`id_clubSaison`),
      KEY `idx_list_saison` (`List_saison`),
      KEY `idx_list_club` (`List_club`),
      KEY `idx_list_sect` (`List_sect`)
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_general_ci
    """
    
    try:
        cursor.execute(create_table_sql)
        print("✅ Table 'clubs_saison' créée ou existe déjà")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la création de la table : {e}")
        return False

def import_csv_to_mysql(csv_file):
    """Importe les données du CSV vers MySQL"""
    
    # Vérifier si le fichier existe
    if not os.path.exists(csv_file):
        print(f"❌ Fichier non trouvé : {csv_file}")
        return False
    
    try:
        # Connexion à MySQL
        connection = mysql.connector.connect(**db_config)
        cursor = connection.cursor()
        print("✅ Connexion MySQL réussie")
        
        # Créer la table
        if not create_table(cursor):
            return False
        
        # Vider la table (optionnel - décommentez si besoin)
        # cursor.execute("TRUNCATE TABLE clubs_saison")
        # print("🗑️ Table vidée")
        
        # Lecture du CSV
        with open(csv_file, 'r', encoding='utf-8-sig') as file:
            # Lire l'en-tête
            reader = csv.DictReader(file, delimiter=';')
            
            # Afficher les noms des colonnes
            print(f"\nNoms des colonnes : {list(reader.fieldnames)}")
            
            # Préparer la requête d'insertion
            insert_query = """
            INSERT INTO clubs_saison 
            (id_clubSaison, List_saison, List_club, List_sect, created_At, update_At) 
            VALUES (%s, %s, %s, %s, %s, NOW())
            """
            
            count = 0
            errors = 0
            
            for row in reader:
                # Extraire les valeurs
                id_clubSaison = row.get('id_clubSaison')
                list_saison = row.get('List_saison')
                list_club = row.get('List_club')
                list_sect = row.get('List_sect')
                created_at_str = row.get('created_At')
                
                # Vérifier que l'id existe
                if not id_clubSaison:
                    print(f"⚠️ Ligne ignorée - id_clubSaison manquant: {row}")
                    errors += 1
                    continue
                
                # Convertir la date
                created_at = convert_date(created_at_str)
                
                values = (
                    id_clubSaison,
                    list_saison if list_saison else None,
                    list_club if list_club else None,
                    list_sect if list_sect else None,
                    created_at
                )
                
                try:
                    cursor.execute(insert_query, values)
                    count += 1
                    
                    # Afficher la progression
                    if count % 50 == 0:
                        print(f"📥 {count} lignes importées...")
                        
                except Exception as e:
                    errors += 1
                    print(f"❌ Erreur ligne {count + errors}: {e}")
                    print(f"   Valeurs: {values}")
            
            # Valider les changements
            connection.commit()
            
            print(f"\n{'='*50}")
            print(f"📊 Récapitulatif de l'importation :")
            print(f"✅ Lignes importées : {count}")
            print(f"❌ Lignes en erreur : {errors}")
            print(f"📁 Fichier source : {csv_file}")
            print(f"{'='*50}")
            
            return True
            
    except mysql.connector.Error as err:
        print(f"❌ Erreur MySQL : {err}")
        return False
    except Exception as e:
        print(f"❌ Erreur générale : {e}")
        return False
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("\n🔌 Connexion MySQL fermée")

def verify_import(cursor):
    """Vérifie que les données ont bien été importées"""
    cursor.execute("SELECT COUNT(*) FROM clubs_saison")
    count = cursor.fetchone()[0]
    
    cursor.execute("SELECT MIN(created_At), MAX(created_At) FROM clubs_saison")
    min_date, max_date = cursor.fetchone()
    
    print(f"\n📊 Vérification :")
    print(f"   Total d'enregistrements : {count}")
    print(f"   Période : du {min_date} au {max_date}")
    
    # Afficher un échantillon
    cursor.execute("SELECT * FROM clubs_saison LIMIT 5")
    sample = cursor.fetchall()
    print(f"\n📋 Échantillon des données :")
    for row in sample:
        print(f"   {row}")

if __name__ == "__main__":
    print("="*50)
    print("📥 IMPORTATION DES DONNÉES CLUBS SAISON")
    print("="*50)
    
    # Spécifier le chemin du fichier CSV
    csv_file_path = "clubs_saison.csv"  # Modifier si nécessaire
    
    # Si le fichier n'existe pas, demander le chemin
    if not os.path.exists(csv_file_path):
        print(f"\n⚠️ Fichier '{csv_file_path}' non trouvé dans le dossier courant")
        csv_file_path = input("Entrez le chemin complet du fichier CSV: ").strip()
    
    # Importer les données
    success = import_csv_to_mysql(csv_file_path)
    
    if success:
        # Vérification optionnelle
        try:
            connection = mysql.connector.connect(**db_config)
            cursor = connection.cursor()
            verify_import(cursor)
            cursor.close()
            connection.close()
        except:
            pass
    
    print("\n✨ Script terminé !")