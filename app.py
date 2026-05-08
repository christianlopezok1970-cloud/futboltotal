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

# Inicializar Tablas
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL)''', commit=True)

try:
    ejecutar_db("ALTER TABLE usuarios ADD COLUMN prestigio INTEGER DEFAULT 0", commit=True)
except:
    pass

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
        return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score"])

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

# --- 4. RENDERIZADO DE PLANTILLA CON SEGURIDAD ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_plantilla(lista, modo="titular", u_id=None, monedas=0, titulares=[]):
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
                            else: st.error("¡Límite!")
                        
                        # --- SEGURIDAD VENDER ---
                        p_venta = int(j[2]) * 20
                        key_confirm = f"v_conf_{id_jugador}"
                        
                        if not st.session_state.get(key_confirm, False):
                            if st.button(f"Vender {p_venta} 🪙", key=f"btn_v_{id_jugador}", use_container_width=True):
                                st.session_state[key_confirm] = True
                                st.rerun()
                        else:
                            st.warning("¿Vender?")
                            c1, c2 = st.columns(2)
                            if c1.button("✅", key=f"si_v_{id_jugador}"):
                                ejecutar_db("DELETE FROM plantilla WHERE id = ?", (id_jugador,), commit=True)
                                ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (p_venta, u_id), commit=True)
                                st.session_state[key_confirm] = False
                                st.rerun()
                            if c2.button("❌", key=f"no_v_{id_jugador}"):
                                st.session_state[key_confirm] = False
                                st.rerun()

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
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas, prestigio) VALUES (?, ?, 1000, 0)", (manager, password), commit=True)
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
    st.download_button("📥 Backup", generar_backup(u_id), f"vdt_{manager}.json", "application/json")

# --- 6. LÓGICA DE JUEGO ---
jugadores_db = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id FROM plantilla WHERE usuario_id = ?", (u_id,))
titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

st.markdown(f"### ⚽ VIRTUAL DT PRO: {manager}")
col_m1, col_m2 = st.columns(2)
col_m1.metric("Presupuesto", f"{int(monedas)} 🪙")

# --- 7. FICHAR CON SEGURIDAD ---
with st.container():
    if not st.session_state.get('conf_fichar', False):
        if st.button("🛒 FICHAR JUGADOR (50 🪙)", use_container_width=True):
            if monedas >= 50:
                st.session_state.conf_fichar = True
                st.rerun()
            else: st.error("Sin monedas")
    else:
        st.warning("¿Confirmas la compra de 50 🪙?")
        cf1, cf2 = st.columns(2)
        if cf1.button("✅ COMPRAR", type="primary"):
            n = df_base.sample(n=1).iloc[0]
            ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", 
                        (u_id, n['Jugador'], n['POS'], int(n['Nivel']), n['Equipo'], float(n['Score'])), commit=True)
            ejecutar_db("UPDATE usuarios SET monedas = monedas - 50 WHERE id = ?", (u_id,), commit=True)
            st.session_state.conf_fichar = False
            st.rerun()
        if cf2.button("❌ CANCELAR"):
            st.session_state.conf_fichar = False
            st.rerun()

st.divider()
st.subheader("🏃 TITULARES")
dibujar_plantilla(titulares, "titular", u_id, monedas, titulares)

st.divider()
st.subheader("📦 SUPLENTES")
dibujar_plantilla(suplentes, "suplente", u_id, monedas, titulares)

# --- 8. RANKING ---
with st.expander("🏆 RANKING"):
    usrs = ejecutar_db("SELECT id, nombre, monedas, prestigio FROM usuarios")
    lb = [{"Manager": u[1], "Total": int(u[2] + u[3]*100)} for u in usrs]
    st.table(pd.DataFrame(lb).sort_values("Total", ascending=False))
