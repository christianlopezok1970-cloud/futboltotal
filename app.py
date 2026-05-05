import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURACIÓN ---
DB_NAME = "liga_master_v3.db"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()

# Inicialización de Tablas
ejecutar_db("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, password TEXT, presupuesto REAL DEFAULT 25000000)", commit=True)
ejecutar_db("""CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                usuario_id INTEGER, 
                nombre_jugador TEXT UNIQUE, 
                posicion TEXT, equipo TEXT, 
                precio REAL, estado TEXT DEFAULT 'Suplente', 
                puntos_jornada INTEGER DEFAULT 0)""", commit=True)

@st.cache_data(ttl=60)
def obtener_mercado():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        # Limpieza de Cotización: quita todo lo que no sea número
        df['PrecioNum'] = pd.to_numeric(df['Cotización'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# --- LOGIN ---
st.set_page_config(page_title="Liga Master Pro", layout="wide")

if 'user' not in st.session_state:
    st.title("⚽ Liga Master")
    u_nom = st.text_input("Usuario").strip()
    u_pass = st.text_input("Contraseña", type="password").strip()
    if st.button("Entrar / Registrarse"):
        res = ejecutar_db("SELECT id FROM usuarios WHERE nombre = ? AND password = ?", (u_nom, u_pass))
        if res:
            st.session_state.user = {"id": res[0][0], "nombre": u_nom}
            st.rerun()
        else:
            try:
                ejecutar_db("INSERT INTO usuarios (nombre, password) VALUES (?,?)", (u_nom, u_pass), commit=True)
                st.success("Cuenta creada. ¡Haz clic en Entrar!")
            except: st.error("Usuario ya existe o datos incorrectos.")
    st.stop()

# --- VALIDACIÓN DE USUARIO (EVITA EL INDEXERROR) ---
res_u = ejecutar_db("SELECT presupuesto FROM usuarios WHERE id = ?", (st.session_state.user["id"],))
if not res_u:
    st.session_state.clear()
    st.rerun()

presupuesto_actual = res_u[0][0]
u_id = st.session_state.user["id"]

# --- INTERFAZ ---
with st.sidebar:
    st.header(f"🎮 {st.session_state.user['nombre']}")
    st.metric("Presupuesto", f"€ {presupuesto_actual:,.0f}")
    if st.button("Salir"):
        st.session_state.clear()
        st.rerun()

t1, t2, t3 = st.tabs(["🛒 MERCADO", "🏃 MI EQUIPO", "🏆 RANKING"])

with t1:
    df_m = obtener_mercado()
    comprados = [j[0] for j in ejecutar_db("SELECT nombre_jugador FROM plantillas")]
    df_disp = df_m[~df_m['Nombre'].isin(comprados)]
    
    busqueda = st.selectbox("Fichar Jugador", [""] + df_disp['Nombre'].tolist())
    if busqueda:
        f = df_disp[df_disp['Nombre'] == busqueda].iloc[0]
        st.write(f"**Costo:** € {f['PrecioNum']:,.0f}")
        if st.button("Confirmar Compra"):
            if presupuesto_actual >= f['PrecioNum']:
                try:
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (f['PrecioNum'], u_id), commit=True)
                    ejecutar_db("INSERT INTO plantillas (usuario_id, nombre_jugador, posicion, equipo, precio) VALUES (?,?,?,?,?)",
                                (u_id, f['Nombre'], f['POS'], f['Equipo'], f['PrecioNum']), commit=True)
                    st.success("¡Fichado!")
                    st.rerun()
                except: st.error("Error: Quizás otro usuario lo compró antes.")
            else: st.error("No tienes suficiente dinero.")

with t2:
    mis_j = ejecutar_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.subheader("Tu Plantilla")
        for j_id, nom, pos, est, precio in mis_j:
            with st.expander(f"{nom} ({pos})"):
                if st.button("Titular/Suplente", key=f"btn_{j_id}"):
                    nuevo = "Titular" if est == "Suplente" else "Suplente"
                    ejecutar_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
                    st.rerun()
                if st.button("Vender 🗑️", key=f"vend_{j_id}"):
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
                    ejecutar_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
                    st.rerun()

    with col2:
        st.subheader("Cancha 1-4-4-2")
        titulares = [j for j in mis_j if j[3] == "Titular"]
        # Mostrar nombres por líneas
        st.info("⚽ DEL: " + ", ".join([j[1] for j in titulares if "DEL" in j[2] or "ATA" in j[2]]))
        st.info("🏃 MED: " + ", ".join([j[1] for j in titulares if "MED" in j[2] or "VOL" in j[2]]))
        st.info("🛡️ DEF: " + ", ".join([j[1] for j in titulares if "DEF" in j[2] or "DFC" in j[2]]))
        st.info("🧤 ARQ: " + ", ".join([j[1] for j in titulares if "ARQ" in j[2] or "POR" in j[2]]))

with t3:
    st.subheader("Ranking de la Jornada")
    if st.checkbox("Admin: Cerrar Jornada"):
        premio = st.number_input("Premio al Ganador", value=5000000)
        if st.button("Asignar Puntos y Pagar"):
            ejecutar_db("UPDATE plantillas SET puntos_jornada = ABS(RANDOM() % 12)", commit=True)
            ganador = ejecutar_db("SELECT usuario_id FROM plantillas GROUP BY usuario_id ORDER BY SUM(puntos_jornada) DESC LIMIT 1")
            if ganador:
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (premio, ganador[0][0]), commit=True)
                st.success("¡Premio entregado!")
                st.rerun()
    
    tabla = ejecutar_db("SELECT u.nombre, SUM(p.puntos_jornada) FROM usuarios u LEFT JOIN plantillas p ON u.id = p.usuario_id GROUP BY u.id ORDER BY 2 DESC")
    st.table(pd.DataFrame(tabla, columns=["Usuario", "Puntos"]))
