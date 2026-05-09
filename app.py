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

# --- 1. CONFIGURACIÓN E INICIALIZACIÓN DE TABLAS ---

# Tabla de Usuarios (Estructura base)
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL)''', commit=True)

# Agregamos las columnas nuevas (usamos try/except por si ya existen de ejecuciones previas)
try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN prestigio INTEGER DEFAULT 0", commit=True)
except: pass

try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN ultima_jornada TEXT DEFAULT ''", commit=True)
except: pass

try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN ganancias_historicas REAL DEFAULT 0", commit=True)
except: pass

# Nuevas columnas para el Ranking de Liga (Simulación de Partidos)
try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN pts_liga INTEGER DEFAULT 0", commit=True)
except: pass
try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN pj INTEGER DEFAULT 0", commit=True)
except: pass
try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN dg INTEGER DEFAULT 0", commit=True)
except: pass

# Tabla de Plantilla
ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT, 
             posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER)''', commit=True)

# --- 2. CARGA DE DATOS (EXCEL/SHEET) ---
@st.cache_data(ttl=300) 
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(50)
        df['Nivel'] = pd.to_numeric(df['Nivel'], errors='coerce').fillna(1)
        return df
    except:
        return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score", "Jornada"])

df_base = load_data()

# --- 3. FUNCIONES DE APOYO ---
def generar_backup(u_id):
    user_data = ejecutar_db("SELECT nombre, monedas, prestigio FROM usuarios WHERE id = ?", (u_id,))
    if not user_data: return "{}"
    user = user_data[0]
    plantilla = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular FROM plantilla WHERE usuario_id = ?", (u_id,))
    data = {
        "manager": user[0], "monedas": user[1], "prestigio_comprado": user[2],
        "jugadores": [{"nombre": j[0], "pos": j[1], "nivel": j[2], "equipo": j[3], "score": j[4], "titular": j[5]} for j in plantilla]
    }
    return json.dumps(data, indent=4)

def sincronizar_scores(u_id, df_web):
    scores_dict = df_web.set_index('Jugador')['Score'].to_dict()
    plantilla_local = ejecutar_db("SELECT id, jugador_nombre FROM plantilla WHERE usuario_id = ?", (u_id,))
    for id_reg, nombre_jug in plantilla_local:
        if nombre_jug in scores_dict:
            nuevo_score = float(scores_dict[nombre_jug])
            ejecutar_db("UPDATE plantilla SET score = ? WHERE id = ?", (nuevo_score, id_reg), commit=True)

# --- 4. ESTILO VISUAL ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0e1117 0%, #000814 100%); }
    .stMetric { background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; }
    h1, h2, h3 { color: #f0f2f6 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 5. AUTENTICACIÓN ---
with st.sidebar:
    st.title("🛡️ ACCESO MANAGER")
    manager = st.text_input("Manager").strip()
    password = st.text_input("Password", type="password").strip()

    if not manager or not password:
        st.info("Ingresa tus credenciales.")
        st.stop()

    datos = ejecutar_db("SELECT id, monedas, prestigio, password FROM usuarios WHERE nombre = ?", (manager,))
    
    if not datos:
        if st.button("CREAR NUEVA CUENTA"):
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas, prestigio, pts_liga, pj, dg) VALUES (?, ?, 1000, 0, 0, 0, 0)", (manager, password), commit=True)
            st.success("¡Cuenta creada! Reingresa.")
            st.rerun()
        st.stop()
    else:
        u_id, monedas, prestigio, u_pass = datos[0]
        if password != u_pass:
            st.error("Contraseña incorrecta")
            st.stop()
        sincronizar_scores(u_id, df_base)
        st.success(f"Conectado: {manager}")

    st.divider()
    st.download_button("📥 Backup", generar_backup(u_id), f"vdt_{manager}.json", "application/json", use_container_width=True)

    if not st.toggle("🔒 Bloquear Reset", value=True):
        if st.button("🔴 RESETEAR CUENTA", use_container_width=True):
            ejecutar_db("DELETE FROM plantilla WHERE usuario_id = ?", (u_id,), commit=True)
            ejecutar_db("UPDATE usuarios SET monedas = 1000, prestigio = 0, pts_liga = 0, pj = 0, dg = 0, ganancias_historicas = 0, ultima_jornada = '' WHERE id = ?", (u_id,), commit=True)
            st.rerun()

# --- 6. LÓGICA DE JUEGO ---
jugadores_db = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id FROM plantilla WHERE usuario_id = ?", (u_id,))
titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

# --- AQUÍ DEFINIMOS LAS VARIABLES PARA EVITAR EL NAMEERROR ---
total_jugadores = len(titulares) + len(suplentes)
valor_club = sum([int(j[2]) * 15 for j in jugadores_db])

st.markdown("### ⚽ VIRTUAL DT PRO")

c1, c2 = st.columns(2)
c1.metric("Presupuesto Actual", f"{int(monedas)} 🪙")

# --- SISTEMA DE RESCATE (CORREGIDO) ---
if monedas < 50 and total_jugadores < 11 and len(suplentes) == 0:
    st.error(f"🚨 CRISIS DE PLANTILLA: Tienes {int(monedas)} 🪙 pero necesitas 50 para fichar.")
    
    posiciones_actuales = [j[1] for j in titulares]
    formacion_ideal = ['ARQ', 'DEF', 'DEF', 'DEF', 'DEF', 'VOL', 'VOL', 'VOL', 'VOL', 'DEL', 'DEL']
    
    posicion_faltante = None
    temp_pos = posiciones_actuales.copy()
    for p in formacion_ideal:
        if p in temp_pos:
            temp_pos.remove(p)
        else:
            posicion_faltante = p
            break
            
    if posicion_faltante:
        with st.expander(f"SOLICITAR REFUERZO GRATUITO ({posicion_faltante})"):
            st.write(f"La liga te asignará un jugador en la posición de **{posicion_faltante}**.")
            if st.button("Fichar Refuerzo de Emergencia"):
                pool = df_base[(df_base['POS'] == posicion_faltante) & (df_base['Nivel'] == 0)]
                if pool.empty:
                    pool = df_base[df_base['POS'] == posicion_faltante].sort_values('Nivel')

                if not pool.empty:
                    n = pool.sample(n=1).iloc[0]
                    ejecutar_db("""INSERT INTO plantilla 
                                 (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) 
                                 VALUES (?, ?, ?, ?, ?, ?, 1)""", 
                                 (u_id, n['Jugador'], n['POS'], int(n['Nivel']), n['Equipo'], float(n['Score'])), 
                                 commit=True)
                    
                    st.success(f"¡{n['Jugador']} (Nivel {n['Nivel']}) se ha unido al equipo!")
                    st.rerun()

# --- LÓGICA DE COBRO CON FILTRO DE JORNADA Y SIMULACIÓN ---
if len(titulares) == 11:
    jornada_actual = str(df_base['Jornada'].iloc[0]) if 'Jornada' in df_base.columns else "S/J"
    
    datos_user = ejecutar_db("SELECT ultima_jornada, ganancias_historicas FROM usuarios WHERE id = ?", (u_id,))
    ultima_cobrada = datos_user[0][0] if datos_user else ""

    ganancia = sum([int(max(0, j[4] - 60)) for j in titulares])
    
    c2.markdown(f"📅 **{jornada_actual}**")
    c2.markdown(f"💰 **Ganancia:** {ganancia} 🪙")

    if ultima_cobrada == jornada_actual:
        c2.success(f"✅ La {jornada_actual} ya fue acreditada.")
    else:
        if 'c_cobro' not in st.session_state: st.session_state.c_cobro = False
        
        if not st.session_state.c_cobro:
            if c2.button("💰 COBRAR JORNADA", use_container_width=True):
                st.session_state.c_cobro = True
                st.rerun()
        else:
            if c2.button("⚠️ CONFIRMAR COBRO", type="primary", use_container_width=True):
                gf, gc, p_pts = 0, 0, 0
                if ganancia < 40: gf, gc, p_pts = 0, 3, 0
                elif 40 <= ganancia <= 49: gf, gc, p_pts = 0, 2, 0
                elif 50 <= ganancia <= 59: gf, gc, p_pts = 0, 1, 0
                elif 60 <= ganancia <= 99: gf, gc, p_pts = 0, 0, 1
                elif 100 <= ganancia <= 109: gf, gc, p_pts = 1, 0, 3
                elif 110 <= ganancia <= 119: gf, gc, p_pts = 2, 0, 3
                elif 120 <= ganancia <= 129: gf, gc, p_pts = 3, 0, 3
                elif 130 <= ganancia <= 139: gf, gc, p_pts = 4, 0, 3
                elif ganancia >= 140: gf, gc, p_pts = 5, 0, 3
                
                dg_jornada = gf - gc

                ejecutar_db("""UPDATE usuarios SET 
                            monedas = monedas + ?, 
                            ganancias_historicas = ganancias_historicas + ?,
                            pts_liga = pts_liga + ?,
                            pj = pj + 1,
                            dg = dg + ?,
                            ultima_jornada = ? 
                            WHERE id = ?""", 
                            (ganancia, ganancia, p_pts, dg_jornada, jornada_actual, u_id), commit=True)
                
                st.session_state.c_cobro = False
                st.success(f"¡{jornada_actual} Cobrada! Resultado: {gf}-{gc}")
                st.rerun()
            if c2.button("Cancelar"):
                st.session_state.c_cobro = False
                st.rerun()
else:
    c2.warning(f"Faltan {11 - len(titulares)} titulares")

# --- 7. RENDERIZADO DE PLANTILLA ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    for i, pk in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{MAPPING_POS[pk]}**")
            for j in [x for x in lista if x[1] == pk]:
                id_jugador = j[6]
                with st.expander(f"{j[0]}"):
                    st.caption(f"{j[3]} | {'★' * int(j[2])}")
                    st.write(f"Score: **{j[4]}**")
                    
                    if modo == "titular":
                        if st.button("⬇️ Bajar", key=f"down_{id_jugador}"):
                            ejecutar_db("UPDATE plantilla SET es_titular = 0 WHERE id = ?", (id_jugador,), commit=True)
                            st.rerun()
                    else:
                        if st.button("⬆️ Subir", key=f"up_{id_jugador}"):
                            actual = len([p for p in titulares if p[1] == pk])
                            lim = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                            if len(titulares) < 11 and actual < lim.get(pk, 0):
                                ejecutar_db("UPDATE plantilla SET es_titular = 1 WHERE id = ?", (id_jugador,), commit=True)
                                st.rerun()
                            else: st.error("Límite!")
                        
                        p_venta = int(j[2]) * 15
                        confirm_key = f"vender_conf_{id_jugador}"
                        
                        if not st.session_state.get(confirm_key, False):
                            if st.button(f"Vender {p_venta} 🪙", key=f"v_{id_jugador}", use_container_width=True):
                                st.session_state[confirm_key] = True
                                st.rerun()
                        else:
                            st.warning("¿Vender?")
                            c_v1, c_v2 = st.columns(2)
                            if c_v1.button("✅", key=f"si_v_{id_jugador}", type="primary"):
                                ejecutar_db("DELETE FROM plantilla WHERE id = ?", (id_jugador,), commit=True)
                                ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (p_venta, u_id), commit=True)
                                st.session_state[confirm_key] = False
                                st.rerun()
                            if c_v2.button("❌", key=f"no_v_{id_jugador}"):
                                st.session_state[confirm_key] = False
                                st.rerun()

st.divider()
st.subheader("TITULARES")
dibujar_plantilla(titulares, "titular")
st.divider()
st.subheader("SUPLENTES")

if not st.session_state.get('conf_fichar', False):
    if st.button("🛒 FICHAR JUGADOR (50 🪙)", use_container_width=True):
        if monedas >= 50:
            st.session_state.conf_fichar = True
            st.rerun()
        else: st.error("No tienes suficientes monedas.")
else:
    st.warning("¿Quieres gastar 50 🪙?")
    cf1, cf2 = st.columns(2)
    if cf1.button("✅ COMPRAR", key="fichar_si", type="primary", use_container_width=True):
        n = df_base.sample(n=1).iloc[0]
        with st.spinner("🔍 Buscando jugador..."):
            import time
            time.sleep(3.5) # Aquí ajustas los segundos de espera
        ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", 
                    (u_id, n['Jugador'], n['POS'], int(n['Nivel']), n['Equipo'], float(n['Score'])), commit=True)
        ejecutar_db("UPDATE usuarios SET monedas = monedas - 50 WHERE id = ?", (u_id,), commit=True)
        st.session_state.conf_fichar = False
        st.rerun()
    if cf2.button("❌ CANCELAR", key="fichar_no", use_container_width=True):
        st.session_state.conf_fichar = False
        st.rerun()

dibujar_plantilla(suplentes, "suplente")

# --- 8. RANKING DE LIGA OFICIAL ---
st.divider()
st.subheader("🏆 TABLA DE POSICIONES")

# Consultamos incluyendo las ganancias_historicas y ordenamos por los 3 criterios
leaderboard = ejecutar_db("""
    SELECT nombre, pj, dg, pts_liga, ganancias_historicas 
    FROM usuarios 
    ORDER BY pts_liga DESC, dg DESC, ganancias_historicas DESC
""")

if leaderboard:
    tabla_liga = []
    for i, (nom, pj, dg, pts, gan) in enumerate(leaderboard):
        # Asignamos medallas por posición
        medalla = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "🏃"
        
        # Agregamos los datos a la lista que verá el usuario
        tabla_liga.append({
            "Pos": medalla, 
            "Manager": nom, 
            "PTS": pts,           # <--- Ahora se ve primero el puntaje
            "PJ": pj, 
            "DG": dg, 
            "Ganancia": f"{int(gan)} 🪙"
        })
    
    # Mostramos la tabla final
    st.table(pd.DataFrame(tabla_liga))

# --- HERRAMIENTA TEMPORAL DE LIMPIEZA ---
with st.sidebar.expander("⚠️ Zona de Administración"):
    pin = st.text_input("PIN de Seguridad", type="password")
    if pin == "2020": 
        usuario_a_borrar = st.text_input("Nombre del usuario a borrar")
        if st.button("BORRAR USUARIO DEFINITIVAMENTE"):
            user_id_data = ejecutar_db("SELECT id FROM usuarios WHERE nombre = ?", (usuario_a_borrar,))
            if user_id_data:
                u_id_borrar = user_id_data[0][0]
                ejecutar_db("DELETE FROM plantilla WHERE usuario_id = ?", (u_id_borrar,), commit=True)
                ejecutar_db("DELETE FROM usuarios WHERE id = ?", (u_id_borrar,), commit=True)
                st.success(f"Eliminado: {usuario_a_borrar}")
                st.rerun()
