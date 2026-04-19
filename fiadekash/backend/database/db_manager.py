# backend/database/db_manager.py
import mysql.connector
from mysql.connector import Error
from config import Config

class DatabaseManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        self.connection = None
        self.connect()
    
    def connect(self):
        """Établit la connexion à la base de données"""
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                autocommit=True,
                use_pure=True  # Force le connecteur Python pur
            )
            print("✅ Connexion à la base de données réussie")
            print(f"📁 Base: {Config.DB_NAME}")
        except Error as e:
            print(f"❌ Erreur de connexion : {e}")
            raise
    
    def get_cursor(self):
        """Retourne un curseur pour exécuter des requêtes"""
        if not self.connection or not self.connection.is_connected():
            self.connect()
        return self.connection.cursor(dictionary=True)
    
    def fetch_all(self, query, params=None):
        """Récupère toutes les lignes d'une requête"""
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params or ())
            result = cursor.fetchall()
            print(f"fetch_all: {len(result)} lignes")  # Debug
            return result
        except Error as e:
            print(f"Erreur fetch_all: {e}")
            raise
        finally:
            cursor.close()
    
    def fetch_one(self, query, params=None):
        """Récupère une seule ligne"""
        cursor = self.get_cursor()
        try:
            cursor.execute(query, params or ())
            return cursor.fetchone()
        finally:
            cursor.close()

# Instance globale
db = DatabaseManager()