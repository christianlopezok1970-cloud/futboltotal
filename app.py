import streamlit as st
import pandas as pd
import json
import base64
import io

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# --- 2. FUNCIONES DE GUARDADO MANUAL (SOLUCIÓN SEGURA) ---
def exportar_partida():
    """Crea un link de descarga para el archivo de partida"""
    datos = {
        "usuario": st.session_state.usuario,
        "monedas": st.session_state.monedas,
        "titulares": st.session_state.titulares,
        "suplentes": st.session_state.suplentes,
        "historial": st.session_state.historial
    }
    # Convertimos a JSON y luego a Base64 para el link
    json_str = json.dumps(datos, indent=4)
    b64 = base64.b64encode(json_str.encode()).decode()
    nombre_archivo = f"partida_{st.session_state.usuario}.json"
    return f'<a href="data:file/json;base64,{b64}" download="{nombre_archivo}" style="text-decoration:none; background-color:#4CAF50; color:white; padding:10px; border-radius:5px;">💾 DESCARGAR MI PARTIDA</a>'

# --- 3. INICIO DE SESIÓN / CARGA ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

with st.sidebar:
    st.title("🛡️ SESIÓN")
    
    # OPCIÓN A: SUBIR ARCHIVO
    archivo_partida = st.file_uploader("Subir archivo de partida (.json)", type="json")
    if archivo_partida:
        try:
            data = json.load(archivo_partida)
            st.session_state.usuario = data['usuario']
            st.session_state.monedas = data['monedas']
            st.session_state.titulares = data['titulares']
            st.session_state.suplentes = data['suplentes']
            st.session_state.historial = data['historial']
            st.session_state.autenticado = True
            st.success("¡Partida cargada!")
        except:
            st.error("Archivo de partida inválido")

    # OPCIÓN B: NUEVA PARTIDA (Si no subió nada)
    if not st.session_state.autenticado:
        u = st.text_input("Nombre de Usuario").strip()
        if st.button("Iniciar Nueva Partida"):
            if u:
                st.session_state.usuario = u
                st.session_state.monedas = 1000
                st.session_state.titulares = []
                st.session_state.suplentes = []
                st.session_state.historial = ["Partida creada"]
                st.session_state.autenticado = True
                st.rerun()

if not st.session_state.autenticado:
    st.info("Sube tu archivo de partida o inicia una nueva desde el panel lateral.")
    st.stop()

# --- 4. CARGA DE DATOS (EXCEL PÚBLICO) ---
@st.cache_data
def load_market():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    df['Score'] = pd.to_numeric(df['Score'], errors='coerce').fillna(50)
    return df

df_base = load_market()

# --- 5. PANEL DE CONTROL (MERCADO) ---
with st.sidebar:
    st.divider()
    st.write(f"🎮 **Agente:** {st.session_state.usuario}")
    st.metric("Presupuesto", f"{st.session_state.monedas} 🪙")
    
    if st.button("🛒 FICHAR JUGADOR (50 🪙)"):
        if st.session_state.monedas >= 50:
            st.session_state.monedas -= 50
            nuevo = df_base.sample(n=1).to_dict('records')[0]
            st.session_state.suplentes.append(nuevo)
            st.session_state.historial.insert(0, f"Fichaje: {nuevo['Jugador']}")
            st.rerun()
        else: st.error("No hay monedas")
    
    st.divider()
    # EL BOTÓN DE SALVAR VIDA
    st.markdown(exportar_partida(), unsafe_allow_html=True)
    st.caption("⚠️ Descarga este archivo antes de cerrar la app para no perder tu progreso.")

# --- 6. LÓGICA DE JUEGO (TABLAS Y PREMIOS) ---
st.title("⚽ AFA Manager Pro 2026")

# Premiación
if len(st.session_state.titulares) == 11:
    st.subheader("🏆 Premiación Jornada")
    ganancia = 0
    for j in st.session_state.titulares:
        sc = float(df_base[df_base['Jugador'] == j['Jugador']]['Score'].values[0])
        ganancia += int((sc - 64) * 3) if sc >= 65 else int(sc - 65)
    
    st.write(f"Balance de hoy: **{ganancia} 🪙**")
    if st.button("COBRAR JORNADA 💰"):
        st.session_state.monedas += ganancia
        st.session_state.historial.insert(0, f"Cobro Jornada: {ganancia} 🪙")
        st.rerun()
else:
    st.info(f"Faltan {11 - len(st.session_state.titulares)} titulares para cobrar la jornada.")

# Tablas (Once Titular)
st.subheader("🔝 Once Titular")
if st.session_state.titulares:
    df_t = pd.DataFrame(st.session_state.titulares)
    st.dataframe(df_t[['POS', 'Jugador', 'Equipo']], use_container_width=True, hide_index=True)
    
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares])
    if st.button("⬇️ Bajar"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()

# Suplentes
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    st.dataframe(df_s[['Jugador', 'POS', 'Equipo']], use_container_width=True, hide_index=True)
    
    subir = st.selectbox("Subir al Once:", [j['Jugador'] for j in st.session_state.suplentes])
    if st.button("⬆️ Subir"):
        idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == subir)
        if len(st.session_state.titulares) < 11:
            st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
            st.rerun()
