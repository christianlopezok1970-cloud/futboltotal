import streamlit as st
import pandas as pd
import json
import base64
import random

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# --- 2. PERSISTENCIA MANUAL (BOTÓN DE DESCARGA) ---
def exportar_partida():
    datos = {
        "usuario": st.session_state.usuario,
        "monedas": st.session_state.monedas,
        "titulares": st.session_state.titulares,
        "suplentes": st.session_state.suplentes,
        "historial": st.session_state.historial
    }
    json_str = json.dumps(datos, indent=4)
    b64 = base64.b64encode(json_str.encode()).decode()
    return f'<a href="data:file/json;base64,{b64}" download="partida_{st.session_state.usuario}.json" style="text-decoration:none; background-color:#4CAF50; color:white; padding:10px; border-radius:5px; display:block; text-align:center;">💾 DESCARGAR PARTIDA</a>'

# --- 3. CARGA DE DATOS ---
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(50)
        return df
    except:
        return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score"])

df_base = load_data()

# --- 4. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

with st.sidebar:
    st.title("🛡️ SESIÓN")
    archivo = st.file_uploader("Cargar partida (.json)", type="json")
    if archivo:
        data = json.load(archivo)
        st.session_state.usuario = data['usuario']
        st.session_state.monedas = data['monedas']
        st.session_state.titulares = data['titulares']
        st.session_state.suplentes = data['suplentes']
        st.session_state.historial = data['historial']
        st.session_state.autenticado = True

    if not st.session_state.autenticado:
        u = st.text_input("Nombre Manager").strip()
        if st.button("Empezar de Cero"):
            if u:
                st.session_state.usuario = u
                st.session_state.monedas = 1000
                st.session_state.titulares = []
                st.session_state.suplentes = []
                st.session_state.historial = ["Cuenta creada"]
                st.session_state.autenticado = True
                st.rerun()
    
    if st.session_state.autenticado:
        st.write(f"Manager: **{st.session_state.usuario}**")
        st.metric("Presupuesto", f"{st.session_state.monedas} 🪙")
        st.divider()
        if st.button("🛒 FICHAR (50 🪙)"):
            if st.session_state.monedas >= 50:
                st.session_state.monedas -= 50
                nuevo = df_base.sample(n=1).to_dict('records')[0]
                st.session_state.suplentes.append(nuevo)
                st.rerun()
        st.divider()
        st.markdown(exportar_partida(), unsafe_allow_html=True)

if not st.session_state.autenticado:
    st.info("Sube tu archivo o crea un usuario nuevo.")
    st.stop()

# --- 5. PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# SINCRONIZAR PUNTAJES (Para que siempre aparezca el score real del excel)
for lista in [st.session_state.titulares, st.session_state.suplentes]:
    for j in lista:
        match = df_base[df_base['Jugador'] == j['Jugador']]
        if not match.empty:
            j['Score'] = float(match.iloc[0]['Score'])

# --- SECCIÓN DE PREMIOS ---
st.subheader("🏆 Jornada Actual")
if len(st.session_state.titulares) == 11:
    ganancia_total = 0
    desglose = []
    for j in st.session_state.titulares:
        sc = j.get('Score', 50)
        puntos = int((sc - 64) * 3) if sc >= 65 else int(sc - 65)
        ganancia_total += puntos
        desglose.append(f"{j['Jugador']}: {puntos} 🪙")
    
    st.write(f"Balance neto proyectado: **{ganancia_total} 🪙**")
    if st.button("COBRAR RECOMPENSA 💰"):
        st.session_state.monedas += ganancia_total
        st.rerun()
else:
    st.info(f"Forma tu 11 titular (Faltan {11 - len(st.session_state.titulares)})")

# --- ONCE TITULAR ---
st.divider()
st.subheader("🔝 Once Titular")
if st.session_state.titulares:
    df_t = pd.DataFrame(st.session_state.titulares)
    st.dataframe(df_t[['POS', 'Jugador', 'Equipo', 'Score']], use_container_width=True, hide_index=True)
    
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares], key="sel_t")
    if st.button("⬇️ Bajar al Banco"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()

# --- SUPLENTES Y VENTAS ---
st.divider()
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    st.dataframe(df_s[['Jugador', 'POS', 'Equipo', 'Score']], use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        subir = st.selectbox("Subir al Once:", [j['Jugador'] for j in st.session_state.suplentes], key="sel_s")
        if st.button("⬆️ Poner de Titular"):
            if len(st.session_state.titulares) < 11:
                idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == subir)
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
    
    with col2:
        vender = st.selectbox("Vender Jugador (100 🪙):", [j['Jugador'] for j in st.session_state.suplentes], key="sel_v")
        if st.button("💰 VENDER"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender)
            st.session_state.suplentes.pop(idx)
            st.session_state.monedas += 100
            st.rerun()
