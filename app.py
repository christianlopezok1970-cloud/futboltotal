import streamlit as st
import sqlite3
import pandas as pd

# --- PASO 1: LOS CIMIENTOS (Base de Datos) ---
DB_NAME = "liga_master_v1.db"

def inicializar_db():
    """Crea las tablas si no existen. Esto corre cada vez que la app inicia."""
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Tabla de usuarios: guarda nombre, clave y dinero
        c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT UNIQUE,
            password TEXT,
            presupuesto REAL DEFAULT 25000000
        )""")
        # Tabla de plantillas: guarda qué jugador es de quién
        # 'nombre_jugador UNIQUE' impide que dos personas compren al mismo
        c.execute("""CREATE TABLE IF NOT EXISTS plantillas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            usuario_id INTEGER,
            nombre_jugador TEXT UNIQUE, 
            equipo TEXT,
            posicion TEXT,
            precio REAL,
            estado TEXT DEFAULT 'Suplente',
            FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
        )""")
        conn.commit()

# Ejecutamos la creación de tablas
inicializar_db()

# --- PASO 2: EL MOTOR DE CONSULTAS ---
def consulta_db(query, params=(), commit=False):
    """Función para hablar con la base de datos de forma segura."""
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        if commit:
            conn.commit()
        return cursor.fetchall()

# --- PASO 3: LECTURA DEL EXCEL (El Mercado) ---
SHEET_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQed5yx4ReWBiR2IFct9y1jkLGVF9SIbn3RbzNYYZLJPhhcq_yy0WuTZWd0vVJAZ2kvD_walSrs-J-S/pub?output=csv"

@st.cache_data(ttl=300)
def cargar_excel():
    try:
        df = pd.read_csv(SHEET_URL)
        df.columns = [c.strip() for c in df.columns]
        
        # Limpieza de la columna 'Cotización' para que sea un número puro
        df['PrecioLimpio'] = (
            df['Cotización']
            .astype(str)
            .str.replace(r'[^\d]', '', regex=True)
        )
        df['PrecioLimpio'] = pd.to_numeric(df['PrecioLimpio'], errors='coerce').fillna(0)
        return df
    except Exception as e:
        st.error(f"Error cargando Excel: {e}")
        return pd.DataFrame()

# --- PRUEBA INICIAL ---
st.title("⚽ Liga Master - Fase de Construcción")
st.write("Cimientos listos. El motor de base de datos y el Excel están vinculados.")

# --- PASO 4: SISTEMA DE IDENTIDAD (Login) ---

if 'user' not in st.session_state:
    st.subheader("🔑 Acceso al Club")
    nombre_usuario = st.text_input("Nombre de tu Usuario / Equipo").strip()
    clave_usuario = st.text_input("Contraseña", type="password").strip()

    if st.button("Ingresar o Registrarse"):
        if nombre_usuario and clave_usuario:
            datos = consulta_db("SELECT id, nombre, presupuesto FROM usuarios WHERE nombre = ? AND password = ?", 
                                (nombre_usuario, clave_usuario))
            
            if datos:
                st.session_state.user = {"id": datos[0][0], "nombre": nombre_usuario}
                st.rerun()
            else:
                try:
                    consulta_db("INSERT INTO usuarios (nombre, password) VALUES (?, ?)", 
                                (nombre_usuario, clave_usuario), commit=True)
                    st.success("¡Usuario creado! Haz clic de nuevo para entrar.")
                except:
                    st.error("Nombre ocupado o contraseña incorrecta.")
        else:
            st.warning("Completa los campos.")
    st.stop()

# --- DATOS DEL USUARIO LOGUEADO ---
u_id = st.session_state.user["id"]
u_nombre = st.session_state.user["nombre"]

# Consultamos presupuesto real
res_presupuesto = consulta_db("SELECT presupuesto FROM usuarios WHERE id = ?", (u_id,))
presupuesto_actual = res_presupuesto[0][0]

# Mostramos solo la info en la barra lateral (Sin botón de cerrar)
st.sidebar.write(f"👤 Jugador: **{u_nombre}**")
st.sidebar.write(f"💰 Fondos: **€ {presupuesto_actual:,.0f}**")

st.write(f"### 🏟️ Oficina de {u_nombre}")

# --- PASO 5: EL MERCADO (Búsqueda y Compra) ---

st.divider()
st.header("🛒 Mercado de Jugadores")

df_mercado = cargar_excel()

# 1. Obtener lista de jugadores que ya tienen dueño
ocupados_data = consulta_db("SELECT nombre_jugador FROM plantillas")
jugadores_ocupados = [j[0] for j in ocupados_data]

# 2. Filtrar disponibles
df_disponibles = df_mercado[~df_mercado['Nombre'].isin(jugadores_ocupados)]

if not df_disponibles.empty:
    seleccion = st.selectbox("Busca un jugador para fichar:", [""] + df_disponibles['Nombre'].tolist())
    
    if seleccion:
        datos_jugador = df_disponibles[df_disponibles['Nombre'] == seleccion].iloc[0]
        
        nombre_j = datos_jugador['Nombre']
        equipo_j = datos_jugador['Equipo']
        posicion_j = datos_jugador['POS']
        precio_j = float(datos_jugador['PrecioLimpio'])
        
        st.write(f"🏷️ **Jugador:** {nombre_j} ({posicion_j})")
        st.write(f"💰 **Precio:** € {precio_j:,.0f}")
        
        # EL BOTÓN DE COMPRA
        if st.button(f"Confirmar Fichaje"):
            # Verificamos presupuesto de nuevo antes de procesar
            if presupuesto_actual >= precio_j:
                # EJECUTAMOS LA TRANSACCIÓN
                # A. Restar dinero
                consulta_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", 
                            (precio_j, u_id), commit=True)
                
                # B. Insertar jugador
                try:
                    consulta_db("""INSERT INTO plantillas (usuario_id, nombre_jugador, equipo, posicion, precio) 
                                   VALUES (?, ?, ?, ?, ?)""", 
                                (u_id, nombre_j, equipo_j, posicion_j, precio_j), commit=True)
                    
                    st.success(f"¡Fichaste a {nombre_j}!")
                    st.balloons()
                    # EL RERUN ES VITAL: Fuerza a la app a volver arriba y leer el presupuesto restado
                    st.rerun()
                except sqlite3.IntegrityError:
                    st.error("Alguien compró este jugador justo ahora.")
            else:
                st.error("No tienes suficiente dinero.")
else:
    st.info("No hay jugadores disponibles.")

# --- PASO 6: MI PLANTILLA Y LA CANCHA ---

st.divider()
st.header("🏃 Tu Plantilla")

# 1. Consultamos los jugadores que pertenecen a este usuario
mis_jugadores = consulta_db("""SELECT id, nombre_jugador, posicion, estado, precio 
                               FROM plantillas WHERE usuario_id = ?""", (u_id,))

if not mis_jugadores:
    st.info("Aún no tienes jugadores. ¡Ve al mercado y ficha tu primera estrella!")
else:
    # Mostramos una tabla simple o tarjetas para gestionar
    for j_id, nom, pos, est, precio in mis_jugadores:
        col_nom, col_est, col_acc = st.columns([3, 2, 2])
        
        col_nom.write(f"**{nom}** ({pos})")
        col_est.write(f"Estado: {est}")
        
        # Botón para cambiar entre Titular y Suplente
        btn_label = "Sentar" if est == "Titular" else "Poner Titular"
        if col_acc.button(btn_label, key=f"tito_{j_id}"):
            nuevo_estado = "Suplente" if est == "Titular" else "Titular"
            consulta_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo_estado, j_id), commit=True)
            st.rerun()

    # --- DIBUJO DE LA CANCHA ---
    st.divider()
    st.header("🏟️ Alineación Titular (1-4-4-2)")

    # Filtramos solo los que marcaste como Titulares
    titulares = [j for j in mis_jugadores if j[3] == "Titular"]

    # Función para organizar jugadores por línea
    def obtener_por_linea(lista, terminos):
        return [j[1] for j in lista if any(t in j[2].upper() for t in terminos)]

    # Clasificamos según el texto de la columna POS
    arqs = obtener_por_linea(titulares, ["ARQ", "POR", "GK"])
    defs = obtener_por_linea(titulares, ["DEF", "DFC", "LAT", "LI", "LD"])
    meds = obtener_por_linea(titulares, ["MED", "VOL", "MC", "MCO", "MCD"])
    dels = obtener_por_linea(titulares, ["DEL", "ATA", "DC", "EXT"])

    # Estilo visual de la cancha
    st.markdown("""
    <style>
        .campo {
            background-color: #2e7d32;
            border: 3px solid white;
            border-radius: 15px;
            padding: 20px;
            text-align: center;
            color: white;
        }
        .linea-cancha { margin-bottom: 20px; font-weight: bold; }
    </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="campo">', unsafe_allow_html=True)
        
        # Delanteros (2)
        st.write("⚽ DELANTEROS")
        c1, c2 = st.columns(2)
        c1.write(dels[0] if len(dels) > 0 else "---")
        c2.write(dels[1] if len(dels) > 1 else "---")
        
        # Mediocampo (4)
        st.write("🏃 MEDIOCAMPO")
        c1, c2, c3, c4 = st.columns(4)
        c1.write(meds[0] if len(meds) > 0 else "---")
        c2.write(meds[1] if len(meds) > 1 else "---")
        c3.write(meds[2] if len(meds) > 2 else "---")
        c4.write(meds[3] if len(meds) > 3 else "---")
        
        # Defensa (4)
        st.write("🛡️ DEFENSA")
        c1, c2, c3, c4 = st.columns(4)
        c1.write(defs[0] if len(defs) > 0 else "---")
        c2.write(defs[1] if len(defs) > 1 else "---")
        c3.write(defs[2] if len(defs) > 2 else "---")
        c4.write(defs[3] if len(defs) > 3 else "---")
        
        # Arquero (1)
        st.write("🧤 ARQUERO")
        st.write(arqs[0] if len(arqs) > 0 else "---")
        
        st.markdown('</div>', unsafe_allow_html=True)
