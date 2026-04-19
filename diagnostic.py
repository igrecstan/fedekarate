"""
Script DIAGNOSTIC — affiche les erreurs exactes ligne par ligne
"""

import pandas as pd
import mysql.connector
from mysql.connector import Error

DB_CONFIG = {
    "host":     "localhost",
    "port":     3306,
    "user":     "root",
    "password": "",
    "database": "fiadekash",
}

FICHIER_SOURCE = "athletes.csv"
CSV_SEPARATEUR = ";"
TABLE_CIBLE    = "athletes"

df = pd.read_csv(
    FICHIER_SOURCE,
    sep=CSV_SEPARATEUR,
    encoding="utf-8-sig",
    dtype=str,
    keep_default_na=False,
)
df.columns = [col.strip().lower().replace(" ", "_").replace("-", "_") for col in df.columns]
df = df.replace("", None)

print(f"Lignes lues : {len(df)}")
print(f"Colonnes    : {list(df.columns)}\n")

try:
    conn = mysql.connector.connect(**DB_CONFIG)
    cursor = conn.cursor()

    # Recrée la table
    cursor.execute(f"DROP TABLE IF EXISTS `{TABLE_CIBLE}`;")
    cols_sql = ", ".join(f"`{c}` TEXT" for c in df.columns)
    cursor.execute(
        f"CREATE TABLE `{TABLE_CIBLE}` ({cols_sql}) "
        f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
    )

    colonnes     = ", ".join(f"`{c}`" for c in df.columns)
    placeholders = ", ".join(["%s"] * len(df.columns))
    insert_sql   = f"INSERT INTO `{TABLE_CIBLE}` ({colonnes}) VALUES ({placeholders})"

    erreurs = []
    for i, row in enumerate(df.itertuples(index=False, name=None), start=1):
        try:
            cursor.execute(insert_sql, row)
        except Error as e:
            erreurs.append((i, e.errno, e.msg, row))

    conn.commit()

    print(f"Insérées : {len(df) - len(erreurs)}")
    print(f"Erreurs  : {len(erreurs)}\n")

    if erreurs:
        print("=== DÉTAIL DES 10 PREMIÈRES ERREURS ===\n")
        for i, errno, msg, row in erreurs[:10]:
            print(f"Ligne {i:4d} | errno={errno} | {msg}")
            print(f"         Valeurs = {row}\n")

        # Sauvegarde complète
        with open("diagnostic_erreurs.txt", "w", encoding="utf-8") as f:
            for i, errno, msg, row in erreurs:
                f.write(f"Ligne {i} | errno={errno} | {msg}\n")
                f.write(f"Valeurs = {row}\n\n")
        print(f"→ Toutes les erreurs sauvegardées dans diagnostic_erreurs.txt")

except Error as e:
    print(f"Erreur connexion : {e}")
finally:
    if conn.is_connected():
        cursor.close()
        conn.close()
