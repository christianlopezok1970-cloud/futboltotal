import streamlit as st
import sqlite3
import pandas as pd

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
DB_NAME = "liga_master_v1.db"

def consulta_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()

# Inicialización (Aseguramos que las tablas existan)
consulta_db("""CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, password TEXT, presupuesto REAL DEFAULT 25000000)""", commit=True)
consulta_db("""CREATE TABLE IF NOT EXISTS plantillas (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_id INTEGER, nombre_jugador TEXT UNIQUE, equipo TEXT, posicion TEXT, precio REAL, estado TEXT DEFAULT 'Suplente')""", commit=True)

# --- 2. CARGA DE EXCEL ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_excel():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip() for c in df.columns]
    df['PrecioLimpio'] = pd.to_numeric(df['Cotización'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
    return df

# --- 3. LOGIN ---
if 'user' not in st.session_state:
    st.title("⚽ Liga Master")
    u_nom = st.text_input("Usuario").strip()
    u_pass = st.text_input("Contraseña", type="password").strip()
    if st.button("Entrar / Registrarse"):
        res = consulta_db("SELECT id, nombre, presupuesto FROM usuarios WHERE nombre = ? AND password = ?", (u_nom, u_pass))
        if res:
            st.session_state.user = {"id": res[0][0], "nombre": res[0][1]}
            st.rerun()
        else:
            try:
                consulta_db("INSERT INTO usuarios (nombre, password) VALUES (?, ?)", (u_nom, u_pass), commit=True)
                st.success("¡Creado! Pulsa de nuevo.")
            except: st.error("Error en login.")
    st.stop()

# --- 4. DATOS DE SESIÓN ---
u_id = st.session_state.user["id"]
presupuesto_actual = consulta_db("SELECT presupuesto FROM usuarios WHERE id = ?", (u_id,))[0][0]

st.sidebar.title(f"👤 {st.session_state.user['nombre']}")
st.sidebar.metric("Presupuesto", f"€ {presupuesto_actual:,.0f}")

# --- 5. MERCADO ---
st.header("🛒 Mercado")
df_m = cargar_excel()
ocupados = [j[0] for j in consulta_db("SELECT nombre_jugador FROM plantillas")]
df_disp = df_m[~df_m['Nombre'].isin(ocupados)]

sel = st.selectbox("Fichar jugador:", [""] + df_disp['Nombre'].tolist())
if sel:
    f = df_disp[df_disp['Nombre'] == sel].iloc[0]
    if st.button(f"Fichar por € {f['PrecioLimpio']:,.0f}"):
        if presupuesto_actual >= f['PrecioLimpio']:
            consulta_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (f['PrecioLimpio'], u_id), commit=True)
            consulta_db("INSERT INTO plantillas (usuario_id, nombre_jugador, equipo, posicion, precio) VALUES (?,?,?,?,?)", 
                        (u_id, f['Nombre'], f['Equipo'], f['POS'], f['PrecioLimpio']), commit=True)
            st.rerun()

# --- 6. LA CANCHA (DISEÑO RESISTENTE) ---
st.divider()
st.header("🏟️ Alineación")

# CSS externo para no romper los contenedores de Streamlit
st.markdown("""
<style>
    [data-testid="stVerticalBlock"] > div:has(div.player-card) {
        background-color: #2e7d32;
        border-radius: 15px;
        padding: 20px;
    }
    .player-card {
        text-align: center;
        background: rgba(255,255,255,0.1);
        border-radius: 10px;
        padding: 10px;
        border: 1px solid rgba(255,255,255,0.2);
    }
    .player-icon { font-size: 30px; background: white; border-radius: 50%; width: 50px; height: 50px; line-height: 50px; margin: 0 auto; color: black; }
    .player-name { font-size: 12px; color: white; margin-top: 5px; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def ficha(lista, idx):
    if idx < len(lista):
        nom = lista[idx][1].split(',')[0].split(' ')[0]
        st.markdown(f'<div class="player-card"><div class="player-icon">⚽</div><div class="player-name">{nom}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="text-align:center; opacity:0.2; color:white">---</div>', unsafe_allow_html=True)

mis_j = consulta_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
titus = [j for j in mis_j if j[3] == "Titular"]

# Filtrado por posiciones
def get_p(l, k): return [j for j in l if any(x in j[2].upper() for x in k)]
dels, meds, defs, arqs = get_p(titus, ["DEL","ATA","DC"]), get_p(titus, ["MED","VOL","MC"]), get_p(titus, ["DEF","DFC","LAT"]), get_p(titus, ["ARQ","POR"])

# Dibujo de la cancha con contenedores nativos
with st.container():
    c1, c2 = st.columns(2); with c1: ficha(dels, 0); with c2: ficha(dels, 1)
    st.write(" ")
    c1, c2, c3, c4 = st.columns(4); with c1: ficha(meds, 0); with c2: ficha(meds, 1); with c3: ficha(meds, 2); with c4: ficha(meds, 3)
    st.write(" ")
    c1, c2, c3, c4 = st.columns(4); with c1: ficha(defs, 0); with c2: ficha(defs, 1); with c3: ficha(defs, 2); with c4: ficha(defs, 3)
    st.write(" ")
    c1, c2, c3 = st.columns([1,1,1]); with c2: ficha(arqs, 0)

# --- 7. GESTIÓN ---
st.divider()
st.header("📋 Mi Plantilla")
for j_id, nom, pos, est, precio in mis_j:
    c1, c2, c3 = st.columns([3, 2, 1])
    c1.write(f"**{nom}** ({pos})")
    if c2.button("Sentar" if est=="Titular" else "Titular", key=f"t_{j_id}"):
        consulta_db("UPDATE plantillas SET estado = ? WHERE id = ?", ("Suplente" if est=="Titular" else "Titular", j_id), commit=True)
        st.rerun()
    if c3.button("🗑️", key=f"v_{j_id}"):
        consulta_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
        consulta_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
        st.rerun()
        
