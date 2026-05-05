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

# Cargamos los datos del Excel
df_mercado = cargar_excel()

# 1. Filtramos para NO mostrar jugadores que ya fueron comprados por alguien
# Consultamos los nombres de los jugadores que ya están en la tabla 'plantillas'
jugadores_ocupados = [j[0] for j in consulta_db("SELECT nombre_jugador FROM plantillas")]

# Creamos un listado de jugadores disponibles (los que no están en la lista de ocupados)
df_disponibles = df_mercado[~df_mercado['Nombre'].isin(jugadores_ocupados)]

# 2. Buscador de Jugadores
if not df_disponibles.empty:
    seleccion = st.selectbox("Busca un jugador para fichar:", [""] + df_disponibles['Nombre'].tolist())
    
    if seleccion != "":
        # Extraemos la fila del jugador elegido
        datos_jugador = df_disponibles[df_disponibles['Nombre'] == seleccion].iloc[0]
        
        nombre_j = datos_jugador['Nombre']
        equipo_j = datos_jugador['Equipo']
        posicion_j = datos_jugador['POS']
        precio_j = datos_jugador['PrecioLimpio']
        
        st.info(f"**Ficha Técnica:** {nombre_j} | {equipo_j} | {posicion_j}")
        st.write(f"💰 **Precio de salida:** € {precio_j:,.0f}")
        
        # 3. Lógica de Compra
        if st.button(f"Confirmar Fichaje de {nombre_j}"):
            if presupuesto_actual >= precio_j:
                try:
                    # A. Restamos el dinero al usuario en la DB
                    consulta_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", 
                                (precio_j, u_id), commit=True)
                    
                    # B. Insertamos el jugador en la tabla plantillas
                    consulta_db("""INSERT INTO plantillas (usuario_id, nombre_jugador, equipo, posicion, precio) 
                                   VALUES (?, ?, ?, ?, ?)""", 
                                (u_id, nombre_j, equipo_j, posicion_j, precio_j), commit=True)
                    
                    st.success(f"¡Fichaje estrella! {nombre_j} se ha unido a tu equipo.")
                    st.balloons()
                    st.rerun() # Recargamos para actualizar el presupuesto en la barra lateral
                except sqlite3.IntegrityError:
                    # Esto ocurre si justo alguien lo compró un segundo antes (por el UNIQUE)
                    st.error("⚠️ ¡Llegaste tarde! Otro usuario acaba de fichar a este jugador.")
            else:
                st.error("❌ No tienes fondos suficientes para esta operación.")
else:
    st.write("No hay más jugadores disponibles en el mercado.")
