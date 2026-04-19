-- ============================================================
--  FI-ADEKASH — Base de données MySQL
--  Module : Authentification & gestion des administrateurs
-- ============================================================

CREATE DATABASE IF NOT EXISTS fiadekash CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE fiadekash;

-- ============================================================
--  1. TABLE : permissions
--  Liste de toutes les actions possibles dans l'admin
-- ============================================================
CREATE TABLE permissions (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    code        VARCHAR(100) NOT NULL UNIQUE,          -- ex: clubs.create, events.delete
    label       VARCHAR(150) NOT NULL,                 -- ex: "Créer un club"
    module      VARCHAR(50)  NOT NULL,                 -- ex: clubs, events, documents, messages
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Permissions de base
INSERT INTO permissions (code, label, module) VALUES
-- Clubs
('clubs.view',     'Voir les clubs',        'clubs'),
('clubs.create',   'Créer un club',         'clubs'),
('clubs.edit',     'Modifier un club',      'clubs'),
('clubs.delete',   'Supprimer un club',     'clubs'),
-- Événements
('events.view',    'Voir les événements',   'events'),
('events.create',  'Créer un événement',    'events'),
('events.edit',    'Modifier un événement', 'events'),
('events.delete',  'Supprimer un événement','events'),
-- Documents
('docs.view',      'Voir les documents',    'documents'),
('docs.create',    'Publier un document',   'documents'),
('docs.edit',      'Modifier un document',  'documents'),
('docs.delete',    'Supprimer un document', 'documents'),
-- Messages
('messages.view',  'Voir les messages',     'messages'),
('messages.delete','Supprimer un message',  'messages'),
-- Admins
('admins.view',    'Voir les admins',       'admins'),
('admins.create',  'Créer un admin',        'admins'),
('admins.edit',    'Modifier un admin',     'admins'),
('admins.delete',  'Supprimer un admin',    'admins'),
-- Rôles
('roles.view',     'Voir les rôles',        'roles'),
('roles.manage',   'Gérer les rôles',       'roles');


-- ============================================================
--  2. TABLE : roles
--  Rôles personnalisables créés par le super admin
-- ============================================================
CREATE TABLE roles (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nom         VARCHAR(100) NOT NULL UNIQUE,          -- ex: Modérateur, Secrétaire
    description VARCHAR(255),
    is_super    TINYINT(1) DEFAULT 0,                  -- 1 = super admin (tous droits)
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Rôles par défaut
INSERT INTO roles (nom, description, is_super) VALUES
('Super Administrateur', 'Accès complet à toutes les fonctionnalités', 1),
('Administrateur',       'Gestion complète sauf la gestion des admins', 0),
('Modérateur',           'Lecture seule + gestion des messages',         0),
('Secrétaire',           'Gestion des documents et événements',          0);


-- ============================================================
--  3. TABLE : role_permissions
--  Association rôle <-> permissions
-- ============================================================
CREATE TABLE role_permissions (
    role_id       INT UNSIGNED NOT NULL,
    permission_id INT UNSIGNED NOT NULL,
    PRIMARY KEY (role_id, permission_id),
    FOREIGN KEY (role_id)       REFERENCES roles(id)       ON DELETE CASCADE,
    FOREIGN KEY (permission_id) REFERENCES permissions(id) ON DELETE CASCADE
);

-- Super Admin : toutes les permissions (inséré dynamiquement)
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions;

-- Administrateur : tout sauf gestion des admins et rôles
INSERT INTO role_permissions (role_id, permission_id)
SELECT 2, id FROM permissions
WHERE module NOT IN ('admins', 'roles');

-- Modérateur : voir clubs/events/docs + gérer messages
INSERT INTO role_permissions (role_id, permission_id)
SELECT 3, id FROM permissions
WHERE code IN ('clubs.view', 'events.view', 'docs.view', 'messages.view', 'messages.delete');

-- Secrétaire : documents et événements complets
INSERT INTO role_permissions (role_id, permission_id)
SELECT 4, id FROM permissions
WHERE module IN ('documents', 'events', 'messages')
  AND code NOT LIKE '%.delete';


-- ============================================================
--  4. TABLE : users
--  Comptes des administrateurs
-- ============================================================
CREATE TABLE users (
    id              INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    nom             VARCHAR(100) NOT NULL,
    prenom          VARCHAR(100) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    login           VARCHAR(80)  NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,              -- bcrypt
    role_id         INT UNSIGNED NOT NULL,
    actif           TINYINT(1) DEFAULT 1,               -- 0 = compte désactivé
    derniere_cnx    DATETIME,
    token_reset     VARCHAR(255),                       -- token réinitialisation mdp
    token_reset_exp DATETIME,
    created_by      INT UNSIGNED,                       -- qui a créé ce compte
    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (role_id)    REFERENCES roles(id) ON DELETE RESTRICT,
    FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE SET NULL
);

-- Super admin par défaut
-- Mot de passe : fiadekash2025 (à changer impérativement)
INSERT INTO users (nom, prenom, email, login, password_hash, role_id, created_by) VALUES
(
    'ADEKASH',
    'Admin',
    'admin@fi-adekash.ci',
    'admin',
    '$2b$12$KIXBFxSQz1Q8v.rH9aGpLuT3mN7YwZpXqVdCeO2sJhR4lA5bMnPkW', -- bcrypt placeholder
    1,
    NULL
);


-- ============================================================
--  5. TABLE : sessions_admin
--  Suivi des connexions (sécurité & audit)
-- ============================================================
CREATE TABLE sessions_admin (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED NOT NULL,
    ip_address  VARCHAR(45),
    user_agent  VARCHAR(255),
    token       VARCHAR(255) NOT NULL UNIQUE,           -- token de session
    expire_at   DATETIME     NOT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);


-- ============================================================
--  6. TABLE : audit_log
--  Historique de toutes les actions admin
-- ============================================================
CREATE TABLE audit_log (
    id          INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id     INT UNSIGNED,
    action      VARCHAR(100) NOT NULL,                  -- ex: clubs.create
    cible       VARCHAR(100),                           -- ex: Club Bouaké
    detail      TEXT,                                   -- JSON des données modifiées
    ip_address  VARCHAR(45),
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);


-- ============================================================
--  VUES UTILES
-- ============================================================

-- Vue : admins avec leur rôle
CREATE OR REPLACE VIEW v_users AS
SELECT
    u.id,
    u.nom,
    u.prenom,
    u.email,
    u.login,
    u.actif,
    u.derniere_cnx,
    u.created_at,
    r.nom        AS role_nom,
    r.is_super,
    r.id         AS role_id
FROM users u
JOIN roles r ON r.id = u.role_id;

-- Vue : permissions d'un utilisateur
CREATE OR REPLACE VIEW v_user_permissions AS
SELECT
    u.id         AS user_id,
    u.login,
    p.code       AS permission,
    p.module
FROM users u
JOIN roles r           ON r.id = u.role_id
LEFT JOIN role_permissions rp ON rp.role_id = r.id
LEFT JOIN permissions p       ON p.id = rp.permission_id
WHERE u.actif = 1
  AND (r.is_super = 1 OR rp.permission_id IS NOT NULL);
