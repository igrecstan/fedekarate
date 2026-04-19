# Arborescence du projet FI-ADEKASH

```
FI-ADEKASH/
│
├── app.py                          ← Point d'entrée Flask
├── admin_auth.py                   ← Blueprint API /api/admin/*
├── requirements.txt                ← Flask, bcrypt, mysql-connector-python
├── reset_admin.py                  ← Utilitaire : créer/réinitialiser le mot de passe admin
├── test_connexion.py               ← Utilitaire : tester la connexion MySQL
├── import_csv.py                   ← Utilitaire : import CSV clubs
├── import_clubs_saison.py          ← Utilitaire : import clubs par saison
│
├── index.html                      ← Page d'accueil publique (slider + président + contact)
├── apropos.html                    ← Page À propos / valeurs
├── events.html                     ← Page Calendrier & événements
├── contacts.html                   ← Page Contact
├── header.html                     ← Fragment navbar (injecté via layout.js)
├── footer.html                     ← Fragment footer (injecté via layout.js)
│
├── admin/                          ← Espace administration
│   ├── admin-login.html            ← Page de connexion admin
│   ├── admin-dashboard.html        ← Dashboard SPA (toutes les sections)
│   ├── clubs.html                  ← Page gestion des clubs
│   ├── evenements.html             ← Page gestion des événements
│   ├── documents.html              ← Page gestion des documents
│   └── messages.html               ← Page gestion des messages
│   ├── css/
│      ├── admin.css
│   ├── includes/
│      ├── sidebar.html            
│   ├── js/
│      ├── admin.js
│      ├── clubs.js
│      ├── dashboard.js
│      ├── documents.js
│      ├── evenements.js
│      ├── message.js	
│   
├── espace-club/                    ← Espace club (authentification par identifiant)
│   ├── connexion.html              ← Page de connexion club
│   └── clubs_autorises.json        ← Liste des identifiants clubs autorisés
│
├── css/
│   ├── styles.css                  ← Styles du site public
│   └── admin.css                   ← Styles de l'espace admin
│
├── js/
│   ├── layout.js                   ← Injection header/footer + menu mobile
│      
│
└── images/
    └── logo.jpg                    ← Logo FI-ADEKASH
```
