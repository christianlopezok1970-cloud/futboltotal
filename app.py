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

# --- 3. LOGIN / REGISTRO ---
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
        return df
    except:
        return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score"])

df_base = load_data()

# --- 5. FORMATO DE ESTRELLAS (PEDIDO) ---
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

# TABLA TITULARES
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
else: st.info("Selecciona jugadores del banco para armar tu equipo.")

st.divider()

# TABLA SUPLENTES
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
            else: st.error(f"Límite de {j['POS']} alcanzado.")

    with c2:
        st.write("**Ventas**")
        vender_nombre = st.selectbox("Vender Jugador:", [j['Jugador'] for j in st.session_state.suplentes], key="v_sup")
        
        # Cálculo de precio para mostrar antes de vender
        idx_v = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender_nombre)
        precio = int(st.session_state.suplentes[idx_v]['Nivel']) * 20
        
        st.info(f"Valor de reventa: **{precio} 🪙**")
        
        if st.button("VENDER AHORA 💰"):
            st.session_state.monedas += precio
            st.session_state.historial.insert(0, f"Venta: {vender_nombre} (+{precio} 🪙)")
            st.session_state.suplentes.pop(idx_v)
            guardar_progreso()
            st.toast(f"Vendido por {precio} 🪙")
            st.rerun()

with st.expander("📜 Ver Historial"):
    for h in st.session_state.historial: st.write(f"- {h}")
