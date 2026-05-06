import streamlit as st
import pandas as pd
import random
import os
import json

# --- 1. CONFIGURACIÓN Y PERSISTENCIA ---
st.set_page_config(page_title="AFA Manager 2026", layout="wide")

# Nombre del archivo donde se guardarán los usuarios de forma permanente
DB_FILE = "usuarios_db.json"

def cargar_usuarios():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f:
            return json.load(f)
    return {"admin": "1234"} # Usuario por defecto

def guardar_usuario(user, password):
    usuarios = cargar_usuarios()
    usuarios[user] = password
    with open(DB_FILE, "w") as f:
        json.dump(usuarios, f)

# --- 2. LOGIN / REGISTRO AUTOMÁTICO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

if not st.session_state.autenticado:
    with st.sidebar:
        st.title("🛡️ ACCESO / REGISTRO")
        st.info("Si es tu primera vez, elige usuario y clave para registrarte.")
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
                    else:
                        st.error("Contraseña incorrecta.")
                else:
                    # REGISTRO AUTOMÁTICO
                    guardar_usuario(u, p)
                    st.session_state.autenticado = True
                    st.session_state.usuario = u
                    st.success("¡Usuario registrado!")
                    st.rerun()
            else:
                st.warning("Escribe algo en ambos campos.")
    st.stop()

# --- 3. CARGA DE JUGADORES (Desde tu Google Sheets) ---
@st.cache_data
def load_data():
    url = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
    df = pd.read_csv(url)
    df.columns = [c.strip() for c in df.columns]
    return df

df_base = load_data()

# --- 4. ESTADO DEL JUEGO ---
if 'creditos' not in st.session_state: st.session_state.creditos = 1000
if 'titulares' not in st.session_state: st.session_state.titulares = []
if 'suplentes' not in st.session_state: st.session_state.suplentes = []
if 'historial' not in st.session_state: st.session_state.historial = []

def formato_nivel(n):
    n = int(n)
    if n == 5: return "🟡 5★ ORO"
    elif n == 4: return "⚪ 4★ PLATA"
    elif n == 3: return "🟤 3★ BRONCE"
    elif n == 2: return "⚪ 2★ BLANCO"
    elif n == 1: return "🔘 1★ GRIS"
    return f"{n}★"

# --- 5. INTERFAZ ---
with st.sidebar:
    st.write(f"🎮 **Manager:** {st.session_state.usuario}")
    st.metric("Presupuesto", f"{st.session_state.creditos} c")
    
    if st.button("Cerrar Sesión"):
        st.session_state.autenticado = False
        st.rerun()

    st.divider()
    if st.button("GIRAR RULETA 🎲"):
        res = random.choices([0, 1, -1, 3], weights=[0.50, 0.25, 0.20, 0.05])[0]
        st.session_state.creditos += res
        st.session_state.historial.insert(0, f"Ruleta: {res}c")
        st.rerun()

    if st.button("COMPRAR PACK (100c)"):
        if st.session_state.creditos >= 100:
            st.session_state.creditos -= 100
            nuevos = df_base.sample(n=2).to_dict('records')
            st.session_state.suplentes.extend(nuevos)
            st.rerun()

st.title("⚽ AFA Manager Pro 2026")

# Render de tablas (Titulares y Suplentes) - [Igual que el código anterior]
# ... [Aquí va el resto del código de tablas que ya teníamos] ...
