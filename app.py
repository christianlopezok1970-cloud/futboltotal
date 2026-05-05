import streamlit as st
import sqlite3
import pandas as pd

# --- CONFIGURACIÓN INICIAL ---
DB_NAME = "liga_master_v2.db"
PRESUPUESTO_INICIAL = 25_000_000
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

# --- MOTOR DE BASE DE DATOS ---
def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit: conn.commit()
        return cursor.fetchall()

def inicializar_tablas():
    # Tabla de Usuarios
    ejecutar_db("""CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT UNIQUE,
        password TEXT,
        presupuesto REAL DEFAULT 25000000
    )""", commit=True)
    
    # Tabla de Plantillas (Cartera)
    ejecutar_db("""CREATE TABLE IF NOT EXISTS plantillas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER,
        nombre_jugador TEXT UNIQUE, 
        posicion TEXT,
        equipo TEXT,
        precio REAL,
        estado TEXT DEFAULT 'Suplente',
        puntos INTEGER DEFAULT 0
    )""", commit=True)

inicializar_tablas()

# --- FUNCIONES DE APOYO ---
@st.cache_data(ttl=60)
def obtener_mercado():
    df = pd.read_csv(SHEET_URL)
    df.columns = [c.strip() for c in df.columns]
    # Limpieza de precios: "€ 10.000.000" -> 10000000
    df['PrecioNum'] = df.iloc[:, 3].replace(r'[\€\.]', '', regex=True).astype(float)
    df['Posicion'] = df.iloc[:, 2].str.upper().str.strip()
    df['Nombre'] = df.iloc[:, 0].strip()
    df['Equipo'] = df.iloc[:, 1].strip()
    return df

# --- INTERFAZ: LOGIN ---
st.set_page_config(page_title="Liga Master AI", layout="wide")

if 'user' not in st.session_state:
    st.title("⚽ Bienvenid@ a Liga Master")
    col1, col2 = st.columns(2)
    with col1:
        u_nom = st.text_input("Usuario")
        u_pass = st.text_input("Contraseña", type="password")
        if st.button("Entrar / Registrarse"):
            user = ejecutar_db("SELECT id, presupuesto FROM usuarios WHERE nombre = ? AND password = ?", (u_nom, u_pass))
            if user:
                st.session_state.user = {"id": user[0][0], "nombre": u_nom}
                st.rerun()
            else:
                # Registro automático para simplificar
                try:
                    ejecutar_db("INSERT INTO usuarios (nombre, password) VALUES (?,?)", (u_nom, u_pass), commit=True)
                    st.success("Usuario creado. ¡Haz clic en Entrar!")
                except: st.error("Credenciales incorrectas")
    st.stop()

# Datos del usuario logueado
u_id = st.session_state.user["id"]
u_info = ejecutar_db("SELECT presupuesto FROM usuarios WHERE id = ?", (u_id,))[0]
presupuesto_actual = u_info[0]

# --- SIDEBAR: ESTADO DEL CLUB ---
with st.sidebar:
    st.header(f"🏟️ {st.session_state.user['nombre']}")
    st.metric("Presupuesto", f"€ {presupuesto_actual:,.0f}")
    if st.button("Cerrar Sesión"):
        del st.session_state.user
        st.rerun()

# --- PESTAÑAS PRINCIPALES ---
tab1, tab2, tab3 = st.tabs(["🛒 Mercado", "🏃 Plantilla & Cancha", "📊 Clasificación"])

with tab1:
    st.subheader("Mercado de Pases")
    df_m = obtener_mercado()
    
    # Filtro: Solo mostrar los que NO han sido comprados por nadie
    jugadores_comprados = [j[0] for j in ejecutar_db("SELECT nombre_jugador FROM plantillas")]
    df_disponible = df_m[~df_m['Nombre'].isin(jugadores_comprados)]
    
    selected_name = st.selectbox("Selecciona un jugador para fichar", [""] + df_disponible['Nombre'].tolist())
    
    if selected_name != "":
        ficha = df_disponible[df_disponible['Nombre'] == selected_name].iloc[0]
        st.write(f"**Posición:** {ficha['Posicion']} | **Equipo:** {ficha['Equipo']}")
        st.write(f"**Precio:** € {ficha['PrecioNum']:,.0f}")
        
        if st.button(f"Fichar a {selected_name}"):
            if presupuesto_actual >= ficha['PrecioNum']:
                try:
                    # 1. Restar presupuesto
                    ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (ficha['PrecioNum'], u_id), commit=True)
                    # 2. Agregar a plantilla
                    ejecutar_db("INSERT INTO plantillas (usuario_id, nombre_jugador, posicion, equipo, precio) VALUES (?,?,?,?,?)",
                                (u_id, ficha['Nombre'], ficha['Posicion'], ficha['Equipo'], ficha['PrecioNum']), commit=True)
                    st.success("¡Fichaje completado!")
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Alguien te ganó de mano. El jugador ya no está disponible.")
            else:
                st.error("Presupuesto insuficiente.")

with tab2:
    st.subheader("Tu Equipo")
    mi_equipo = ejecutar_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
    
    if not mi_equipo:
        st.info("Aún no tienes jugadores. Ve al Mercado.")
    else:
        # Gestión de Venta y Estados
        for j_id, nom, pos, est, precio in mi_equipo:
            c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
            c1.write(f"**{nom}** ({pos})")
            c2.write(f"Estado: {est}")
            
            # Botón Titular/Suplente
            label_btn = "Banquillo" if est == "Titular" else "Hacer Titular"
            if c3.button(label_btn, key=f"est_{j_id}"):
                nuevo = "Suplente" if est == "Titular" else "Titular"
                ejecutar_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
                st.rerun()
                
            # Botón Venta
            if c4.button("🗑️", key=f"del_{j_id}", help="Vender jugador"):
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
                ejecutar_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
                st.rerun()

    # --- DIBUJO DE LA CANCHA 1-4-4-2 ---
    st.divider()
    st.subheader("🏟️ Alineación 1-4-4-2")
    titulares = [j for j in mi_equipo if j[3] == "Titular"]
    
    # Lógica simple de dibujo
    def dibujar_linea(jugadores_pos):
        cols = st.columns(len(jugadores_pos) if jugadores_pos else 1)
        for idx, j in enumerate(jugadores_pos):
            cols[idx].markdown(f"**{j[1]}**")

    # Separar por posiciones
    arqs = [j for j in titulares if "ARQ" in j[2] or "POR" in j[2]]
    defs = [j for j in titulares if "DEF" in j[2] or "LAT" in j[2] or "DFC" in j[2]]
    meds = [j for j in titulares if "MED" in j[2] or "VOL" in j[2] or "MC" in j[2]]
    dels = [j for j in titulares if "DEL" in j[2] or "ATA" in j[2] or "DC" in j[2]]

    st.markdown("<div style='background-color:#2e7d32; padding:20px; border-radius:10px; text-align:center; color:white'>", unsafe_allow_html=True)
    st.write("--- DELANTEROS ---")
    dibujar_linea(dels[:2])
    st.write("--- MEDIOCAMPO ---")
    dibujar_linea(meds[:4])
    st.write("--- DEFENSA ---")
    dibujar_linea(defs[:4])
    st.write("--- ARQUERO ---")
    dibujar_linea(arqs[:1])
    st.markdown("</div>", unsafe_allow_html=True)

with tab3:
    st.subheader("Performance de la Liga")
    st.info("Los puntos se asignan al finalizar la jornada.")
    
    # Sistema de premios (Botón simulador para el admin)
    if st.checkbox("Simular Fin de Jornada (Admin)"):
        if st.button("Asignar Puntos Aleatorios y Premiar"):
            # Asignar puntos al azar entre 1 y 10 a todos los jugadores comprados
            ejecutar_db("UPDATE plantillas SET puntos = ABS(RANDOM() % 10)", commit=True)
            
            # Calcular qué usuario sumó más
            ranking = ejecutar_db("""
                SELECT usuario_id, SUM(puntos) as total 
                FROM plantillas 
                GROUP BY usuario_id 
                ORDER BY total DESC LIMIT 1
            """)
            
            if ranking:
                ganador_id, puntos_max = ranking[0]
                premio = 5_000_000
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (premio, ganador_id), commit=True)
                st.success(f"¡El usuario ID {ganador_id} ganó la jornada con {puntos_max} puntos y recibe €5M!")
                st.rerun()

    # Mostrar Tabla General
    tabla = ejecutar_db("""
        SELECT u.nombre, SUM(p.puntos) as pts 
        FROM usuarios u 
        LEFT JOIN plantillas p ON u.id = p.usuario_id 
        GROUP BY u.id ORDER BY pts DESC
    """)
    st.table(pd.DataFrame(tabla, columns=["Usuario", "Puntos Totales"]))
