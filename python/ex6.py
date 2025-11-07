import tkinter as tk
from tkinter import ttk, messagebox
import oracledb
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

# ========================================
# CONFIGURATION
# ========================================

# Tkinter = Interface graphique
# Treeview = Tableau de données
# oracledb = Récupération des données
# Classes CRUD = Logique métier

DB_USER = "system"
DB_PASSWORD = "oracle"
DB_HOST = "localhost"
DB_PORT = 1521
DB_SERVICE = "XE"
DB_SCHEMA = "AGENCE_VOYAGE"

class DatabaseConnection:
    """Gère la connexion à la base de données"""
    
    @staticmethod
    def get_connection():
        try:
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                service_name=DB_SERVICE
            )
            cursor = conn.cursor()
            cursor.execute(f"ALTER SESSION SET CURRENT_SCHEMA={DB_SCHEMA}")
            cursor.close()
            return conn
        except oracledb.DatabaseError as e:
            raise Exception(f"Erreur de connexion : {e}")


# ========================================
# OPÉRATIONS CRUD - CLIENT
# ========================================

class ClientCRUD:
    """Opérations CRUD pour la table CLIENT"""
    
    @staticmethod
    def create(nom, prenom, age, permis, adresse, ville):
        """CREATE - Ajouter un nouveau client"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT MAX(SUBSTR(\"CodeC\", 2)) FROM CLIENT")
            max_id = cursor.fetchone()[0]
            new_id = f"C{int(max_id or 0) + 1}"
            
            sql = """
            INSERT INTO CLIENT ("CodeC", "Nom", "Prenom", "age", "Permis", "Adresse", "Ville")
            VALUES (:1, :2, :3, :4, :5, :6, :7)
            """
            cursor.execute(sql, [new_id, nom, prenom, age, permis, adresse, ville])
            conn.commit()
            return f"✅ Client {new_id} créé avec succès"
        except Exception as e:
            conn.rollback()
            return f"❌ Erreur : {e}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def read(code_client=None):
        """READ - Récupérer les clients"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            if code_client:
                sql = 'SELECT * FROM CLIENT WHERE "CodeC" = :1'
                cursor.execute(sql, [code_client])
            else:
                sql = 'SELECT * FROM CLIENT FETCH FIRST 50 ROWS ONLY'
                cursor.execute(sql)
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return columns, rows
        except Exception as e:
            return None, f"❌ Erreur : {e}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def update(code_client, nom=None, prenom=None, age=None, adresse=None, ville=None):
        """UPDATE - Mettre à jour un client"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            updates = []
            params = []
            
            if nom:
                updates.append('"Nom" = :1')
                params.append(nom)
            if prenom:
                updates.append('"Prenom" = :2')
                params.append(prenom)
            if age:
                updates.append('"age" = :3')
                params.append(age)
            if adresse:
                updates.append('"Adresse" = :4')
                params.append(adresse)
            if ville:
                updates.append('"Ville" = :5')
                params.append(ville)
            
            if not updates:
                return "⚠️  Aucun champ à mettre à jour"
            
            params.append(code_client)
            sql = f'UPDATE CLIENT SET {", ".join(updates)} WHERE "CodeC" = :{len(params)}'
            cursor.execute(sql, params)
            conn.commit()
            return f"✅ Client {code_client} mis à jour"
        except Exception as e:
            conn.rollback()
            return f"❌ Erreur : {e}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def delete(code_client):
        """DELETE - Supprimer un client"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            sql = 'DELETE FROM CLIENT WHERE "CodeC" = :1'
            cursor.execute(sql, [code_client])
            conn.commit()
            return f"✅ Client {code_client} supprimé"
        except Exception as e:
            conn.rollback()
            return f"❌ Erreur : {e}"
        finally:
            cursor.close()
            conn.close()
    
    @staticmethod
    def search(critere, valeur):
        """SEARCH - Rechercher des clients"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        try:
            sql = f'SELECT * FROM CLIENT WHERE "{critere}" LIKE :1'
            cursor.execute(sql, [f"%{valeur}%"])
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            return columns, rows
        except Exception as e:
            return None, f"❌ Erreur : {e}"
        finally:
            cursor.close()
            conn.close()


# ========================================
# APPLICATION GUI
# ========================================

class AgenceVoyageApp:
    """Application GUI pour la gestion de l'agence de location"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 Gestion Agence de Location - Base de Données")
        self.root.geometry("1400x800")
        
        # Créer le notebook (onglets)
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Onglets
        self.create_crud_tab()
        self.create_visualization_tab()
        self.create_statistics_tab()
        
    def create_crud_tab(self):
        """Crée l'onglet CRUD"""
        crud_frame = ttk.Frame(self.notebook)
        self.notebook.add(crud_frame, text="📋 CRUD Opérations")
        
        client_frame = ttk.LabelFrame(crud_frame, text="Gestion des Clients", padding=10)
        client_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        button_frame = ttk.Frame(client_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        ttk.Button(button_frame, text="➕ Créer Client", command=self.create_client_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📖 Lire Clients", command=self.read_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="✏️  Mettre à jour", command=self.update_client_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🗑️  Supprimer", command=self.delete_client_window).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🔍 Rechercher", command=self.search_client_window).pack(side=tk.LEFT, padx=5)
        
        self.crud_tree = ttk.Treeview(client_frame)
        self.crud_tree.pack(fill=tk.BOTH, expand=True, pady=10)
        
        scrollbar = ttk.Scrollbar(client_frame, orient=tk.VERTICAL, command=self.crud_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.crud_tree.configure(yscrollcommand=scrollbar.set)
    
    def create_client_window(self):
        """Fenêtre pour créer un client"""
        window = tk.Toplevel(self.root)
        window.title("Créer un nouveau client")
        window.geometry("400x300")
        
        ttk.Label(window, text="Nom :").grid(row=0, column=0, padx=10, pady=5)
        nom_entry = ttk.Entry(window)
        nom_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Prénom :").grid(row=1, column=0, padx=10, pady=5)
        prenom_entry = ttk.Entry(window)
        prenom_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Âge :").grid(row=2, column=0, padx=10, pady=5)
        age_entry = ttk.Entry(window)
        age_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Permis :").grid(row=3, column=0, padx=10, pady=5)
        permis_entry = ttk.Entry(window)
        permis_entry.grid(row=3, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Adresse :").grid(row=4, column=0, padx=10, pady=5)
        adresse_entry = ttk.Entry(window)
        adresse_entry.grid(row=4, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Ville :").grid(row=5, column=0, padx=10, pady=5)
        ville_entry = ttk.Entry(window)
        ville_entry.grid(row=5, column=1, padx=10, pady=5)
        
        def save_client():
            result = ClientCRUD.create(
                nom_entry.get(), prenom_entry.get(), int(age_entry.get()),
                permis_entry.get(), adresse_entry.get(), ville_entry.get()
            )
            messagebox.showinfo("Résultat", result)
            window.destroy()
        
        ttk.Button(window, text="Créer", command=save_client).grid(row=6, column=1, pady=20)
    
    def read_clients(self):
        """Affiche tous les clients"""
        columns, rows = ClientCRUD.read()
        self.display_data(columns, rows)
    
    def update_client_window(self):
        """Fenêtre pour mettre à jour un client"""
        window = tk.Toplevel(self.root)
        window.title("Mettre à jour un client")
        window.geometry("400x250")
        
        ttk.Label(window, text="Code Client :").grid(row=0, column=0, padx=10, pady=5)
        code_entry = ttk.Entry(window)
        code_entry.grid(row=0, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Nouveau Nom (optionnel) :").grid(row=1, column=0, padx=10, pady=5)
        nom_entry = ttk.Entry(window)
        nom_entry.grid(row=1, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Nouveau Prénom (optionnel) :").grid(row=2, column=0, padx=10, pady=5)
        prenom_entry = ttk.Entry(window)
        prenom_entry.grid(row=2, column=1, padx=10, pady=5)
        
        ttk.Label(window, text="Nouvelle Ville (optionnel) :").grid(row=3, column=0, padx=10, pady=5)
        ville_entry = ttk.Entry(window)
        ville_entry.grid(row=3, column=1, padx=10, pady=5)
        
        def update_client():
            result = ClientCRUD.update(
                code_entry.get(),
                nom=nom_entry.get() or None,
                prenom=prenom_entry.get() or None,
                ville=ville_entry.get() or None
            )
            messagebox.showinfo("Résultat", result)
            window.destroy()
        
        ttk.Button(window, text="Mettre à jour", command=update_client).grid(row=4, column=1, pady=20)
    
    def delete_client_window(self):
        """Fenêtre pour supprimer un client"""
        window = tk.Toplevel(self.root)
        window.title("Supprimer un client")
        window.geometry("300x100")
        
        ttk.Label(window, text="Code Client à supprimer :").pack(padx=10, pady=10)
        code_entry = ttk.Entry(window)
        code_entry.pack(padx=10, pady=5)
        
        def delete_client():
            if messagebox.askyesno("Confirmation", "Êtes-vous sûr ?"):
                result = ClientCRUD.delete(code_entry.get())
                messagebox.showinfo("Résultat", result)
                window.destroy()
        
        ttk.Button(window, text="Supprimer", command=delete_client).pack(pady=10)
    
    def search_client_window(self):
        """Fenêtre pour rechercher des clients"""
        window = tk.Toplevel(self.root)
        window.title("Rechercher des clients")
        window.geometry("400x150")
        
        ttk.Label(window, text="Critère de recherche :").pack(padx=10, pady=5)
        
        ttk.Label(window, text="Champ :").pack(side=tk.LEFT, padx=10)
        critere_var = tk.StringVar(value="Nom")
        critere_combo = ttk.Combobox(window, textvariable=critere_var, values=["Nom", "Prenom", "Ville"])
        critere_combo.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(window, text="Valeur :").pack(side=tk.LEFT, padx=10)
        valeur_entry = ttk.Entry(window)
        valeur_entry.pack(side=tk.LEFT, padx=5)
        
        def search():
            columns, rows = ClientCRUD.search(critere_var.get(), valeur_entry.get())
            self.display_data(columns, rows)
            window.destroy()
        
        ttk.Button(window, text="Rechercher", command=search).pack(pady=10)
    
    def display_data(self, columns, rows):
        """Affiche les données dans le tableau"""
        for item in self.crud_tree.get_children():
            self.crud_tree.delete(item)
        
        self.crud_tree['columns'] = columns
        self.crud_tree.column('#0', width=0, stretch=tk.NO)
        
        for col in columns:
            self.crud_tree.column(col, anchor=tk.CENTER, width=100)
            self.crud_tree.heading(col, text=col, anchor=tk.CENTER)
        
        for row in rows:
            self.crud_tree.insert(parent='', index='end', text='', values=row)
    
    def create_visualization_tab(self):
        """Crée l'onglet Visualisations"""
        viz_frame = ttk.Frame(self.notebook)
        self.notebook.add(viz_frame, text="📊 Visualisations")
        
        button_frame = ttk.Frame(viz_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="📈 Graphique 1 : Clients par ville", command=self.viz_clients_par_ville).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📈 Graphique 2 : Âge des clients", command=self.viz_age_clients).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📈 Graphique 3 : Locations par mois", command=self.viz_locations_par_mois).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📈 Graphique 4 : Top véhicules", command=self.viz_top_vehicules).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="📈 Graphique 5 : Notes de locations", command=self.viz_notes_locations).pack(side=tk.LEFT, padx=5)
        
        self.viz_frame = ttk.Frame(viz_frame)
        self.viz_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def viz_clients_par_ville(self):
        """Visualisation 1 : Clients par ville"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT "Ville", COUNT(*) FROM CLIENT GROUP BY "Ville"')
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data:
            messagebox.showwarning("Attention", "Aucune donnée")
            return
        
        villes = [row[0] for row in data]
        counts = [row[1] for row in data]
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.bar(villes, counts, color='skyblue', edgecolor='navy')
        ax.set_xlabel('Ville')
        ax.set_ylabel('Nombre de clients')
        ax.set_title('📍 Nombre de clients par ville')
        fig.tight_layout()
        
        self.display_graph(fig)
    
    def viz_age_clients(self):
        """Visualisation 2 : Distribution des âges"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT "age" FROM CLIENT WHERE "age" IS NOT NULL')
        ages = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        
        if not ages:
            messagebox.showwarning("Attention", "Aucune donnée")
            return
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.hist(ages, bins=10, color='lightcoral', edgecolor='black')
        ax.set_xlabel('Âge')
        ax.set_ylabel('Nombre de clients')
        ax.set_title('👥 Distribution des âges des clients')
        fig.tight_layout()
        
        self.display_graph(fig)
    
    def viz_locations_par_mois(self):
        """Visualisation 3 : Locations par mois"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT "mois", COUNT(*) FROM LOCATION GROUP BY "mois" ORDER BY "mois"')
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data:
            messagebox.showwarning("Attention", "Aucune donnée")
            return
        
        mois = [f"Mois {row[0]}" for row in data]
        counts = [row[1] for row in data]
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(mois, counts, marker='o', color='green', linewidth=2)
        ax.set_xlabel('Mois')
        ax.set_ylabel('Nombre de locations')
        ax.set_title('📅 Nombre de locations par mois')
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        
        self.display_graph(fig)
    
    def viz_top_vehicules(self):
        """Visualisation 4 : Top 10 véhicules les plus loués"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT LOCATION."immat", COUNT(*) as nb_locations
            FROM LOCATION
            GROUP BY LOCATION."immat"
            ORDER BY nb_locations DESC
            FETCH FIRST 10 ROWS ONLY
        """)
        
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data:
            messagebox.showwarning("Attention", "Aucune donnée")
            return
        
        immat = [row[0] for row in data]
        counts = [row[1] for row in data]
        
        fig = Figure(figsize=(10, 5), dpi=100)
        ax = fig.add_subplot(111)
        ax.barh(immat, counts, color='mediumpurple', edgecolor='purple')
        ax.set_xlabel('Nombre de locations')
        ax.set_title('🏆 Top 10 véhicules les plus loués')
        fig.tight_layout()
        
        self.display_graph(fig)
    
    def viz_notes_locations(self):
        """Visualisation 5 : Distribution des notes"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT "note", COUNT(*) FROM LOCATION WHERE "note" IS NOT NULL GROUP BY "note" ORDER BY "note"')
        data = cursor.fetchall()
        cursor.close()
        conn.close()
        
        if not data:
            messagebox.showwarning("Attention", "Aucune donnée")
            return
        
        notes = [str(int(row[0])) if row[0] else 'NULL' for row in data]
        counts = [row[1] for row in data]
        
        fig = Figure(figsize=(8, 4), dpi=100)
        ax = fig.add_subplot(111)
        colors = ['#ff6b6b', '#feca57', '#48dbfb', '#1dd1a1', '#5f27cd']
        ax.pie(counts, labels=notes, autopct='%1.1f%%', colors=colors[:len(notes)], startangle=90)
        ax.set_title('⭐ Distribution des notes de locations')
        fig.tight_layout()
        
        self.display_graph(fig)
    
    def display_graph(self, fig):
        """Affiche le graphique"""
        for widget in self.viz_frame.winfo_children():
            widget.destroy()
        
        canvas = FigureCanvasTkAgg(fig, master=self.viz_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def create_statistics_tab(self):
        """Crée l'onglet Statistiques"""
        stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(stats_frame, text="📊 Statistiques")
        
        button_frame = ttk.Frame(stats_frame)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Button(button_frame, text="📋 Résumé général", command=self.show_summary).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="💰 Statistiques locations", command=self.show_location_stats).pack(side=tk.LEFT, padx=5)
        ttk.Button(button_frame, text="🚗 Statistiques véhicules", command=self.show_vehicle_stats).pack(side=tk.LEFT, padx=5)
        
        self.stats_text = tk.Text(stats_frame, height=20, width=80)
        self.stats_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        scrollbar = ttk.Scrollbar(stats_frame, orient=tk.VERTICAL, command=self.stats_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.stats_text.configure(yscrollcommand=scrollbar.set)
    
    def show_summary(self):
        """Affiche un résumé général"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM CLIENT")
        nb_clients = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM VOITURE")
        nb_voitures = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM LOCATION")
        nb_locations = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT \"Ville\") FROM CLIENT")
        nb_villes = cursor.fetchone()[0]
        
        cursor.execute("SELECT AVG(\"age\") FROM CLIENT")
        age_moyen = cursor.fetchone()[0]
        
        cursor.close()
        conn.close()
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"""
════════════════════════════════════════════
📊 RÉSUMÉ GÉNÉRAL
════════════════════════════════════════════

👥 Nombre de clients              : {nb_clients}
🚗 Nombre de véhicules            : {nb_voitures}
📅 Nombre de locations            : {nb_locations}
🌍 Nombre de villes               : {nb_villes}
📈 Âge moyen des clients           : {age_moyen:.1f} ans

════════════════════════════════════════════
        """)
    
    def show_location_stats(self):
        """Affiche les statistiques des locations"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(*) as nb_locations,
                SUM("km") as total_km,
                AVG("km") as moyenne_km,
                AVG("duree") as moyenne_duree,
                AVG("note") as moyenne_note
            FROM LOCATION
        """)
        
        row = cursor.fetchone()
        cursor.close()
        conn.close()
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"""
════════════════════════════════════════════
📅 STATISTIQUES DES LOCATIONS
════════════════════════════════════════════

📋 Nombre total de locations      : {row[0]}
🛣️  Kilométrage total             : {row[1] or 0:.0f} km
🛣️  Kilométrage moyen par location: {row[2] or 0:.0f} km
⏱️  Durée moyenne de location      : {row[3] or 0:.1f} jours
⭐ Note moyenne                    : {row[4] or 0:.2f} / 5

════════════════════════════════════════════
        """)
    
    def show_vehicle_stats(self):
        """Affiche les statistiques des véhicules"""
        conn = DatabaseConnection.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT 
                COUNT(DISTINCT "Marque") as nb_marques,
                COUNT(*) as nb_voitures
            FROM VOITURE
        """)
        
        row = cursor.fetchone()
        
        cursor.execute("""
            SELECT "Marque", COUNT(*) 
            FROM VOITURE 
            GROUP BY "Marque"
            ORDER BY COUNT(*) DESC
        """)
        
        marques = cursor.fetchall()
        cursor.close()
        conn.close()
        
        marques_text = "\n".join([f"  • {m[0]}: {m[1]} voitures" for m in marques])
        
        self.stats_text.delete(1.0, tk.END)
        self.stats_text.insert(tk.END, f"""
════════════════════════════════════════════
🚗 STATISTIQUES DES VÉHICULES
════════════════════════════════════════════

🏭 Nombre de marques               : {row[0]}
🚗 Nombre total de véhicules       : {row[1]}

Répartition par marque:
{marques_text}

════════════════════════════════════════════
        """)


if __name__ == "__main__":
    root = tk.Tk()
    app = AgenceVoyageApp(root)
    root.mainloop()