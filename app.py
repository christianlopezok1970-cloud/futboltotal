import streamlit as st
import pandas as pd
import sqlite3
import json
import base64
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

# Inicializar Tablas con sistema de Prestigio
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL, prestigio INTEGER DEFAULT 0)''', commit=True)
ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT, 
              posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER)''', commit=True)

# --- 2. FUNCIONES DE APOYO ---
def generar_backup(u_id):
    # Obtiene datos del usuario y su plantilla para respaldo externo
    user = ejecutar_db("SELECT nombre, monedas, prestigio FROM usuarios WHERE id = ?", (u_id,))[0]
    plantilla = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular FROM plantilla WHERE usuario_id = ?", (u_id,))
    
    data = {
        "manager": user[0],
        "monedas": user[1],
        "prestigio_comprado": user[2],
        "jugadores": [
            {"nombre": j[0], "pos": j[1], "nivel": j[2], "equipo": j[3], "score": j[4], "titular": j[5]} 
            for j in plantilla
        ]
    }
    return json.dumps(data, indent=4)

# --- 3. ESTILO VISUAL ---
st.markdown("""
    <style>
    .stApp { background: linear-gradient(180deg, #0e1117 0%, #000814 100%); }
    .stMetric { background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; }
    h1, h2, h3 { color: #f0f2f6 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CARGA DE DATOS (Google Sheets) ---
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

# --- 5. AUTENTICACIÓN Y GESTIÓN ---
with st.sidebar:
    st.title("🛡️ ACCESO MANAGER")
    manager = st.text_input("Manager").strip()
    password = st.text_input("Password", type="password").strip()

    if not manager or not password:
        st.info("Ingresa tus credenciales para continuar.")
        st.stop()

    datos = ejecutar_db("SELECT id, monedas, prestigio, password FROM usuarios WHERE nombre = ?", (manager,))
    
    if not datos:
        if st.button("CREAR NUEVA CUENTA"):
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas, prestigio) VALUES (?, ?, 1000, 0)", (manager, password), commit=True)
            st.success("Cuenta creada. ¡Vuelve a pulsar para entrar!")
            st.rerun()
        st.stop()
    else:
        u_id, monedas, prestigio, u_pass = datos[0]
        if password != u_pass:
            st.error("Contraseña incorrecta")
            st.stop()
        st.success(f"Conectado: {manager}")

    # Panel de Control (Backup y Reset con Seguridad)
    st.divider()
    st.subheader("⚙️ Configuración")
    
    json_backup = generar_backup(u_id)
    st.download_button(
        label="📥 Descargar Backup",
        data=json_backup,
        file_name=f"partida_{manager}.json",
        mime="application/json",
        use_container_width=True
    )

    if not st.toggle("🔒 Bloquear Reset", value=True):
        if st.button("🔴 RESETEAR CUENTA", use_container_width=True):
            ejecutar_db("DELETE FROM plantilla WHERE usuario_id = ?", (u_id,), commit=True)
            ejecutar_db("UPDATE usuarios SET monedas = 1000, prestigio = 0 WHERE id = ?", (u_id,), commit=True)
            st.rerun()

# --- 6. LÓGICA DE JUEGO ---
jugadores_db = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id FROM plantilla WHERE usuario_id = ?", (u_id,))
titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

st.markdown(f"### ⚽ VIRTUAL DT PRO")

col_m1, col_m2 = st.columns(2)
col_m1.metric("Presupuesto Actual", f"{int(monedas)} 🪙") # Sin decimales

# Sistema de Cobro con Doble Seguridad
if len(titulares) == 11:
    ganancia = sum([int((j[4]-64)*3) if j[4]>=65 else int(j[4]-65) for j in titulares])
    col_m2.markdown(f"**Balance Jornada:** {ganancia} 🪙")
    
    if 'confirmar_cobro' not in st.session_state: st.session_state.confirmar_cobro = False

    if not st.session_state.confirmar_cobro:
        if col_m2.button("💰 COBRAR JORNADA", use_container_width=True):
            st.session_state.confirmar_cobro = True
            st.rerun()
    else:
        c1, c2 = col_m2.columns(2)
        if c1.button("✅ CONFIRMAR", type="primary", use_container_width=True):
            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (ganancia, u_id), commit=True)
            st.session_state.confirmar_cobro = False
            st.toast("¡Cobro realizado!")
            st.rerun()
        if c2.button("❌", use_container_width=True):
            st.session_state.confirmar_cobro = False
            st.rerun()
else:
    col_m2.warning(f"Faltan {11 - len(titulares)} titulares")

# Sistema de Prestigio
with st.expander("💎 Oficina de Prestigio"):
    st.write(f"Prestigio: **{prestigio} pts**")
    costo_p = 500
    if st.button(f"Comprar 1 Pto de Prestigio ({costo_p} 🪙)", use_container_width=True):
        if monedas >= costo_p:
            ejecutar_db("UPDATE usuarios SET monedas = monedas - ?, prestigio = prestigio + 1 WHERE id = ?", (costo_p, u_id), commit=True)
            st.rerun()
        else: st.error("No tienes suficientes monedas.")

# --- 7. RENDERIZADO DE PLANTILLA ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    for i, pos_key in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{MAPPING_POS[pos_key]}**")
            jugs_pos = [j for j in lista if j[1] == pos_key]
            for j in jugs_pos:
                with st.expander(f"{j[0]}"):
                    # Nivel mostrado en estrellas
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
                            else: st.error("Límite de posición alcanzado.")
                        
                        # Venta con Doble Seguridad y emoji
                        precio_v = int(j[2]) * 20
                        key_v = f"venda_{j[6]}"
                        if key_v not in st.session_state: st.session_state[key_v] = False

                        if not st.session_state[key_v]:
                            if st.button(f"Vender {precio_v} 🪙", key=f"btn_v_{j[6]}", use_container_width=True):
                                st.session_state[key_v] = True
                                st.rerun()
                        else:
                            st.warning("¿Vender?")
                            cv1, cv2 = st.columns(2)
                            if cv1.button("✅", key=f"v_si_{j[6]}"):
                                ejecutar_db("DELETE FROM plantilla WHERE id = ?", (j[6],), commit=True)
                                ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (precio_v, u_id), commit=True)
                                st.session_state[key_v] = False
                                st.rerun()
                            if cv2.button("❌", key=f"v_no_{j[6]}"):
                                st.session_state[key_v] = False
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
    else: st.error("No tienes monedas suficientes.")

dibujar_plantilla(suplentes, modo="suplente")

# --- 8. RANKING DINÁMICO (VALOR TOTAL) ---
st.divider()
with st.expander("🏆 RANKING GLOBAL DE MANAGERS"):
    # Ranking basado en: Monedas + Valor Plantilla + Bonus Prestigio
    users = ejecutar_db("SELECT id, nombre, monedas, prestigio FROM usuarios")
    lb = []
    for u in users:
        u_id_val, u_nom, u_mon, u_pre = u
        plantilla_u = ejecutar_db("SELECT nivel FROM plantilla WHERE usuario_id = ?", (u_id_val,))
        valor_jugs = sum([j[0] * 20 for j in plantilla_u])
        total_score = int(u_mon + valor_jugs + (u_pre * 100))
        lb.append({"Manager": u_nom, "Valor Total 💎": total_score, "Prestigio": u_pre, "Caja": int(u_mon)})
    
    df_rank = pd.DataFrame(lb).sort_values(by="Valor Total 💎", ascending=False)
    st.table(df_rank)
