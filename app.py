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


# --- PASO 6: CANCHA DEFINITIVA (ESTILO 365SCORES) ---

st.divider()
st.header("🏟️ Tu Alineación Titular")

# 1. Obtener datos
mis_jugadores = consulta_db("SELECT id, nombre_jugador, posicion, estado, precio FROM plantillas WHERE usuario_id = ?", (u_id,))
titulares = [j for j in mis_jugadores if j[3] == "Titular"]

# 2. Estilo CSS "Cancha Real"
st.markdown("""
<style>
    /* Contenedor principal que simula el césped */
    .cancha-v3 {
        background: #2e7d32;
        background-image: 
            linear-gradient(rgba(255,255,255,0.1) 2px, transparent 2px),
            linear-gradient(90deg, rgba(255,255,255,0.1) 2px, transparent 2px);
        background-size: 100% 40px; /* Franjas de césped */
        border: 3px solid #ffffff55;
        border-radius: 15px;
        padding: 30px 10px;
        box-shadow: inset 0 0 50px rgba(0,0,0,0.4);
    }
    /* Estilo de la ficha del jugador */
    .jugador-ficha {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin-bottom: 15px;
    }
    .jugador-circulo {
        width: 55px; height: 55px;
        background: white;
        border-radius: 50%;
        border: 2px solid #00d4ff;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5);
    }
    .jugador-nombre {
        background: rgba(0, 0, 0, 0.85);
        color: #00d4ff;
        font-size: 11px;
        font-weight: bold;
        padding: 2px 8px;
        border-radius: 5px;
        margin-top: 6px;
        width: 95%;
        text-align: center;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }
</style>
""", unsafe_allow_html=True)

def draw_player(lista, idx):
    if idx < len(lista):
        # Limpieza de nombre (quitar comas y apellidos largos)
        nom = lista[idx][1].replace(',', '').split(' ')[0]
        return f'''
        <div class="jugador-ficha">
            <div class="jugador-circulo">⚽</div>
            <div class="jugador-nombre">{nom}</div>
        </div>
        '''
    return '<div class="jugador-ficha" style="opacity:0.2"><div class="jugador-circulo" style="background:transparent; border:2px dashed white"></div></div>'

# Clasificación de titulares por posición
def get_pos(lista, keys):
    return [j for j in lista if any(k in j[2].upper() for k in keys)]

dels = get_pos(titulares, ["DEL", "ATA", "DC", "EXT"])
meds = get_pos(titulares, ["MED", "VOL", "MC", "MCO", "MCD"])
defs = get_pos(titulares, ["DEF", "DFC", "LAT", "LI", "LD"])
arqs = get_pos(titulares, ["ARQ", "POR", "GK"])

# --- RENDERIZADO DE LA CANCHA ---
# Envolvemos las columnas de Streamlit en un div con clase 'cancha-v3'
st.markdown('<div class="cancha-v3">', unsafe_allow_html=True)

# Delanteros
c1, c2 = st.columns(2)
with c1: st.markdown(draw_player(dels, 0), unsafe_allow_html=True)
with c2: st.markdown(draw_player(dels, 1), unsafe_allow_html=True)

# Medios
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(draw_player(meds, 0), unsafe_allow_html=True)
with c2: st.markdown(draw_player(meds, 1), unsafe_allow_html=True)
with c3: st.markdown(draw_player(meds, 2), unsafe_allow_html=True)
with c4: st.markdown(draw_player(meds, 3), unsafe_allow_html=True)

# Defensas
c1, c2, c3, c4 = st.columns(4)
with c1: st.markdown(draw_player(defs, 0), unsafe_allow_html=True)
with c2: st.markdown(draw_player(defs, 1), unsafe_allow_html=True)
with c3: st.markdown(draw_player(defs, 2), unsafe_allow_html=True)
with c4: st.markdown(draw_player(defs, 3), unsafe_allow_html=True)

# Arquero
c1, c2, c3 = st.columns([1, 1, 1])
with c2: st.markdown(draw_player(arqs, 0), unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# --- GESTIÓN DE JUGADORES (LISTA Y VENTA) ---
st.divider()
st.subheader("📋 Gestión de Jugadores")

if not mis_jugadores:
    st.info("No tienes jugadores comprados.")
else:
    for j_id, nom, pos, est, precio in mis_jugadores:
        col1, col2, col3, col4 = st.columns([3, 1, 2, 1])
        col1.write(f"**{nom}** ({pos})")
        col2.write(f"€ {precio:,.0f}")
        
        # Botón para Titularidad
        btn_t = "Sentar" if est == "Titular" else "Titular"
        if col3.button(btn_t, key=f"t_{j_id}"):
            nuevo = "Suplente" if est == "Titular" else "Titular"
            consulta_db("UPDATE plantillas SET estado = ? WHERE id = ?", (nuevo, j_id), commit=True)
            st.rerun()
            
        # Botón para Vender
        if col4.button("🗑️", key=f"v_{j_id}"):
            consulta_db("UPDATE usuarios SET presupuesto = presupuesto + ? WHERE id = ?", (precio, u_id), commit=True)
            consulta_db("DELETE FROM plantillas WHERE id = ?", (j_id,), commit=True)
            st.rerun()
