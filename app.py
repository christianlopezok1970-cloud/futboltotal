import streamlit as st
import sqlite3
import pandas as pd

# --- 1. CONFIGURACIÓN DE BASE DE DATOS Y DATOS ---
DB_NAME = 'futboltotal.db'
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    """Ejecutor robusto con manejo de errores para evitar el OperationalError"""
    try:
        with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
            c = conn.cursor()
            c.execute(query, params)
            if commit:
                conn.commit()
            return c.fetchall()
    except sqlite3.OperationalError as e:
        st.error(f"Error de base de datos: {e}")
        return []

# Inicialización de tablas con las columnas necesarias
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
               (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, 
                presupuesto REAL, prestigio INTEGER)''', commit=True)

ejecutar_db('''CREATE TABLE IF NOT EXISTS cartera 
               (id INTEGER PRIMARY KEY, usuario_id INTEGER, nombre_jugador TEXT, 
                club TEXT, posicion TEXT, estado TEXT DEFAULT 'Suplente')''', commit=True)

@st.cache_data(ttl=60)
def cargar_jugadores():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        df['ValorNum'] = df.iloc[:, 3].apply(lambda x: int(''.join(filter(str.isdigit, str(x)))) if pd.notnull(x) else 1000000)
        df['Posicion'] = df.iloc[:, 2].astype(str).str.upper().str.strip()
        df['Display'] = df.iloc[:, 0] + " [" + df['Posicion'] + "]"
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

# --- 2. ESTILOS VISUALES ---
st.set_page_config(page_title="Futbol Total 1-4-4-2", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .campo-contenedor {
        background: linear-gradient(to bottom, #2e7d32 0%, #1b5e20 100%);
        border: 3px solid #ffffff;
        border-radius: 15px;
        padding: 30px 10px;
        box-shadow: inset 0px 0px 40px rgba(0,0,0,0.5);
    }
    .ficha { text-align: center; width: 80px; }
    .bola {
        width: 50px; height: 50px;
        background: white; border-radius: 50%;
        border: 3px solid #00d4ff;
        margin: 0 auto; color: black;
        line-height: 45px; font-weight: bold; font-size: 20px;
    }
    .txt-nom {
        font-size: 11px; color: white;
        background: rgba(0,0,0,0.8);
        margin-top: 5px; border-radius: 4px;
        padding: 2px 5px; font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. SISTEMA DE USUARIO ---
with st.sidebar:
    st.title("🏆 Futbol Total")
    agente = st.text_input("Usuario").strip()
    clave = st.text_input("Clave", type="password").strip()

if not agente or not clave:
    st.info("Ingresa para gestionar tu equipo.")
    st.stop()

# Verificar o crear usuario
user_data = ejecutar_db("SELECT id, presupuesto FROM usuarios WHERE nombre = ?", (agente,))
if not user_data:
    ejecutar_db("INSERT INTO usuarios (nombre, password, presupuesto, prestigio) VALUES (?, ?, 2500000, 10)", (agente, clave), commit=True)
    st.rerun()

u_id, presupuesto = user_data[0]

# --- 4. MERCADO Y COMPRAS ---
df_j = cargar_jugadores()
st.sidebar.metric("Presupuesto Disponible", f"€ {presupuesto:,.0f}")

with st.expander("🔍 BUSCAR Y FICHAR"):
    seleccion = st.selectbox("Mercado de Pases", [""] + df_j['Display'].tolist())
    if seleccion:
        jug = df_j[df_j['Display'] == seleccion].iloc[0]
        costo = jug['ValorNum']
        st.info(f"Costo de fichaje: € {costo:,}")
        
        if st.button("CONFIRMAR OPERACIÓN"):
            if presupuesto >= costo:
                # 1. Restar dinero | 2. Agregar a cartera
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (costo, u_id), commit=True)
                ejecutar_db("INSERT INTO cartera (usuario_id, nombre_jugador, club, posicion, estado) VALUES (?,?,?,?,?)", 
                            (u_id, jug.iloc[0], jug.iloc[1], jug['Posicion'], "Suplente"), commit=True)
                st.success(f"¡{jug.iloc[0]} se ha unido al club!")
                st.rerun()
            else:
                st.error("Presupuesto insuficiente.")

# --- 5. CANCHA TÁCTICA 1-4-4-2 ---
def render_ficha(lista, i):
    if i < len(lista):
        nom = lista[i].split(',')[0].split(' ')[0]
        return f'<div class="ficha"><div class="bola">⚽</div><div class="txt-nom">{nom}</div></div>'
    return '<div class="ficha" style="opacity:0.15"><div class="bola"></div></div>'

# Filtrar solo los jugadores marcados como 'Titular'
titulares = ejecutar_db("SELECT nombre_jugador, posicion FROM cartera WHERE usuario_id = ? AND estado = 'Titular'", (u_id,))
equipo = {"DEL": [], "MED": [], "DEF": [], "ARQ": []}

for n, p in titulares:
    p_up = p.upper()
    if any(x in p_up for x in ["DEL", "ATA", "DC", "EXT"]): equipo["DEL"].append(n)
    elif any(x in p_up for x in ["MED", "VOL", "MC", "MCO", "MCD"]): equipo["MED"].append(n)
    elif any(x in p_up for x in ["DEF", "DFC", "LAT", "DFI", "DFD"]): equipo["DEF"].append(n)
    elif any(x in p_up for x in ["ARQ", "POR", "GK"]): equipo["ARQ"].append(n)

st.subheader("🏟️ Alineación Titular (1-4-4-2)")
html_cancha = f"""
<div class="campo-contenedor">
    <!-- DELANTEROS -->
    <div style="display: flex; justify-content: center; gap: 60px; margin-bottom: 35px;">
        {render_ficha(equipo["DEL"], 0)} {render_ficha(equipo["DEL"], 1)}
    </div>
    <!-- MEDIOCAMPO -->
    <div style="display: flex; justify-content: space-around; margin-bottom: 35px;">
        {render_ficha(equipo["MED"], 0)} {render_ficha(equipo["MED"], 1)} 
        {render_ficha(equipo["MED"], 2)} {render_ficha(equipo["MED"], 3)}
    </div>
    <!-- DEFENSA -->
    <div style="display: flex; justify-content: space-around; margin-bottom: 35px;">
        {render_ficha(equipo["DEF"], 0)} {render_ficha(equipo["DEF"], 1)} 
        {render_ficha(equipo["DEF"], 2)} {render_ficha(equipo["DEF"], 3)}
    </div>
    <!-- ARQUERO -->
    <div style="display: flex; justify-content: center;">
        {render_ficha(equipo["ARQ"], 0)}
    </div>
</div>
"""
st.markdown(html_cancha, unsafe_allow_html=True)

# --- 6. GESTIÓN DE PLANTEL ---
st.divider()
st.subheader("📋 Gestión del Plantel")
mi_plantel = ejecutar_db("SELECT id, nombre_jugador, posicion, estado FROM cartera WHERE usuario_id = ?", (u_id,))

if not mi_plantel:
    st.info("Tu plantel está vacío. Ficha jugadores en el mercado.")
else:
    for id_db, nom, pos, estado in mi_plantel:
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"**{nom}**")
        col1.caption(f"Posición: {pos} | Estado: {estado}")
        
        # Botón dinámico para cambiar estado
        btn_label = "Sentar al Banco" if estado == "Titular" else "Subir a Titular"
        btn_color = "secondary" if estado == "Titular" else "primary"
        
        if col2.button(btn_label, key=f"st_{id_db}"):
            nuevo_estado = "Suplente" if estado == "Titular" else "Titular"
            ejecutar_db("UPDATE cartera SET estado = ? WHERE id = ?", (nuevo_estado, id_db), commit=True)
            st.rerun()
            
        if col3.button("🗑️", key=f"v_{id_db}"):
            ejecutar_db("DELETE FROM cartera WHERE id = ?", (id_db,), commit=True)
            st.rerun()
