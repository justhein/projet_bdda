import oracledb
import time
from datetime import datetime, timedelta

# ========================================
# CONFIGURATION DE LA CONNEXION
# ========================================

DB_USER = "system"
DB_PASSWORD = "oracle"
DB_HOST = "localhost"
DB_PORT = 1521
DB_SERVICE = "XE"
DB_SCHEMA = "AGENCE_VOYAGE"

def get_connection():
    """Crée une nouvelle connexion à la base de données"""
    try:
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE
        )
        
        # Basculer au schéma AGENCE_VOYAGE
        cursor = conn.cursor()
        cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA={DB_SCHEMA}")
        cursor.close()
        
        return conn
    except oracledb.DatabaseError as e:
        print(f"❌ Erreur de connexion : {e}")
        return None


# ========================================
# PARTIE 1 : CRÉER LES OBJETS PL/SQL
# ========================================

def creer_procedures_et_triggers():
    """Crée toutes les procédures et triggers"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    
    try:
        print("\n" + "="*60)
        print("CRÉATION DES PROCÉDURES ET TRIGGERS")
        print("="*60)
        
        # 1. Procédure d'attribution de notes
        print("\n1️⃣  Création de ATTRIBUER_NOTE_LOCATION...")
        sql_note = """
        CREATE OR REPLACE PROCEDURE ATTRIBUER_NOTE_LOCATION IS
        BEGIN
            UPDATE LOCATION
            SET "note" = CASE
                WHEN "km" IS NULL OR "duree" IS NULL THEN NULL
                WHEN "duree" = 1 THEN NULL
                WHEN "km" > 1000 AND "duree" > 50 THEN 5
                WHEN "km" > 500 AND "duree" > 30 THEN 4
                WHEN "km" > 200 AND "duree" > 10 THEN 3
                WHEN "km" > 100 AND "duree" > 5 THEN 2
                ELSE NULL
            END
            WHERE "note" IS NULL;
            
            DBMS_OUTPUT.PUT_LINE('✓ Attribution des notes terminée');
            COMMIT;
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('❌ Erreur : ' || SQLERRM);
                ROLLBACK;
        END ATTRIBUER_NOTE_LOCATION;
        """
        cursor.execute(sql_note)
        print("   ✅ ATTRIBUER_NOTE_LOCATION créée")
        
        # 2. Procédure de mise à jour des avis
        print("\n2️⃣  Création de METTRE_A_JOUR_AVIS...")
        sql_avis = """
        CREATE OR REPLACE PROCEDURE METTRE_A_JOUR_AVIS IS
        BEGIN
            UPDATE LOCATION
            SET "avis" = CASE
                WHEN "note" IS NULL THEN 'non évalué'
                WHEN "note" >= 4 THEN 'très satisfait'
                WHEN "note" >= 3 THEN 'satisfait'
                WHEN "note" >= 2 THEN 'moyen'
                WHEN "note" >= 1 THEN 'peu satisfait'
                ELSE 'non évalué'
            END
            WHERE "avis" IS NULL;
            
            DBMS_OUTPUT.PUT_LINE('✓ Mise à jour des avis terminée');
            COMMIT;
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('❌ Erreur : ' || SQLERRM);
                ROLLBACK;
        END METTRE_A_JOUR_AVIS;
        """
        cursor.execute(sql_avis)
        print("   ✅ METTRE_A_JOUR_AVIS créée")
        
        # 3. Procédure d'analyse par client
        print("\n3️⃣  Création de ANALYSER_CLIENT...")
        sql_analyser = """
        CREATE OR REPLACE PROCEDURE ANALYSER_CLIENT(p_code_client IN VARCHAR2) IS
            v_duree_totale NUMBER;
            v_nb_vehicules NUMBER;
            v_moyenne_notes NUMBER;
            v_nb_locations NUMBER;
            v_nom_client VARCHAR2(100);
            v_prenom_client VARCHAR2(100);
        BEGIN
            DBMS_OUTPUT.PUT_LINE('========================================');
            DBMS_OUTPUT.PUT_LINE('ANALYSE CLIENT');
            DBMS_OUTPUT.PUT_LINE('========================================');
            
            BEGIN
                SELECT "Nom", "Prenom" 
                INTO v_nom_client, v_prenom_client
                FROM CLIENT 
                WHERE "CodeC" = p_code_client;
            EXCEPTION
                WHEN NO_DATA_FOUND THEN
                    DBMS_OUTPUT.PUT_LINE('❌ Client ' || p_code_client || ' non trouvé');
                    RETURN;
            END;
            
            DBMS_OUTPUT.PUT_LINE('Client : ' || v_prenom_client || ' ' || v_nom_client || ' (' || p_code_client || ')');
            DBMS_OUTPUT.PUT_LINE('');
            
            SELECT SUM("duree") INTO v_duree_totale FROM LOCATION WHERE "CodeC" = p_code_client;
            SELECT COUNT(DISTINCT "immat") INTO v_nb_vehicules FROM LOCATION WHERE "CodeC" = p_code_client;
            SELECT AVG("note") INTO v_moyenne_notes FROM LOCATION WHERE "CodeC" = p_code_client AND "note" IS NOT NULL;
            SELECT COUNT(*) INTO v_nb_locations FROM LOCATION WHERE "CodeC" = p_code_client;
            
            DBMS_OUTPUT.PUT_LINE('Nombre de locations : ' || v_nb_locations);
            DBMS_OUTPUT.PUT_LINE('Durée totale : ' || NVL(v_duree_totale, 0) || ' jours');
            DBMS_OUTPUT.PUT_LINE('Nombre de véhicules différents : ' || v_nb_vehicules);
            DBMS_OUTPUT.PUT_LINE('Moyenne des notes : ' || ROUND(NVL(v_moyenne_notes, 0), 2));
            DBMS_OUTPUT.PUT_LINE('========================================');
            
        EXCEPTION
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('❌ Erreur : ' || SQLERRM);
        END ANALYSER_CLIENT;
        """
        cursor.execute(sql_analyser)
        print("   ✅ ANALYSER_CLIENT créée")
        
        # 4. Ajouter colonne "etat" à VOITURE
        print("\n4️⃣  Ajout de la colonne 'etat' à VOITURE...")
        try:
            cursor.execute('''ALTER TABLE VOITURE ADD ("etat" VARCHAR2(20) DEFAULT 'disponible')''')
            print("   ✅ Colonne 'etat' ajoutée")
        except oracledb.DatabaseError as e:
            if "ORA-01430" in str(e) or "column already exists" in str(e):
                print("   ✅ Colonne 'etat' existe déjà")
            else:
                print(f"   ⚠️  {e}")
        
        # 5. Créer la table HISTORIQUE_ETAT_VOITURE
        print("\n5️⃣  Création de la table HISTORIQUE_ETAT_VOITURE...")
        try:
            sql_historique = """
            CREATE TABLE HISTORIQUE_ETAT_VOITURE (
                id_historique NUMBER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
                "Immat" VARCHAR2(10) NOT NULL,
                ancien_etat VARCHAR2(20),
                nouvel_etat VARCHAR2(20) NOT NULL,
                date_changement TIMESTAMP DEFAULT SYSTIMESTAMP,
                motif VARCHAR2(100),
                CONSTRAINT FK_HIST_VOITURE FOREIGN KEY ("Immat") REFERENCES VOITURE("Immat") ON DELETE CASCADE
            )
            """
            cursor.execute(sql_historique)
            print("   ✅ Table HISTORIQUE_ETAT_VOITURE créée")
        except oracledb.DatabaseError as e:
            if "ORA-00955" in str(e) or "already exists" in str(e):
                print("   ✅ Table HISTORIQUE_ETAT_VOITURE existe déjà")
            else:
                print(f"   ⚠️  {e}")
        
        # 6. Procédure MARQUER_VOITURE_RETOURNEE
        print("\n6️⃣  Création de MARQUER_VOITURE_RETOURNEE...")
        sql_retour = """
        CREATE OR REPLACE PROCEDURE MARQUER_VOITURE_RETOURNEE(p_immat IN VARCHAR2, p_motif IN VARCHAR2 DEFAULT 'Retour de location') IS
            v_ancien_etat VARCHAR2(20);
        BEGIN
            SELECT "etat" INTO v_ancien_etat FROM VOITURE WHERE "Immat" = p_immat;
            
            UPDATE VOITURE SET "etat" = 'disponible' WHERE "Immat" = p_immat;
            
            INSERT INTO HISTORIQUE_ETAT_VOITURE ("Immat", ancien_etat, nouvel_etat, motif)
            VALUES (p_immat, v_ancien_etat, 'disponible', p_motif);
            
            COMMIT;
            DBMS_OUTPUT.PUT_LINE('✓ Voiture ' || p_immat || ' marquée comme disponible');
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                DBMS_OUTPUT.PUT_LINE('❌ Voiture ' || p_immat || ' non trouvée');
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('❌ Erreur : ' || SQLERRM);
                ROLLBACK;
        END MARQUER_VOITURE_RETOURNEE;
        """
        cursor.execute(sql_retour)
        print("   ✅ MARQUER_VOITURE_RETOURNEE créée")
        
        # 7. Procédure METTRE_EN_REPARATION
        print("\n7️⃣  Création de METTRE_EN_REPARATION...")
        sql_reparation = """
        CREATE OR REPLACE PROCEDURE METTRE_EN_REPARATION(p_immat IN VARCHAR2, p_raison IN VARCHAR2) IS
            v_ancien_etat VARCHAR2(20);
        BEGIN
            SELECT "etat" INTO v_ancien_etat FROM VOITURE WHERE "Immat" = p_immat;
            
            UPDATE VOITURE SET "etat" = 'en réparation' WHERE "Immat" = p_immat;
            
            INSERT INTO HISTORIQUE_ETAT_VOITURE ("Immat", ancien_etat, nouvel_etat, motif)
            VALUES (p_immat, v_ancien_etat, 'en réparation', p_raison);
            
            COMMIT;
            DBMS_OUTPUT.PUT_LINE('✓ Voiture ' || p_immat || ' en réparation : ' || p_raison);
        EXCEPTION
            WHEN NO_DATA_FOUND THEN
                DBMS_OUTPUT.PUT_LINE('❌ Voiture ' || p_immat || ' non trouvée');
            WHEN OTHERS THEN
                DBMS_OUTPUT.PUT_LINE('❌ Erreur : ' || SQLERRM);
                ROLLBACK;
        END METTRE_EN_REPARATION;
        """
        cursor.execute(sql_reparation)
        print("   ✅ METTRE_EN_REPARATION créée")
        
        print("\n✅ Toutes les procédures et triggers créés avec succès !\n")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        cursor.close()
        conn.close()
        return False


# ========================================
# PARTIE 2 : EXÉCUTER LES PROCÉDURES
# ========================================

def attribuer_notes():
    """Exécute ATTRIBUER_NOTE_LOCATION"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print("\n" + "="*60)
        print("EXÉCUTION : ATTRIBUER_NOTE_LOCATION")
        print("="*60)
        
        cursor.callproc("ATTRIBUER_NOTE_LOCATION")
        
        # Afficher les résultats
        cursor.execute("SELECT \"CodeC\", \"immat\", \"km\", \"duree\", \"note\" FROM LOCATION WHERE \"note\" IS NOT NULL FETCH FIRST 10 ROWS ONLY")
        resultats = cursor.fetchall()
        
        print("\n📊 Exemples de notes attribuées :")
        print("-" * 80)
        print(f"{'Client':<10} {'Immat':<10} {'KM':<8} {'Durée':<8} {'Note':<6}")
        print("-" * 80)
        
        for row in resultats:
            print(f"{row[0]:<10} {row[1]:<10} {row[2]:<8} {row[3]:<8} {row[4]:<6}")
        
        print("-" * 80)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


def mettre_a_jour_avis():
    """Exécute METTRE_A_JOUR_AVIS"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print("\n" + "="*60)
        print("EXÉCUTION : METTRE_A_JOUR_AVIS")
        print("="*60)
        
        cursor.callproc("METTRE_A_JOUR_AVIS")
        
        # Afficher les résultats
        cursor.execute("SELECT \"CodeC\", \"immat\", \"note\", \"avis\" FROM LOCATION WHERE \"avis\" IS NOT NULL FETCH FIRST 10 ROWS ONLY")
        resultats = cursor.fetchall()
        
        print("\n📝 Exemples d'avis attribués :")
        print("-" * 80)
        print(f"{'Client':<10} {'Immat':<10} {'Note':<6} {'Avis':<20}")
        print("-" * 80)
        
        for row in resultats:
            print(f"{row[0]:<10} {row[1]:<10} {row[2]:<6} {row[3]:<20}")
        
        print("-" * 80)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


def analyser_client(code_client):
    """Exécute ANALYSER_CLIENT"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print("\n" + "="*60)
        print(f"EXÉCUTION : ANALYSER_CLIENT ('{code_client}')")
        print("="*60)
        
        # Appeler la procédure (elle affiche le résultat via DBMS_OUTPUT)
        cursor.callproc("ANALYSER_CLIENT", [code_client])
        
        # Récupérer les statistiques manuellement
        sql = f"""
            SELECT 
                COALESCE(SUM(CAST("duree" AS NUMBER)), 0) as duree_totale,
                COUNT(DISTINCT "immat") as nb_vehicules,
                ROUND(COALESCE(AVG(CAST("note" AS NUMBER)), 0), 2) as moyenne_notes,
                COUNT(*) as nb_locations
            FROM LOCATION
            WHERE "CodeC" = '{code_client}'
        """
        
        cursor.execute(sql)
        
        result = cursor.fetchone()
        if result:
            duree_totale, nb_vehicules, moyenne_notes, nb_locations = result
            
            print(f"\n📋 Statistiques du client {code_client} :")
            print("-" * 60)
            print(f"Nombre de locations      : {nb_locations}")
            print(f"Durée totale de location : {int(duree_totale) if duree_totale else 0} jours")
            print(f"Nombre de véhicules      : {nb_vehicules}")
            print(f"Moyenne des notes        : {moyenne_notes if moyenne_notes else 0}")
            print("-" * 60)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


def afficher_etats_voitures():
    """Affiche les états des voitures"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print("\n" + "="*60)
        print("ÉTATS DES VOITURES")
        print("="*60)
        
        cursor.execute("""
            SELECT "Immat", "modele", "Marque", "etat" 
            FROM VOITURE 
            FETCH FIRST 15 ROWS ONLY
        """)
        
        resultats = cursor.fetchall()
        
        print(f"\n{'Immat':<12} {'Modèle':<15} {'Marque':<12} {'État':<20}")
        print("-" * 60)
        
        for row in resultats:
            etat = row[3] or 'disponible'
            print(f"{row[0]:<12} {row[1]:<15} {row[2]:<12} {etat:<20}")
        
        print("-" * 60)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


def afficher_historique():
    """Affiche l'historique des changements d'état"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print("\n" + "="*60)
        print("HISTORIQUE DES CHANGEMENTS D'ÉTAT")
        print("="*60)
        
        cursor.execute("""
            SELECT "Immat", ancien_etat, nouvel_etat, date_changement, motif 
            FROM HISTORIQUE_ETAT_VOITURE 
            ORDER BY date_changement DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        resultats = cursor.fetchall()
        
        if not resultats:
            print("\n✅ Aucun changement d'état pour l'instant")
        else:
            print(f"\n{'Immat':<12} {'Ancien état':<15} {'Nouvel état':<15} {'Date':<20} {'Motif':<30}")
            print("-" * 95)
            
            for row in resultats:
                immat, ancien, nouveau, date_chg, motif = row
                print(f"{immat:<12} {ancien or '-':<15} {nouveau:<15} {str(date_chg)[:19]:<20} {motif or '-':<30}")
            
            print("-" * 95)
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


def marquer_en_reparation(immat, raison):
    """Met une voiture en réparation"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print(f"\n⚙️  Mise en réparation de {immat}...")
        cursor.callproc("METTRE_EN_REPARATION", [immat, raison])
        print(f"✅ {immat} en réparation")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


def marquer_retournee(immat, motif="Retour de location"):
    """Marque une voiture comme retournée"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = conn.cursor()
    try:
        print(f"\n✅ Retour de {immat}...")
        cursor.callproc("MARQUER_VOITURE_RETOURNEE", [immat, motif])
        print(f"✅ {immat} marquée comme disponible")
        
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Erreur : {e}")
        cursor.close()
        conn.close()
        return False


# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("EXERCICE 5 : PL/SQL & TRIGGERS")
    print("="*60)
    
    # Étape 1 : Créer les procédures et triggers
    if creer_procedures_et_triggers():
        
        # Étape 2 : Exécuter ATTRIBUER_NOTE_LOCATION
        attribuer_notes()
        
        # Étape 3 : Exécuter METTRE_A_JOUR_AVIS
        mettre_a_jour_avis()
        
        # Étape 4 : Analyser des clients
        analyser_client('C667')
        analyser_client('C654')
        
        # Étape 5 : Afficher les états des voitures
        afficher_etats_voitures()
        
        # Étape 6 : Mettre une voiture en réparation
        marquer_en_reparation('11RS75', 'Vidange et révision')
        
        # Étape 7 : Marquer comme retournée
        marquer_retournee('11FG62', 'Retour test')
        
        # Étape 8 : Afficher l'historique
        afficher_historique()
        
        print("\n" + "="*60)
        print("✅ EXERCICE 5 COMPLÉTÉ")
        print("="*60)
    else:
        print("\n❌ Impossible de créer les procédures")