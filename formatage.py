import re
from datetime import datetime

# ========== 1. NETTOYAGE ET CONVERSION DES DATES ==========

def convert_date_format(date_str):
    """
    Convertit une date du format '19/02/2023' vers '2023-02-19' (format attendu par ta BDD)
    """
    try:
        # Nettoyer la chaîne (enlever espaces)
        date_str = date_str.strip()
        # Essayer le format DD/MM/YYYY
        dt = datetime.strptime(date_str, '%d/%m/%Y')
        # Retourner au format YYYY-MM-DD (avec tiret comme demandé)
        return dt.strftime('%Y-%m-%d')
    except ValueError:
        try:
            # Essayer le format YYYY/MM/DD
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt.strftime('%Y-%m-%d')
        except ValueError:
            print(f"⚠️ Format de date non reconnu : {date_str}")
            return None

# ========== 2. LIRE LES DONNÉES DEPUIS LE FICHIER ==========

# Lire depuis le fichier donnees.txt
try:
    with open('donnees.txt', 'r', encoding='utf-8') as f:
        raw_data = f.read()
    print("✅ Fichier 'donnees.txt' lu avec succès")
except FileNotFoundError:
    print("❌ Fichier 'donnees.txt' non trouvé !")
    print("👉 Crée d'abord le fichier avec les données")
    exit(1)

# ========== 3. PARSER LES LIGNES ==========

updates = []
lines = raw_data.strip().split('\n')

for line in lines:
    line = line.strip()
    if not line:
        continue
    
    # Séparer par tabulation ou espace
    parts = re.split(r'[\t\s]+', line)
    if len(parts) >= 2:
        date_raw = parts[0].strip()
        id_raw = parts[1].strip()
        
        # Convertir la date
        date_converted = convert_date_format(date_raw)
        
        if date_converted and id_raw.isdigit():
            updates.append((int(id_raw), date_converted))

print(f"📊 {len(updates)} lignes valides parsées")

if len(updates) == 0:
    print("❌ Aucune donnée valide trouvée !")
    exit(1)

# ========== 4. GÉNÉRER LA REQUÊTE SQL PAR BLOCS ==========

def generate_update_queries(updates, batch_size=150):
    """
    Génère des requêtes UPDATE par lots
    """
    queries = []
    
    for i in range(0, len(updates), batch_size):
        batch = updates[i:i+batch_size]
        
        # Construire le CASE WHEN
        case_when = '\n    '.join([f"WHEN {id_val} THEN '{date_val}'" for id_val, date_val in batch])
        ids_list = ','.join([str(id_val) for id_val, _ in batch])
        
        query = f"""UPDATE `athletes_saison` 
SET `created_at` = CASE `id_athsaison`
    {case_when}
END
WHERE `id_athsaison` IN ({ids_list});"""
        
        queries.append(query)
    
    return queries

# Générer les requêtes
queries = generate_update_queries(updates, batch_size=150)

print(f"📦 {len(queries)} requêtes générées (par lots de 150)")

# ========== 5. SAUVEGARDER LES REQUÊTES ==========

# Sauvegarder dans un fichier
with open('update_queries.sql', 'w', encoding='utf-8') as f:
    for i, query in enumerate(queries):
        f.write(f"-- Bloc {i+1} (IDs {updates[i*150][0]} à {updates[min((i+1)*150, len(updates))-1][0]})\n")
        f.write(query)
        f.write("\n\n")

print("💾 Requêtes sauvegardées dans 'update_queries.sql'")

# Afficher un aperçu
if queries:
    print("\n🔍 Aperçu de la première requête :")
    lines_preview = queries[0].split('\n')[:10]
    print('\n'.join(lines_preview))
    print("...\n")

# ========== 6. OPTION : AFFICHER DES STATISTIQUES ==========

# Compter les dates uniques
dates_unique = set([date for _, date in updates])
print(f"\n📅 Statistiques :")
print(f"   - Nombre total d'IDs à mettre à jour : {len(updates)}")
print(f"   - Nombre de dates différentes : {len(dates_unique)}")
print(f"   - Première date : {min(dates_unique)}")
print(f"   - Dernière date : {max(dates_unique)}")