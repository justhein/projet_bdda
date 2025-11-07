import oracledb
import time
import threading
import hashlib
from datetime import datetime

# ========================================
# CONFIGURATION DE LA CONNEXION
# ========================================

# Paramètres de connexion Oracle
DB_USER = "system"
DB_PASSWORD = "oracle"
DB_HOST = "localhost"
DB_PORT = 1521
DB_SERVICE = "XE"

# Schéma cible
DB_SCHEMA = "AGENCE_VOYAGE"

def get_connection():
    """Crée une nouvelle connexion à la base de données et se connecte au schéma AGENCE_VOYAGE"""
    try:
        # Connexion à system
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
# PARTIE 1 : CRÉER LA TABLE DE TEST
# ========================================

def creer_table_test():
    """Crée la table COMPTE_BANCAIRE pour les tests"""
    conn = get_connection()
    if not conn:
        return False
    
    cursor = None
    try:
        cursor = conn.cursor()
        
        # Supprimer si elle existe
        try:
            cursor.execute("DROP TABLE COMPTE_BANCAIRE")
            conn.commit()
            print("✓ Table existante supprimée")
        except Exception as e:
            print(f"  (Table n'existait pas ou erreur : {e})")
        
        # Créer la nouvelle table
        sql = """
        CREATE TABLE COMPTE_BANCAIRE (
            compte_id NUMBER PRIMARY KEY,
            client_name VARCHAR2(100),
            solde NUMBER(10, 2) NOT NULL,
            date_modification TIMESTAMP DEFAULT SYSTIMESTAMP
        )
        """
        print("📝 Création de la table...")
        cursor.execute(sql)
        conn.commit()
        print("✓ Table créée")
        
        # Insérer les données initiales
        print("📝 Insertion des données...")
        cursor.execute("INSERT INTO COMPTE_BANCAIRE VALUES (1, 'Alice', 1000, SYSTIMESTAMP)")
        cursor.execute("INSERT INTO COMPTE_BANCAIRE VALUES (2, 'Bob', 500, SYSTIMESTAMP)")
        conn.commit()
        print("✅ Table COMPTE_BANCAIRE créée avec succès")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création : {e}")
        if conn:
            conn.rollback()
        return False
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


# ========================================
# PARTIE 2 : PROBLÈME DE MISE À JOUR PERDUE
# ========================================

def demonstration_mise_a_jour_perdue():
    """
    Démontre le problème de mise à jour perdue :
    - Deux transactions modifient le même solde
    - La deuxième écrase la première
    """
    print("\n" + "="*60)
    print("PARTIE 1 : PROBLÈME DE MISE À JOUR PERDUE")
    print("="*60)
    print("Scenario : Deux clients ajoutent de l'argent en même temps")
    print("Alice : solde initial = 1000€")
    print("Session 1 : Ajouter 100€")
    print("Session 2 : Ajouter 50€")
    print("Résultat attendu : 1150€")
    print()
    
    # Réinitialiser le solde
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = 1000 WHERE compte_id = 1")
    conn.commit()
    cursor.close()
    conn.close()
    
    # Variables partagées
    resultats = {}
    
    def session_1():
        """Session 1 : Ajouter 100€"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("[SESSION 1] Lecture du solde...")
            cursor.execute("SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 1")
            solde = cursor.fetchone()[0]
            resultats['session1_solde_initial'] = solde
            print(f"[SESSION 1] Solde lu : {solde}€")
            
            # Simuler le traitement
            time.sleep(1)
            
            nouveau_solde = solde + 100
            print(f"[SESSION 1] Mise à jour : {solde}€ + 100€ = {nouveau_solde}€")
            
            cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = :solde WHERE compte_id = 1", 
                          {"solde": nouveau_solde})
            time.sleep(0.5)  # Garder la transaction ouverte
            
            conn.commit()
            print("[SESSION 1] ✓ Mise à jour validée")
            resultats['session1_final'] = nouveau_solde
            
        except Exception as e:
            print(f"[SESSION 1] ❌ Erreur : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def session_2():
        """Session 2 : Ajouter 50€"""
        time.sleep(0.5)  # Attendre que Session 1 commence
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("[SESSION 2] Lecture du solde...")
            cursor.execute("SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 1")
            solde = cursor.fetchone()[0]
            resultats['session2_solde_initial'] = solde
            print(f"[SESSION 2] Solde lu : {solde}€")
            
            nouveau_solde = solde + 50
            print(f"[SESSION 2] Mise à jour : {solde}€ + 50€ = {nouveau_solde}€")
            
            cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = :solde WHERE compte_id = 1", 
                          {"solde": nouveau_solde})
            
            conn.commit()
            print("[SESSION 2] ✓ Mise à jour validée")
            resultats['session2_final'] = nouveau_solde
            
        except Exception as e:
            print(f"[SESSION 2] ❌ Erreur : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    # Exécuter les deux sessions en parallèle
    t1 = threading.Thread(target=session_1)
    t2 = threading.Thread(target=session_2)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    # Vérifier le résultat final
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 1")
    solde_final = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print("\n" + "-"*60)
    print("RÉSULTATS :")
    print(f"Session 1 : Ajoute 100€ → {resultats.get('session1_final', '?')}€")
    print(f"Session 2 : Ajoute 50€  → {resultats.get('session2_final', '?')}€")
    print(f"Solde final dans la BDD : {solde_final}€")
    print(f"Solde attendu : 1150€")
    print(f"Solde réel : {solde_final}€")
    
    if solde_final == 1150:
        print("✅ PAS DE PROBLÈME (ou par chance)")
    else:
        print(f"❌ MISE À JOUR PERDUE ! Différence : {1150 - solde_final}€")
    print("-"*60)


# ========================================
# PARTIE 3 : PROBLÈME DE LECTURE SALE
# ========================================

def demonstration_lecture_sale():
    """
    Démontre le problème de lecture sale :
    - Session 1 lit des données
    - Session 2 modifie et annule
    - Session 1 a lu des données invalides
    """
    print("\n" + "="*60)
    print("PARTIE 2 : PROBLÈME DE LECTURE SALE (Dirty Read)")
    print("="*60)
    print("Scenario : Session 1 lit une valeur modifiée mais non validée")
    print("Bob : solde initial = 500€")
    print("Session 2 : Modifie à 100€ (mais sans valider)")
    print("Session 1 : Lit et traite avec les 500€ lus")
    print("Session 2 : Fait ROLLBACK (annule)")
    print()
    
    # Réinitialiser le solde
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = 500 WHERE compte_id = 2")
    conn.commit()
    cursor.close()
    conn.close()
    
    resultats = {}
    event_continue = threading.Event()
    
    def session_1_dirty():
        """Session 1 : Lire et traiter"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("[SESSION 1] Lecture du solde de Bob...")
            cursor.execute("SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 2")
            solde = cursor.fetchone()[0]
            resultats['solde_lu'] = solde
            print(f"[SESSION 1] Solde lu : {solde}€")
            
            # Attendre que Session 2 modifie
            event_continue.wait(timeout=3)
            
            # Traiter avec les données lues
            print(f"[SESSION 1] Traitement : transfert de 400€ depuis le solde de {solde}€")
            nouveau_solde = solde - 400
            resultats['solde_apres_traitement'] = nouveau_solde
            
            cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = :solde WHERE compte_id = 2", 
                          {"solde": nouveau_solde})
            conn.commit()
            print(f"[SESSION 1] ✓ Mise à jour : {nouveau_solde}€")
            
        except Exception as e:
            print(f"[SESSION 1] ❌ Erreur : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def session_2_dirty():
        """Session 2 : Modifier sans valider, puis annuler"""
        time.sleep(0.5)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("[SESSION 2] Modification du solde à 100€ (sans valider)...")
            cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = 100 WHERE compte_id = 2")
            print("[SESSION 2] ✓ Modification effectuée (mais pas validée)")
            
            resultats['session2_modifie'] = True
            time.sleep(1)
            
            print("[SESSION 2] ⚠️  ROLLBACK (annulation)")
            conn.rollback()
            resultats['session2_rollback'] = True
            
            # Signaler à Session 1 de continuer
            event_continue.set()
            
        except Exception as e:
            print(f"[SESSION 2] ❌ Erreur : {e}")
        finally:
            cursor.close()
            conn.close()
    
    # Exécuter les deux sessions
    t1 = threading.Thread(target=session_1_dirty)
    t2 = threading.Thread(target=session_2_dirty)
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    # Vérifier le résultat final
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 2")
    solde_final = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    
    print("\n" + "-"*60)
    print("RÉSULTATS :")
    print(f"Session 1 a lu : {resultats.get('solde_lu', '?')}€")
    print(f"Session 2 a modifié à : 100€ (puis ROLLBACK)")
    print(f"Session 1 a calculé : {resultats.get('solde_apres_traitement', '?')}€")
    print(f"Solde final dans la BDD : {solde_final}€")
    
    if solde_final == 100:
        print("✅ RÉSULTAT CORRECT (par chance, Session 2 avait annulé)")
    else:
        print(f"⚠️  LECTURE SALE ! Session 1 a agi sur des données invalides")
    print("-"*60)


# ========================================
# PARTIE 4 : SELECT FOR UPDATE (SOLUTION)
# ========================================

def demonstration_select_for_update():
    """
    Démontre la solution avec SELECT FOR UPDATE :
    - Verrouille les lignes
    - Empêche les conflits
    """
    print("\n" + "="*60)
    print("PARTIE 3 : SOLUTION AVEC SELECT FOR UPDATE")
    print("="*60)
    print("Scenario : Transfert sécurisé avec verrouillage")
    print()
    
    # Réinitialiser les soldes
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = 1000 WHERE compte_id = 1")
    cursor.execute("UPDATE COMPTE_BANCAIRE SET solde = 500 WHERE compte_id = 2")
    conn.commit()
    cursor.close()
    conn.close()
    
    resultats = {}
    event_session2_pret = threading.Event()
    
    def transfert_avec_verrou(compte_source, compte_dest, montant, nom_session):
        """Effectue un transfert sécurisé avec SELECT FOR UPDATE"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print(f"[{nom_session}] Début du transfert : {montant}€")
            
            # Verrouiller le compte source
            print(f"[{nom_session}] Verrouillage du compte source ({compte_source})...")
            cursor.execute(
                f"SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = {compte_source} FOR UPDATE"
            )
            solde_source = cursor.fetchone()[0]
            print(f"[{nom_session}] ✓ Verrou acquis. Solde : {solde_source}€")
            
            # Verrouiller le compte destination
            print(f"[{nom_session}] Verrouillage du compte destination ({compte_dest})...")
            cursor.execute(
                f"SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = {compte_dest} FOR UPDATE"
            )
            solde_dest = cursor.fetchone()[0]
            print(f"[{nom_session}] ✓ Verrou acquis. Solde : {solde_dest}€")
            
            # Vérifier les fonds
            if solde_source < montant:
                print(f"[{nom_session}] ❌ Solde insuffisant !")
                conn.rollback()
                return False
            
            # Signal que les verrous sont acquis
            if nom_session == "SESSION 1":
                event_session2_pret.set()
                time.sleep(2)  # Garder les verrous
            else:
                # Session 2 attend
                event_session2_pret.wait(timeout=5)
            
            # Effectuer le transfert
            print(f"[{nom_session}] Transfert en cours...")
            nouveau_solde_source = solde_source - montant
            nouveau_solde_dest = solde_dest + montant
            
            cursor.execute(
                "UPDATE COMPTE_BANCAIRE SET solde = :solde WHERE compte_id = :compte",
                {"solde": nouveau_solde_source, "compte": compte_source}
            )
            cursor.execute(
                "UPDATE COMPTE_BANCAIRE SET solde = :solde WHERE compte_id = :compte",
                {"solde": nouveau_solde_dest, "compte": compte_dest}
            )
            
            conn.commit()
            print(f"[{nom_session}] ✓ Transfert validé et verrous libérés")
            resultats[nom_session] = "succès"
            return True
            
        except Exception as e:
            print(f"[{nom_session}] ❌ Erreur : {e}")
            conn.rollback()
            resultats[nom_session] = f"erreur: {e}"
            return False
        finally:
            cursor.close()
            conn.close()
    
    # Exécuter les deux transferts
    print("Transfer 1 : Alice → Bob (300€)")
    print("Transfer 2 : Bob → Alice (100€)")
    print()
    
    t1 = threading.Thread(target=lambda: transfert_avec_verrou(1, 2, 300, "SESSION 1"))
    t2 = threading.Thread(target=lambda: transfert_avec_verrou(2, 1, 100, "SESSION 2"))
    
    t1.start()
    t2.start()
    
    t1.join()
    t2.join()
    
    # Vérifier les résultats
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT compte_id, client_name, solde FROM COMPTE_BANCAIRE ORDER BY compte_id")
    resultats_finaux = cursor.fetchall()
    cursor.close()
    conn.close()
    
    print("\n" + "-"*60)
    print("RÉSULTATS FINAUX :")
    for compte_id, client_name, solde in resultats_finaux:
        print(f"{client_name} (Compte {compte_id}) : {solde}€")
    
    print("\nRésumé des transferts :")
    for session, resultat in resultats.items():
        print(f"{session} : {resultat}")
    
    print("-"*60)


# ========================================
# PARTIE 5 : NOWAIT vs WAIT
# ========================================

def demonstration_nowait_vs_wait():
    """
    Démontre la différence entre NOWAIT et WAIT
    """
    print("\n" + "="*60)
    print("BONUS : NOWAIT vs WAIT")
    print("="*60)
    print()
    
    def session_verrou():
        """Acquiert un verrou et le garde"""
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("[VERROU] Acquisition du verrou sur le compte 1...")
            cursor.execute(
                "SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 1 FOR UPDATE"
            )
            print("[VERROU] ✓ Verrou acquis. Garde 5 secondes...")
            time.sleep(5)
            conn.commit()
            print("[VERROU] Verrou libéré")
        except Exception as e:
            print(f"[VERROU] ❌ Erreur : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def session_nowait():
        """Essaie d'acquérir avec NOWAIT"""
        time.sleep(1)  # Attendre que le verrou soit acquis
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("\n[NOWAIT] Tentative d'accès SANS attente...")
            cursor.execute(
                "SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 1 FOR UPDATE NOWAIT"
            )
            print("[NOWAIT] ✓ Verrou acquis")
            conn.commit()
        except oracledb.DatabaseError as e:
            if "ORA-00054" in str(e) or "resource busy" in str(e):
                print("[NOWAIT] ❌ Erreur : Resource busy (NOWAIT ne peut pas attendre)")
            else:
                print(f"[NOWAIT] ❌ Erreur : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    def session_wait():
        """Essaie d'acquérir avec WAIT"""
        time.sleep(1)  # Attendre que le verrou soit acquis
        
        conn = get_connection()
        cursor = conn.cursor()
        
        try:
            print("\n[WAIT] Tentative d'accès en attente de 6 secondes...")
            start = time.time()
            cursor.execute(
                "SELECT solde FROM COMPTE_BANCAIRE WHERE compte_id = 1 FOR UPDATE WAIT 6"
            )
            elapsed = time.time() - start
            print(f"[WAIT] ✓ Verrou acquis après {elapsed:.1f} secondes")
            conn.commit()
        except oracledb.DatabaseError as e:
            elapsed = time.time() - start
            if "ORA-30006" in str(e) or "WAIT timeout" in str(e):
                print(f"[WAIT] ⏱️  Timeout après {elapsed:.1f} secondes (WAIT expiré)")
            else:
                print(f"[WAIT] ❌ Erreur : {e}")
            conn.rollback()
        finally:
            cursor.close()
            conn.close()
    
    # Test NOWAIT
    print("TEST 1 : NOWAIT (erreur immédiate si verrouillé)")
    t_verrou = threading.Thread(target=session_verrou)
    t_nowait = threading.Thread(target=session_nowait)
    
    t_verrou.start()
    t_nowait.start()
    
    t_verrou.join()
    t_nowait.join()
    
    time.sleep(2)
    
    # Test WAIT
    print("\n" + "-"*60)
    print("TEST 2 : WAIT 6 (attend jusqu'à 6 secondes)")
    t_verrou = threading.Thread(target=session_verrou)
    t_wait = threading.Thread(target=session_wait)
    
    t_verrou.start()
    t_wait.start()
    
    t_verrou.join()
    t_wait.join()


# ========================================
# MAIN
# ========================================

if __name__ == "__main__":
    print("\n" + "="*60)
    print("DÉMONSTRATION DES PROBLÈMES DE CONCURRENCE EN PYTHON")
    print("="*60)
    
    # Créer la table
    if creer_table_test():
        # Exécuter les démonstrations
        demonstration_mise_a_jour_perdue()
        demonstration_lecture_sale()
        demonstration_select_for_update()
        demonstration_nowait_vs_wait()
        
        print("\n" + "="*60)
        print("✅ EXERCICE TERMINÉ")
        print("="*60)
    else:
        print("❌ Impossible de procéder sans la table de test")