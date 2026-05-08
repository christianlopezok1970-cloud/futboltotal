import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# --- 1. CONFIGURACIÓN Y DB ---
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
ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT, 
              posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER)''', commit=True)

# --- 2. ESTILO (Mix entre el DT y el Azul) ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0e1117 0%, #000814 100%); }
    .stMetric { background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CARGA DE DATOS ---
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

# --- 4. AUTENTICACIÓN ---
with st.sidebar:
    st.title("🛡️ ACCESO MANAGER")
    manager = st.text_input("Manager").strip()
    password = st.text_input("Password", type="password").strip()

    if not manager or not password:
        st.info("Ingresa tus credenciales para jugar.")
        st.stop()

    datos = ejecutar_db("SELECT id, monedas, password FROM usuarios WHERE nombre = ?", (manager,))
    
    if not datos:
        if st.button("CREAR NUEVA CUENTA"):
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas) VALUES (?, ?, 1000)", (manager, password), commit=True)
            st.success("Cuenta creada. ¡Vuelve a pulsar para entrar!")
            st.rerun()
        st.stop()
    else:
        u_id, monedas, u_pass = datos[0]
        if password != u_pass:
            st.error("Contraseña incorrecta")
            st.stop()
        st.success(f"Bienvenido, {manager}")

# --- 5. LÓGICA DE JUEGO (Sincronización con DB) ---
jugadores_db = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id FROM plantilla WHERE usuario_id = ?", (u_id,))
titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

st.markdown(f"### ⚽ VIRTUAL DT - Manager: {manager}")

c_pres, c_recom = st.columns(2)
c_pres.metric("Presupuesto Actual", f"{int(monedas)} 🪙")

# --- BLOQUE CORREGIDO CON SEGURIDAD ---
if len(titulares) == 11:
    ganancia = sum([int((j[4]-64)*3) if j[4]>=65 else int(j[4]-65) for j in titulares])
    c_recom.markdown(f"**Balance Proyectado:** \n{ganancia} 🪙")
    
    if 'confirmar_cobro' not in st.session_state:
        st.session_state.confirmar_cobro = False

    if not st.session_state.confirmar_cobro:
        if c_recom.button("💰 COBRAR JORNADA", use_container_width=True):
            st.session_state.confirmar_cobro = True
            st.rerun()
    else:
        col_si, col_no = c_recom.columns(2)
        if col_si.button("⚠️ CONFIRMAR", type="primary", use_container_width=True):
            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (ganancia, u_id), commit=True)
            st.session_state.confirmar_cobro = False
            st.toast(f"¡Cobraste {ganancia} monedas!")
            st.rerun()
        if col_no.button("CANCELAR", use_container_width=True):
            st.session_state.confirmar_cobro = False
            st.rerun()
else:
    c_recom.warning(f"Faltan {11 - len(titulares)} titulares")
# --- 6. RENDERIZADO DE CANCHA ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    for i, pos_key in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{MAPPING_POS[pos_key]}**")
            # Filtrar jugadores por posición en la lista (index 1 es POS)
            jugs_pos = [j for j in lista if j[1] == pos_key]
            for j in jugs_pos:
                with st.expander(f"{j[0]}"):
                    st.caption(f"{j[3]} | {'★' * int(j[2])}")
                    st.write(f"Score: {j[4]}")
                    
                    if modo == "titular":
                        if st.button("⬇️ Bajar", key=f"down_{j[6]}"):
                            ejecutar_db("UPDATE plantilla SET es_titular = 0 WHERE id = ?", (j[6],), commit=True)
                            st.rerun()
                    else:
                        if st.button("⬆️ Subir", key=f"up_{j[6]}"):
                            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                            actual = len([p for p in titulares if p[1] == pos_key])
                            if len(titulares) < 11 and actual < limites.get(pos_key, 0):
                                ejecutar_db("UPDATE plantilla SET es_titular = 1 WHERE id = ?", (j[6],), commit=True)
                                st.rerun()
                            else: st.error("Límite!")
                        
                        precio_venta = int(j[2]) * 20
                        if st.button(f"Vender ${precio_venta}", key=f"sell_{j[6]}"):
                            ejecutar_db("DELETE FROM plantilla WHERE id = ?", (j[6],), commit=True)
                            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (precio_venta, u_id), commit=True)
                            st.rerun()

st.divider()
st.subheader("🏃 TITULARES")
dibujar_plantilla(titulares, modo="titular")

st.divider()
st.subheader("📦 BANCO DE SUPLENTES")
if st.button("🛒 FICHAR JUGADOR (50 🪙)", use_container_width=True):
    if monedas >= 50:
        nuevo = df_base.sample(n=1).iloc[0]
        ejecutar_db('''INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) 
                       VALUES (?,?,?,?,?,?,0)''', 
                    (u_id, nuevo['Jugador'], nuevo['POS'], int(nuevo['Nivel']), nuevo['Equipo'], float(nuevo['Score'])), commit=True)
        ejecutar_db("UPDATE usuarios SET monedas = monedas - 50 WHERE id = ?", (u_id,), commit=True)
        st.rerun()
    else: st.error("Sin monedas")

dibujar_plantilla(suplentes, modo="suplente")

# --- 7. RANKING COMPARTIDO ---
st.divider()
with st.expander("🏆 RANKING GLOBAL DE MANAGERS"):
    ranking = ejecutar_db("SELECT nombre, monedas FROM usuarios ORDER BY monedas DESC")
    st.table(pd.DataFrame(ranking, columns=["Manager", "Monedas"]))
