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

# --- INICIALIZACIÓN Y MIGRACIONES ---
ejecutar_db('''CREATE TABLE IF NOT EXISTS usuarios 
             (id INTEGER PRIMARY KEY, nombre TEXT UNIQUE, password TEXT, monedas REAL, 
             prestigio INTEGER DEFAULT 0, ultima_jornada TEXT DEFAULT '', 
             ganancias_historicas REAL DEFAULT 0, pts_liga INTEGER DEFAULT 0, 
             pj INTEGER DEFAULT 0, dg INTEGER DEFAULT 0)''', commit=True)

ejecutar_db('''CREATE TABLE IF NOT EXISTS plantilla 
             (id INTEGER PRIMARY KEY, usuario_id INTEGER, jugador_nombre TEXT, 
             posicion TEXT, nivel INTEGER, equipo TEXT, score REAL, es_titular INTEGER,
             ultima_oferta_fecha TEXT DEFAULT '', ultima_oferta_valor INTEGER DEFAULT 0)''', commit=True)

# Asegurar columnas de mercado si no existen
try:
    ejecutar_db("ALTER TABLE plantilla ADD COLUMN ultima_oferta_fecha TEXT DEFAULT ''", commit=True)
    ejecutar_db("ALTER TABLE plantilla ADD COLUMN ultima_oferta_valor INTEGER DEFAULT 0", commit=True)
except: pass

# --- 2. FUNCIONES DE APOYO ---
def es_oferta_valida(fecha_str):
    """Verifica si ya se pidió una oferta desde el último reset de las 8:00 AM"""
    if not fecha_str: return False
    ahora = datetime.now()
    # Calcular el último reset (hoy a las 8am o ayer a las 8am)
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
total_jugadores = len(jugadores_db)

st.markdown("### ⚽ VIRTUAL DT PRO")

# MÉTRICAS PRINCIPALES
c1, c2 = st.columns(2)
c1.metric("Presupuesto Actual", f"{int(monedas)} 🪙")

# --- SISTEMA DE COBRO Y PUNTAJE ---
# --- REEMPLAZA LA SECCIÓN DEL BOTÓN DE COBRO POR ESTA ---

if len(titulares) == 11:
    jornada_actual = str(df_base['Jornada'].iloc[0]) if 'Jornada' in df_base.columns else "S/J"
    ganancia = sum([int(max(0, j[4] - 60)) for j in titulares])
    
    c2.markdown(f"📅 **{jornada_actual}** | 📈 **Puntos:** {ganancia}")
    
    ultima_cobrada = ejecutar_db("SELECT ultima_jornada FROM usuarios WHERE id = ?", (u_id,))[0][0]

    if ultima_cobrada == jornada_actual:
        c2.success(f"✅ Jornada ya acreditada.")
    else:
        # --- CAPA DE SEGURIDAD VISUAL ---
        st.sidebar.divider() # Un separador para que se vea limpio
        confirmar = c2.checkbox("Confirmar validez de la formación", key="check_seguridad")
        
        # El botón solo se habilita si 'confirmar' es True
        if c2.button("💰 COBRAR JORNADA", 
                     use_container_width=True, 
                     type="primary", 
                     disabled=not confirmar): # <--- Aquí está la clave
            
            # Ejecutamos el cobro
            gf, gc, p_pts = 0, 0, 0
            if ganancia < 40: gf, gc, p_pts = 0, 3, 0
            elif 40 <= ganancia <= 59: gf, gc, p_pts = 0, 1, 0
            elif 60 <= ganancia <= 99: gf, gc, p_pts = 1, 1, 1
            elif ganancia >= 100: gf, gc, p_pts = 2, 0, 3
            
            ejecutar_db("""UPDATE usuarios SET 
                        monedas = monedas + ?, 
                        ganancias_historicas = ganancias_historicas + ?,
                        pts_liga = pts_liga + ?, 
                        pj = pj + 1, 
                        dg = dg + ?, 
                        ultima_jornada = ? 
                        WHERE id = ?""", 
                        (ganancia, ganancia, p_pts, (gf-gc), jornada_actual, u_id), commit=True)
            
            st.balloons()
            st.success(f"¡Cobrado! Resultado: {gf}-{gc}")
            time.sleep(2)
            st.rerun()
else:
    c2.warning(f"⚠️ Faltan {11 - len(titulares)} titulares")

# --- 5. RENDERIZADO DE PLANTILLA ---
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
                        # LÓGICA DE VENTA CORREGIDA (Única oferta hasta las 8 AM)
                        ya_busco_hoy = es_oferta_valida(f_ofert)
                        
                        if not ya_busco_hoy:
                            if st.button("🔍 Buscar Oferta", key=f"bus_{id_reg}", use_container_width=True):
                                with st.status("Buscando...", expanded=False):
                                    time.sleep(10)
                                    oferta = int((int(niv) * 15) * random.uniform(0.70, 1.30))
                                    ejecutar_db("UPDATE plantilla SET ultima_oferta_valor = ?, ultima_oferta_fecha = ? WHERE id = ?", 
                                               (oferta, datetime.now().strftime('%Y-%m-%d %H:%M:%S'), id_reg), commit=True)
                                st.rerun()
                        elif v_ofert > 0:
                            st.info(f"Oferta: {v_ofert} 🪙")
                            c_a, c_r = st.columns(2)
                            if c_a.button("✅", key=f"ok_{id_reg}"):
                                ejecutar_db("DELETE FROM plantilla WHERE id = ?", (id_reg,), commit=True)
                                ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (v_ofert, u_id), commit=True)
                                st.rerun()
                            if c_r.button("❌", key=f"no_{id_reg}"):
                                ejecutar_db("UPDATE plantilla SET ultima_oferta_valor = 0 WHERE id = ?", (id_reg,), commit=True)
                                st.rerun()
                        else:
                            st.error("⌛ Oferta agotada hasta las 8:00 AM")

                        if st.button("⬆️ Subir", key=f"up_{id_reg}"):
                            actual = len([p for p in titulares if p[1] == pk])
                            lim = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                            if len(titulares) < 11 and actual < lim.get(pk, 0):
                                ejecutar_db("UPDATE plantilla SET es_titular = 1 WHERE id = ?", (id_reg,), commit=True)
                                st.rerun()

st.divider()
st.subheader("TITULARES")
dibujar_plantilla(titulares, "titular")

# --- 6. OJEADOR (FICHAJES) ---
st.divider()
st.subheader("🕵️ OJEADOR")
co1, co2 = st.columns([1, 2])
with co1:
    if st.button("BUSCAR JUGADOR (Costo: 5 🪙)", use_container_width=True):
        if monedas >= 5:
            ejecutar_db("UPDATE usuarios SET monedas = monedas - 5 WHERE id = ?", (u_id,), commit=True)
            with st.status("Buscando..."):
                time.sleep(10)
                cand = df_base.sample(n=1).iloc[0]
                precio = int((int(cand['Nivel']) * 15) * random.uniform(0.70, 1.30))
                st.session_state.prospecto = {"n": cand['Jugador'], "p": cand['POS'], "l": int(cand['Nivel']), "e": cand['Equipo'], "s": float(cand['Score']), "pr": precio}
            st.rerun()
        else: st.error("Sin monedas.")

# --- BUSCAR ESTA PARTE EN TU SECCIÓN DE OJEADOR ---
if 'prospecto' in st.session_state:
    p = st.session_state.prospecto
    with co2:
        # 1. Creamos las estrellas visuales según el nivel
        estrellas = '★' * p['l'] 
        
        # 2. Usamos un encabezado de nivel 3 para que el nombre sea grande
        st.markdown(f"### 🏃 {p['n']}") 
        
        # 3. Mostramos la info secundaria en un formato destacado pero limpio
        st.markdown(f"**Posición:** {p['p']} | **Nivel:** {estrellas}")
        st.markdown(f"Equipo: :green[{p['e']}] | Score Actual: :orange[{p['s']}]")
        
        # 4. El precio en grande para generar impacto
        st.success(f"### 💰 Precio: {p['pr']} 🪙")
        
        ca1, ca2 = st.columns(2)
        if ca1.button("🤝 FICHAR JUGADOR", type="primary", use_container_width=True):
            if monedas >= p['pr']:
                ejecutar_db("INSERT INTO plantilla (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) VALUES (?,?,?,?,?,?,0)", 
                            (u_id, p['n'], p['p'], p['l'], p['e'], p['s']), commit=True)
                ejecutar_db("UPDATE usuarios SET monedas = monedas - ? WHERE id = ?", (p['pr'], u_id), commit=True)
                del st.session_state.prospecto
                st.rerun()
            else: 
                st.error("No tienes monedas suficientes.")
        
        if ca2.button("🚫 DESCARTAR", use_container_width=True):
            del st.session_state.prospecto
            st.rerun()

st.subheader("SUPLENTES")
dibujar_plantilla(suplentes, "suplente")

# --- 7. RANKING ---
st.divider()
st.subheader("🏆 TABLA DE LIGA")
ranking = ejecutar_db("SELECT nombre, pj, dg, pts_liga, ganancias_historicas FROM usuarios ORDER BY pts_liga DESC, dg DESC")
if ranking:
    st.table(pd.DataFrame(ranking, columns=["Manager", "PJ", "DG", "PTS", "Ganancia Total"]))
