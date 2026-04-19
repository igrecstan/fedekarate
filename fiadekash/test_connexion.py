import mysql.connector

# Testez différentes combinaisons
configs = [
    {'host': 'localhost', 'user': 'root', 'password': '', 'database': 'fiadekash'},
    {'host': 'localhost', 'user': 'root', 'password': 'root', 'database': 'fiadekash'},
    {'host': '127.0.0.1', 'user': 'root', 'password': '', 'database': 'fiadekash'},
    {'host': 'localhost', 'user': 'root', 'password': 'mysql', 'database': 'fiadekash'},
]

for i, config in enumerate(configs, 1):
    try:
        print(f"Test {i}: user={config['user']}, password='{config['password']}'")
        conn = mysql.connector.connect(**config)
        print("✅ Connexion réussie !")
        print(f"Configuration à utiliser : {config}")
        conn.close()
        break
    except Exception as e:
        print(f"❌ Échec : {e}\n")