import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
import io
from PIL import Image

# --- 1. CONFIGURACIÓN DE BASE DE DATOS MÉDICA ---
DB_NAME = 'gestion_medica_v1.db'

def ejecutar_db(query, params=(), commit=False):
    with sqlite3.connect(DB_NAME, check_same_thread=False) as conn:
        c = conn.cursor()
        c.execute(query, params)
        if commit: conn.commit()
        return c.fetchall()

# Creación de tablas profesionales
ejecutar_db('''CREATE TABLE IF NOT EXISTS pacientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT,
                dni TEXT UNIQUE,
                telefono TEXT,
                historial_clinico TEXT,
                fecha_registro TEXT)''', commit=True)

ejecutar_db('''CREATE TABLE IF NOT EXISTS galerias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER,
                imagen_data BLOB,
                descripcion TEXT,
                fecha TEXT)''', commit=True)

ejecutar_db('''CREATE TABLE IF NOT EXISTS agenda (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                paciente_id INTEGER,
                fecha TEXT,
                hora TEXT,
                motivo TEXT)''', commit=True)

# --- 2. ESTILO MÉDICO (AZUL PROFUNDO Y BLANCO) ---
st.set_page_config(page_title="Medical Suite Pro", layout="wide")

st.markdown("""
    <style>
    .stApp {
        background: linear-gradient(180deg, #002147 0%, #f0f2f6 100%);
    }
    .main-card {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        color: #333;
        margin-bottom: 20px;
    }
    h1, h2, h3 { color: #002147 !important; }
    .stButton>button {
        background-color: #004E98;
        color: white;
        border-radius: 8px;
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. LÓGICA DE NAVEGACIÓN ---
with st.sidebar:
    st.title("🏥 Medical Suite")
    menu = st.radio("Menú Principal", ["Agenda Hoy", "Pacientes", "Nueva Ficha"])

# --- 4. SECCIÓN: NUEVA FICHA (CON FOTOS) ---
if menu == "Nueva Ficha":
    st.header("📝 Registro de Paciente")
    with st.container():
        st.markdown('<div class="main-card">', unsafe_allow_html=True)
        col1, col2 = st.columns(2)
        nombre = col1.text_input("Nombre Completo")
        dni = col2.text_input("DNI / Identificación")
        tel = col1.text_input("Teléfono")
        notas = st.text_area("Antecedentes y Notas Médicas")
        
        st.subheader("📸 Capturas Clínicas (JPG)")
        archivos_fotos = st.file_uploader("Subir imágenes", type=['jpg', 'jpeg', 'png'], accept_multiple_files=True)
        
        if st.button("Guardar Paciente"):
            if nombre and dni:
                # Guardar paciente
                ejecutar_db("INSERT INTO pacientes (nombre, dni, telefono, historial_clinico, fecha_registro) VALUES (?,?,?,?,?)",
                           (nombre, dni, tel, notas, datetime.now().strftime("%Y-%m-%d")), commit=True)
                
                # Obtener ID del paciente recién creado
                p_id = ejecutar_db("SELECT id FROM pacientes WHERE dni = ?", (dni,))[0][0]
                
                # Guardar fotos
                for archivo in archivos_fotos:
                    blob_data = archivo.read()
                    ejecutar_db("INSERT INTO galerias (paciente_id, imagen_data, descripcion, fecha) VALUES (?,?,?,?)",
                               (p_id, blob_data, "Captura inicial", datetime.now().strftime("%Y-%m-%d")), commit=True)
                
                st.success(f"Ficha de {nombre} creada con éxito.")
        st.markdown('</div>', unsafe_allow_html=True)

# --- 5. SECCIÓN: AGENDA VISUAL SIMPLE ---
elif menu == "Agenda Hoy":
    st.header("📅 Agenda de Citas")
    
    col_cal, col_list = st.columns([1, 2])
    
    with col_cal:
        fecha_sel = st.date_input("Seleccionar Fecha", datetime.now())
    
    with col_list:
        st.subheader(f"Citas para el {fecha_sel}")
        citas = ejecutar_db("""
            SELECT a.hora, p.nombre, a.motivo 
            FROM agenda a JOIN pacientes p ON a.paciente_id = p.id 
            WHERE a.fecha = ? ORDER BY a.hora ASC""", (fecha_sel.strftime("%Y-%m-%d"),))
        
        if not citas:
            st.info("No hay citas programadas.")
        else:
            for hora, p_nom, motivo in citas:
                with st.container():
                    st.markdown(f"""
                        <div style="background:white; padding:10px; border-left:5px solid #004E98; margin-bottom:10px; border-radius:5px;">
                            <span style="font-weight:bold; color:#002147;">{hora}</span> - {p_nom} <br>
                            <small style="color:gray;">Motivo: {motivo}</small>
                        </div>
                    """, unsafe_allow_html=True)

    # Botón para agendar nueva cita
    with st.expander("➕ Programar nueva cita"):
        todos_pacientes = ejecutar_db("SELECT id, nombre FROM pacientes")
        dict_p = {p[1]: p[0] for p in todos_pacientes}
        p_cita = st.selectbox("Paciente", options=list(dict_p.keys()))
        f_cita = st.date_input("Fecha", key="f_cita")
        h_cita = st.time_input("Hora")
        m_cita = st.text_input("Motivo")
        
        if st.button("Confirmar Cita"):
            ejecutar_db("INSERT INTO agenda (paciente_id, fecha, hora, motivo) VALUES (?,?,?,?)",
                       (dict_p[p_cita], f_cita.strftime("%Y-%m-%d"), h_cita.strftime("%H:%M"), m_cita), commit=True)
            st.rerun()

# --- 6. SECCIÓN: BUSCADOR DE PACIENTES ---
elif menu == "Pacientes":
    st.header("🔍 Buscador de Pacientes")
    busqueda = st.text_input("Ingresa nombre o DNI")
    
    if busqueda:
        resultados = ejecutar_db("SELECT id, nombre, dni, historial_clinico FROM pacientes WHERE nombre LIKE ? OR dni LIKE ?", 
                                (f'%{busqueda}%', f'%{busqueda}%'))
        
        for p_id, p_nom, p_dni, p_hist in resultados:
            with st.expander(f"👤 {p_nom} (DNI: {p_dni})"):
                st.write(f"**Historial:** {p_hist}")
                
                # Mostrar fotos del paciente
                fotos = ejecutar_db("SELECT imagen_data, fecha FROM galerias WHERE paciente_id = ?", (p_id,))
                if fotos:
                    st.subheader("Galería de Imágenes")
                    cols = st.columns(3)
                    for idx, (img_blob, f_img) in enumerate(fotos):
                        img = Image.open(io.BytesIO(img_blob))
                        cols[idx % 3].image(img, caption=f"Fecha: {f_img}", use_container_width=True)
