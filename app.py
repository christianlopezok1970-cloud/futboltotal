import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURACIÓN DE BASE DE DATOS Y DATOS ---
DB_NAME = 'futboltotal.db' 
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# Inicializar tablas
ejecutar_db('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, presupuesto REAL, prestigio INTEGER)', commit=True)
ejecutar_db('CREATE TABLE IF NOT EXISTS cartera (id INTEGER PRIMARY KEY, usuario_id INTEGER, nombre_jugador TEXT, club TEXT, posicion TEXT)', commit=True)

@st.cache_data(ttl=60)
def cargar_jugadores():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        # Limpieza de datos
        df['ValorNum'] = df.iloc[:, 3].apply(lambda x: int(''.join(filter(str.isdigit, str(x)))) if pd.notnull(x) else 1000000)
        df['Posicion'] = df.iloc[:, 2].astype(str).str.upper().str.strip()
        df['Display'] = df.iloc[:, 0] + " [" + df['Posicion'] + "]"
        return df
    except:
        return pd.DataFrame()

# --- ESTILOS CSS (Aislados para evitar errores) ---
st.set_page_config(page_title="Futbol Total", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .campo {
        background: #2e7d32;
        border: 4px solid white;
        border-radius: 15px;
        padding: 40px 10px;
        text-align: center;
        box-shadow: inset 0px 0px 30px rgba(0,0,0,0.5);
    }
    .slot-jugador {
        width: 80px;
        margin: 0 auto;
    }
    .circulo {
        width: 50px; height: 50px;
        background: white; border-radius: 50%;
        border: 2px solid #00d4ff;
        margin: 0 auto; color: black;
        line-height: 50px; font-weight: bold;
    }
    .nombre-j {
        font-size: 10px; color: white;
        background: rgba(0,0,0,0.7);
        margin-top: 5px; border-radius: 3px;
    }
</style>
""", unsafe_allow_html=True)

# --- LOGIN ---
with st.sidebar:
    st.title("🏆 Futbol Total")
    agente = st.text_input("Usuario").strip()
    clave = st.text_input("Clave", type="password").strip()

if not agente or not clave:
    st.warning("Ingresa para continuar.")
    st.stop()

user = ejecutar_db("SELECT id, presupuesto FROM usuarios WHERE nombre = ?", (agente,))
if not user:
    ejecutar_db("INSERT INTO usuarios (nombre, password, presupuesto, prestigio) VALUES (?, ?, 2500000, 10)", (agente, clave), commit=True)
    st.rerun()
u_id, presupuesto = user[0]

# --- MERCADO ---
df_j = cargar_jugadores()
st.sidebar.subheader(f"Caja: € {presupuesto:,}")

with st.expander("🔍 Fichar Jugadores"):
    seleccion = st.selectbox("Mercado", [""] + df_j['Display'].tolist())
    if seleccion:
        j = df_j[df_j['Display'] == seleccion].iloc[0]
        if st.button(f"Fichar {j.iloc[0]} por €{j['ValorNum']:,}"):
            if presupuesto >= j['ValorNum']:
                ejecutar_db("INSERT INTO cartera (usuario_id, nombre_jugador, club, posicion) VALUES (?,?,?,?)", 
                            (u_id, j.iloc[0], j.iloc[1], j['Posicion']), commit=True)
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (j['ValorNum'], u_id), commit=True)
                st.rerun()

# --- LÓGICA DE LA CANCHA (Blindada) ---
def render_ficha(lista, idx):
    if idx < len(lista):
        nombre = lista[idx].split(',')[0]
        return f'<div class="slot-jugador"><div class="circulo">⚽</div><div class="nombre-j">{nombre}</div></div>'
    return f'<div class="slot-jugador" style="opacity:0.2"><div class="circulo"></div></div>'

cartera = ejecutar_db("SELECT nombre_jugador, posicion FROM cartera WHERE usuario_id = ?", (u_id,))
pos = {"DEL": [], "MED": [], "DEF": [], "ARQ": []}

for n, p in cartera:
    if "DEL" in p or "ATA" in p: pos["DEL"].append(n)
    elif "MED" in p or "VOL" in p: pos["MED"].append(n)
    elif "DEF" in p: pos["DEF"].append(n)
    elif "ARQ" in p or "POR" in p: pos["ARQ"].append(n)

# Dibujar cancha
cancha_html = f"""
<div class="campo">
    <div style="display: flex; justify-content: center; margin-bottom: 30px;">
        {render_ficha(pos["DEL"], 0)}
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 30px;">
        {render_ficha(pos["MED"], 0)} {render_ficha(pos["MED"], 1)} {render_ficha(pos["MED"], 2)}
    </div>
    <div style="display: flex; justify-content: center; gap: 80px; margin-bottom: 30px;">
        {render_ficha(pos["MED"], 3)} {render_ficha(pos["MED"], 4)}
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 30px;">
        {render_ficha(pos["DEF"], 0)} {render_ficha(pos["DEF"], 1)} {render_ficha(pos["DEF"], 2)} {render_ficha(pos["DEF"], 3)}
    </div>
    <div style="display: flex; justify-content: center;">
        {render_ficha(pos["ARQ"], 0)}
    </div>
</div>
"""

st.markdown(cancha_html, unsafe_allow_html=True)

# --- LISTA Y VENTA ---
with st.expander("📋 Mi Plantel"):
    items = ejecutar_db("SELECT id, nombre_jugador FROM cartera WHERE usuario_id = ?", (u_id,))
    for id_j, nom_j in items:
        colA, colB = st.columns([3, 1])
        colA.write(nom_j)
        if colB.button("Vender", key=f"v_{id_j}"):
            ejecutar_db("DELETE FROM cartera WHERE id = ?", (id_j,), commit=True)
            st.rerun()
