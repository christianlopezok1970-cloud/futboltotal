import streamlit as st
import pandas as pd
import json
import base64
import random

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# --- 2. FUNCIONES DE APOYO ---
def formato_estrellas(nivel):
    try:
        n = int(nivel)
        return "★" * n
    except:
        return "★"

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
    return f'<a href="data:file/json;base64,{b64}" download="partida_{st.session_state.usuario}.json" style="text-decoration:none; background-color:#4CAF50; color:white; padding:12px; border-radius:8px; display:block; text-align:center; font-weight:bold; margin-top:10px;">💾 GUARDAR PARTIDA (DESCARGAR)</a>'

# --- 3. CARGA DE DATOS (EXCEL) ---
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

# --- 4. GESTIÓN DE SESIÓN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

with st.sidebar:
    st.title("🛡️ MI SESIÓN")
    archivo = st.file_uploader("Cargar archivo .json", type="json")
    if archivo:
        data = json.load(archivo)
        st.session_state.usuario = data['usuario']
        st.session_state.monedas = data['monedas']
        st.session_state.titulares = data['titulares']
        st.session_state.suplentes = data['suplentes']
        st.session_state.historial = data['historial']
        st.session_state.autenticado = True
        st.success("¡Partida cargada!")

    if not st.session_state.autenticado:
        u = st.text_input("Nombre del Manager")
        if st.button("Empezar Nueva Aventura"):
            if u:
                st.session_state.usuario = u
                st.session_state.monedas = 1000
                st.session_state.titulares = []
                st.session_state.suplentes = []
                st.session_state.historial = []
                st.session_state.autenticado = True
                st.rerun()
    
    if st.session_state.autenticado:
        st.write(f"Manager: **{st.session_state.usuario}**")
        st.metric("Presupuesto", f"{st.session_state.monedas} 🪙")
        st.divider()
        if st.button("🛒 FICHAR ALEATORIO (50 🪙)"):
            if st.session_state.monedas >= 50:
                st.session_state.monedas -= 50
                nuevo = df_base.sample(n=1).to_dict('records')[0]
                st.session_state.suplentes.append(nuevo)
                st.rerun()
        st.divider()
        st.markdown(exportar_partida(), unsafe_allow_html=True)

if not st.session_state.autenticado:
    st.stop()

# --- 5. PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Sincronizar Scores y Niveles con el Excel
for lista in [st.session_state.titulares, st.session_state.suplentes]:
    for j in lista:
        match = df_base[df_base['Jugador'] == j['Jugador']]
        if not match.empty:
            j['Score'] = float(match.iloc[0]['Score'])
            j['Nivel'] = int(match.iloc[0]['Nivel'])

# --- SECCIÓN DE PREMIOS ---
st.subheader("🏆 Premios de la Jornada")
if len(st.session_state.titulares) == 11:
    ganancia_total = 0
    for j in st.session_state.titulares:
        sc = j.get('Score', 50)
        puntos = int((sc - 64) * 3) if sc >= 65 else int(sc - 65)
        ganancia_total += puntos
    
    st.write(f"Balance de hoy: **{ganancia_total} 🪙**")
    if st.button("COBRAR RECOMPENSA 💰"):
        st.session_state.monedas += ganancia_total
        st.session_state.historial.insert(0, f"Cobro: {ganancia_total} 🪙")
        st.rerun()
else:
    st.info(f"Faltan {11 - len(st.session_state.titulares)} titulares para calcular premios.")

# --- ONCE TITULAR ---
st.divider()
st.subheader("🔝 Once Titular")
if st.session_state.titulares:
    df_t = pd.DataFrame(st.session_state.titulares)
    df_t['Rango'] = df_t['Nivel'].apply(formato_estrellas)
    st.dataframe(df_t[['POS', 'Jugador', 'Equipo', 'Score', 'Rango']], use_container_width=True, hide_index=True)
    
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares], key="q")
    if st.button("⬇️ Bajar al Banco"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()

# --- SUPLENTES Y VENTAS ---
st.divider()
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    df_s['Rango'] = df_s['Nivel'].apply(formato_estrellas)
    st.dataframe(df_s[['Jugador', 'POS', 'Rango', 'Equipo']], use_container_width=True, hide_index=True)

    col1, col2 = st.columns(2)
    with col1:
        subir = st.selectbox("Subir al Once:", [j['Jugador'] for j in st.session_state.suplentes], key="s")
        if st.button("⬆️ Poner de Titular"):
            if len(st.session_state.titulares) < 11:
                idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == subir)
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
    
    with col2:
        vender = st.selectbox("Vender Jugador:", [j['Jugador'] for j in st.session_state.suplentes], key="v")
        # PRECIO DE VENTA DINÁMICO: Nivel 1=20, Nivel 5=100
        idx_v = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender)
        precio_v = int(st.session_state.suplentes[idx_v].get('Nivel', 1)) * 20
        
        if st.button(f"💰 VENDER POR {precio_v} 🪙"):
            st.session_state.monedas += precio_v
            st.session_state.suplentes.pop(idx_v)
            st.rerun()
