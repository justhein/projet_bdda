-- Création de la séquence pour l'autoincrémentation de user_id
CREATE SEQUENCE seq_user_id
START WITH 1
INCREMENT BY 1
NOCACHE
NOCYCLE;

-- Création de la table ACESS
CREATE TABLE ACESS (
    user_id NUMBER PRIMARY KEY,
    login VARCHAR2(50) NOT NULL,
    password VARCHAR2(100) NOT NULL,
    access_level CHAR(1) CHECK (access_level IN ('L','E','U','D','T'))
);

-- Trigger pour remplir automatiquement user_id à l'insertion
CREATE OR REPLACE TRIGGER trg_acess_user_id
BEFORE INSERT ON ACESS
FOR EACH ROW
BEGIN
    IF :NEW.user_id IS NULL THEN
        SELECT seq_user_id.NEXTVAL INTO :NEW.user_id FROM dual;
    END IF;
END;
/



-- ex3 q2
-- Trigger pour remplir ACESS automatiquement pour CLIENT et PROPRIETAIRE
CREATE OR REPLACE TRIGGER trg_acess_default
BEFORE INSERT ON ACESS
FOR EACH ROW
DECLARE
    v_password_raw VARCHAR2(100);
BEGIN
    -- Si le login et password sont NULL, on suppose que c'est pour un client
    IF :NEW.login IS NULL THEN
        -- On met le login en nom.prenom depuis CLIENT
        SELECT LOWER(c.Nom || '.' || c.Prenom)
        INTO :NEW.login
        FROM CLIENT c
        WHERE c.CodeC = :NEW.user_id;

        -- On génère un mot de passe MD5 (Oracle utilise standard_hash)
        v_password_raw := :NEW.login || '123'; -- tu peux adapter la base du password
        :NEW.password := standard_hash(v_password_raw,'MD5');

        -- Niveau d'accès par défaut
        :NEW.access_level := 'L';
    END IF;

    -- Si login est fourni mais access_level NULL (pour PROPRIETAIRE)
    IF :NEW.access_level IS NULL THEN
        :NEW.access_level := 'E';
    END IF;
END;
/

-- ex3 q3: création des user
-- a) Utilisateur lecture seule
CREATE USER user_read IDENTIFIED BY password123;

-- b) Utilisateur modification (insert/update)
CREATE USER user_write IDENTIFIED BY password123;

-- c) Utilisateur total
CREATE USER user_admin IDENTIFIED BY password123;

-- Tous les utilisateurs doivent pouvoir se connecter
GRANT CREATE SESSION TO user_read;
GRANT CREATE SESSION TO user_write;
GRANT CREATE SESSION TO user_admin;

-- Exemple: lecture seulement sur CLIENT et VOITURE
GRANT SELECT ON CLIENT TO user_read;
GRANT SELECT ON VOITURE TO user_read;
GRANT SELECT ON PROPRIETAIRE TO user_read;
GRANT SELECT ON LOCATION TO user_read;
GRANT SELECT ON ACESS TO user_read;

-- Exemple: insert/update sur CLIENT et LOCATION
GRANT SELECT, INSERT, UPDATE ON CLIENT TO user_write;
GRANT SELECT, INSERT, UPDATE ON LOCATION TO user_write;
GRANT SELECT, INSERT, UPDATE ON PROPRIETAIRE TO user_write;
GRANT SELECT, INSERT, UPDATE ON VOITURE TO user_write;
GRANT SELECT, INSERT, UPDATE ON ACESS TO user_write;

-- Tous droits sur toutes les tables
GRANT ALL PRIVILEGES TO user_admin;
GRANT GRANT ANY PRIVILEGE TO user_admin;


-- CONNEXION AVEC CHAQUE USER
-- user_read
SELECT * FROM CLIENT; -- fonctionne 
INSERT INTO CLIENT (codec, PRENOM ) VALUES ('C999', 'Martin'); -- SQL Error [1031] [42000]: ORA-01031: insufficient privileges

-- user_write
INSERT INTO CLIENT (CodeC, Nom, Prenom, age, Permis, Adresse, Ville)
VALUES ('C989', 'Test', 'User', 30, 'B', '123 Rue Test', 'Paris');
UPDATE CLIENT
SET Nom = 'TestUpdated'
WHERE CodeC = 'C989';
-- Exemple sur PROPRIETAIRE (non autorisé)
INSERT INTO PROPRIETAIRE (codeP, Pseudo, email, ville, anneeI)
VALUES ('P999', 'PropTest', 'test@ex.com', 'Paris', 2025);





