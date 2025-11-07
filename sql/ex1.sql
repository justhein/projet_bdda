-- ========================================
-- TABLE CLIENT
-- ========================================

-- PRIMARY KEY
ALTER TABLE CLIENT ADD CONSTRAINT PK_CLIENT PRIMARY KEY ("CodeC");

-- Format du code client : C suivi de nombres
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_CODE_FORMAT 
    CHECK ("CodeC" LIKE 'C%' AND LENGTH("CodeC") >= 4);

-- Nom obligatoire et non vide
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_NOM_NOT_NULL 
    CHECK ("Nom" IS NOT NULL AND LENGTH(TRIM("Nom")) > 0);

-- Prénom peut être NULL mais pas vide
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_PRENOM_FORMAT 
    CHECK ("Prenom" IS NULL OR LENGTH(TRIM("Prenom")) > 0);

-- Âge entre 18 et 120 ans
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_AGE_RANGE 
    CHECK ("age" >= 18 AND "age" <= 120);

-- Numéro de permis : optionnel mais unique s'il existe
ALTER TABLE CLIENT ADD CONSTRAINT UQ_CLIENT_PERMIS UNIQUE ("Permis");
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_PERMIS_FORMAT 
    CHECK ("Permis" IS NULL OR (LENGTH("Permis") >= 6 AND REGEXP_LIKE("Permis", '^[0-9]+$')));

-- Adresse obligatoire et non vide
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_ADRESSE_NOT_NULL 
    CHECK ("Adresse" IS NOT NULL AND LENGTH(TRIM("Adresse")) > 0);

-- Adresse : longueur maximale 200 caractères
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_ADRESSE_LENGTH 
    CHECK (LENGTH("Adresse") <= 200);

-- Ville obligatoire
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_VILLE_NOT_NULL 
    CHECK ("Ville" IS NOT NULL AND LENGTH(TRIM("Ville")) > 0);

-- Villes acceptées (liste)
ALTER TABLE CLIENT ADD CONSTRAINT CK_CLIENT_VILLE_LIST 
    CHECK ("Ville" IN ('Paris', 'Lyon', 'Marseille', 'Nantes', 'Neuilly', 'Montreuil', 'Vatican', 'Courbevoie'));

-- Index pour recherche rapide par ville et nom
CREATE INDEX IDX_CLIENT_VILLE ON CLIENT("Ville");
CREATE INDEX IDX_CLIENT_NOM ON CLIENT("Nom");


-- ========================================
-- TABLE PROPRIETAIRE
-- ========================================

-- PRIMARY KEY
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT PK_PROPRIETAIRE PRIMARY KEY ("codeP");

-- Format du code propriétaire : P suivi de nombres
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT CK_PROP_CODE_FORMAT 
    CHECK ("codeP" LIKE 'P%' AND LENGTH("codeP") >= 3);

-- Pseudo obligatoire et unique
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT UQ_PROPRIETAIRE_PSEUDO UNIQUE ("Pseudo");
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT CK_PROP_PSEUDO_NOT_NULL 
    CHECK ("Pseudo" IS NOT NULL AND LENGTH(TRIM("Pseudo")) > 0);

-- Pseudo : longueur 3-50 caractères
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT CK_PROP_PSEUDO_LENGTH 
    CHECK (LENGTH("Pseudo") BETWEEN 3 AND 50);

-- Email : optionnel mais unique et valide si présent
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT UQ_PROPRIETAIRE_EMAIL UNIQUE ("email");
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT CK_PROP_EMAIL_FORMAT 
    CHECK ("email" IS NULL OR ("email" LIKE '%@%.%' AND LENGTH("email") BETWEEN 5 AND 100));

-- Ville obligatoire
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT CK_PROP_VILLE_NOT_NULL 
    CHECK ("Ville" IS NOT NULL AND LENGTH(TRIM("Ville")) > 0);

-- Année d'inscription : entre 2000 et l'année actuelle
ALTER TABLE PROPRIETAIRE ADD CONSTRAINT CK_PROP_ANNEE_RANGE 
    CHECK ("anneeI" >= 2000 AND "anneeI" <= TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY')));

-- Index pour recherche
CREATE INDEX IDX_PROPRIETAIRE_PSEUDO ON PROPRIETAIRE("Pseudo");
CREATE INDEX IDX_PROPRIETAIRE_EMAIL ON PROPRIETAIRE("email");
CREATE INDEX IDX_PROPRIETAIRE_VILLE ON PROPRIETAIRE("Ville");


-- ========================================
-- TABLE VOITURE - CONTRAINTES COMPLÈTES
-- ========================================

-- PRIMARY KEY
ALTER TABLE VOITURE ADD CONSTRAINT PK_VOITURE PRIMARY KEY ("Immat");

-- Format immatriculation : format français XX###XX ou similaire
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_IMMAT_FORMAT 
    CHECK ("Immat" NOT LIKE '%[^A-Z0-9]%' AND LENGTH("Immat") BETWEEN 6 AND 10);

-- Marque obligatoire et non vide
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_MARQUE_NOT_NULL 
    CHECK ("Marque" IS NOT NULL AND LENGTH(TRIM("Marque")) > 0);

-- Marques acceptées
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_MARQUE_LIST 
    CHECK ("Marque" IN ('Renault', 'Peugeot', 'Citroen', 'Ferrari', 'Tesla', 'Dodge', 'Autre'));

-- Modèle obligatoire et non vide
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_MODELE_NOT_NULL 
    CHECK ("modele" IS NOT NULL AND LENGTH(TRIM("modele")) > 0);

-- Catégorie obligatoire et valide
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_CATEGORIE_LIST 
    CHECK ("Categorie" IN ('luxe', 'premium', 'cabriolet', 'familiale', 'utilitaire', 'berline', 'citadine'));

-- Couleur : optionnel
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_COULEUR_LIST 
    CHECK ("couleur" IS NULL OR "couleur" IN ('Rouge', 'Vert', 'Blanc', 'Noir', 'Bleu', 'Gris', 'Beige'));

-- Places : entre 1 et 9
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_PLACES_RANGE 
    CHECK ("places" >= 1 AND "places" <= 9);

-- Année d'achat : entre 1900 et l'année actuelle
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_ACHAT_RANGE 
    CHECK ("achatA" >= 1900 AND "achatA" <= TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY')));

-- Compteur kilométrique : >= 0 et réaliste (< 1 000 000 km)
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_COMPTEUR_RANGE 
    CHECK ("compteur" >= 0 AND "compteur" < 1000000);

-- Prix journalier : entre 10€ et 500€
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_PRIX_RANGE 
    CHECK ("prixJ" >= 10 AND "prixJ" <= 500);

-- État de la voiture : valeurs acceptées
ALTER TABLE VOITURE ADD CONSTRAINT CK_VOITURE_ETAT_LIST 
    CHECK ("etat" IN ('disponible', 'en location', 'en réparation', 'vendue'));

-- FOREIGN KEY vers PROPRIETAIRE
ALTER TABLE VOITURE ADD CONSTRAINT FK_VOITURE_PROPRIETAIRE 
    FOREIGN KEY ("codeP") REFERENCES PROPRIETAIRE("codeP") ON DELETE CASCADE;

-- Chaque propriétaire ne peut pas avoir trop de voitures (max 100)
-- (Contrôle via trigger)

-- Index pour recherche
CREATE INDEX IDX_VOITURE_MARQUE ON VOITURE("Marque");
CREATE INDEX IDX_VOITURE_PROPRIETAIRE ON VOITURE("codeP");
CREATE INDEX IDX_VOITURE_ETAT ON VOITURE("etat");


-- ========================================
-- TABLE LOCATION
-- ========================================

-- PRIMARY KEY : Combinaison de colonnes pour identifier une location unique
ALTER TABLE LOCATION ADD CONSTRAINT PK_LOCATION 
    PRIMARY KEY ("CodeC", "immat", "annee", "mois", "numloc");

-- Client obligatoire
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_CLIENT_NOT_NULL 
    CHECK ("CodeC" IS NOT NULL);

-- Immatriculation obligatoire
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_IMMAT_NOT_NULL 
    CHECK ("immat" IS NOT NULL);

-- Année : entre 2000 et l'année actuelle
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_ANNEE_RANGE 
    CHECK ("annee" >= 2000 AND "annee" <= TO_NUMBER(TO_CHAR(SYSDATE, 'YYYY')));

-- Mois : entre 1 et 12
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_MOIS_RANGE 
    CHECK ("mois" >= 1 AND "mois" <= 12);

-- Numéro de location : format alphanumérique
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_NUMLOC_FORMAT 
    CHECK ("numloc" IS NOT NULL AND LENGTH(TRIM("numloc")) > 0);

-- Kilométrage : >= 0 et <= 100 000 km max
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_KM_RANGE 
    CHECK ("km" >= 0 AND "km" <= 100000);

-- Durée : >= 0 jours
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_DUREE_RANGE 
    CHECK ("duree" >= 0 AND "duree" <= 365);

-- Villes de départ et d'arrivée : obligatoires
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_VILLED_NOT_NULL 
    CHECK ("villed" IS NOT NULL AND LENGTH(TRIM("villed")) > 0);

ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_VILLEA_NOT_NULL 
    CHECK ("villea" IS NOT NULL AND LENGTH(TRIM("villea")) > 0);

-- Dates obligatoires
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_DATED_NOT_NULL 
    CHECK ("dated" IS NOT NULL);

ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_DATEF_NOT_NULL 
    CHECK ("datef" IS NOT NULL);

-- Date de fin >= date de départ
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_DATES_ORDER 
    CHECK ("datef" >= "dated");

-- Note : optionnel, entre 0 et 5 si présent
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_NOTE_RANGE 
    CHECK ("note" IS NULL OR ("note" >= 0 AND "note" <= 5));

-- Avis : optionnel, longueur max
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_AVIS_LENGTH 
    CHECK ("avis" IS NULL OR LENGTH("avis") <= 100);

-- Avis acceptés
ALTER TABLE LOCATION ADD CONSTRAINT CK_LOC_AVIS_LIST 
    CHECK ("avis" IS NULL OR "avis" IN ('très satisfait', 'satisfait', 'moyen', 'peu satisfait', 'non évalué'));

-- FOREIGN KEY vers CLIENT
ALTER TABLE LOCATION ADD CONSTRAINT FK_LOCATION_CLIENT 
    FOREIGN KEY ("CodeC") REFERENCES CLIENT("CodeC") ON DELETE CASCADE;

-- FOREIGN KEY vers VOITURE
ALTER TABLE LOCATION ADD CONSTRAINT FK_LOCATION_VOITURE 
    FOREIGN KEY ("immat") REFERENCES VOITURE("Immat") ON DELETE CASCADE;

-- Index pour recherche
CREATE INDEX IDX_LOCATION_CLIENT ON LOCATION("CodeC");
CREATE INDEX IDX_LOCATION_VOITURE ON LOCATION("immat");
CREATE INDEX IDX_LOCATION_ANNEE_MOIS ON LOCATION("annee", "mois");
CREATE INDEX IDX_LOCATION_DATED ON LOCATION("dated");


-- ========================================
-- TABLE HISTORIQUE_ETAT_VOITURE
-- ========================================

-- PRIMARY KEY
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT PK_HISTORIQUE_ETAT 
    PRIMARY KEY (id_historique);

-- Immatriculation obligatoire
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT CK_HIST_IMMAT_NOT_NULL 
    CHECK ("Immat" IS NOT NULL);

-- Nouvel état obligatoire et valide
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT CK_HIST_ETAT_NOT_NULL 
    CHECK (nouvel_etat IS NOT NULL);

ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT CK_HIST_ETAT_LIST 
    CHECK (nouvel_etat IN ('disponible', 'en location', 'en réparation', 'vendue'));

-- Ancien état : optionnel mais valide
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT CK_HIST_ANCIEN_ETAT_LIST 
    CHECK (ancien_etat IS NULL OR ancien_etat IN ('disponible', 'en location', 'en réparation', 'vendue'));

-- Les deux états ne peuvent pas être identiques
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT CK_HIST_ETAT_DIFFERENT 
    CHECK (ancien_etat != nouvel_etat OR ancien_etat IS NULL);

-- Motif : optionnel, longueur max
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT CK_HIST_MOTIF_LENGTH 
    CHECK (motif IS NULL OR LENGTH(motif) <= 100);

-- FOREIGN KEY vers VOITURE
ALTER TABLE HISTORIQUE_ETAT_VOITURE ADD CONSTRAINT FK_HIST_VOITURE 
    FOREIGN KEY ("Immat") REFERENCES VOITURE("Immat") ON DELETE CASCADE;

-- Index pour recherche
CREATE INDEX IDX_HIST_IMMAT ON HISTORIQUE_ETAT_VOITURE("Immat");
CREATE INDEX IDX_HIST_DATE ON HISTORIQUE_ETAT_VOITURE(date_changement);


-- ========================================
-- TABLE ACCESS
-- ========================================

-- PRIMARY KEY
ALTER TABLE ACCESS ADD CONSTRAINT PK_ACCESS PRIMARY KEY (user_id);

-- Login : obligatoire, unique, alphanumérique
ALTER TABLE ACCESS ADD CONSTRAINT UQ_ACCESS_LOGIN UNIQUE (login);
ALTER TABLE ACCESS ADD CONSTRAINT CK_ACCESS_LOGIN_NOT_NULL 
    CHECK (login IS NOT NULL AND LENGTH(TRIM(login)) > 0);

-- Password : obligatoire, longueur min 10
ALTER TABLE ACCESS ADD CONSTRAINT CK_ACCESS_PASSWORD_NOT_NULL 
    CHECK (password IS NOT NULL AND LENGTH(password) >= 10);

-- Access level : obligatoire et valide
ALTER TABLE ACCESS ADD CONSTRAINT CK_ACCESS_LEVEL_LIST 
    CHECK (access_level IN ('L', 'E', 'U', 'D', 'T'));

-- Index
CREATE INDEX IDX_ACCESS_LOGIN ON ACCESS(login);


-- ========================================
-- VÉRIFICATION DES CONTRAINTES
-- ========================================

-- Afficher toutes les contraintes créées
SELECT constraint_name, constraint_type, table_name 
FROM user_constraints 
WHERE table_name IN ('CLIENT', 'PROPRIETAIRE', 'VOITURE', 'LOCATION', 'HISTORIQUE_ETAT_VOITURE', 'ACCESS')
ORDER BY table_name, constraint_type;

COMMIT;

DBMS_OUTPUT.PUT_LINE('✅ Toutes les contraintes améliorées ont été créées avec succès !');