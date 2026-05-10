import streamlit as st
import pandas as pd
import sqlite3
import json
import time
import random
from datetime import datetime, timedelta

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="Futbol Total - Pro", layout="wide")
DB_NAME = 'virtual_dt_pro.db'

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# --- INICIALIZACIÓN DE TABLAS Y MIGRACIONES ---
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL, 
             prestigio INTEGER DEFAULT 0, ultima_jornada TEXT DEFAULT '', 
             ganancias_historicas REAL DEFAULT 0, pts_liga INTEGER DEFAULT 0, 
             pj INTEGER DEFAULT 0, dg INTEGER DEFAULT 0)''', commit=True)

ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT, 
             posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER)''', commit=True)

# MIGRACIÓN: Columnas para ofertas de venta
try:
    ejecutar_db("ALTER TABLE plantilla ADD COLUMN ultima_oferta_fecha TEXT DEFAULT ''", commit=True)
    ejecutar_db("ALTER TABLE plantilla ADD COLUMN ultima_oferta_valor INTEGER DEFAULT 0", commit=True)
except: pass

# --- 2. FUNCIONES DE APOYO ---
def get_proximo_reset():
    """Calcula el próximo reset de las 8:00 AM"""
    ahora = datetime.now()
    reset_hoy = ahora.replace(hour=8, minute=0, second=0, microsecond=0)
    if ahora >= reset_hoy:
        return reset_hoy + timedelta(days=1)
    return reset_hoy

def es_oferta_valida(fecha_str):
    """Verifica si la oferta se hizo después del último reset de las 8:00 AM"""
    if not fecha_str: return False
    ahora = datetime.now()
    ultimo_reset = ahora.replace(hour=8, minute=0, second=0, microsecond=0)
    if ahora < ultimo_reset:
        ultimo_reset -= timedelta(days=1)
    
    fecha_oferta = datetime.strptime(fecha_str, '%Y-%m-%d %H:%M:%S')
    return fecha_oferta > ultimo_reset

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

# --- 3. AUTENTICACIÓN (SIDERBAR) ---
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
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas) VALUES (?, ?, 1000)", (manager, password), commit=True)
            st.success("¡Cuenta creada!")
            st.rerun()
        st.stop()
    else:
        u_id, monedas, prestigio, u_pass = datos[0]
        if password != u_pass:
            st.error("Contraseña incorrecta")
            st.stop()
        st.success(f"Conectado: {manager}")

# --- 4. LÓGICA DE PLANTILLA ---
# Actualizamos el SELECT para traer los datos de ofertas
jugadores_db = ejecutar_db("""SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id, 
                             ultima_oferta_fecha, ultima_oferta_valor FROM plantilla WHERE usuario_id = ?""", (u_id,))

titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    mapping = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}
    cols = st.columns(4)
    
    for i, pk in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{mapping[pk]}**")
            for j in [x for x in lista if x[1] == pk]:
                nom, pos, niv, eq, sco, tit, id_reg, f_ofert, v_ofert = j
                with st.expander(f"{nom}"):
                    st.caption(f"{eq} | {'★' * int(niv)}")
                    st.write(f"Score: **{sco}**")
                    
                    if modo == "titular":
                        if st.button("⬇️ Bajar", key=f"down_{id_reg}"):
                            ejecutar_db("UPDATE plantilla SET es_titular = 0 WHERE id = ?", (id_reg,), commit=True)
                            st.rerun()
                    else:
                        # --- LÓGICA DE MERCADO DE VENTA (RESET 8:00 AM) ---
                        valida = es_oferta_valida(f_ofert)
                        p_base = int(niv) * 15
                        
                        if not valida or v_ofert == 0:
                            if st.button("🔍 Buscar Oferta", key=f"bus_{id_reg}", use_container_width=True):
                                with st.status("Buscando comprador...", expanded=False):
                                    time.sleep(10) # 10 segundos fijos
                                    dado = random.randint(1, 100)
                                    # Rango +- 30%
                                    modificador = random.uniform(0.70, 1.30)
                                    oferta = int(p_base * modificador)
                                    ahora_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                                    ejecutar_db("UPDATE plantilla SET ultima_oferta_valor = ?, ultima_oferta_fecha = ? WHERE id = ?", 
                                               (oferta, ahora_str, id_reg), commit=True)
                                st.rerun()
                        else:
                            st.info(f"Oferta: {v_ofert} 🪙")
                            c1, c2 = st.columns(2)
                            if c1.button("✅", key=f"ok_{id_reg}"):
                                ejecutar_db("DELETE FROM plantilla WHERE id = ?", (id_reg,), commit=True)
                                ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (v_ofert, u_id), commit=True)
                                st.rerun()
                            if c2.button("❌", key=f"no_{id_reg}"):
                                # Rechazar bloquea hasta las 8 AM poniendo el valor en 0
                                ejecutar_db("UPDATE plantilla SET ultima_oferta_valor = 0 WHERE id = ?", (id_reg,), commit=True)
                                st.rerun()
                        
                        if st.button("⬆️ Subir", key=f"up_{id_reg}"):
                            actual = len([p for p in titulares if p[1] == pk])
                            lim = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                            if len(titulares) < 11 and actual < lim.get(pk, 0):
                                ejecutar_db("UPDATE plantilla SET es_titular = 1 WHERE id = ?", (id_reg,), commit=True)
                                st.rerun()

# --- 5. RENDERIZADO PRINCIPAL ---
st.subheader("TITULARES")
dibujar_plantilla(titulares, "titular")
st.divider()

# --- 6. SISTEMA DE OJEADOR (COMPRA) ---
st.subheader("🛒 MERCADO DE FICHAJES")
col_oj1, col_oj2 = st.columns([1, 2])

with col_oj1:
    if st.button("🕵️ CONTRATAR OJEADOR (5 🪙)", use_container_width=True):
        if monedas >= 5:
            ejecutar_db("UPDATE usuarios SET monedas = monedas - 5 WHERE id = ?", (u_id,), commit=True)
            with st.status("El ojeador está viajando...", expanded=True) as status:
                progress_bar = st.progress(0)
                for i in range(100):
                    time.sleep(0.1) # 10 segundos totales
                    progress_bar.progress(i + 1)
                
                # Buscamos jugador al azar
                candidato = df_base.sample(n=1).iloc[0]
                base_c = int(candidato['Nivel']) * 15
                precio_c = int(base_c * random.uniform(0.70, 1.30)) # +- 30%
                
                st.session_state.ojeador_res = {
                    "nombre": candidato['Jugador'], "pos": candidato['POS'],
                    "nivel": int(candidato['Nivel']), "equipo": candidato['Equipo'],
                    "score": float(candidato['Score']), "precio": precio_c
                }
                status.update(label="¡Jugador encontrado!", state="complete")
            st.rerun()
        else: st.error("Monedas insuficientes")

if 'ojeador_res' in st.session_state:
    res = st.session_state.ojeador_res
    with col_oj2:
        st.markdown(f"### {res['nombre']} ({res['pos']})")
        st.write(f"Nivel: {'★' * res['nivel']} | Equipo: {res['equipo']}")
        st.markdown(f"## Precio: {res['precio']} 🪙")
        
        ca1, ca2 = st.columns(2)
        if ca1.button("🤝 FICHAR AHORA", type="primary"):
            if monedas >= res['precio']:
                ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", 
                            (u_id, res['nombre'], res['pos'], res['nivel'], res['equipo'], res['score']), commit=True)
                ejecutar_db("UPDATE usuarios SET monedas = monedas - ? WHERE id = ?", (res['precio'], u_id), commit=True)
                del st.session_state.ojeador_res
                st.success("¡Fichado!")
                st.rerun()
            else: st.error("No te alcanza.")
        if ca2.button("🚫 DESCARTAR"):
            del st.session_state.ojeador_res
            st.rerun()

st.divider()
st.subheader("SUPLENTES")
dibujar_plantilla(suplentes, "suplente")

# --- 7. TABLA DE POSICIONES (RANKING) ---
st.divider()
st.subheader("🏆 TABLA DE POSICIONES")
leaderboard = ejecutar_db("SELECT nombre, pj, dg, pts_liga, ganancias_historicas FROM usuarios ORDER BY pts_liga DESC, dg DESC")
if leaderboard:
    df_leader = pd.DataFrame(leaderboard, columns=["Manager", "PJ", "DG", "PTS", "Ganancia"])
    st.table(df_leader)
