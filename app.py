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

# --- FUNCIONES ---

def ordenar_titulares():
    orden_pos = {'ARQ': 0, 'DEF': 1, 'VOL': 2, 'DEL': 3}
    st.session_state.titulares.sort(key=lambda x: orden_pos.get(x['POS'], 99))

def formato_nivel(n):
    # Formato uniforme: Número + Estrella
    n = int(n)
    if n == 5: return "5★ (ORO)"
    if n == 4: return "4★ (PLATA)"
    if n == 3: return "3★ (BRONCE)"
    return f"{n}★"

# --- PANEL LATERAL ---
with st.sidebar:
    st.header("👤 PANEL DE CONTROL")
    st.metric("Presupuesto", f"{st.session_state.creditos} c")
    
    st.divider()
    
    st.subheader("🎡 Ruleta Instantánea")
    if st.button("GIRAR RULETA 🎲"):
        res = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
        st.session_state.creditos += res
        st.session_state.historial.insert(0, f"Ruleta: {res}c")
        if res > 0: st.success(f"+{res} créditos")
        elif res < 0: st.error(f"{res} crédito")
        else: st.info("0 créditos")

    st.divider()
    
    if st.button("🛒 COMPRAR PACK (100c)"):
        if st.session_state.creditos >= 100:
            if len(st.session_state.suplentes) <= 23:
                st.session_state.creditos -= 100
                nuevos = df_base.sample(n=2).to_dict('records')
                st.session_state.suplentes.extend(nuevos)
                st.session_state.historial.insert(0, f"Pack: {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}")
                st.toast("¡Fichajes realizados!")
            else: st.warning("Banco lleno")
        else: st.error("Créditos insuficientes")

# --- PANEL PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Listado Superior: Titulares
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    ordenar_titulares()
    df_tit = pd.DataFrame(st.session_state.titulares)
    df_tit['Nivel'] = df_tit['Nivel'].apply(formato_nivel)
    st.table(df_tit[['POS', 'Jugador', 'Equipo', 'Nivel', 'Score']])
    
    quitar = st.selectbox("Quitar titular:", [j['Jugador'] for j in st.session_state.titulares])
    if st.button("Mandar al banco ⬇️"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()
else:
    st.info("Sin titulares.")

st.divider()

# Listado Inferior: Suplentes
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_sup = pd.DataFrame(st.session_state.suplentes)
    df_sup['Nivel_V'] = df_sup['Nivel'].apply(formato_nivel)
    st.dataframe(df_sup[['Jugador', 'POS', 'Nivel_V', 'Equipo']], use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        subir = st.selectbox("Subir al Once:", [j['Jugador'] for j in st.session_state.suplentes], key="s1")
        if st.button("Confirmar Titular ⬆️"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == subir)
            j = st.session_state.suplentes[idx]
            conteo = [p['POS'] for p in st.session_state.titulares].count(j['POS'])
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            if conteo < limites.get(j['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
            else: st.error(f"Límite de {j['POS']} alcanzado")

    with c2:
        vender = st.selectbox("Vender jugador:", [j['Jugador'] for j in st.session_state.suplentes], key="s2")
        if st.button("CONFIRMAR VENTA 💰"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender)
            pago = int(st.session_state.suplentes[idx]['Nivel']) * 20
            st.session_state.creditos += pago
            st.session_state.suplentes.pop(idx)
            st.rerun()

with st.expander("📜 Historial"):
    for h in st.session_state.historial: st.write(f"- {h}")
