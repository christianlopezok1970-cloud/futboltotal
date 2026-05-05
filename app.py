import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import random

# --- 1. CONFIGURACIÓN DE BASE DE DATOS ---
DB_NAME = 'agencia_global_v41.db'
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

def formatear_abreviado(monto):
    try:
        monto = float(monto)
        if monto >= 1_000_000: 
            return f"{monto / 1_000_000:.1f}M".replace('.0M', 'M').replace('.', ',')
        elif monto >= 1_000: 
            return f"{monto / 1_000:.0f}K"
        return f"{monto:.0f}"
    except: return "0"

def formatear_total(monto):
    try: return f"{int(float(monto)):,}".replace(',', '.')
    except: return "0"

@st.cache_data(ttl=60)
def cargar_datos_completos_google():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        def limpiar_valor(val):
            try:
                s = str(val).replace('.','').replace(',','')
                return int(''.join(filter(str.isdigit, s)))
            except: return 1000000
        df['ValorNum'] = df.iloc[:, 3].apply(limpiar_valor)
        df['Display'] = df.iloc[:, 0] + " (" + df.iloc[:, 1] + ") - € " + df['ValorNum'].apply(formatear_abreviado) + " [" + df.iloc[:, 2] + "]"
        df['ScoreOficial'] = pd.to_numeric(df.iloc[:, 4], errors='coerce').fillna(0)
        return df
    except: return pd.DataFrame()

# Tablas
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, presupuesto REAL, prestigio INTEGER)''', commit=True)
ejecutar_db('''CREATE TABLE IF NOT EXISTS cartera 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, nombre_jugador TEXT, 
              porcentaje REAL, costo_compra REAL, club TEXT)''', commit=True)
ejecutar_db('''CREATE TABLE IF NOT EXISTS historial 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, detalle TEXT, monto REAL, fecha TEXT)''', commit=True)

# --- 2. LÓGICA DE NEGOCIO ---
def calcular_balance_fecha(pts, costo):
    pts = round(float(pts), 1)
    if pts >= 6.6: return int(costo * ((pts - 6.5) * 10 / 100))
    elif pts <= 6.3: return int(costo * ((pts - 6.4) * 10 / 100))
    return 0

def calcular_cambio_prestigio(pts):
    p = round(float(pts), 1)
    if p >= 8.0: return 2
    if p >= 7.0: return 1
    if p <= 5.9: return -2
    if p <= 6.7: return -1
    return 0

# --- ESTILO AZUL CHAMPIONS ---
st.set_page_config(page_title="Pro Fútbol Manager v41", layout="wide")

st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #001633 0%, #000814 100%); }
    h1, h2, h3, h4, p, span, label { color: #f0f2f6 !important; }
    div[data-testid="stVerticalBlock"] > div[style*="border"] {
        background-color: rgba(255, 255, 255, 0.05);
        border: 1px solid #003366 !important;
        border-radius: 10px;
    }
    section[data-testid="stSidebar"] { background-color: #000b1a; }
    .stButton>button { background-color: #004494; color: white; border-radius: 5px; border: none; width: 100%; }
    .stButton>button:hover { background-color: #005bc4; color: white; }
    .stMetric { background: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; border: 1px solid #004494; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. INTERFAZ E INICIO DE SESIÓN ---
st.subheader("Pro Fútbol Manager")

with st.sidebar:
    st.title("🔐 Acceso Agente")
    manager = st.text_input("Nombre del Agente:").strip()
    password = st.text_input("Contraseña:", type="password").strip()

if not manager or not password:
    st.info("👋 Por favor, introduce tu nombre y contraseña.")
    st.stop()

datos = ejecutar_db("SELECT id, presupuesto, prestigio, password FROM usuarios WHERE nombre = ?", (manager,))

if not datos:
    ejecutar_db("INSERT INTO usuarios (nombre, password, presupuesto, prestigio) VALUES (?, ?, 2000000, 10)", (manager, password), commit=True)
    st.success(f"Cuenta creada para {manager}. ¡Bienvenido!")
    st.rerun()
else:
    u_id, presupuesto, prestigio, u_pass = datos[0]
    if password != u_pass:
        st.error("❌ Contraseña incorrecta.")
        st.stop()

df_oficial = cargar_datos_completos_google()

# --- 4. PROCESAMIENTO AUTOMÁTICO ---
if not df_oficial.empty:
    cartera_activa = ejecutar_db("SELECT nombre_jugador, costo_compra FROM cartera WHERE usuario_id = ?", (u_id,))
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    for j_nom, j_costo in cartera_activa:
        match = df_oficial[df_oficial.iloc[:, 0].str.strip() == j_nom.strip()]
        if not match.empty:
            pts_oficial = float(match['ScoreOficial'].values[0])
            if pts_oficial > 0:
                check_detalle = f"Auto-Jornada: {j_nom.strip()}"
                ya_cobrado = ejecutar_db("SELECT id FROM historial WHERE usuario_id = ? AND detalle = ? AND fecha LIKE ?", (u_id, check_detalle, f"{fecha_hoy}%"))
                if not ya_cobrado:
                    bal = calcular_balance_fecha(pts_oficial, j_costo)
                    pres_mod = calcular_cambio_prestigio(pts_oficial)
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ?, prestigio = prestigio + ? WHERE id = ?", (bal, pres_mod, u_id), commit=True)
                    ejecutar_db("INSERT INTO historial (usuario_id, detalle, monto, fecha) VALUES (?,?,?,?)", (u_id, check_detalle, bal, datetime.now().strftime("%Y-%m-%d %H:%M")), commit=True)
                    st.toast(f"✅ Jornada procesada: {j_nom}")
    
    datos = ejecutar_db("SELECT id, presupuesto, prestigio, password FROM usuarios WHERE id = ?", (u_id,))
    u_id, presupuesto, prestigio, _ = datos[0]

# --- 5. SIDEBAR (Métricas) ---
st.sidebar.metric("Caja Global", f"€ {formatear_total(presupuesto)}")
st.sidebar.metric("Reputación", f"{prestigio} pts")

# --- 6. SCOUTING Y MERCADO (Simplificado) ---
with st.expander("🔍 Scouting y Mercado"):
    if not df_oficial.empty:
        c1, c2 = st.columns(2)
        seleccion = c1.selectbox("Buscar Jugador:", options=[""] + df_oficial['Display'].tolist())
        if seleccion:
            dj = df_oficial[df_oficial['Display'] == seleccion].iloc[0]
            nom = dj.iloc[0]
            ya_lo_tiene = ejecutar_db("SELECT id FROM cartera WHERE usuario_id = ? AND nombre_jugador = ?", (u_id, nom))
            if not ya_lo_tiene:
                v_m_t = int(dj['ValorNum'])
                pct = c2.select_slider("Porcentaje:", [1, 5, 10, 25, 50, 75, 100], value=10)
                costo_f = (v_m_t * pct) / 100
                if st.button("FICHAR"):
                    if presupuesto >= costo_f:
                        ejecutar_db("INSERT INTO cartera (usuario_id, nombre_jugador, porcentaje, costo_compra, club) VALUES (?,?,?,?,?)", (u_id, nom, pct, costo_f, dj.iloc[1]), commit=True)
                        ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (costo_f, u_id), commit=True)
                        st.rerun()

# --- 7. MIS REPRESENTADOS ---
st.markdown("### 📋 Mi Cartera de Jugadores")
cartera = ejecutar_db("SELECT id, nombre_jugador, porcentaje, costo_compra, club FROM cartera WHERE usuario_id = ?", (u_id,))
if not cartera:
    st.info("Aún no tienes jugadores. Ve a Scouting para fichar tu primer equipo.")

for j_id, j_nom, j_pct, j_costo, j_club in cartera:
    with st.container(border=True):
        col1, col2, col3 = st.columns([3, 2, 1])
        col1.write(f"**{j_nom}** ({j_club})")
        col2.write(f"Participación: {int(j_pct)}%")
        if col3.button("VENDER", key=f"v_{j_id}"):
            ejecutar_db("DELETE FROM cartera WHERE id = ?", (j_id,), commit=True)
            ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (j_costo * 0.9, u_id), commit=True)
            st.rerun()

# --- 9. MODO ENTRENAMIENTO 11 VS 11 (NUEVO) ---
st.divider()
st.header("⚽ Centro de Entrenamiento (11 vs 11)")

# Necesitamos al menos 11 jugadores en cartera para jugar
if len(cartera) < 11:
    st.warning(f"Necesitas al menos 11 jugadores en tu cartera para un entrenamiento completo. Tienes: {len(cartera)}")
else:
    if st.button("🚀 INICIAR SIMULACIÓN DE PARTIDO", type="primary"):
        # 1. Seleccionar tus 11 (usamos los primeros 11 de la cartera)
        mis_11 = random.sample(cartera, 11)
        
        # 2. Generar Rival (11 aleatorios del Google Sheet)
        rival_11 = df_oficial.sample(11)
        
        # 3. Calcular Poder de Ataque/Defensa (Basado en ScoreOficial y Valor)
        # Mi Poder: Suma de Scores oficiales de mis 11
        mi_score_total = 0
        for j in mis_11:
            match = df_oficial[df_oficial.iloc[:, 0].str.strip() == j[1].strip()]
            val = match['ScoreOficial'].values[0] if not match.empty else 6.0
            mi_score_total += val
        
        rival_score_total = rival_11['ScoreOficial'].sum()
        
        # 4. Simulación del marcador
        # Un score de 7.0 promedio (77 total) suele dar 1-2 goles. 
        goles_yo = int((mi_score_total / 10) * random.uniform(0.1, 0.5))
        goles_rival = int((rival_score_total / 10) * random.uniform(0.1, 0.5))
        
        # 5. Mostrar el "Relato"
        st.subheader("🏟️ RESULTADO DEL ENTRENAMIENTO")
        col_res1, col_res2, col_res3 = st.columns(3)
        col_res1.metric(f"TU EQUIPO ({manager})", goles_yo)
        col_res2.markdown("<h1 style='text-align:center;'>VS</h1>", unsafe_allow_html=True)
        col_res3.metric("EQUIPO RIVAL SPARING", goles_rival)
        
        with st.expander("Ver detalle del encuentro"):
            c_a, c_b = st.columns(2)
            c_a.write("**Tu Alineación (Score Promedio):**")
            c_a.write(f"{mi_score_total/11:.2f}")
            for j in mis_11: c_a.caption(f"👕 {j[1]}")
            
            c_b.write("**Alineación Rival (Score Promedio):**")
            c_b.write(f"{rival_score_total/11:.2f}")
            for idx, row in rival_11.iterrows(): c_b.caption(f"🏃 {row.iloc[0]}")
        
        # Recompensa por ganar entrenamiento
        if goles_yo > goles_rival:
            premio = 50000
            ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (premio, u_id), commit=True)
            st.success(f"🏆 ¡Victoria! Has ganado € {formatear_total(premio)} por el éxito del entrenamiento.")
        elif goles_yo == goles_rival:
            st.info("🤝 Empate técnico. Los jugadores han ganado experiencia.")
        else:
            st.error("❌ Derrota. Debes mejorar tu cartera de representados.")

# --- 8. RANKING E HISTORIAL ---
st.divider()
c_rank, c_hist = st.columns(2)
with c_rank:
    with st.expander("🏆 Ranking de Agentes"):
        res = ejecutar_db("SELECT nombre, prestigio, presupuesto FROM usuarios ORDER BY prestigio DESC")
        st.table(pd.DataFrame(res, columns=['Agente', 'Rep', 'Caja']))
with c_hist:
    with st.expander("📜 Historial de Operaciones"):
        h = ejecutar_db("SELECT fecha, detalle, monto FROM historial WHERE usuario_id = ? ORDER BY id DESC LIMIT 10", (u_id,))
        st.dataframe(pd.DataFrame(h, columns=['Fecha', 'Evento', 'Monto']), hide_index=True)
