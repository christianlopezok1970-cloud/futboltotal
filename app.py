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
    return f'<a href="data:file/json;base64,{b64}" download="partida_{st.session_state.usuario}.json" style="text-decoration:none; background-color:#4CAF50; color:white; padding:12px; border-radius:8px; display:block; text-align:center; font-weight:bold;">💾 GUARDAR PROGRESO (DESCARGAR)</a>'

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
        st.metric("Presupuesto", f"{st.session_state.monedas} 🪙")
        if st.button("🛒 FICHAR (50 🪙)"):
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
st.title(f"🥅 Campo de Juego: 1-4-4-2")

# --- RESUMEN DE PUNTAJES ---
if st.session_state.titulares:
    suma_pts = sum([j['Score'] for j in st.session_state.titulares])
    ganancia = sum([int((j['Score']-64)*3) if j['Score']>=65 else int(j['Score']-65) for j in st.session_state.titulares])
    
    c1, c2 = st.columns(2)
    c1.metric("Puntaje Total", f"{suma_pts:.1f} pts")
    if len(st.session_state.titulares) == 11:
        c2.metric("Balance Jornada", f"{ganancia} 🪙")
        if st.button("💰 COBRAR RECOMPENSA"):
            st.session_state.monedas += ganancia
            st.rerun()
    else:
        c2.warning(f"Faltan {11 - len(st.session_state.titulares)} jugadores")

# --- LISTADOS SEPARADOS POR POSICIÓN ---
st.divider()
posiciones_orden = ["ARQ", "DEF", "VOL", "DEL"]
titulares_df = pd.DataFrame(st.session_state.titulares) if st.session_state.titulares else pd.DataFrame()

cols = st.columns(4)
for i, pos in enumerate(posiciones_orden):
    with cols[i]:
        st.markdown(f"### {pos}")
        if not titulares_df.empty:
            df_pos = titulares_df[titulares_df['POS'] == pos]
            if not df_pos.empty:
                for _, jug in df_pos.iterrows():
                    with st.expander(f"{jug['Jugador']}"):
                        st.write(f"{jug['Equipo']} | {formato_estrellas(jug['Nivel'])}")
                        st.write(f"Score: {jug['Score']}")
                        if st.button("⬇️ Bajar", key=f"b_{jug['Jugador']}"):
                            idx = next(idx for idx, j in enumerate(st.session_state.titulares) if j['Jugador'] == jug['Jugador'])
                            st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
                            st.rerun()
            else: st.caption("Vacío")
        else: st.caption("Vacío")

# --- BANCO DE SUPLENTES Y VENTAS ---
st.divider()
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    df_s['Rango'] = df_s['Nivel'].apply(formato_estrellas)
    st.dataframe(df_s[['Jugador', 'POS', 'Rango', 'Equipo', 'Score']], use_container_width=True, hide_index=True)

    col_subir, col_vender = st.columns(2)
    with col_subir:
        s = st.selectbox("Elegir para subir:", [j['Jugador'] for j in st.session_state.suplentes])
        if st.button("⬆️ Subir al 11"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == s)
            jug = st.session_state.suplentes[idx]
            
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            actual = [p['POS'] for p in st.session_state.titulares].count(jug['POS'])
            
            if len(st.session_state.titulares) < 11 and actual < limites.get(jug['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
            else:
                st.error(f"Cupo lleno para {jug['POS']} (Máximo {limites.get(jug['POS'])})")

    with col_vender:
        v = st.selectbox("Elegir para vender:", [j['Jugador'] for j in st.session_state.suplentes], key="v_sel")
        idx_v = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == v)
        precio = int(st.session_state.suplentes[idx_v]['Nivel']) * 20
        if st.button(f"💰 VENDER POR {precio} 🪙"):
            st.session_state.monedas += precio
            st.session_state.suplentes.pop(idx_v)
            st.rerun()
