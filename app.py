import streamlit as st
import sqlite3
import pandas as pd

# --- 1. CONFIGURACIÓN E INFRAESTRUCTURA ---
DB_NAME = "liga_master_final.db"
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()

# Inicialización de tablas
ejecutar_db("CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY AUTOINCREMENT, nombre TEXT UNIQUE, password TEXT, presupuesto REAL DEFAULT 25000000)", commit=True)
ejecutar_db("""CREATE TABLE IF NOT EXISTS plantillas (
                id INTEGER PRIMARY KEY AUTOINCREMENT, 
                usuario_id INTEGER, 
                nombre_jugador TEXT UNIQUE, 
                posicion TEXT, equipo TEXT, 
                precio REAL, estado TEXT DEFAULT 'Suplente', 
                puntos_jornada INTEGER DEFAULT 0)""", commit=True)

@st.cache_data(ttl=60)
def cargar_mercado():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        # Limpieza de Cotización (Columna 4)
        df['PrecioNum'] = pd.to_numeric(df['Cotización'].astype(str).str.replace(r'[^\d]', '', regex=True), errors='coerce').fillna(0)
        return df
    except:
        return pd.DataFrame()

# --- 2. AUTENTICACIÓN ---
st.set_page_config(page_title="Liga Master Directo", layout="wide")

if 'user' not in st.session_state:
    st.title("⚽ Liga Master: Iniciar Sesión")
    u_nom = st.text_input("Usuario")
    u_pass = st.text_input("Contraseña", type="password")
    if st.button("Ingresar / Registrarse"):
        res = ejecutar_db("SELECT id FROM usuarios WHERE nombre = ? AND password = ?", (u_nom, u_pass))
        if res:
            st.session_state.user = {"id": res[0][0], "nombre": u_nom}
            st.rerun()
        else:
            try:
                ejecutar_db("INSERT INTO usuarios (nombre, password) VALUES (?,?)", (u_nom, u_pass), commit=True)
                st.success("Usuario creado con éxito. Haz clic en Ingresar.")
            except: st.error("Error: El usuario ya existe o la clave es incorrecta.")
    st.stop()

# --- 3. ESTADO DEL JUEGO ---
u_id = st.session_state.user["id"]
res_u = ejecutar_db("SELECT presupuesto FROM usuarios WHERE id = ?", (u_id,))
if not res_u:
    st.session_state.clear()
    st.rerun()
presupuesto_actual = res_u[0][0]

# --- 4. CABECERA Y MERCADO ---
st.title(f"🏆 Club: {st.session_state.user['nombre']}")
st.sidebar.metric("💰 Presupuesto", f"€ {presupuesto_actual:,.0f}")
if st.sidebar.button("Cerrar Sesión"):
    st.session_state.clear()
    st.rerun()

st.header("🛒 Mercado de Fichajes")
df_m = cargar_mercado()
comprados = [j[0] for j in ejecutar_db("SELECT nombre_jugador FROM plantillas")]
df_disp = df_m[~df_m['Nombre'].isin(comprados)]

with st.expander("Abrir Mercado de Jugadores"):
    sel = st.selectbox("Elegir jugador para comprar", [""] + df_disp['Nombre'].tolist())
    if sel:
        f = df_disp[df_disp['Nombre'] == sel].iloc[0]
        st.write(f"**{f['Nombre']}** ({f['POS']}) - Costo: **€ {f['PrecioNum']:,.0f}**")
        if st.button("Confirmar Fichaje"):
            if presupuesto_actual >= f['PrecioNum']:
                try:
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (f['PrecioNum'], u_id), commit=True)
                    ejecutar_db("INSERT INTO plantillas (usuario_id, nombre_jugador, posicion, equipo, precio) VALUES (?,?,?,?,?)",
                                (u_id, f['Nombre'], f['POS'], f['Equipo'], f['PrecioNum']), commit=True)
                    st.success(f"¡{f['Nombre']} fichado!")
                    st.rerun()
                except: st.error("Error: Jugador no disponible.")
            else: st.error("No tienes suficiente presupuesto.")

st.divider()

# --- 5. CANCHA VISUAL (1-4-4-2) ---
st.header("🏟️ Tu Alineación Titular")

mis_j = ejecutar_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
titulares = [j for j in mis_j if j[3] == "Titular"]

# Lógica de dibujo de cancha con CSS
st.markdown("""
<style>
    .campo {
        background: #2e7d32;
        border: 4px solid white;
        border-radius: 20px;
        padding: 40px 10px;
        text-align: center;
        color: white;
        box-shadow: inset 0px 0px 50px rgba(0,0,0,0.5);
    }
    .linea { display: flex; justify-content: space-around; margin-bottom: 40px; }
    .jugador { background: rgba(255,255,255,0.2); border-radius: 10px; padding: 10px; width: 120px; border: 1px solid white; }
    .pos-label { font-size: 0.8em; color: #ccff00; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def render_jugador(lista, filtro):
    encontrados = [j for j in lista if any(x in j[2].upper() for x in filtro)]
    return encontrados

# Filtrado por posiciones
dels = render_jugador(titulares, ["DEL", "ATA", "DC", "EXT"])
meds = render_jugador(titulares, ["MED", "VOL", "MC", "MCO", "MCD"])
defs = render_jugador(titulares, ["DEF", "DFC", "LAT", "LI", "LD"])
arqs = render_jugador(titulares, ["ARQ", "POR", "GK"])

with st.container():
    st.markdown('<div class="campo">', unsafe_allow_html=True)
    
    # Delanteros
    col1, col2 = st.columns(2)
    with col1: st.write(f"⚽ {dels[0][1]}" if len(dels) > 0 else "---")
    with col2: st.write(f"⚽ {dels[1][1]}" if len(dels) > 1 else "---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Medios
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.write(f"🏃 {meds[0][1]}" if len(meds) > 0 else "---")
    with col2: st.write(f"🏃 {meds[1][1]}" if len(meds) > 1 else "---")
    with col3: st.write(f"🏃 {meds[2][1]}" if len(meds) > 2 else "---")
    with col4: st.write(f"🏃 {meds[3][1]}" if len(meds) > 3 else "---")
    st.markdown("<br>", unsafe_allow_html=True)

    # Defensas
    col1, col2, col3, col4 = st.columns(4)
    with col1: st.write(f"🛡️ {defs[0][1]}" if len(defs) > 0 else "---")
    with col2: st.write(f"🛡️ {defs[1][1]}" if len(defs) > 1 else "---")
    with col3: st.write(f"🛡️ {defs[2][1]}" if len(defs) > 2 else "---")
    with col4: st.write(f"🛡️ {defs[3][1]}" if len(defs) > 3 else "---")
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Arquero
    st.write(f"🧤 {arqs[0][1]}" if len(arqs) > 0 else "---")
    
    st.markdown('</div>', unsafe_allow_html=True)

st.divider()

# --- 6. GESTIÓN DE PLANTILLA ---
st.header("📋 Gestión de Jugadores")
if not mis_j:
    st.info("No tienes jugadores en tu plantilla.")
else:
    for j_id, nom, pos, est, precio in mis_j:
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(f"**{nom}** ({pos})")
        c2.write(f"Estado actual: **{est}**")
        if c3.button(f"Poner {'Suplente' if est == 'Titular' else 'Titular'}", key=f"btn_{j_id}"):
            nuevo = "Suplente" if est == "Titular" else "Titular"
            ejecutar_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
            st.rerun()
        if c4.button("Vender", key=f"vend_{j_id}"):
            ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
            ejecutar_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
            st.rerun()

st.divider()

# --- 7. RANKING Y PREMIOS ---
st.header("🏆 Tabla General y Premios")
if st.checkbox("⚙️ Menú de Administrador"):
    premio = st.number_input("Valor del Premio de Jornada", value=5000000)
    if st.button("Finalizar Jornada (Repartir Puntos y Premio)"):
        # Asignar puntos aleatorios a todos los jugadores
        ejecutar_db("UPDATE plantillas SET puntos_jornada = ABS(RANDOM() % 15)", commit=True)
        # Ganador
        ganador = ejecutar_db("SELECT usuario_id FROM plantillas GROUP BY usuario_id ORDER BY SUM(puntos_jornada) DESC LIMIT 1")
        if ganador:
            ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (premio, ganador[0][0]), commit=True)
            st.success("Puntos repartidos y premio entregado al ganador.")
            st.balloons()
            st.rerun()

tabla = ejecutar_db("""SELECT u.nombre, SUM(p.puntos_jornada) as total_pts 
                     FROM usuarios u LEFT JOIN plantillas p ON u.id = p.usuario_id 
                     GROUP BY u.id ORDER BY total_pts DESC""")
st.table(pd.DataFrame(tabla, columns=["Usuario", "Puntos Totales"]))
