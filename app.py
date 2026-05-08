import streamlit as st
import pandas as pd
import sqlite3
import json
from datetime import datetime

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="Futbol Total - Pro", layout="wide")
DB_NAME = 'virtual_dt_pro.db'

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# Inicializar Tablas
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL)''', commit=True)

# Parche de seguridad para la columna prestigio
try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN prestigio INTEGER DEFAULT 0", commit=True)
except:
    pass

ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT UNIQUE, 
              posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER)''', commit=True)
# Nota: jugador_nombre ahora es UNIQUE para evitar duplicados a nivel base de datos.

# --- 2. FUNCIONES DE APOYO ---
def generar_backup(u_id):
    user_data = ejecutar_db("SELECT nombre, monedas, prestigio FROM usuarios WHERE id = ?", (u_id,))
    if not user_data: return "{}"
    user = user_data[0]
    plantilla = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular FROM plantilla WHERE usuario_id = ?", (u_id,))
    return json.dumps({
        "manager": user[0], "monedas": user[1], "prestigio": user[2],
        "jugadores": [{"nombre": j[0], "pos": j[1], "nivel": j[2], "equipo": j[3], "score": j[4], "titular": j[5]} for j in plantilla]
    }, indent=4)

# --- 3. ESTILO VISUAL ---
st.markdown("<style>.stApp { background: linear-gradient(180deg, #0e1117 0%, #000814 100%); } .stMetric { background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; }</style>", unsafe_allow_html=True)

# --- 4. CARGA DE DATOS ---
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(50)
        df['Nivel'] = pd.to_numeric(df['Nivel'], errors='coerce').fillna(1)
        return df
    except:
        return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score"])

df_base = load_data()

# --- 5. AUTENTICACIÓN ---
with st.sidebar:
    st.title("🛡️ ACCESO")
    manager = st.text_input("Manager").strip()
    password = st.text_input("Password", type="password").strip()

    if not manager or not password:
        st.info("Ingresa para jugar.")
        st.stop()

    datos = ejecutar_db("SELECT id, monedas, prestigio, password FROM usuarios WHERE nombre = ?", (manager,))
    if not datos:
        if st.button("CREAR CUENTA"):
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas, prestigio) VALUES (?, ?, 1000, 0)", (manager, password), commit=True)
            st.success("¡Creado! Reingresa.")
            st.rerun()
        st.stop()
    else:
        u_id, monedas, prestigio, u_pass = datos[0]
        if password != u_pass: st.error("Error de password"); st.stop()
        st.success(f"Manager: {manager}")

    st.divider()
    if not st.toggle("🔒 Bloquear Reset", value=True):
        if st.button("🔴 RESETEAR CUENTA"):
            ejecutar_db("DELETE FROM plantilla WHERE usuario_id = ?", (u_id,), commit=True)
            ejecutar_db("UPDATE usuarios SET monedas = 1000, prestigio = 0 WHERE id = ?", (u_id,), commit=True)
            st.rerun()
    st.download_button("📥 Backup JSON", generar_backup(u_id), f"vdt_{manager}.json", use_container_width=True)

# --- 6. LÓGICA DE JUEGO ---
jugadores_db = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id FROM plantilla WHERE usuario_id = ?", (u_id,))
titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

st.markdown("### ⚽ VIRTUAL DT PRO")
c1, c2 = st.columns(2)
c1.metric("Presupuesto", f"{int(monedas)} 🪙")

if len(titulares) == 11:
    ganancia = sum([int((j[4]-64)*3) if j[4]>=65 else int(j[4]-65) for j in titulares])
    c2.markdown(f"**Balance:** {ganancia} 🪙")
    if 'c_cobro' not in st.session_state: st.session_state.c_cobro = False
    if not st.session_state.c_cobro:
        if c2.button("💰 COBRAR", use_container_width=True):
            st.session_state.c_cobro = True; st.rerun()
    else:
        if c2.button("✅ CONFIRMAR", type="primary", use_container_width=True):
            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (ganancia, u_id), commit=True)
            st.session_state.c_cobro = False; st.rerun()
        if c2.button("Cancelar"): st.session_state.c_cobro = False; st.rerun()
else:
    c2.warning(f"Faltan {11-len(titulares)} titulares")

# --- 7. RENDERIZADO ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    for i, pk in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{MAPPING_POS[pk]}**")
            for j in [x for x in lista if x[1] == pk]:
                with st.expander(f"{j[0]}"):
                    st.caption(f"{j[3]} | {'★' * int(j[2])}")
                    if modo == "titular":
                        if st.button("⬇️ Bajar", key=f"d_{j[6]}"):
                            ejecutar_db("UPDATE plantilla SET es_titular = 0 WHERE id = ?", (j[6],), commit=True); st.rerun()
                    else:
                        if st.button("⬆️ Subir", key=f"u_{j[6]}"):
                            lim = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                            if len(titulares) < 11 and len([p for p in titulares if p[1]==pk]) < lim[pk]:
                                ejecutar_db("UPDATE plantilla SET es_titular = 1 WHERE id = ?", (j[6],), commit=True); st.rerun()
                        p_v = int(j[2]) * 20
                        if st.button(f"Vender {p_v} 🪙", key=f"v_{j[6]}"):
                            ejecutar_db("DELETE FROM plantilla WHERE id = ?", (j[6],), commit=True)
                            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (p_v, u_id), commit=True); st.rerun()

st.divider()
st.subheader("🏃 TITULARES")
dibujar_plantilla(titulares, "titular")
st.divider()
st.subheader("📦 SUPLENTES")

if st.button("🛒 FICHAR JUGADOR (50 🪙)", use_container_width=True):
    if monedas >= 50:
        # 1. Obtener lista de nombres de jugadores ya comprados (Global)
        ocupados = [x[0] for x in ejecutar_db("SELECT jugador_nombre FROM plantilla")]
        
        # 2. Filtrar el DataFrame para obtener solo los disponibles
        disponibles = df_base[~df_base['Jugador'].isin(ocupados)]
        
        if not disponibles.empty:
            n = disponibles.sample(n=1).iloc[0]
            try:
                ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", 
                            (u_id, n['Jugador'], n['POS'], int(n['Nivel']), n['Equipo'], float(n['Score'])), commit=True)
                ejecutar_db("UPDATE usuarios SET monedas = monedas - 50 WHERE id = ?", (u_id,), commit=True)
                st.toast(f"¡Fichaste a {n['Jugador']}!")
                st.rerun()
            except sqlite3.IntegrityError:
                st.error("Error de duplicado. Intenta de nuevo.")
        else:
            st.error("¡No quedan jugadores disponibles en el mercado!")
    else: st.error("No tienes monedas.")

dibujar_plantilla(suplentes, "suplente")

# --- 8. RANKING ---
st.divider()
with st.expander("🏆 RANKING"):
    usrs = ejecutar_db("SELECT id, nombre, monedas, prestigio FROM usuarios")
    lb = []
    for u in usrs:
        val_j = sum([x[0]*20 for x in ejecutar_db("SELECT nivel FROM plantilla WHERE usuario_id=?", (u[0],))])
        total = int(u[2] + val_j + (u[3]*100))
        lb.append({"Manager": u[1], "Valor Total 💎": total, "Prestigio": u[3]})
    st.table(pd.DataFrame(lb).sort_values("Valor Total 💎", ascending=False))
