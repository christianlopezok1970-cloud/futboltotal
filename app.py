import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import random
import threading
import time

class AFAManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AFA Manager Pro 2026 - Liga Argentina")
        self.root.geometry("1000x750")
        self.root.configure(bg="#f4f4f4")
        
        # --- Datos ---
        self.url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
        try:
            self.df = pd.read_csv(self.url)
            self.df.columns = [c.strip() for c in self.df.columns]
        except Exception as e:
            messagebox.showerror("Error de Conexión", f"No se pudo cargar el Excel: {e}")
            self.root.destroy()

        self.creditos = 0
        self.titulares = []  # Lista de dicts
        self.suplentes = []   # Lista de dicts (máx 25)
        self.historial_log = []

        self.setup_ui()

    def setup_ui(self):
        # PANEL LATERAL (Azul oscuro)
        self.side_panel = tk.Frame(self.root, width=280, bg="#1a252f", padx=15, pady=20)
        self.side_panel.pack(side="left", fill="y")

        # Usuario y Créditos
        tk.Label(self.side_panel, text="MANAGER_01", fg="white", bg="#1a252f", font=("Arial", 12, "bold")).pack()
        self.lbl_creditos = tk.Label(self.side_panel, text=f"$ {self.creditos}", fg="#2ecc71", bg="#1a252f", font=("Consolas", 20, "bold"))
        self.lbl_creditos.pack(pady=20)

        # Botón Comprar con Doble Seguridad
        self.btn_buy = tk.Button(self.side_panel, text="COMPRAR JUGADORES\n(100 Créditos)", bg="#27ae60", fg="white", 
                                font=("Arial", 10, "bold"), height=3, command=self.comprar_pack_confirmado)
        self.btn_buy.pack(fill="x", pady=10)

        # RULETA
        tk.Label(self.side_panel, text="RULETA SEMANAL", fg="#bdc3c7", bg="#1a252f").pack(pady=(30, 5))
        self.lbl_ruleta = tk.Label(self.side_panel, text="--", fg="white", bg="#34495e", font=("Arial", 24, "bold"), height=2)
        self.lbl_ruleta.pack(fill="x", pady=5)
        self.btn_spin = tk.Button(self.side_panel, text="GIRAR (Azar) 🎡", command=self.spin_ruleta, bg="#f39c12", font=("Arial", 10, "bold"))
        self.btn_spin.pack(fill="x")

        # PANEL CENTRAL
        self.main_panel = tk.Frame(self.root, bg="#f4f4f4", padx=20, pady=10)
        self.main_panel.pack(side="right", expand=True, fill="both")

        # Listado Superior: Titulares
        tk.Label(self.main_panel, text="ONCE TITULAR (1-4-4-2)", bg="#f4f4f4", font=("Arial", 11, "bold")).pack(anchor="w")
        self.tree_tit = ttk.Treeview(self.main_panel, columns=("Jugador", "POS", "Nivel", "Equipo", "Score"), show="headings", height=11)
        self.config_tree(self.tree_tit)
        self.tree_tit.pack(fill="x", pady=5)
        tk.Button(self.main_panel, text="MANDAR AL BANCO 🛋️", command=self.mandar_al_banco).pack(anchor="e")

        # Listado Inferior: Suplentes
        tk.Label(self.main_panel, text="BANCO DE SUPLENTES (Máx 25)", bg="#f4f4f4", font=("Arial", 11, "bold")).pack(anchor="w", pady=(20, 0))
        self.tree_sup = ttk.Treeview(self.main_panel, columns=("Jugador", "POS", "Nivel", "Equipo", "Score"), show="headings", height=10)
        self.config_tree(self.tree_sup)
        self.tree_sup.pack(fill="x", pady=5)

        # Botones de Acción
        self.actions_frame = tk.Frame(self.main_panel, bg="#f4f4f4")
        self.actions_frame.pack(fill="x")
        tk.Button(self.actions_frame, text="PONER DE TITULAR ⬆️", bg="#3498db", fg="white", command=self.poner_titular).pack(side="left", padx=5)
        tk.Button(self.actions_frame, text="VENDER JUGADOR (Doble Seguridad) 💰", bg="#e74c3c", fg="white", command=self.vender_confirmado).pack(side="right", padx=5)

        # Historial
        self.txt_historial = tk.Text(self.main_panel, height=4, state="disabled", font=("Courier", 9), bg="#ecf0f1")
        self.txt_historial.pack(fill="x", pady=10)

    def config_tree(self, tree):
        for col in ("Jugador", "POS", "Nivel", "Equipo", "Score"):
            tree.heading(col, text=col)
        tree.column("POS", width=60, anchor="center")
        tree.column("Nivel", width=100, anchor="center")
        tree.column("Score", width=80, anchor="center")

    # --- LÓGICA ---
    def log(self, msj):
        self.txt_historial.config(state="normal")
        self.txt_historial.insert("1.0", f"> {msj}\n")
        self.txt_historial.config(state="disabled")

    def spin_ruleta(self):
        self.btn_spin.config(state="disabled")
        def ani():
            for _ in range(15):
                self.lbl_ruleta.config(text=random.choice(["+1", "0", "-1", "+3"]))
                time.sleep(0.05)
            res = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
            self.creditos += res
            self.lbl_ruleta.config(text=f"{res}c", fg="#2ecc71" if res > 0 else ("#e74c3c" if res < 0 else "white"))
            self.lbl_creditos.config(text=f"$ {self.creditos}")
            self.btn_spin.config(state="normal")
        threading.Thread(target=ani).start()

    def comprar_pack_confirmado(self):
        if self.creditos < 100:
            messagebox.showwarning("Saldo Insuficiente", "Necesitas 100 créditos.")
            return
        if messagebox.askyesno("Confirmación", "¿Comprar 2 jugadores por 100 créditos?"):
            if len(self.suplentes) >= 24:
                messagebox.showerror("Error", "Banco lleno.")
                return
            self.creditos -= 100
            nuevos = self.df.sample(n=2).to_dict('records')
            self.suplentes.extend(nuevos)
            self.log(f"Compraste a {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}")
            self.actualizar_tablas()

    def vender_confirmado(self):
        sel = self.tree_sup.selection()
        if not sel: return
        idx = self.tree_sup.index(sel[0])
        jugador = self.suplentes[idx]
        valor = jugador['Nivel'] * 20
        if messagebox.askyesno("VENDER", f"¿Vender a {jugador['Jugador']} por {valor} créditos?"):
            self.creditos += valor
            self.log(f"Vendido {jugador['Jugador']} (+{valor}c)")
            self.suplentes.pop(idx)
            self.actualizar_tablas()

    def poner_titular(self):
        sel = self.tree_sup.selection()
        if not sel: return
        idx = self.tree_sup.index(sel[0])
        j = self.suplentes[idx]
        
        # Control 1-4-4-2
        conteo = [p['POS'] for p in self.titulares].count(j['POS'])
        reglas = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
        
        if conteo < reglas.get(j['POS'], 0):
            self.titulares.append(self.suplentes.pop(idx))
            self.actualizar_tablas()
        else:
            messagebox.showwarning("Límite", f"Ya tienes suficientes jugadores en la posición {j['POS']}.")

    def mandar_al_banco(self):
        sel = self.tree_tit.selection()
        if not sel: return
        idx = self.tree_tit.index(sel[0])
        if len(self.suplentes) < 25:
            self.suplentes.append(self.titulares.pop(idx))
            self.actualizar_tablas()

    def actualizar_tablas(self):
        self.lbl_creditos.config(text=f"$ {self.creditos}")
        for i in self.tree_tit.get_children(): self.tree_tit.delete(i)
        for i in self.tree_sup.get_children(): self.tree_sup.delete(i)
        
        for j in self.titulares:
            self.tree_tit.insert("", "end", values=(j['Jugador'], j['POS'], "⭐"*int(j['Nivel']), j['Equipo'], j['Score']))
        for j in self.suplentes:
            self.tree_sup.insert("", "end", values=(j['Jugador'], j['POS'], "⭐"*int(j['Nivel']), j['Equipo'], j['Score']))

if __name__ == "__main__":
    root = tk.Tk()
    app = AFAManagerApp(root)
    root.mainloop()
