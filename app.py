import streamlit as st
import pandas as pd
import random

# Configuración de página
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# 1. Carga de datos
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

# 2. Inicialización del Estado (Presupuesto: 1000)
if 'creditos' not in st.session_state:
    st.session_state.creditos = 1000
if 'titulares' not in st.session_state:
    st.session_state.titulares = []
if 'suplentes' not in st.session_state:
    st.session_state.suplentes = []
if 'historial' not in st.session_state:
    st.session_state.historial = []

# Función para ordenar titulares por jerarquía de posición
def ordenar_titulares():
    if not st.session_state.titulares:
        return
    # Definimos el orden lógico del fútbol
    orden_pos = {'ARQ': 0, 'DEF': 1, 'VOL': 2, 'DEL': 3}
    st.session_state.titulares.sort(key=lambda x: orden_pos.get(x['POS'], 99))

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("👤 PANEL DE CONTROL")
    st.metric("Presupuesto", f"{st.session_state.creditos} c")
    
    st.divider()
    
    # RULETA INSTANTÁNEA
    st.subheader("🎡 Ruleta de Créditos")
    if st.button("OBTENER RESULTADO 🎲"):
        res = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
        st.session_state.creditos += res
        st.session_state.historial.insert(0, f"Ruleta: {res}c")
        if res > 0: st.success(f"Resultado: +{res}")
        elif res < 0: st.error(f"Resultado: -{abs(res)}")
        else: st.info("Resultado: 0")

    st.divider()
    
    # COMPRA
    if st.button("🛒 COMPRAR PACK (100c)"):
        if st.session_state.creditos >= 100:
            if len(st.session_state.suplentes) < 25:
                st.session_state.creditos -= 100
                nuevos = df_base.sample(n=2).to_dict('records')
                st.session_state.suplentes.extend(nuevos)
                st.session_state.historial.insert(0, f"Fichaje: {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}")
                st.toast("¡Nuevos jugadores en el banco!")
            else:
                st.warning("Banco lleno")
        else:
            st.error("Créditos insuficientes")

# --- PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Sección 1: Titulares ORDENADOS
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    ordenar_titulares() # Llamamos al ordenamiento antes de mostrar
    df_tit = pd.DataFrame(st.session_state.titulares)
    df_tit['Nivel'] = df_tit['Nivel'].apply(lambda x: "⭐" * int(x))
    # Mostramos la tabla limpia
    st.table(df_tit[['POS', 'Jugador', 'Equipo', 'Nivel', 'Score']])
    
    # Dropdown para sacar al banco
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares])
    if st.button("Confirmar salida ⬇️"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()
else:
    st.info("El 11 titular está vacío.")

st.divider()

# Sección 2: Suplentes
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_sup = pd.DataFrame(st.session_state.suplentes)
    df_sup['Estrellas'] = df_sup['Nivel'].apply(lambda x: "⭐" * int(x))
    st.dataframe(df_sup[['Jugador', 'POS', 'Estrellas', 'Equipo']], use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Subir al 11**")
        elegido = st.selectbox("Elegir jugador:", [j['Jugador'] for j in st.session_state.suplentes], key="up")
        if st.button("Poner de Titular ⬆️"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == elegido)
            j = st.session_state.suplentes[idx]
            
            # Lógica 1-4-4-2
            conteo = [p['POS'] for p in st.session_state.titulares].count(j['POS'])
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            
            if conteo < limites.get(j['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                ordenar_titulares() # Ordenar inmediatamente
                st.rerun()
            else:
                st.error(f"Ya tienes suficientes jugadores en {j['POS']}.")

    with c2:
        st.write("**Venta Directa**")
        v_juego = st.selectbox("Elegir para vender:", [j['Jugador'] for j in st.session_state.suplentes], key="sell")
        if st.button("VENDER 💰"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == v_juego)
            j_v = st.session_state.suplentes[idx]
            pago = int(j_v['Nivel']) * 20
            st.session_state.creditos += pago
            st.session_state.suplentes.pop(idx)
            st.rerun()
else:
    st.info("No tienes suplentes.")

with st.expander("📜 Historial"):
    for h in st.session_state.historial:
        st.write(h)
