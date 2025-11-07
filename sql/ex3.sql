-- ========================================
-- QUESTION 1 : CRÉER LA TABLE ACCESS
-- ========================================

CREATE TABLE ACESS (
    user_id NUMBER GENERATED ALWAYS AS IDENTITY (START WITH 1 INCREMENT BY 1) PRIMARY KEY,
    login VARCHAR2(100) NOT NULL UNIQUE,
    password VARCHAR2(255) NOT NULL,
    access_level CHAR(1) DEFAULT 'L' NOT NULL,
    CONSTRAINT CK_ACCESS_LEVEL CHECK (access_level IN ('L', 'E', 'U', 'D', 'T'))
);

-- ========================================
-- QUESTION 2 : REMPLIR LA TABLE ACCESS
-- ========================================

-- 2.1 Ajouter les CLIENTS avec :
-- - login = nom.prenom
-- - password = MD5(nom.prenom) généré automatiquement
-- - access_level = 'L' (lecture par défaut)

-- Pour les CLIENTS (avec CodeC pour l'unicité)
-- Supprimer les données (pas la table)
DELETE FROM ACESS;

-- Réinsérer les clients
INSERT INTO ACESS (login, password, access_level)
SELECT 
    LOWER("Nom" || '.' || "Prenom" || '.' || "CodeC") AS login,
    '***' || SUBSTR("Nom", 1, 3) || SUBSTR("Prenom", 1, 3) || '***' AS password,
    'L' AS access_level
FROM CLIENT;

-- Réinsérer les propriétaires
INSERT INTO ACESS (login, password, access_level)
SELECT 
    "email" || '.' || "codeP" AS login,
    '***' || SUBSTR("Pseudo", 1, 3) || '***' AS password,
    'E' AS access_level
FROM PROPRIETAIRE
WHERE "email" IS NOT NULL;

-- Vérifier
SELECT * FROM ACESS;

-- ========================================
-- QUESTION 3 : CRÉER PLUSIEURS UTILISATEURS
-- ========================================

-- 3.a UTILISATEUR 1 : Lecture limitée (lecture seule sur CLIENT et PROPRIETAIRE)
CREATE USER user_lecteur IDENTIFIED BY "Lecteur123!";
GRANT CONNECT TO user_lecteur;
GRANT SELECT ON AGENCE_VOYAGE.CLIENT TO user_lecteur;
GRANT SELECT ON AGENCE_VOYAGE.PROPRIETAIRE TO user_lecteur;

-- 3.b UTILISATEUR 2 : Modifications (INSERT et UPDATE sur LOCATION et VOITURE)
CREATE USER user_modif IDENTIFIED BY "Modif123!";
GRANT CONNECT TO user_modif;
GRANT SELECT ON AGENCE_VOYAGE.LOCATION TO user_modif;
GRANT SELECT ON AGENCE_VOYAGE.VOITURE TO user_modif;
GRANT INSERT ON AGENCE_VOYAGE.LOCATION TO user_modif;
GRANT UPDATE ON AGENCE_VOYAGE.LOCATION TO user_modif;
GRANT INSERT ON AGENCE_VOYAGE.VOITURE TO user_modif;
GRANT UPDATE ON AGENCE_VOYAGE.VOITURE TO user_modif;

-- 3.c UTILISATEUR 3 : Tous les droits (admin) avec possibilité de partager les droits
DROP USER user_admin;
CREATE USER user_admin IDENTIFIED BY "Admin123!";
GRANT DBA TO user_admin;
GRANT GRANT ANY PRIVILEGE TO user_admin;
GRANT GRANT ANY OBJECT PRIVILEGE TO user_admin;

-- Vérifier les utilisateurs créés
SELECT username FROM dba_users WHERE username IN ('USER_LECTEUR', 'USER_MODIF', 'USER_ADMIN');

-- ========================================
-- QUESTION 4 : TESTER LES OPÉRATIONS
-- ========================================

-- NOTE : Exécutez les sections suivantes en vous connectant avec chaque utilisateur

-- ========== TEST AVEC USER_LECTEUR ==========
-- Connexion : user_lecteur / Lecteur123!

SELECT * FROM AGENCE_VOYAGE.CLIENT;

INSERT INTO AGENCE_VOYAGE.CLIENT VALUES ('C999', 'Test', 'User', 25, '999999', 'rue Test', 'Paris');

UPDATE AGENCE_VOYAGE.CLIENT SET "Nom" = 'Updated' WHERE "CodeC" = 'C672';

DELETE FROM AGENCE_VOYAGE.CLIENT WHERE "CodeC" = 'C672';


-- ========== TEST AVEC USER_MODIF ==========
-- Connexion : user_modif / Modif123!

SELECT * FROM AGENCE_VOYAGE.LOCATION WHERE ROWNUM <= 5;

 INSERT INTO AGENCE_VOYAGE.LOCATION ("CodeC", "immat", "annee", "mois", "numloc", "km", "duree", "villed", "villea", "dated", "datef", "note", "avis")
 VALUES ('C672', '11FG62', 2025, 1, 'X-999', 100, 3, 'Paris', 'Lyon', TO_DATE('2025-01-15', 'YYYY-MM-DD'), TO_DATE('2025-01-18', 'YYYY-MM-DD'), NULL, NULL);

 UPDATE AGENCE_VOYAGE.LOCATION SET "km" = 150 WHERE "numloc" = 'X-999';

 DELETE FROM AGENCE_VOYAGE.CLIENT WHERE "CodeC" = 'C672';

 SELECT * FROM AGENCE_VOYAGE.CLIENT;


-- ========== TEST AVEC USER_ADMIN ==========
-- Connexion : user_admin / Admin123!

SELECT * FROM AGENCE_VOYAGE.CLIENT FETCH FIRST 5 ROWS ONLY;

 INSERT INTO AGENCE_VOYAGE.CLIENT VALUES ('C974', 'Admin', 'Test', 45, '888888', 'rue Admin', 'Marseille');

 UPDATE AGENCE_VOYAGE.CLIENT SET "Nom" = 'AdminUpdated' WHERE "CodeC" = 'C974';

 DELETE FROM AGENCE_VOYAGE.CLIENT WHERE "CodeC" = 'C974';

 GRANT SELECT ON AGENCE_VOYAGE.VOITURE TO user_lecteur;