import streamlit as st
import pandas as pd
import random

# Configuración de página
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# 1. Carga de datos (982 jugadores)
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except:
        return pd.DataFrame(columns=["Código", "Jugador", "POS", "Nivel", "Equipo", "Score", "Jornada"])

df_base = load_data()

# 2. Inicialización del Estado (Presupuesto Inicial: 1000)
if 'creditos' not in st.session_state:
    st.session_state.creditos = 1000
if 'titulares' not in st.session_state:
    st.session_state.titulares = []
if 'suplentes' not in st.session_state:
    st.session_state.suplentes = []
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("👤 PANEL DE CONTROL")
    st.metric("Presupuesto Actual", f"{st.session_state.creditos} c")
    
    st.divider()
    
    # RULETA INSTANTÁNEA (Botón sin giro)
    st.subheader("🎡 Ruleta de Créditos")
    if st.button("OBTENER RESULTADO 🎲"):
        res = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
        st.session_state.creditos += res
        st.session_state.historial.insert(0, f"Ruleta: {res}c")
        if res > 0: st.success(f"Resultado: +{res} créditos")
        elif res < 0: st.error(f"Resultado: -{abs(res)} crédito")
        else: st.info("Resultado: 0 créditos")

    st.divider()
    
    # COMPRA DE JUGADORES (Doble seguridad con confirmación de Streamlit)
    st.subheader("🛒 Mercado")
    if st.button("COMPRAR PACK (100c)"):
        if st.session_state.creditos >= 100:
            if len(st.session_state.suplentes) < 25:
                st.session_state.creditos -= 100
                nuevos = df_base.sample(n=2).to_dict('records')
                st.session_state.suplentes.extend(nuevos)
                st.session_state.historial.insert(0, f"Fichaje: {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}")
                st.toast(f"¡Nuevos fichajes: {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}!")
            else:
                st.warning("Banco lleno (Máximo 25 suplentes)")
        else:
            st.error("Créditos insuficientes")

# --- PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Sección 1: Titulares (Listado Superior)
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    df_tit = pd.DataFrame(st.session_state.titulares)
    df_tit['Nivel_Stars'] = df_tit['Nivel'].apply(lambda x: "⭐" * int(x))
    st.table(df_tit[['Jugador', 'POS', 'Nivel_Stars', 'Equipo', 'Score']])
    
    # Botón para mandar al banco
    quitar = st.selectbox("Seleccionar titular para mandar al banco:", [j['Jugador'] for j in st.session_state.titulares], key="drop_tit")
    if st.button("Mandar al banco 🛋️"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()
else:
    st.warning("Sin formación definida. Sube jugadores desde el banco.")

st.divider()

# Sección 2: Suplentes (Listado Inferior)
st.subheader("⏬ Banco de Suplentes (Máx 25)")
if st.session_state.suplentes:
    df_sup = pd.DataFrame(st.session_state.suplentes)
    df_sup['Estrellas'] = df_sup['Nivel'].apply(lambda x: "⭐" * int(x))
    st.dataframe(df_sup[['Jugador', 'POS', 'Estrellas', 'Equipo']], use_container_width=True)

    col_acc1, col_acc2 = st.columns(2)
    
    # Subir a Titular
    with col_acc1:
        st.write("**Gestión Táctica**")
        elegido = st.selectbox("Elegir jugador para el 11:", [j['Jugador'] for j in st.session_state.suplentes], key="up_sup")
        if st.button("Poner de Titular ⬆️"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == elegido)
            jugador = st.session_state.suplentes[idx]
            
            # Validación de formación 1-4-4-2
            conteo = [p['POS'] for p in st.session_state.titulares].count(jugador['POS'])
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            
            if conteo < limites.get(jugador['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
            else:
                st.error(f"Posición {jugador['POS']} completa. Manda a alguien al banco primero.")

    # Vender Jugador
    with col_acc2:
        st.write("**Mercado de Venta**")
        vender = st.selectbox("Elegir jugador para vender:", [j['Jugador'] for j in st.session_state.suplentes], key="sell_sup")
        if st.button("VENDER JUGADOR 💰"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender)
            jugador = st.session_state.suplentes[idx]
            ganancia = int(jugador['Nivel']) * 20
            st.session_state.creditos += ganancia
            st.session_state.suplentes.pop(idx)
            st.success(f"Vendido: {jugador['Jugador']} (+{ganancia}c)")
            st.rerun()
else:
    st.info("El banco está vacío. Compra packs para obtener jugadores.")

# Historial de Movimientos
st.divider()
with st.expander("📜 Historial de Movimientos"):
    for item in st.session_state.historial:
        st.write(f"- {item}")
