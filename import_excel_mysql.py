"""
Script d'importation v4 FINAL : Excel/CSV → MySQL
--------------------------------------------------
Correction définitive : les valeurs NaN (float) sont
converties en None avant l'envoi à MySQL.

Prérequis :
    pip install pandas openpyxl mysql-connector-python
"""

import math
import pandas as pd
import mysql.connector
from mysql.connector import Error


# ─────────────────────────────────────────────
#  CONFIG — Modifiez ces valeurs
# ─────────────────────────────────────────────
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
# ─────────────────────────────────────────────


def nan_vers_none(valeur):
    """Convertit float NaN en None (NULL MySQL). Laisse le reste intact."""
    if valeur is None:
        return None
    if isinstance(valeur, float) and math.isnan(valeur):
        return None
    return valeur


def lire_fichier(chemin: str) -> pd.DataFrame:
    ext = chemin.rsplit(".", 1)[-1].lower()
    if ext in ("xlsx", "xls"):
        df = pd.read_excel(chemin, dtype=str)
    elif ext == "csv":
        df = pd.read_csv(chemin, sep=CSV_SEPARATEUR, encoding="utf-8-sig", dtype=str)
    else:
        raise ValueError(f"Format non supporté : .{ext}")

    df.columns = [
        col.strip().lower().replace(" ", "_").replace("-", "_")
        for col in df.columns
    ]
    print(f"✔ Fichier lu : {len(df)} lignes, {len(df.columns)} colonnes")
    print(f"  Colonnes : {list(df.columns)}\n")
    return df


def importer(df: pd.DataFrame):
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        cursor = conn.cursor()
        print(f"✔ Connecté à '{DB_CONFIG['database']}'\n")

        # Recrée la table proprement
        cursor.execute(f"DROP TABLE IF EXISTS `{TABLE_CIBLE}`;")
        cols_sql = ", ".join(f"`{c}` TEXT" for c in df.columns)
        cursor.execute(
            f"CREATE TABLE `{TABLE_CIBLE}` ({cols_sql}) "
            f"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
        )
        print(f"✔ Table `{TABLE_CIBLE}` recréée.\n")

        colonnes     = ", ".join(f"`{c}`" for c in df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_sql   = f"INSERT INTO `{TABLE_CIBLE}` ({colonnes}) VALUES ({placeholders})"

        total   = len(df)
        erreurs = 0

        for i, row in enumerate(df.itertuples(index=False, name=None), start=1):
            # ✅ Correction clé : convertit chaque NaN en None
            valeurs = tuple(nan_vers_none(v) for v in row)
            try:
                cursor.execute(insert_sql, valeurs)
            except Error as e:
                erreurs += 1
                print(f"\n  ⚠ Ligne {i} | errno={e.errno} | {e.msg}")
                print(f"     Valeurs : {valeurs}")

            if i % 100 == 0 or i == total:
                print(f"  Progression : {i}/{total} lignes", end="\r")

        conn.commit()
        print(f"\n\n{'='*50}")
        print(f"✅ Import terminé")
        print(f"   Total lignes   : {total}")
        print(f"   Insérées       : {total - erreurs}")
        print(f"   Erreurs        : {erreurs}")
        print(f"{'='*50}")

    except Error as e:
        print(f"\n❌ Erreur MySQL : {e}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()
            print("  Connexion fermée.")


if __name__ == "__main__":
    df = lire_fichier(FICHIER_SOURCE)
    importer(df)