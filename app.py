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


# --- PASO 6: MI PLANTILLA Y CANCHA PRO (1-4-4-2) ---

st.divider()
st.header("🏟️ Tu Alineación Titular")

# 1. Obtener datos actualizados
mis_jugadores = consulta_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
titulares = [j for j in mis_jugadores if j[3] == "Titular"]

# Estilos para la cancha y las fichas
st.markdown("""
<style>
    .stApp { background-color: #0e1117; }
    .cancha-container {
        background: linear-gradient(to bottom, #1b5e20 0%, #2e7d32 100%);
        border: 4px solid #ffffff33;
        border-radius: 20px;
        padding: 40px 10px;
        position: relative;
        box-shadow: 0 10px 30px rgba(0,0,0,0.5);
    }
    .ficha-player {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
    }
    .circulo {
        width: 60px; height: 60px;
        background: white;
        border-radius: 50%;
        border: 3px solid #00d4ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    .nombre-player {
        background: rgba(0,0,0,0.7);
        color: white;
        font-size: 11px;
        padding: 2px 8px;
        border-radius: 4px;
        margin-top: 5px;
        font-weight: bold;
        text-align: center;
        width: 90px;
        overflow: hidden;
        white-space: nowrap;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

# Función para renderizar la ficha de un jugador en la cancha
def ficha_html(lista, index):
    if index < len(lista):
        nombre = lista[index][1].split(' ')[0] # Primer nombre
        return f'''
        <div class="ficha-player">
            <div class="circulo">⚽</div>
            <div class="nombre-player">{nombre}</div>
        </div>
        '''
    return '<div class="ficha-player" style="opacity:0.2"><div class="circulo"></div></div>'

# Clasificación por líneas
def filtrar_pos(lista, terminos):
    return [j for j in lista if any(t in j[2].upper() for t in terminos)]

dels = filtrar_pos(titulares, ["DEL", "ATA", "DC", "EXT"])
meds = filtrar_pos(titulares, ["MED", "VOL", "MC", "MCO", "MCD"])
defs = filtrar_pos(titulares, ["DEF", "DFC", "LAT", "LI", "LD"])
arqs = filtrar_pos(titulares, ["ARQ", "POR", "GK"])

# --- DIBUJO DE LA CANCHA ---
with st.container():
    st.markdown('<div class="cancha-container">', unsafe_allow_html=True)
    
    # Delanteros (2)
    c1, c2 = st.columns(2)
    with c1: st.markdown(ficha_html(dels, 0), unsafe_allow_html=True)
    with c2: st.markdown(ficha_html(dels, 1), unsafe_allow_html=True)
    
    st.write("<br>", unsafe_allow_html=True)
    
    # Mediocampo (4)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ficha_html(meds, 0), unsafe_allow_html=True)
    with c2: st.markdown(ficha_html(meds, 1), unsafe_allow_html=True)
    with c3: st.markdown(ficha_html(meds, 2), unsafe_allow_html=True)
    with c4: st.markdown(ficha_html(meds, 3), unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)

    # Defensa (4)
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(ficha_html(defs, 0), unsafe_allow_html=True)
    with c2: st.markdown(ficha_html(defs, 1), unsafe_allow_html=True)
    with c3: st.markdown(ficha_html(defs, 2), unsafe_allow_html=True)
    with c4: st.markdown(ficha_html(defs, 3), unsafe_allow_html=True)

    st.write("<br>", unsafe_allow_html=True)

    # Arquero (1)
    col_arq = st.columns([1, 1, 1]) # Para centrar al arquero
    with col_arq[1]: st.markdown(ficha_html(arqs, 0), unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- GESTIÓN DE PLANTILLA (SENTAR Y VENDER) ---
st.divider()
st.header("📋 Gestión de Jugadores")

if not mis_jugadores:
    st.info("No tienes jugadores.")
else:
    for j_id, nom, pos, est, precio in mis_jugadores:
        c1, c2, c3, c4 = st.columns([3, 2, 2, 1])
        c1.write(f"**{nom}** ({pos})")
        c2.write(f"€ {precio:,.0f}")
        
        # Botón Titular/Suplente
        txt_est = "Sentar" if est == "Titular" else "Titular"
        if c3.button(txt_est, key=f"est_{j_id}"):
            nuevo = "Suplente" if est == "Titular" else "Titular"
            consulta_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
            st.rerun()
            
        # BOTÓN DE VENTA (Recupera el dinero)
        if c4.button("🗑️", key=f"del_{j_id}", help="Vender jugador"):
            # 1. Devolver dinero
            consulta_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
            # 2. Eliminar de la plantilla
            consulta_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
            st.success(f"Vendiste a {nom}")
            st.rerun()
