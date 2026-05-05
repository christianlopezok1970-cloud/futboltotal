import streamlit as st
import sqlite3
import pandas as pd

# 1. CONFIGURACIÓN DE BASE DE DATOS
DB_NAME = 'futboltotal.db'
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# Crear tablas con columna 'estado' para titulares
ejecutar_db('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, presupuesto REAL, prestigio INTEGER)', commit=True)
ejecutar_db('CREATE TABLE IF NOT EXISTS cartera (id INTEGER PRIMARY KEY, usuario_id INTEGER, nombre_jugador TEXT, club TEXT, posicion TEXT, estado TEXT DEFAULT "Suplente")', commit=True)

@st.cache_data(ttl=60)
def cargar_jugadores():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        df['ValorNum'] = df.iloc[:, 3].apply(lambda x: int(''.join(filter(str.isdigit, str(x)))) if pd.notnull(x) else 1000000)
        df['Posicion'] = df.iloc[:, 2].astype(str).str.upper().str.strip()
        df['Display'] = df.iloc[:, 0] + " [" + df['Posicion'] + "]"
        return df
    except:
        return pd.DataFrame()

# 2. ESTILOS CSS
st.set_page_config(page_title="Futbol Total 1-4-4-2", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .campo-contenedor {
        background-color: #2e7d32;
        border: 3px solid #ffffff;
        border-radius: 15px;
        padding: 30px 5px;
        box-shadow: inset 0px 0px 20px rgba(0,0,0,0.5);
    }
    .ficha { text-align: center; width: 75px; }
    .bola {
        width: 45px; height: 45px;
        background: white; border-radius: 50%;
        border: 2px solid #00d4ff;
        margin: 0 auto; color: black;
        line-height: 45px; font-weight: bold;
    }
    .txt-nom {
        font-size: 10px; color: white;
        background: rgba(0,0,0,0.8);
        margin-top: 4px; border-radius: 3px;
        padding: 2px;
    }
</style>
""", unsafe_allow_html=True)

# 3. LOGIN
with st.sidebar:
    st.title("🏆 Futbol Total")
    agente = st.text_input("Usuario").strip()
    clave = st.text_input("Clave", type="password").strip()

if not agente or not clave:
    st.info("Ingresa para gestionar tu equipo.")
    st.stop()

user_data = ejecutar_db("SELECT id, presupuesto FROM usuarios WHERE nombre = ?", (agente,))
if not user_data:
    ejecutar_db("INSERT INTO usuarios (nombre, password, presupuesto, prestigio) VALUES (?, ?, 2500000, 10)", (agente, clave), commit=True)
    st.rerun()
u_id, presupuesto = user_data[0]

# 4. MERCADO (COMPRA CON DESCUENTO)
df_j = cargar_jugadores()
st.sidebar.subheader(f"Caja: €{presupuesto:,.0f}")

with st.expander("🔍 MERCADO DE PASES"):
    seleccion = st.selectbox("Buscar jugador", [""] + df_j['Display'].tolist())
    if seleccion:
        jug = df_j[df_j['Display'] == seleccion].iloc[0]
        costo = jug['ValorNum']
        st.write(f"Precio: €{costo:,}")
        if st.button("CONFIRMAR COMPRA"):
            if presupuesto >= costo:
                # Insertar jugador y descontar presupuesto
                ejecutar_db("INSERT INTO cartera (usuario_id, nombre_jugador, club, posicion) VALUES (?,?,?,?)", 
                            (u_id, jug.iloc[0], jug.iloc[1], jug['Posicion']), commit=True)
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (costo, u_id), commit=True)
                st.success(f"¡{jug.iloc[0]} fichado!")
                st.rerun()
            else:
                st.error("Fondos insuficientes.")

# 5. LÓGICA DE CANCHA 1-4-4-2
def render_ficha(lista, i):
    if i < len(lista):
        nom = lista[i].split(',')[0].split(' ')[0]
        return f'<div class="ficha"><div class="bola">⚽</div><div class="txt-nom">{nom}</div></div>'
    return '<div class="ficha" style="opacity:0.2"><div class="bola"></div></div>'

# Obtener solo titulares
titulares_db = ejecutar_db("SELECT nombre_jugador, posicion FROM cartera WHERE usuario_id = ? AND estado = 'Titular'", (u_id,))
equipo = {"DEL": [], "MED": [], "DEF": [], "ARQ": []}

for n, p in titulares_db:
    p_up = p.upper()
    if any(x in p_up for x in ["DEL", "ATA", "DC"]): equipo["DEL"].append(n)
    elif any(x in p_up for x in ["MED", "VOL", "MC"]): equipo["MED"].append(n)
    elif any(x in p_up for x in ["DEF", "DFC", "LAT"]): equipo["DEF"].append(n)
    elif any(x in p_up for x in ["ARQ", "POR", "GK"]): equipo["ARQ"].append(n)

st.subheader("🏟️ Alineación (1-4-4-2)")
html_cancha = f"""
<div class="campo-contenedor">
    <div style="display: flex; justify-content: center; gap: 40px; margin-bottom: 30px;">
        {render_ficha(equipo["DEL"], 0)} {render_ficha(equipo["DEL"], 1)}
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 30px;">
        {render_ficha(equipo["MED"], 0)} {render_ficha(equipo["MED"], 1)} 
        {render_ficha(equipo["MED"], 2)} {render_ficha(equipo["MED"], 3)}
    </div>
    <div style="display: flex; justify-content: space-around; margin-bottom: 30px;">
        {render_ficha(equipo["DEF"], 0)} {render_ficha(equipo["DEF"], 1)} 
        {render_ficha(equipo["DEF"], 2)} {render_ficha(equipo["DEF"], 3)}
    </div>
    <div style="display: flex; justify-content: center;">
        {render_ficha(equipo["ARQ"], 0)}
    </div>
</div>
"""
st.markdown(html_cancha, unsafe_allow_html=True)

# 6. GESTIÓN DE PLANTEL (TITULAR/SUPLENTE)
st.divider()
st.subheader("📋 Gestión del Plantel")
mi_plantel = ejecutar_db("SELECT id, nombre_jugador, posicion, estado FROM cartera WHERE usuario_id = ?", (u_id,))

for id_db, nom, pos, estado in mi_plantel:
    col1, col2, col3 = st.columns([3, 2, 1])
    col1.write(f"**{nom}** ({pos})")
    
    # Botón Titular/Suplente
    label = "Sentar al banco" if estado == "Titular" else "Poner de Titular"
    nuevo_estado = "Suplente" if estado == "Titular" else "Titular"
    
    if col2.button(label, key=f"btn_{id_db}"):
        ejecutar_db("UPDATE cartera SET estado = ? WHERE id = ?", (nuevo_estado, id_db), commit=True)
        st.rerun()
    
    if col3.button("❌", key=f"del_{id_db}"):
        ejecutar_db("DELETE FROM cartera WHERE id = ?", (id_db,), commit=True)
        st.rerun()
