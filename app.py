import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- 1. CONFIGURACIÓN DE BASE DE DATOS Y SHEET ---
DB_NAME = 'agencia_v2_pro.db' 
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# Inicialización de tablas
ejecutar_db('CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, presupuesto REAL, prestigio INTEGER)', commit=True)
ejecutar_db('CREATE TABLE IF NOT EXISTS cartera (id INTEGER PRIMARY KEY, usuario_id INTEGER, nombre_jugador TEXT, club TEXT, posicion TEXT)', commit=True)

# --- 2. FUNCIONES AUXILIARES Y CARGA DE DATOS ---
def formatear_total(monto):
    try: return f"{int(float(monto)):,}".replace(',', '.')
    except: return "0"

@st.cache_data(ttl=60)
def cargar_datos_completos_google():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        # Limpieza de cotización (Columna D)
        df['ValorNum'] = df.iloc[:, 3].apply(lambda x: int(''.join(filter(str.isdigit, str(x)))) if pd.notnull(x) else 1000000)
        # Posición (Columna C)
        df['Posicion'] = df.iloc[:, 2].str.upper().str.strip()
        df['Display'] = df.iloc[:, 0] + " [" + df['Posicion'] + "]"
        return df
    except: return pd.DataFrame()

def generar_ficha_jugador(lista, indice):
    """Genera el círculo del jugador en la cancha o un espacio vacío si no existe"""
    if indice < len(lista):
        nombre = lista[indice]
        return f'''
        <div style="text-align: center; width: 85px;">
            <div style="width: 55px; height: 55px; background: white; border-radius: 50%; border: 3px solid #00D4FF; margin: 0 auto; color: black; line-height: 55px; font-weight: bold; font-size: 20px; box-shadow: 0px 0px 10px rgba(0,212,255,0.5);">⚽</div>
            <div style="font-size: 11px; color: white; background: rgba(0,0,0,0.7); margin-top: 5px; border-radius: 5px; padding: 2px; font-weight: bold;">{nombre}</div>
        </div>
        '''
    return '<div style="width: 85px; opacity: 0.2;"><div style="width: 55px; height: 55px; background: #ffffff55; border-radius: 50%; margin: 0 auto;"></div></div>'

# --- 3. INTERFAZ Y ESTILOS ---
st.set_page_config(page_title="Agencia Scouting V2", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #050505 0%, #1a0033 100%); }
    h1, h2, h3, h4, p, span, label { color: #f0f2f6 !important; }
    .campo-tactico {
        background-color: #2e7d32;
        background-image: radial-gradient(circle, #388e3c 1px, transparent 1px);
        background-size: 20px 20px;
        border: 4px solid #ffffffaa;
        border-radius: 20px;
        padding: 30px 10px;
        box-shadow: inset 0px 0px 50px rgba(0,0,0,0.5);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. ACCESO DE USUARIO ---
with st.sidebar:
    st.title("⚽ Manager V2")
    manager = st.text_input("Agente:").strip()
    password = st.text_input("Contraseña:", type="password").strip()

if not manager or not password:
    st.info("👋 Ingresa para gestionar tu equipo.")
    st.stop()

# Lógica de Login
datos = ejecutar_db("SELECT id, presupuesto, prestigio, password FROM usuarios WHERE nombre = ?", (manager,))
if not datos:
    ejecutar_db("INSERT INTO usuarios (nombre, password, presupuesto, prestigio) VALUES (?, ?, 2500000, 15)", (manager, password), commit=True)
    st.rerun()
u_id, presupuesto, prestigio, u_pass = datos[0]
if password != u_pass:
    st.error("❌ Clave incorrecta")
    st.stop()

df_oficial = cargar_datos_completos_google()

# --- 5. MERCADO DE FICHAJES ---
st.sidebar.metric("Caja", f"€ {formatear_total(presupuesto)}")
st.sidebar.metric("Prestigio", f"{prestigio} pts")

with st.expander("🔍 Mercado de Fichajes"):
    if not df_oficial.empty:
        sel = st.selectbox("Buscar Jugador:", [""] + df_oficial['Display'].tolist())
        if sel:
            datos_j = df_oficial[df_oficial['Display'] == sel].iloc[0]
            nom, club, pos, costo = datos_j.iloc[0], datos_j.iloc[1], datos_j['Posicion'], datos_j['ValorNum']
            
            st.write(f"**Posición:** {pos} | **Club:** {club} | **Costo:** € {formatear_total(costo)}")
            
            if st.button("FICHAR PARA EL EQUIPO"):
                ya_fichado = ejecutar_db("SELECT id FROM cartera WHERE usuario_id = ? AND nombre_jugador = ?", (u_id, nom))
                if ya_fichado:
                    st.warning("Ya tienes a este jugador.")
                elif presupuesto >= costo:
                    ejecutar_db("INSERT INTO cartera (usuario_id, nombre_jugador, club, posicion) VALUES (?,?,?,?)", (u_id, nom, club, pos), commit=True)
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (costo, u_id), commit=True)
                    st.success(f"¡{nom} se unió a tu equipo!")
                    st.rerun()
                else:
                    st.error("Saldo insuficiente.")

# --- 6. CAMPO TÁCTICO (4-2-3-1) ---
st.subheader("🏟️ Formación Titular (4-2-3-1)")

# Obtener jugadores actuales y organizarlos por posición
cartera_raw = ejecutar_db("SELECT nombre_jugador, posicion FROM cartera WHERE usuario_id = ?", (u_id,))
equipo = {"ARQ": [], "DEF": [], "MED": [], "DEL": []}
for n, p in cartera_raw:
    for cat in equipo.keys():
        if cat in p: equipo[cat].append(n)

# Renderizado de la cancha con HTML/CSS dinámico
st.markdown(f"""
<div class="campo-tactico">
    <!-- DELANTERO -->
    <div style="display: flex; justify-content: center; margin-bottom: 35px;">
        {generar_ficha_jugador(equipo["DEL"], 0)}
    </div>
    <!-- MEDIOS ATAQUE -->
    <div style="display: flex; justify-content: space-around; margin-bottom: 35px;">
        {generar_ficha_jugador(equipo["MED"], 0)}
        {generar_ficha_jugador(equipo["MED"], 1)}
        {generar_ficha_jugador(equipo["MED"], 2)}
    </div>
    <!-- MEDIOS DEFENSA -->
    <div style="display: flex; justify-content: center; gap: 80px; margin-bottom: 35px;">
        {generar_ficha_jugador(equipo["MED"], 3)}
        {generar_ficha_jugador(equipo["MED"], 4)}
    </div>
    <!-- DEFENSA -->
    <div style="display: flex; justify-content: space-around; margin-bottom: 35px;">
        {generar_ficha_jugador(equipo["DEF"], 0)}
        {generar_ficha_jugador(equipo["DEF"], 1)}
        {generar_ficha_jugador(equipo["DEF"], 2)}
        {generar_ficha_jugador(equipo["DEF"], 3)}
    </div>
    <!-- ARQUERO -->
    <div style="display: flex; justify-content: center;">
        {generar_ficha_jugador(equipo["ARQ"], 0)}
    </div>
</div>
""", unsafe_allow_html=True)

# --- 7. GESTIÓN DE PLANTEL ---
with st.expander("📋 Lista de Plantel y Ventas"):
    cartera_v = ejecutar_db("SELECT id, nombre_jugador, club, posicion FROM cartera WHERE usuario_id = ?", (u_id,))
    for c_id, n, cl, p in cartera_v:
        col1, col2 = st.columns([4, 1])
        col1.write(f"**{n}** ({p}) - {cl}")
        if col2.button("Vender", key=f"v_{c_id}"):
            ejecutar_db("DELETE FROM cartera WHERE id = ?", (c_id,), commit=True)
            # Recupera el 90% del valor (opcional, basado en df_oficial)
            st.rerun()
