import csv
import mysql.connector
from datetime import datetime

db_config = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'fiadekash'
}

def convert_french_date(date_str):
    months = {
        'janv': '01', 'févr': '02', 'mars': '03', 'avr': '04',
        'mai': '05', 'juin': '06', 'juil': '07', 'août': '08',
        'sept': '09', 'oct': '10', 'nov': '11', 'déc': '12'
    }
    
    if not date_str or date_str == '00-00-00':
        return None
    
    try:
        parts = date_str.split('-')
        if len(parts) == 3:
            day = parts[0].zfill(2)
            month = months.get(parts[1][:4], '01')
            year = parts[2]
            if len(year) == 2:
                year = '20' + year if int(year) < 30 else '19' + year
            return f"{year}-{month}-{day}"
    except:
        pass
    return None

try:
    connection = mysql.connector.connect(**db_config)
    cursor = connection.cursor()
    print("✅ Connexion MySQL réussie")
    
    with open('club.csv', 'r', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file, delimiter=';')
        
        # Mapping des colonnes (utilise .get() pour éviter KeyError)
        count = 0
        for row in reader:
            # Extraire les valeurs avec .get()
            id_club = row.get('id_club')
            list_sect = row.get('List_sect')
            nom_club = row.get('NOM DU CLUB')
            num_club = row.get('NUM CLUB')
            nom_prenoms = row.get('NOM ET PRENOMS')
            grade = row.get('GRADE')
            contact = row.get('CONTACTS')
            whatsapp = row.get('WHATSAPP')
            email = row.get('EMAIL')
            declaration = row.get('N° DE DECLARATION')
            dates = row.get('DATES')
            
            # Vérifier que les données essentielles existent
            if not id_club or not nom_club:
                print(f"⚠️ Ligne ignorée - données manquantes: {row}")
                continue
            
            created_at = convert_french_date(dates)
            
            sql = """INSERT INTO club (
                id_club, List_sect, `nom du club`, `num club`, `nom et prenoms`,
                grade, contact, whatapps, email, `N° declaration`, created_At, update_At
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())"""
            
            values = (
                id_club, list_sect, nom_club, num_club, nom_prenoms,
                grade, contact, whatsapp, email if email else None, 
                declaration if declaration else None, created_at
            )
            
            try:
                cursor.execute(sql, values)
                count += 1
                if count % 10 == 0:  # Afficher tous les 10 imports
                    print(f"✅ {count} lignes importées...")
            except Exception as e:
                print(f"❌ Erreur ligne {count+1}: {e}")
                print(f"   Club: {nom_club}")
    
    connection.commit()
    print(f"\n✅ Import terminé ! {count} lignes importées avec succès")
    
except Exception as e:
    print(f"❌ Erreur : {e}")
finally:
    if 'connection' in locals() and connection.is_connected():
        cursor.close()
        connection.close()