-- ============================================================================
-- TP BASES DE DONNÉES AVANCÉES - QUESTION 1
-- Agence de Voyage - Création et remplissage de la base
-- ============================================================================

-- 1.1 CRÉATION DE LA BASE DE DONNÉES
-- ============================================================================

DROP DATABASE IF EXISTS agence_voyage;
CREATE DATABASE agence_voyage CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE agence_voyage;

-- ============================================================================
-- 1.2 CRÉATION DES TABLES (sans contraintes pour faciliter l'import)
-- ============================================================================

-- Table PROPRIETAIRE
CREATE TABLE Proprietaire (
    CodeP VARCHAR(10) PRIMARY KEY,
    pseudo VARCHAR(50),
    email VARCHAR(100),
    ville VARCHAR(50),
    anneeI YEAR
);

-- Table CLIENT
CREATE TABLE Client (
    CodeC VARCHAR(10) PRIMARY KEY,
    Nom VARCHAR(50),
    Prenom VARCHAR(50),
    age INT,
    Permis VARCHAR(20),
    Adresse VARCHAR(100),
    Ville VARCHAR(50)
);

-- Table VOITURE
CREATE TABLE Voiture (
    Immat VARCHAR(10) PRIMARY KEY,
    modele VARCHAR(50),
    Marque VARCHAR(50),
    Categorie VARCHAR(30),
    couleur VARCHAR(20),
    places INT,
    achatA YEAR,
    compteur INT,
    prixJ DECIMAL(10,2),
    codeP VARCHAR(10)
);

-- Table LOCATION
CREATE TABLE Location (
    CodeC VARCHAR(10),
    immat VARCHAR(10),
    annee YEAR,
    mois INT,
    numloc VARCHAR(20),
    km INT,
    duree INT,
    villed VARCHAR(50),
    villea VARCHAR(50),
    dated DATE,
    datef DATE,
    note INT,
    avis VARCHAR(100),
    PRIMARY KEY (CodeC, immat, annee, mois, numloc)
);

-- ============================================================================
-- ALTERNATIVE : Si LOAD DATA LOCAL INFILE ne fonctionne pas
-- Vous pouvez utiliser l'import CSV via DBeaver ou MySQL Workbench
-- ============================================================================

-- ============================================================================
-- 1.4 VÉRIFICATION ET CORRECTION DES DONNÉES
-- ============================================================================

-- a) Mise à jour aléatoire de datef (fin de location)
-- datef = dated + valeur aléatoire entre 0 et 100 jours

UPDATE Location
SET datef = DATE_ADD(dated, INTERVAL FLOOR(RAND() * 101) DAY);

-- b) Recalcul de la durée en nombre de jours
UPDATE Location
SET duree = DATEDIFF(datef, dated);

-- Vérification des données mises à jour
SELECT 
    CodeC, 
    immat, 
    dated, 
    datef, 
    duree,
    DATEDIFF(datef, dated) AS duree_verifiee
FROM Location
LIMIT 10;

-- ============================================================================
-- 1.5 AJOUT DES CONTRAINTES D'INTÉGRITÉ
-- ============================================================================

-- ============================================================================
-- Contraintes sur la table CLIENT
-- ============================================================================

-- Contrainte : Age doit être positif et réaliste
ALTER TABLE Client
ADD CONSTRAINT chk_age_positif CHECK (age > 0 AND age < 120);

-- Contrainte : Nom ne peut pas être vide
ALTER TABLE Client
ADD CONSTRAINT chk_nom_non_vide CHECK (Nom IS NOT NULL AND TRIM(Nom) != '');

-- ============================================================================
-- Contraintes sur la table VOITURE
-- ============================================================================

-- Ajout de la contrainte de clé étrangère vers Proprietaire
ALTER TABLE Voiture
ADD CONSTRAINT fk_voiture_proprietaire 
    FOREIGN KEY (codeP) REFERENCES Proprietaire(CodeP)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Contrainte : nombre de places doit être positif
ALTER TABLE Voiture
ADD CONSTRAINT chk_places_positif CHECK (places > 0 AND places <= 10);

-- Contrainte : prix journalier doit être positif
ALTER TABLE Voiture
ADD CONSTRAINT chk_prix_positif CHECK (prixJ > 0);

-- Contrainte : compteur kilométrique doit être positif
ALTER TABLE Voiture
ADD CONSTRAINT chk_compteur_positif CHECK (compteur >= 0);

-- Contrainte : année d'achat réaliste
ALTER TABLE Voiture
ADD CONSTRAINT chk_achat_realiste CHECK (achatA >= 1990 AND achatA <= YEAR(CURDATE()));

-- ============================================================================
-- Contraintes sur la table LOCATION
-- ============================================================================

-- Ajout des contraintes de clés étrangères
ALTER TABLE Location
ADD CONSTRAINT fk_location_client 
    FOREIGN KEY (CodeC) REFERENCES Client(CodeC)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

ALTER TABLE Location
ADD CONSTRAINT fk_location_voiture 
    FOREIGN KEY (immat) REFERENCES Voiture(Immat)
    ON DELETE RESTRICT
    ON UPDATE CASCADE;

-- Contrainte : durée de location doit être positive ou nulle
ALTER TABLE Location
ADD CONSTRAINT chk_duree_positive CHECK (duree >= 0);

-- Contrainte : kilomètres doivent être positifs
ALTER TABLE Location
ADD CONSTRAINT chk_km_positif CHECK (km >= 0);

-- Contrainte : datef doit être >= dated
ALTER TABLE Location
ADD CONSTRAINT chk_dates_coherentes CHECK (datef >= dated);

-- Contrainte : mois entre 1 et 12
ALTER TABLE Location
ADD CONSTRAINT chk_mois_valide CHECK (mois BETWEEN 1 AND 12);

-- Contrainte : note entre 0 et 5 ou NULL
ALTER TABLE Location
ADD CONSTRAINT chk_note_valide CHECK (note IS NULL OR (note >= 0 AND note <= 5));

-- ============================================================================
-- Contraintes sur la table PROPRIETAIRE
-- ============================================================================

-- Contrainte : année d'inscription réaliste
ALTER TABLE Proprietaire
ADD CONSTRAINT chk_annee_inscription CHECK (anneeI >= 2000 AND anneeI <= YEAR(CURDATE()));

-- Contrainte : format email valide (basique)
ALTER TABLE Proprietaire
ADD CONSTRAINT chk_email_format CHECK (email IS NULL OR email LIKE '%@%.%');

-- ============================================================================
-- Index pour améliorer les performances
-- ============================================================================

-- Index sur les clés étrangères (si pas créés automatiquement)
CREATE INDEX idx_voiture_proprietaire ON Voiture(codeP);
CREATE INDEX idx_location_client ON Location(CodeC);
CREATE INDEX idx_location_voiture ON Location(immat);

-- Index sur les champs fréquemment recherchés
CREATE INDEX idx_client_ville ON Client(Ville);
CREATE INDEX idx_voiture_categorie ON Voiture(Categorie);
CREATE INDEX idx_location_dates ON Location(dated, datef);

-- ============================================================================
-- 1.6 VÉRIFICATION DES CONTRAINTES
-- ============================================================================

-- Affichage de toutes les contraintes de la base
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    CONSTRAINT_TYPE
FROM information_schema.TABLE_CONSTRAINTS
WHERE TABLE_SCHEMA = 'agence_voyage'
ORDER BY TABLE_NAME, CONSTRAINT_TYPE;

-- Vérification des clés étrangères
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    REFERENCED_TABLE_NAME,
    REFERENCED_COLUMN_NAME
FROM information_schema.KEY_COLUMN_USAGE
WHERE TABLE_SCHEMA = 'agence_voyage' 
    AND REFERENCED_TABLE_NAME IS NOT NULL;

-- Vérification des contraintes CHECK
SELECT 
    TABLE_NAME,
    CONSTRAINT_NAME,
    CHECK_CLAUSE
FROM information_schema.CHECK_CONSTRAINTS
WHERE CONSTRAINT_SCHEMA = 'agence_voyage';

-- ============================================================================
-- TESTS DES CONTRAINTES
-- ============================================================================

-- Test 1 : Tentative d'insertion d'un client avec un âge invalide (doit échouer)
-- INSERT INTO Client VALUES ('C999', 'Test', 'Test', -5, '12345', 'Rue Test', 'Paris');

-- Test 2 : Tentative d'insertion d'une location avec des dates incohérentes (doit échouer)
-- INSERT INTO Location VALUES ('C654', '11FG62', 2024, 5, 'TEST-01', 100, 5, 'Paris', 'Lyon', '2024-05-10', '2024-05-05', NULL, NULL);

-- Test 3 : Tentative d'insertion d'une voiture avec un prix négatif (doit échouer)
-- INSERT INTO Voiture VALUES ('99XX99', 'Test', 'Test', 'berline', 'Noir', 5, 2020, 5000, -10, 'P12');

-- Test 4 : Tentative de suppression d'un propriétaire ayant des voitures (doit échouer)
-- DELETE FROM Proprietaire WHERE CodeP = 'P12';

-- ============================================================================
-- STATISTIQUES DE LA BASE
-- ============================================================================

SELECT 'PROPRIETAIRES' AS Table_Name, COUNT(*) AS Nombre_Lignes FROM Proprietaire
UNION ALL
SELECT 'CLIENTS', COUNT(*) FROM Client
UNION ALL
SELECT 'VOITURES', COUNT(*) FROM Voiture
UNION ALL
SELECT 'LOCATIONS', COUNT(*) FROM Location;

-- ============================================================================
-- FIN DU SCRIPT
-- ============================================================================