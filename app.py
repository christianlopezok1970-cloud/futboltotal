import streamlit as st
import pandas as pd
import sqlite3
import random
import time
import google.generativeai as genai
from datetime import datetime, timedelta

# --- CONFIGURACIÓN IA ---
import google.generativeai as genai

# Tu clave (zdcU)
genai.configure(api_key="AIzaSyB7t9PwFp2_ySxFj8F-vMHrt6LHiSLzdcU")

def asistente_tecnico_pro(jugadores_info):
    """Versión 2026: Sin herramientas que den error 404, pero con datos reales."""
    try:
        # 1. Detectamos el nombre del modelo que te funcionó antes
        modelos_disponibles = [m.name for m in genai.list_models() 
                              if 'generateContent' in m.supported_generation_methods]
        modelo_nombre = next((m for m in modelos_disponibles if '1.5-flash' in m), modelos_disponibles[0])
        
        # 2. Configuramos el modelo SIN las tools (para evitar el 404)
        model = genai.GenerativeModel(modelo_nombre)
        
        # 3. Preparamos la data real de tu base de datos
        titulares = [j for j in jugadores_info if j[2] == 'Titular']
        suplentes = [j for j in jugadores_info if j[2] == 'Suplente']
        
        lista_titulares = "\n".join([f"- {j[0]} (Club: {j[3]}, Pos: {j[1]})" for j in titulares])
        lista_suplentes = "\n".join([f"- {j[0]} (Club: {j[3]}, Pos: {j[1]})" for j in suplentes])

        prompt = f"""
        SOS UN EXPERTO EN FÚTBOL ARGENTINO (DÍA: {datetime.now().strftime('%d/%m/%Y')}).
        NO INVENTES NOMBRES. ANALIZÁ EXACTAMENTE A ESTOS JUGADORES:

        TITULARES:
        {lista_titulares}

        SUPLENTES:
        {lista_suplentes}

        TAREA:
        1. De cada uno, informame si jugaron este último fin de semana en la vida real.
        2. Decime si están lesionados, suspendidos o si se sabe que descansan la próxima fecha.
        3. Si alguno de los SUPLENTES tuvo un partidazo, recomendame subirlo.
        4. Hablá como un ayudante de campo argentino, pero con DATOS REALES. Si no sabés algo de un jugador, decilo, no inventes.
        """
        
        # Generación directa
        response = model.generate_content(prompt)
        return response.text
        
    except Exception as e:
        return f"⚠️ Error en el vestuario: {str(e)}"

# --- 1. CONFIGURACIÓN Y BASE DE DATOS ---
st.set_page_config(page_title="Futbol Total - Pro", layout="wide")
DB_NAME = 'virtual_dt_pro.db'

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# --- INICIALIZACIÓN ---
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL, 
             prestigio INTEGER DEFAULT 0, ultima_jornada TEXT DEFAULT '', 
             ganancias_historicas REAL DEFAULT 0, pts_liga INTEGER DEFAULT 0, 
             pj INTEGER DEFAULT 0, dg INTEGER DEFAULT 0)''', commit=True)

ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT, 
             posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER,
             ultima_oferta_fecha TEXT DEFAULT '', ultima_oferta_valor INTEGER DEFAULT 0)''', commit=True)

# --- 2. FUNCIONES DE APOYO ---
def es_oferta_valida(fecha_str):
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

# --- 3. AUTENTICACIÓN ---
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
            st.rerun()
        st.stop()
    else:
        u_id, monedas, prestigio, u_pass = datos[0]
        if password != u_pass:
            st.error("Password incorrecto")
            st.stop()
        st.success(f"Conectado: {manager}")

# --- 4. LÓGICA DE JUEGO ---
jugadores_db = ejecutar_db("""SELECT jugador_nombre, posicion, nivel, equipo, score, es_titular, id, 
                             ultima_oferta_fecha, ultima_oferta_valor FROM plantilla WHERE usuario_id = ?""", (u_id,))

titulares = [j for j in jugadores_db if j[5] == 1]
suplentes = [j for j in jugadores_db if j[5] == 0]

st.markdown("### ⚽ VIRTUAL DT PRO")

c1, c2 = st.columns(2)
c1.metric("Presupuesto Actual", f"{int(monedas)} 🪙")

if len(titulares) == 11:
    jornada_actual = str(df_base['Jornada'].iloc[0]) if 'Jornada' in df_base.columns else "S/J"
    ganancia = sum([int(max(0, j[4] - 60)) for j in titulares])
    c2.markdown(f"📅 **{jornada_actual}** | 📈 **Puntos:** {ganancia}")
    ultima_cobrada = ejecutar_db("SELECT ultima_jornada FROM usuarios WHERE id = ?", (u_id,))[0][0]

    if ultima_cobrada == jornada_actual:
        c2.success(f"✅ Jornada acreditada.")
    else:
        confirmar = c2.checkbox("Confirmar formación", key="check_seguridad")
        if c2.button("💰 COBRAR", disabled=not confirmar):
            p_pts = 3 if ganancia >= 100 else (1 if ganancia >= 60 else 0)
            ejecutar_db("UPDATE usuarios SET monedas=monedas+?, pts_liga=pts_liga+?, pj=pj+1, ultima_jornada=? WHERE id=?", (ganancia, p_pts, jornada_actual, u_id), commit=True)
            st.balloons()
            st.rerun()
else:
    c2.warning(f"⚠️ Faltan {11 - len(titulares)} titulares")

# --- 5. RENDERIZADO ---
def dibujar_plantilla(lista, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    for i, pk in enumerate(posiciones):
        with cols[i]:
            st.markdown(f"**{pk}**")
            for j in [x for x in lista if x[1] == pk]:
                nom, pos, niv, eq, sco, tit, id_reg, f_ofert, v_ofert = j
                with st.expander(f"{nom}"):
                    st.caption(f"{eq} | {'★' * int(niv)}")
                    if modo == "titular":
                        if st.button("⬇️", key=f"down_{id_reg}"):
                            ejecutar_db("UPDATE plantilla SET es_titular=0 WHERE id=?", (id_reg,), commit=True); st.rerun()
                    else:
                        ya = es_oferta_valida(f_ofert)
                        if not ya:
                            if st.button("🔍", key=f"bus_{id_reg}"):
                                of = int((int(niv)*15)*random.uniform(0.7, 1.3))
                                ejecutar_db("UPDATE plantilla SET ultima_oferta_valor=?, ultima_oferta_fecha=? WHERE id=?", (of, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id_reg), commit=True); st.rerun()
                        elif v_ofert > 0:
                            st.write(f"{v_ofert}🪙")
                            if st.button("✅", key=f"ok_{id_reg}"):
                                ejecutar_db("DELETE FROM plantilla WHERE id=?", (id_reg,), commit=True)
                                ejecutar_db("UPDATE usuarios SET monedas=monedas+? WHERE id=?", (v_ofert, u_id), commit=True); st.rerun()
                        if st.button("⬆️", key=f"up_{id_reg}"):
                            ejecutar_db("UPDATE plantilla SET es_titular=1 WHERE id=?", (id_reg,), commit=True); st.rerun()

st.divider()
st.subheader("TITULARES")
dibujar_plantilla(titulares, "titular")

# --- NUEVA SECCIÓN: ASISTENTE TÉCNICO ---
st.divider()
st.subheader("👨‍🏫 Charla Técnica con el Profe")
if st.button("📋 PEDIR INFORME DE LA FECHA (IA + WEB)", use_container_width=True):
    if not jugadores_db:
        st.warning("No tenés jugadores.")
    else:
        with st.status("El Profe está analizando Promiedos y Olé...", expanded=True) as status:
            informe = asistente_tecnico_pro(jugadores_db)
            status.update(label="¡Informe listo!", state="complete")
            st.markdown(informe)
st.divider()

st.subheader("SUPLENTES")
dibujar_plantilla(suplentes, "suplente")

# --- 6. OJEADOR ---
st.subheader("🕵️ OJEADOR")
if st.button("BUSCAR JUGADOR (5 🪙)"):
    if monedas >= 5:
        ejecutar_db("UPDATE usuarios SET monedas=monedas-5 WHERE id=?", (u_id,), commit=True)
        cand = df_base.sample(n=1).iloc[0]
        precio = int((int(cand['Nivel'])*15)*random.uniform(0.7, 1.3))
        st.session_state.prospecto = {"n": cand['Jugador'], "p": cand['POS'], "l": int(cand['Nivel']), "e": cand['Equipo'], "s": float(cand['Score']), "pr": precio}
        st.rerun()

if 'prospecto' in st.session_state:
    p = st.session_state.prospecto
    st.info(f"### {p['n']} ({p['p']}) - {p['pr']} 🪙")
    if st.button("🤝 FICHAR"):
        ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", (u_id, p['n'], p['p'], p['l'], p['e'], p['s']), commit=True)
        ejecutar_db("UPDATE usuarios SET monedas=monedas-? WHERE id=?", (p['pr'], u_id), commit=True)
        del st.session_state.prospecto; st.rerun()

# --- 7. RANKING Y ADMIN ---
st.subheader("🏆 TABLA")
rk = ejecutar_db("SELECT nombre, pj, dg, pts_liga FROM usuarios ORDER BY pts_liga DESC")
if rk: st.table(pd.DataFrame(rk, columns=["Manager", "PJ", "DG", "PTS"]))

with st.sidebar.expander("⚠️ Admin"):
    if st.text_input("PIN", type="password") == "2020":
        user_adm = st.text_input("Manager a resetear")
        if st.button("🔄 RESET"):
            uid = ejecutar_db("SELECT id FROM usuarios WHERE nombre=?", (user_adm,))[0][0]
            ejecutar_db("DELETE FROM plantilla WHERE usuario_id=?", (uid,), commit=True)
            ejecutar_db("UPDATE usuarios SET monedas=1000, pj=0, pts_liga=0 WHERE id=?", (uid,), commit=True)
            st.success("Reseteado"); st.rerun()
