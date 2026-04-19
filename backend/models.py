from database.db_manager import db
from datetime import datetime

# Ne pas importer routes.clubs ici !

class ClubModel:
    @staticmethod
    def get_all(limit=None, offset=None):
        """Récupère tous les clubs"""
        try:
            query = "SELECT * FROM club ORDER BY id_club"
            if limit is not None:
                query += f" LIMIT {limit}"
                if offset is not None:
                    query += f" OFFSET {offset}"
            result = db.fetch_all(query)
            print(f"🔍 {len(result)} clubs trouvés")
            return result
        except Exception as e:
            print(f"❌ Erreur get_all clubs: {e}")
            raise
    
    @staticmethod
    def get_by_id(club_id):
        """Récupère un club par son ID"""
        return db.fetch_one("SELECT * FROM club WHERE id_club = %s", (club_id,))
    
    @staticmethod
    def create(data):
        """Crée un nouveau club"""
        return db.insert('club', data)
    
    @staticmethod
    def update(club_id, data):
        """Met à jour un club"""
        return db.update('club', data, 'id_club = %s', [club_id])
    
    @staticmethod
    def delete(club_id):
        """Supprime un club"""
        return db.delete('club', 'id_club = %s', [club_id])
    
    @staticmethod
    def count():
        """Compte le nombre de clubs"""
        result = db.fetch_one("SELECT COUNT(*) as total FROM club")
        return result['total'] if result else 0


class ClubSaisonModel:
    @staticmethod
    def get_all_by_saison(saison_id):
        """Récupère tous les clubs d'une saison"""
        query = """
            SELECT cs.*, c.`nom du club`, c.`num club`, c.`nom et prenoms`, c.grade
            FROM clubs_saison cs
            JOIN club c ON cs.List_club = c.id_club
            WHERE cs.List_saison = %s
            ORDER BY cs.id_clubSaison
        """
        return db.fetch_all(query, (saison_id,))
    
    @staticmethod
    def get_saisons():
        """Récupère la liste des saisons"""
        query = "SELECT DISTINCT List_saison FROM clubs_saison ORDER BY List_saison"
        return db.fetch_all(query)
    
    @staticmethod
    def add_club_to_saison(saison_id, club_id, secteur_id):
        """Ajoute un club à une saison"""
        data = {
            'List_saison': saison_id,
            'List_club': club_id,
            'List_sect': secteur_id,
            'created_At': datetime.now().date()
        }
        return db.insert('clubs_saison', data)
    
    @staticmethod
    def remove_club_from_saison(saison_id, club_id):
        """Retire un club d'une saison"""
        return db.delete('clubs_saison', 'List_saison = %s AND List_club = %s', [saison_id, club_id])


class EventModel:
    _events = []
    _next_id = 1
    
    @classmethod
    def get_all(cls):
        return cls._events
    
    @classmethod
    def get_by_id(cls, event_id):
        return next((e for e in cls._events if e['id'] == event_id), None)
    
    @classmethod
    def create(cls, data):
        event = {
            'id': cls._next_id,
            **data,
            'created_at': datetime.now().isoformat()
        }
        cls._events.append(event)
        cls._next_id += 1
        return event['id']
    
    @classmethod
    def update(cls, event_id, data):
        event = cls.get_by_id(event_id)
        if event:
            event.update(data)
            return True
        return False
    
    @classmethod
    def delete(cls, event_id):
        cls._events = [e for e in cls._events if e['id'] != event_id]
        return True


class DocumentModel:
    _documents = []
    _next_id = 1
    
    @classmethod
    def get_all(cls):
        return cls._documents
    
    @classmethod
    def get_by_id(cls, doc_id):
        return next((d for d in cls._documents if d['id'] == doc_id), None)
    
    @classmethod
    def create(cls, data):
        doc = {
            'id': cls._next_id,
            **data,
            'created_at': datetime.now().isoformat()
        }
        cls._documents.append(doc)
        cls._next_id += 1
        return doc['id']
    
    @classmethod
    def update(cls, doc_id, data):
        doc = cls.get_by_id(doc_id)
        if doc:
            doc.update(data)
            return True
        return False
    
    @classmethod
    def delete(cls, doc_id):
        cls._documents = [d for d in cls._documents if d['id'] != doc_id]
        return True