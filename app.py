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
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, 
              monedas REAL, prestigio INTEGER DEFAULT 0, ultimo_resultado REAL DEFAULT 0)''', commit=True)

# Parches de seguridad para columnas nuevas
try: ejecutar_db("ALTER TABLE usuarios ADD COLUMN prestigio INTEGER DEFAULT 0", commit=True)
except: pass
try: ejecutar_db("ALTER TABLE usuarios ADD COLUMN ultimo_resultado REAL DEFAULT 0", commit=True)
except: pass

ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT UNIQUE, 
              posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER)''', commit=True)

# --- 2. FUNCIONES DE APOYO ---
def generar_backup(u_id):
    user_data = ejecutar_db("SELECT nombre, monedas, prestigio, ultimo_resultado FROM usuarios WHERE id = ?", (u_id,))
    if not user_data: return "{}"
    user = user_data[0]
    plantilla = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular FROM plantilla WHERE usuario_id = ?", (u_id,))
    return json.dumps({
        "manager": user[0], "monedas": user[1], "prestigio": user[2], "puntos_fecha": user[3],
        "jugadores": [{"nombre": j[0], "pos": j[1], "nivel": j[2], "equipo": j[3], "score": j[4], "titular": j[5]} for j in plantilla]
    }, indent=4)

# --- 3. ESTILO VISUAL ---
st.markdown("<style>.stApp { background: linear-gradient(180deg, #0e1117 0%, #000814 100%); } .stMetric { background-color: rgba(255,255,255,0.05); padding: 10px; border-radius: 10px; }</style>", unsafe_allow_html=True)

# --- 4. CARGA DE DATOS ---
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

# --- 5. AUTENTICACIÓN ---
with st.sidebar:
    st.title("🛡️ ACCESO")
    manager = st.text_input("Manager").strip()
    password = st.text_input("Password", type="password").strip()

    if not manager or not password:
        st.info("Ingresa para jugar.")
        st.stop()

    datos = ejecutar_db("SELECT id, monedas, prestigio, ultimo_resultado, password FROM usuarios WHERE nombre = ?", (manager,))
    if not datos:
        if st.button("CREAR CUENTA"):
            ejecutar_db("INSERT INTO usuarios (nombre, password, monedas, prestigio, ultimo_resultado) VALUES (?, ?, 1000, 0, 0)", (manager, password), commit=True)
            st.success("¡Creado! Reingresa.")
            st.rerun()
        st.stop()
    else:
        u_id, monedas, prestigio, ult_res, u_pass = datos[0]
        if password != u_pass: st.error("Error de password"); st.stop()
        st.success(f"Conectado: {manager}")

    st.divider()
    if not st.toggle("🔒 Bloquear Reset", value=True):
        if st.button("🔴 RESETEAR CUENTA", use_container_width=True):
            ejecutar_db("DELETE FROM plantilla WHERE usuario_id = ?", (u_id,), commit=True)
            ejecutar_db("UPDATE usuarios SET monedas = 1000, prestigio = 0, ultimo_resultado = 0 WHERE id = ?", (u_id,), commit=True)
            st.rerun()
    st.download_button("📥 Backup JSON", generar_backup(u_id), f"vdt_{manager}.json", use_container_width=True)

# --- 6. LÓGICA DE JUEGO (Competencia con Score Actualizado) ---
jugadores_db = ejecutar_db("SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id FROM plantilla WHERE usuario_id = ?", (u_id,))
titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

st.markdown("### ⚽ VIRTUAL DT PRO")
c1, c2, c3 = st.columns(3)
c1.metric("Presupuesto", f"{int(monedas)} 🪙")
c2.metric("Nivel Club", f"{prestigio} 💎")
c3.metric("Puntos Última Fecha", f"{int(ult_res)} pts")

if len(titulares) == 11:
    # Cálculo basado estrictamente en el SCORE de la base de datos
    pts_base = sum([int((j[4]-64)*3) if j[4]>=65 else int(j[4]-65) for j in titulares])
    bonus = prestigio * 10 
    total_fecha = pts_base + bonus
    
    st.info(f"**Suma Score Titulares:** {sum([j[4] for j in titulares]):.1f} | **Puntos Ganados:** {pts_base} + {bonus} (Bonus)")
    
    if 'c_cobro' not in st.session_state: st.session_state.c_cobro = False
    if not st.session_state.c_cobro:
        if st.button("💰 COBRAR JORNADA", use_container_width=True):
            st.session_state.c_cobro = True; st.rerun()
    else:
        if st.button("✅ CONFIRMAR Y REGISTRAR RANKING", type="primary", use_container_width=True):
            ejecutar_db("UPDATE usuarios SET monedas = monedas + ?, ultimo_resultado = ? WHERE id = ?", (total_fecha, total_fecha, u_id), commit=True)
            st.session_state.c_cobro = False; st.rerun()
        if st.button("Cancelar"): st.session_state.c_cobro = False; st.rerun()
else:
    st.warning(f"Formación incompleta: Necesitas 11 titulares para puntuar (Tienes {len(titulares)}).")

with st.expander("💎 Oficina de Prestigio"):
    st.write(f"Prestigio actual: {prestigio}. Cada nivel te da +10 monedas extra por fecha.")
    if st.button("Comprar 1 Nivel (500 🪙)"):
        if monedas >= 500:
            ejecutar_db("UPDATE usuarios SET monedas = monedas - 500, prestigio = prestigio + 1 WHERE id = ?", (u_id,), commit=True)
            st.rerun()

# --- 7. RENDERIZADO DE PLANTILLA (Con Score Visible) ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    for i, pk in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{MAPPING_POS[pk]}**")
            for j in [x for x in lista if x[1] == pk]:
                # j[4] es el Score de la base de datos
                with st.expander(f"{j[0]} | Score: {j[4]}"):
                    st.caption(f"{j[3]} | {'★' * int(j[2])}")
                    if modo == "titular":
                        if st.button("⬇️ Banco", key=f"d_{j[6]}"):
                            ejecutar_db("UPDATE plantilla SET es_titular = 0 WHERE id = ?", (j[6],), commit=True); st.rerun()
                    else:
                        if st.button("⬆️ Titular", key=f"u_{j[6]}"):
                            lim = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                            actual = len([p for p in titulares if p[1]==pk])
                            if len(titulares) < 11 and actual < lim[pk]:
                                ejecutar_db("UPDATE plantilla SET es_titular = 1 WHERE id = ?", (j[6],), commit=True); st.rerun()
                        
                        p_v = int(j[2]) * 20
                        if st.button(f"Vender {p_v} 🪙", key=f"v_{j[6]}"):
                            ejecutar_db("DELETE FROM plantilla WHERE id = ?", (j[6],), commit=True)
                            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (p_v, u_id), commit=True); st.rerun()

st.divider()
st.subheader("🏃 FORMACIÓN TITULAR")
dibujar_plantilla(titulares, "titular")
st.divider()
st.subheader("📦 BANCO / MERCADO (Jugadores Únicos)")

if st.button("🛒 FICHAR JUGADOR AL AZAR (50 🪙)", use_container_width=True):
    if monedas >= 50:
        ocupados = [x[0] for x in ejecutar_db("SELECT jugador_nombre FROM plantilla")]
        disponibles = df_base[~df_base['Jugador'].isin(ocupados)]
        if not disponibles.empty:
            n = disponibles.sample(n=1).iloc[0]
            try:
                ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", 
                            (u_id, n['Jugador'], n['POS'], int(n['Nivel']), n['Equipo'], float(n['Score'])), commit=True)
                ejecutar_db("UPDATE usuarios SET monedas = monedas - 50 WHERE id = ?", (u_id,), commit=True)
                st.rerun()
            except sqlite3.IntegrityError: st.error("Duplicado detectado, intenta de nuevo.")
        else: st.error("¡Mercado agotado!")
    else: st.error("Sin monedas.")

dibujar_plantilla(suplentes, "suplente")

# --- 8. RANKING ---
st.divider()
with st.expander("🏆 RANKING DE LA FECHA"):
    rank_db = ejecutar_db("SELECT nombre, ultimo_resultado, prestigio FROM usuarios ORDER BY ultimo_resultado DESC, prestigio DESC")
    if rank_db:
        lb = [{"Manager": r[0], "Puntos": int(r[1]), "Nivel": r[2]} for r in rank_db]
        st.table(pd.DataFrame(lb))
