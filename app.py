import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURACIÓN Y BASES DE DATOS ---
DB_NAME = "liga_master_v3.db"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()

# Inicialización limpia
ejecutar_db("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, password TEXT, presupuesto REAL DEFAULT 25000000)", commit=True)
ejecutar_db("""CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                usuario_id INTEGER, 
                nombre_jugador TEXT UNIQUE, 
                posicion TEXT, equipo TEXT, 
                precio REAL, estado TEXT DEFAULT 'Suplente', 
                puntos_jornada INTEGER DEFAULT 0)""", commit=True)

# --- CARGA DE DATOS ---
@st.cache_data(ttl=60)
def obtener_mercado():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        
        # Limpieza de Cotización (Columna 4)
        df['PrecioNum'] = (df['Cotización'].astype(str)
                           .str.replace(r'[^\d]', '', regex=True))
        df['PrecioNum'] = pd.to_numeric(df['PrecioNum'], errors='coerce').fillna(0)
        
        # Asegurar tipos de datos para evitar errores de comparación
        df['Nombre'] = df['Nombre'].astype(str).str.strip()
        df['POS'] = df['POS'].astype(str).str.upper().str.strip()
        df['Equipo'] = df['Equipo'].astype(str).str.strip()
        return df
    except Exception as e:
        st.error(f"Error en Excel: {e}")
        return pd.DataFrame()

# --- AUTENTICACIÓN ---
st.set_page_config(page_title="Liga Master Pro", layout="wide")

if 'user' not in st.session_state:
    st.title("⚽ Liga Master: Acceso")
    u_nom = st.text_input("Usuario").strip()
    u_pass = st.text_input("Contraseña", type="password").strip()
    if st.button("Entrar / Registrarse"):
        res = ejecutar_db("SELECT id, presupuesto FROM usuarios WHERE nombre = ? AND password = ?", (u_nom, u_pass))
        if res:
            st.session_state.user = {"id": res[0][0], "nombre": u_nom}
            st.rerun()
        else:
            try:
                ejecutar_db("INSERT INTO usuarios (nombre, password) VALUES (?,?)", (u_nom, u_pass), commit=True)
                st.success("Cuenta creada. ¡Presiona entrar!")
            except: st.error("Error de login")
    st.stop()

u_id = st.session_state.user["id"]
u_info = ejecutar_db("SELECT presupuesto FROM usuarios WHERE id = ?", (u_id,))[0]
presupuesto_actual = u_info[0]

# --- INTERFAZ PRINCIPAL ---
with st.sidebar:
    st.header(f"🎮 {st.session_state.user['nombre']}")
    st.metric("Tu Presupuesto", f"€ {presupuesto_actual:,.0f}")
    if st.button("Log Out"):
        del st.session_state.user
        st.rerun()

t1, t2, t3 = st.tabs(["🛒 MERCADO", "🏃 MI EQUIPO", "🏆 RANKING"])

# --- TAB 1: MERCADO ---
with t1:
    st.subheader("Fichajes Disponibles")
    df_m = obtener_mercado()
    comprados = [j[0] for j in ejecutar_db("SELECT nombre_jugador FROM plantillas")]
    df_disp = df_m[~df_m['Nombre'].isin(comprados)]

    # Buscador amigable
    busqueda = st.selectbox("Buscar Jugador", [""] + df_disp['Nombre'].tolist())
    if busqueda:
        f = df_disp[df_disp['Nombre'] == busqueda].iloc[0]
        st.info(f"**{f['Nombre']}** | {f['Equipo']} | {f['POS']} | **Costo: € {f['PrecioNum']:,.0f}**")
        
        if st.button("CONFIRMAR COMPRA"):
            if presupuesto_actual >= f['PrecioNum']:
                try:
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (f['PrecioNum'], u_id), commit=True)
                    ejecutar_db("INSERT INTO plantillas (usuario_id, nombre_jugador, posicion, equipo, precio) VALUES (?,?,?,?,?)",
                                (u_id, f['Nombre'], f['POS'], f['Equipo'], f['PrecioNum']), commit=True)
                    st.success("¡Fichaje realizado!")
                    st.rerun()
                except: st.error("Este jugador acaba de ser comprado por otro usuario.")
            else:
                st.error("Fondos insuficientes.")

# --- TAB 2: MI EQUIPO & CANCHA ---
with t2:
    mis_jugadores = ejecutar_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
    
    col_lista, col_cancha = st.columns([1, 1])

    with col_lista:
        st.write("### Gestión de Plantilla")
        for j_id, nom, pos, est, precio in mis_jugadores:
            with st.expander(f"{nom} ({pos}) - {est}"):
                c1, c2 = st.columns(2)
                if c1.button("Cambiar Rol", key=f"rol_{j_id}"):
                    nuevo = "Titular" if est == "Suplente" else "Suplente"
                    ejecutar_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
                    st.rerun()
                if c2.button("Vender (Reembolso)", key=f"vend_{j_id}"):
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
                    ejecutar_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
                    st.rerun()

    with col_cancha:
        st.write("### Táctica 1-4-4-2")
        titulares = [j for j in mis_jugadores if j[3] == "Titular"]
        
        def filtrar(p_list):
            return [j[1] for j in titulares if any(x in j[2] for x in p_list)]

        arq = filtrar(["ARQ", "POR", "GK"])
        defensas = filtrar(["DEF", "DFC", "LAT", "LI", "LD"])
        medios = filtrar(["MED", "VOL", "MC", "MCO", "MCD"])
        delanteros = filtrar(["DEL", "ATA", "DC", "EXT"])

        # Visualización de cancha sencilla
        st.markdown("""<style>.campo { background:#1b5e20; padding:15px; border-radius:10px; border:2px solid white; text-align:center; color:white; }</style>""", unsafe_allow_html=True)
        st.markdown(f"""<div class='campo'>
            <p>⚽ DEL: {', '.join(delanteros[:2])}</p><hr>
            <p>🏃 MED: {', '.join(medios[:4])}</p><hr>
            <p>🛡️ DEF: {', '.join(defensas[:4])}</p><hr>
            <p>🧤 ARQ: {', '.join(arq[:1])}</p>
        </div>""", unsafe_allow_html=True)

# --- TAB 3: PUNTUACIÓN Y PREMIOS ---
with t3:
    st.write("### Resultados de la Jornada")
    
    if st.checkbox("⚙️ Modo Administrador (Cerrar Jornada)"):
        premio_x = st.number_input("Monto del Premio (en €)", value=2000000)
        if st.button("Finalizar Jornada y Entregar Premio"):
            # 1. Asignar puntos aleatorios (simulando los del Excel)
            ejecutar_db("UPDATE plantillas SET puntos_jornada = ABS(RANDOM() % 15)", commit=True)
            
            # 2. Buscar al ganador
            ganador = ejecutar_db("""SELECT usuario_id, SUM(puntos_jornada) as total 
                                   FROM plantillas GROUP BY usuario_id 
                                   ORDER BY total DESC LIMIT 1""")
            if ganador:
                g_id, g_pts = ganador[0]
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (premio_x, g_id), commit=True)
                st.balloons()
                st.success(f"¡Jornada Cerrada! El ganador sumó {g_pts} puntos y ganó €{premio_x:,.0f}")
                st.rerun()

    # Tabla de posiciones
    tabla = ejecutar_db("""SELECT u.nombre, SUM(p.puntos_jornada) as total_pts 
                         FROM usuarios u LEFT JOIN plantillas p ON u.id = p.usuario_id 
                         GROUP BY u.id ORDER BY total_pts DESC""")
    st.table(pd.DataFrame(tabla, columns=["Usuario", "Puntos de Jornada"]))
