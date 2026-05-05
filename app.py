import streamlit as st
import sqlite3
import pandas as pd

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
DB_NAME = "liga_master_v1.db"

def consulta_db(query, params=(), commit=False):
    """Maneja la conexión y ejecución de comandos SQL."""
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()

# Inicialización de tablas al arrancar la app
consulta_db("""CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                nombre TEXT UNIQUE, 
                password TEXT, 
                presupuesto REAL DEFAULT 25000000)""", commit=True)

consulta_db("""CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                usuario_id INTEGER, 
                nombre_jugador TEXT UNIQUE, 
                equipo TEXT, 
                posicion TEXT, 
                precio REAL, 
                estado TEXT DEFAULT 'Suplente')""", commit=True)

# --- 2. MOTOR DE CARGA DE DATOS (EXCEL) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

@st.cache_data(ttl=60)
def cargar_excel():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        # Limpieza de precios: de "$ 1.200.000" a 1200000.0
        df['PrecioLimpio'] = pd.to_numeric(df['Cotización'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

# --- 3. SISTEMA DE IDENTIDAD (LOGIN) ---
if 'user' not in st.session_state:
    st.title("⚽ Liga Master")
    u_nom = st.text_input("Usuario / Equipo").strip()
    u_pass = st.text_input("Contraseña", type="password").strip()
    
    if st.button("Entrar / Registrarse"):
        if u_nom and u_pass:
            res = consulta_db("SELECT id, nombre FROM usuarios WHERE nombre = ? AND password = ?", (u_nom, u_pass))
            if res:
                st.session_state.user = {"id": res[0][0], "nombre": res[0][1]}
                st.rerun()
            else:
                try:
                    consulta_db("INSERT INTO usuarios (nombre, password) VALUES (?, ?)", (u_nom, u_pass), commit=True)
                    st.success("¡Usuario creado! Haz clic de nuevo para ingresar.")
                except:
                    st.error("Nombre de usuario ocupado o contraseña incorrecta.")
        else:
            st.warning("Completa los campos para continuar.")
    st.stop()

# --- 4. DATOS DEL USUARIO LOGUEADO ---
u_id = st.session_state.user["id"]
u_nombre = st.session_state.user["nombre"]
res_p = consulta_db("SELECT presupuesto FROM usuarios WHERE id = ?", (u_id,))
presupuesto_actual = res_p[0][0]

# Barra lateral informativa
st.sidebar.title(f"👤 {u_nombre}")
st.sidebar.metric("Presupuesto", f"€ {presupuesto_actual:,.0f}")

# --- 5. MERCADO DE FICHAJES ---
st.header("🛒 Mercado de Jugadores")
df_m = cargar_excel()
ocupados = [j[0] for j in consulta_db("SELECT nombre_jugador FROM plantillas")]
df_disp = df_m[~df_m['Nombre'].isin(ocupados)]

with st.expander("Ver jugadores disponibles"):
    sel = st.selectbox("Selecciona un jugador para fichar:", [""] + df_disp['Nombre'].tolist())
    if sel:
        f = df_disp[df_disp['Nombre'] == sel].iloc[0]
        st.write(f"**{f['Nombre']}** ({f['POS']}) - Costo: **€ {f['PrecioLimpio']:,.0f}**")
        if st.button(f"Confirmar Fichaje"):
            if presupuesto_actual >= f['PrecioLimpio']:
                try:
                    consulta_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (f['PrecioLimpio'], u_id), commit=True)
                    consulta_db("INSERT INTO plantillas (usuario_id, nombre_jugador, equipo, posicion, precio) VALUES (?,?,?,?,?)", 
                                (u_id, f['Nombre'], f['Equipo'], f['POS'], f['PrecioLimpio']), commit=True)
                    st.success(f"¡{f['Nombre']} fichado!")
                    st.rerun()
                except: st.error("Error al procesar el fichaje.")
            else:
                st.error("No tienes fondos suficientes.")

# --- 6. LA CANCHA (DISEÑO VISUAL) ---
st.divider()
st.header("🏟️ Tu Alineación")

# CSS para el estilo de cancha y fichas
st.markdown("""
<style>
    /* El contenedor del campo de juego */
    .cancha-fondo {
        background-color: #1e5622;
        background-image: linear-gradient(rgba(255,255,255,0.1) 2px, transparent 2px), linear-gradient(90deg, rgba(255,255,255,0.1) 2px, transparent 2px);
        background-size: 100% 40px;
        border: 3px solid white;
        border-radius: 15px;
        padding: 30px 10px;
        text-align: center;
    }
    .player-card {
        background: rgba(0, 0, 0, 0.5);
        border: 1px solid #00d4ff;
        border-radius: 10px;
        padding: 8px;
        margin-bottom: 10px;
    }
    .player-icon { font-size: 20px; background: white; border-radius: 50%; width: 40px; height: 40px; line-height: 40px; margin: 0 auto; color: black; }
    .player-name { font-size: 10px; color: white; margin-top: 5px; font-weight: bold; text-transform: uppercase; }
</style>
""", unsafe_allow_html=True)

def render_ficha(lista, idx):
    if idx < len(lista):
        nom = lista[idx][1].replace(',', '').split(' ')[0]
        st.markdown(f'<div class="player-card"><div class="player-icon">👕</div><div class="player-name">{nom}</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="opacity:0.2; color:white; font-size:24px;">◌</div>', unsafe_allow_html=True)

# Obtener titulares
mis_jugadores = consulta_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
titus = [j for j in mis_jugadores if j[3] == "Titular"]

# Clasificación táctica
def filtrar(l, k): return [j for j in l if any(x in j[2].upper() for x in k)]
dels = filtrar(titus, ["DEL","ATA","DC","EXT"])
meds = filtrar(titus, ["MED","VOL","MC","MCO","MCD"])
defs = filtrar(titus, ["DEF","DFC","LAT","LI","LD"])
arqs = filtrar(titus, ["ARQ","POR","GK"])

# Renderizado del campo (CORREGIDO)
st.markdown('<div class="cancha-fondo">', unsafe_allow_html=True)

# Delanteros
c1, c2, c3, c4 = st.columns([1, 2, 2, 1])
with c2: 
    render_ficha(dels, 0)
with c3: 
    render_ficha(dels, 1)

st.write("")

# Medios
c1, c2, c3, c4 = st.columns(4)
with c1: 
    render_ficha(meds, 0)
with c2: 
    render_ficha(meds, 1)
with c3: 
    render_ficha(meds, 2)
with c4: 
    render_ficha(meds, 3)

st.write("")

# Defensas
c1, c2, c3, c4 = st.columns(4)
with c1: 
    render_ficha(defs, 0)
with c2: 
    render_ficha(defs, 1)
with c3: 
    render_ficha(defs, 2)
with c4: 
    render_ficha(defs, 3)

st.write("")

# Arquero
c1, c2, c3 = st.columns([1, 1, 1])
with c2: 
    render_ficha(arqs, 0)

st.markdown('</div>', unsafe_allow_html=True)

# --- 7. GESTIÓN DE PLANTILLA ---
st.divider()
st.header("📋 Mi Plantilla")
if not mis_jugadores:
    st.info("No tienes jugadores aún.")
else:
    for j_id, nom, pos, est, precio in mis_jugadores:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"**{nom}** ({pos})")
        
        btn_txt = "Sentar" if est == "Titular" else "Titular"
        if col2.button(btn_txt, key=f"btn_est_{j_id}"):
            nuevo = "Suplente" if est == "Titular" else "Titular"
            consulta_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
            st.rerun()
            
        if col3.button("🗑️", key=f"btn_del_{j_id}", help="Vender jugador"):
            consulta_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
            consulta_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
            st.rerun()
