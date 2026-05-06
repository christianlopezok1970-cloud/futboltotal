import streamlit as st
import pandas as pd
import random

# Configuración de página
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# 1. Carga de datos (con cache para que sea rápido)
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    return df

df_base = load_data()

# 2. Inicialización del Estado (Session State)
if 'creditos' not in st.session_state:
    st.session_state.creditos = 0
if 'titulares' not in st.session_state:
    st.session_state.titulares = []
if 'suplentes' not in st.session_state:
    st.session_state.suplentes = []
if 'historial' not in st.session_state:
    st.session_state.historial = []

# --- PANEL LATERAL ---
with st.sidebar:
    st.title("👤 MANAGER_01")
    st.metric("Créditos", f"{st.session_state.creditos} c")
    
    st.divider()
    
    # RULETA
    st.subheader("🎡 Ruleta Infinita")
    if st.button("GIRAR RULETA"):
        res = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
        st.session_state.creditos += res
        st.session_state.historial.insert(0, f"Ruleta: {res}c")
        if res > 0: st.success(f"¡Ganaste {res}c!")
        elif res < 0: st.error(f"Perdiste {res}c")
        else: st.info("Salió 0")

    st.divider()
    
    # COMPRA
    if st.button("🛒 COMPRAR PACK (100c)"):
        if st.session_state.creditos >= 100:
            if len(st.session_state.suplentes) < 25:
                st.session_state.creditos -= 100
                nuevos = df_base.sample(n=2).to_dict('records')
                st.session_state.suplentes.extend(nuevos)
                st.session_state.historial.insert(0, f"Compra: {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}")
                st.balloons()
            else:
                st.warning("Banco lleno (Máx 25)")
        else:
            st.error("Créditos insuficientes")

# --- PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Sección Titulares
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    df_tit = pd.DataFrame(st.session_state.titulares)
    # Mostramos estrellas visuales
    df_tit['Nivel'] = df_tit['Nivel'].apply(lambda x: "⭐" * int(x))
    st.table(df_tit[['Jugador', 'POS', 'Nivel', 'Equipo', 'Score']])
    
    col_t1, col_t2 = st.columns([1, 4])
    with col_t1:
        quitar = st.selectbox("Mandar al banco a:", [j['Jugador'] for j in st.session_state.titulares], key="drop_tit")
        if st.button("Confirmar cambio ⬇️"):
            idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
            st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
            st.rerun()
else:
    st.info("No hay titulares definidos. Selecciona jugadores del banco.")

st.divider()

# Sección Suplentes
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_sup = pd.DataFrame(st.session_state.suplentes)
    df_sup['Stars'] = df_sup['Nivel'].apply(lambda x: "⭐" * int(x))
    st.dataframe(df_sup[['Jugador', 'POS', 'Stars', 'Equipo']], use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        elegido = st.selectbox("Subir a titular:", [j['Jugador'] for j in st.session_state.suplentes], key="up_sup")
        if st.button("Poner de Titular ⬆️"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == elegido)
            jugador = st.session_state.suplentes[idx]
            
            # Validar 1-4-4-2
            conteo = [p['POS'] for p in st.session_state.titulares].count(jugador['POS'])
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            
            if conteo < limites.get(jugador['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
            else:
                st.error(f"Límite de {jugador['POS']} alcanzado.")

    with c2:
        vender = st.selectbox("Vender por créditos:", [j['Jugador'] for j in st.session_state.suplentes], key="sell_sup")
        if st.button("VENDER JUGADOR 💰"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender)
            jugador = st.session_state.suplentes[idx]
            valor = jugador['Nivel'] * 20
            st.session_state.creditos += valor
            st.session_state.suplentes.pop(idx)
            st.success(f"Vendido {jugador['Jugador']} por {valor}c")
            st.rerun()

# Historial al final
with st.expander("📜 Historial de movimientos"):
    for h in st.session_state.historial:
        st.write(h)
