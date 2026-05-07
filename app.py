import streamlit as st
import pandas as pd
import random
import os
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

DB_USERS = "usuarios_db.json"
DB_PARTIDAS = "partidas_db.json"

# --- 2. PERSISTENCIA ---
def cargar_json(archivo, defecto):
    if os.path.exists(archivo):
        try:
            with open(archivo, "r") as f: return json.load(f)
        except: return defecto
    return defecto

def guardar_json(archivo, datos):
    with open(archivo, "w") as f: json.dump(datos, f)

def guardar_progreso():
    if 'usuario' in st.session_state and st.session_state.autenticado:
        partidas = cargar_json(DB_PARTIDAS, {})
        partidas[st.session_state.usuario] = {
            "monedas": st.session_state.monedas,
            "titulares": st.session_state.titulares,
            "suplentes": st.session_state.suplentes,
            "historial": st.session_state.historial
        }
        guardar_json(DB_PARTIDAS, partidas)

# --- 3. LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    with st.sidebar:
        st.title("🛡️ ACCESO / REGISTRO")
        u = st.text_input("Usuario").strip()
        p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar / Crear Cuenta"):
            if u and p:
                usuarios = cargar_json(DB_USERS, {"admin": "1234"})
                if u in usuarios:
                    if usuarios[u] == p:
                        st.session_state.autenticado = True
                        st.session_state.usuario = u
                    else: st.error("Clave incorrecta.")
                else:
                    usuarios[u] = p
                    guardar_json(DB_USERS, usuarios)
                    st.session_state.autenticado = True
                    st.session_state.usuario = u
                
                if st.session_state.autenticado:
                    partidas = cargar_json(DB_PARTIDAS, {})
                    progreso = partidas.get(st.session_state.usuario, {
                        "monedas": 1000, "titulares": [], "suplentes": [], "historial": ["Partida iniciada"]
                    })
                    st.session_state.monedas = progreso["monedas"]
                    st.session_state.titulares = progreso["titulares"]
                    st.session_state.suplentes = progreso["suplentes"]
                    st.session_state.historial = progreso["historial"]
                    st.rerun()
    st.stop()

# --- 4. DATOS ---
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        # Limpiar Score: si es NaN o <= 0, poner 50 por defecto
        df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(50)
        df.loc[df['Score'] <= 0, 'Score'] = 50
        return df
    except:
        return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score"])

df_base = load_data()

# --- 5. FORMATO ---
def formato_nivel(n):
    try: n = int(n)
    except: return f"{n}★"
    if n == 5: return "★★★★★"
    if n == 4: return "★★★★"
    if n == 3: return "★★★"
    if n == 2: return "★★"
    return "★"

def ordenar_titulares():
    orden = {'ARQ': 0, 'DEF': 1, 'VOL': 2, 'DEL': 3}
    st.session_state.titulares.sort(key=lambda x: orden.get(x['POS'], 99))

# --- 6. SIDEBAR ---
with st.sidebar:
    st.write(f"🎮 **Manager:** {st.session_state.usuario}")
    st.metric("Presupuesto", f"{st.session_state.monedas} 🪙")
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    st.divider()
    st.subheader("🛒 Mercado")
    if st.button("FICHAR JUGADOR (50 🪙)"):
        if st.session_state.monedas >= 50:
            if len(st.session_state.suplentes) < 30:
                st.session_state.monedas -= 50
                nuevo = df_base.sample(n=1).to_dict('records')[0]
                st.session_state.suplentes.append(nuevo)
                st.session_state.historial.insert(0, f"Fichaje: {nuevo['Jugador']}")
                guardar_progreso()
                st.toast(f"¡{nuevo['Jugador']} fichado!")
                st.rerun()
            else: st.warning("Banco lleno")
        else: st.error("No tienes suficientes 🪙")

# --- 7. PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# --- LÓGICA DE PREMIOS POR SUMATORIA ---
st.subheader("🏆 Premiación de Jornada")
if len(st.session_state.titulares) == 11:
    ganancia_total = 0
    detalles = []
    
    for j in st.session_state.titulares:
        sc = float(j.get('Score', 50))
        if sc >= 65:
            puntos_ganados = int((sc - 64) * 3)
        else:
            puntos_ganados = int(sc - 65) # Dará negativo: 64 -> -1, etc.
        
        ganancia_total += puntos_ganados
        detalles.append(f"{j['Jugador']} ({sc} pts): {'+' if puntos_ganados > 0 else ''}{puntos_ganados}")

    col1, col2 = st.columns([2,1])
    col1.write(f"Balance de la jornada: **{'+' if ganancia_total > 0 else ''}{ganancia_total} 🪙**")
    
    with col1.expander("Ver desglose por jugador"):
        for d in detalles: st.write(d)

    if col2.button("COBRAR RECOMPENSA 💰"):
        st.session_state.monedas += ganancia_total
        # Evitar monedas negativas si el balance fue muy malo
        if st.session_state.monedas < 0: st.session_state.monedas = 0
        
        st.session_state.historial.insert(0, f"Balance Jornada: {ganancia_total} 🪙")
        guardar_progreso()
        if ganancia_total >= 0:
            st.success(f"¡Ganaste {ganancia_total} 🪙!")
        else:
            st.error(f"Perdiste {abs(ganancia_total)} 🪙 por bajo rendimiento.")
        st.rerun()
else:
    st.info("Forma tu 11 titular para calcular la ganancia de la jornada.")

st.divider()

# --- TABLAS ---
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    ordenar_titulares()
    df_t = pd.DataFrame(st.session_state.titulares)
    df_t['Nivel_Stars'] = df_t['Nivel'].apply(formato_nivel)
    st.dataframe(df_t[['POS', 'Jugador', 'Equipo', 'Nivel_Stars', 'Score']], use_container_width=True, hide_index=True, height=422)
    
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares], key="q_tit")
    if st.button("Bajar al banco ⬇️"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        guardar_progreso()
        st.rerun()

st.divider()

st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    df_s['Nivel_Stars'] = df_s['Nivel'].apply(formato_nivel)
    st.dataframe(df_s[['Jugador', 'POS', 'Nivel_Stars', 'Equipo']], use_container_width=True, hide_index=True, height=300)

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Táctica**")
        subir = st.selectbox("Subir al Once:", [j['Jugador'] for j in st.session_state.suplentes], key="s_sup")
        if st.button("Poner de Titular ⬆️"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == subir)
            j = st.session_state.suplentes[idx]
            conteo = [p['POS'] for p in st.session_state.titulares].count(j['POS'])
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            if conteo < limites.get(j['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                guardar_progreso()
                st.rerun()
            else: st.error(f"Límite alcanzado.")

    with c2:
        st.write("**Ventas**")
        vender_n = st.selectbox("Vender Jugador:", [j['Jugador'] for j in st.session_state.suplentes], key="v_sup")
        idx_v = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender_n)
        precio = int(st.session_state.suplentes[idx_v]['Nivel']) * 20
        st.info(f"Precio: {precio} 🪙")
        if st.button("VENDER 💰"):
            st.session_state.monedas += precio
            st.session_state.suplentes.pop(idx_v)
            guardar_progreso()
            st.rerun()

with st.expander("📜 Ver Historial"):
    for h in st.session_state.historial: st.write(f"- {h}")
