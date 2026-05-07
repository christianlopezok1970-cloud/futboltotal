import streamlit as st
import pandas as pd
import json
import base64

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# --- 2. FUNCIONES DE APOYO ---
def formato_estrellas(nivel):
    return "★" * int(nivel) if str(nivel).isdigit() else "★"

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
    return f'<a href="data:file/json;base64,{b64}" download="partida_{st.session_state.usuario}.json" style="text-decoration:none; background-color:#4CAF50; color:white; padding:10px; border-radius:8px; display:block; text-align:center; font-weight:bold;">💾 GUARDAR PROGRESO</a>'

# --- 3. CARGA DE DATOS ---
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
    st.title("🛡️ SESIÓN")
    archivo = st.file_uploader("Cargar Partida (.json)", type="json")
    if archivo:
        data = json.load(archivo)
        st.session_state.update(data)
        st.session_state.autenticado = True

    if not st.session_state.autenticado:
        u = st.text_input("Nombre Manager").strip()
        if st.button("Nueva Partida"):
            if u:
                st.session_state.usuario, st.session_state.monedas = u, 1000
                st.session_state.titulares, st.session_state.suplentes, st.session_state.historial = [], [], []
                st.session_state.autenticado = True
                st.rerun()
    
    if st.session_state.autenticado:
        st.write(f"Manager: **{st.session_state.usuario}**")
        st.metric("Presupuesto", f"{st.session_state.monedas} 🪙")
        if st.button("🛒 FICHAR JUGADOR (50 🪙)"):
            if st.session_state.monedas >= 50:
                st.session_state.monedas -= 50
                nuevo = df_base.sample(n=1).to_dict('records')[0]
                st.session_state.suplentes.append(nuevo)
                st.rerun()
        st.divider()
        st.markdown(exportar_partida(), unsafe_allow_html=True)

if not st.session_state.autenticado: st.stop()

# Sincronizar datos
for lista in [st.session_state.titulares, st.session_state.suplentes]:
    for j in lista:
        match = df_base[df_base['Jugador'] == j['Jugador']]
        if not match.empty:
            j['Score'], j['Nivel'] = float(match.iloc[0]['Score']), int(match.iloc[0]['Nivel'])

# --- 5. PANEL PRINCIPAL ---
st.title(f"🥅 Campo de Juego")

# --- RECOMPENSA (Solo si están los 11) ---
if len(st.session_state.titulares) == 11:
    ganancia = sum([int((j['Score']-64)*3) if j['Score']>=65 else int(j['Score']-65) for j in st.session_state.titulares])
    st.info(f"Balance Jornada: **{ganancia} 🪙**")
    if st.button("💰 COBRAR RECOMPENSA"):
        st.session_state.monedas += ganancia
        st.rerun()
else:
    st.caption(f"Faltan {11 - len(st.session_state.titulares)} jugadores para completar el 1-4-4-2")

# --- FUNCION DE RENDERIZADO ---
MAPPING_POS = {"ARQ": "Arquero", "DEF": "Defensores", "VOL": "Volantes", "DEL": "Delanteros"}

def dibujar_lineas(lista_jugadores, modo="titular"):
    posiciones = ["ARQ", "DEF", "VOL", "DEL"]
    cols = st.columns(4)
    df = pd.DataFrame(lista_jugadores) if lista_jugadores else pd.DataFrame()
    
    for i, pos_key in enumerate(posiciones):
        with cols[i]:
            # Título más pequeño y nombre completo
            st.markdown(f"**{MAPPING_POS[pos_key]}**")
            if not df.empty and pos_key in df['POS'].values:
                df_pos = df[df['POS'] == pos_key]
                for _, jug in df_pos.iterrows():
                    with st.expander(f"{jug['Jugador']}"):
                        st.caption(f"{jug['Equipo']} | {formato_estrellas(jug['Nivel'])}")
                        st.write(f"Score: {jug['Score']}")
                        
                        if modo == "titular":
                            if st.button("⬇️ Bajar", key=f"t_{jug['Jugador']}"):
                                idx = next(idx for idx, j in enumerate(st.session_state.titulares) if j['Jugador'] == jug['Jugador'])
                                st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
                                st.rerun()
                        else:
                            if st.button("⬆️ Subir", key=f"s_{jug['Jugador']}"):
                                idx = next(idx for idx, j in enumerate(st.session_state.suplentes) if j['Jugador'] == jug['Jugador'])
                                limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
                                actual = [p['POS'] for p in st.session_state.titulares].count(pos_key)
                                if len(st.session_state.titulares) < 11 and actual < limites.get(pos_key, 0):
                                    st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                                    st.rerun()
                                else: st.error("Límite alcanzado")
                            
                            precio = int(jug['Nivel']) * 20
                            if st.button(f"💰 ${precio}", key=f"v_{jug['Jugador']}"):
                                idx = next(idx for idx, j in enumerate(st.session_state.suplentes) if j['Jugador'] == jug['Jugador'])
                                st.session_state.monedas += precio
                                st.session_state.suplentes.pop(idx)
                                st.rerun()
            else:
                st.caption("---")

# --- SECCIÓN TITULARES ---
st.divider()
st.subheader("📋 Alineación Titular (1-4-4-2)")
dibujar_lineas(st.session_state.titulares, modo="titular")

# --- SECCIÓN SUPLENTES (Con diferenciación) ---
st.divider()
st.info("📦 **BANCO DE SUPLENTES**") # Cuadro de color para diferenciar
dibujar_lineas(st.session_state.suplentes, modo="suplente")
