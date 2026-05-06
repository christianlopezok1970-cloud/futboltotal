import streamlit as st
import pandas as pd
import random
import os
import json

# --- 1. CONFIGURACIÓN ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")
DB_FILE = "usuarios_db.json"

def cargar_usuarios():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f: return json.load(f)
        except: return {"admin": "1234"}
    return {"admin": "1234"}

def guardar_usuario(user, password):
    usuarios = cargar_usuarios()
    usuarios[user] = password
    with open(DB_FILE, "w") as f: json.dump(usuarios, f)

# --- 2. LOGIN ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False
if 'ultimo_giro' not in st.session_state:
    st.session_state.ultimo_giro = None

if not st.session_state.autenticado:
    with st.sidebar:
        st.title("🛡️ ACCESO / REGISTRO")
        u = st.text_input("Usuario")
        p = st.text_input("Contraseña", type="password")
        if st.button("Ingresar / Crear Cuenta"):
            if u and p:
                usuarios = cargar_usuarios()
                if u in usuarios:
                    if usuarios[u] == p:
                        st.session_state.autenticado = True
                        st.session_state.usuario = u
                        st.rerun()
                    else: st.error("Contraseña incorrecta.")
                else:
                    guardar_usuario(u, p)
                    st.session_state.autenticado = True
                    st.session_state.usuario = u
                    st.rerun()
    st.stop()

# --- 3. DATOS ---
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    try:
        df = pd.read_csv(url)
        df.columns = [c.strip() for c in df.columns]
        return df
    except: return pd.DataFrame(columns=["Jugador", "POS", "Nivel", "Equipo", "Score"])

df_base = load_data()

if 'creditos' not in st.session_state: st.session_state.creditos = 1000
if 'titulares' not in st.session_state: st.session_state.titulares = []
if 'suplentes' not in st.session_state: st.session_state.suplentes = []
if 'historial' not in st.session_state: st.session_state.historial = []

# --- 4. TU FUNCIÓN DE NIVELES PERSONALIZADA ---
def formato_nivel(n):
    try: 
        n = int(n)
    except: 
        return f"{n}★"
    
    # Combinamos tu arreglo de estrellas con los colores pedidos
    if n == 5: return "🟡 ★★★★★ (ORO)"
    if n == 4: return "⚪ ★★★★ (PLATA)"
    if n == 3: return "🟤 ★★★ (BRONCE)"
    if n == 2: return "⚪ ★★ (BLANCO)"
    if n == 1: return "🔘 ★ (GRIS)"
    return f"{n}★"

def ordenar_titulares():
    orden = {'ARQ': 0, 'DEF': 1, 'VOL': 2, 'DEL': 3}
    st.session_state.titulares.sort(key=lambda x: orden.get(x['POS'], 99))

# --- 5. SIDEBAR (CON RESULTADOS VISIBLES) ---
with st.sidebar:
    st.write(f"🎮 **Manager:** {st.session_state.usuario}")
    st.metric("Presupuesto", f"{st.session_state.creditos} c")
    
    st.divider()
    st.subheader("🎡 Ruleta de Créditos")
    
    if st.session_state.ultimo_giro is not None:
        res = st.session_state.ultimo_giro
        if res > 0: st.success(f"¡Último giro: +{res}c! 🤑")
        elif res < 0: st.error(f"¡Último giro: {res}c! 💸")
        else: st.info("¡Último giro: 0c! 😐")

    if st.button("GIRAR RULETA 🎲"):
        resultado = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
        st.session_state.creditos += resultado
        st.session_state.ultimo_giro = resultado
        st.session_state.historial.insert(0, f"Ruleta: {resultado}c")
        st.rerun()

    st.divider()
    if st.button("🛒 COMPRAR PACK (100c)"):
        if st.session_state.creditos >= 100 and len(st.session_state.suplentes) < 25:
            st.session_state.creditos -= 100
            st.session_state.ultimo_giro = None
            nuevos = df_base.sample(n=2).to_dict('records')
            st.session_state.suplentes.extend(nuevos)
            st.session_state.historial.insert(0, f"Pack: {nuevos[0]['Jugador']} y {nuevos[1]['Jugador']}")
            st.rerun()
        elif st.session_state.creditos < 100: st.error("Sin créditos")

# --- 6. CUERPO PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Titulares
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    ordenar_titulares()
    df_t = pd.DataFrame(st.session_state.titulares)
    df_t['Rareza'] = df_t['Nivel'].apply(formato_nivel)
    st.table(df_t[['POS', 'Jugador', 'Equipo', 'Rareza', 'Score']])
    
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares])
    if st.button("Bajar al banco ⬇️"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()
else: st.info("Armá tu equipo con los suplentes.")

st.divider()

# Suplentes
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    df_s['Rareza'] = df_s['Nivel'].apply(formato_nivel)
    st.dataframe(df_s[['Jugador', 'POS', 'Rareza', 'Equipo']], use_container_width=True, hide_index=True)

    c1, c2 = st.columns(2)
    with c1:
        st.write("**Táctica**")
        subir = st.selectbox("Poner de Titular:", [j['Jugador'] for j in st.session_state.suplentes])
        if st.button("Subir al 11 ⬆️"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == subir)
            j = st.session_state.suplentes[idx]
            conteo = [p['POS'] for p in st.session_state.titulares].count(j['POS'])
            limites = {'ARQ': 1, 'DEF': 4, 'VOL': 4, 'DEL': 2}
            if conteo < limites.get(j['POS'], 0):
                st.session_state.titulares.append(st.session_state.suplentes.pop(idx))
                st.rerun()
            else: st.error(f"Posición {j['POS']} llena.")

    with c2:
        st.write("**Mercado**")
        vender = st.selectbox("Vender jugador:", [j['Jugador'] for j in st.session_state.suplentes], key="v")
        if st.button("VENDER 💰"):
            idx = next(i for i, j in enumerate(st.session_state.suplentes) if j['Jugador'] == vender)
            pago = int(st.session_state.suplentes[idx]['Nivel']) * 20
            st.session_state.creditos += pago
            st.session_state.suplentes.pop(idx)
            st.rerun()

with st.expander("📜 Historial"):
    for h in st.session_state.historial[:10]: st.write(f"- {h}")
