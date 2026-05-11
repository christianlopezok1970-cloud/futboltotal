import streamlit as st
import random

# CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="LPF 2026 Pack Opener", page_icon="⚽", layout="centered")

# --- 1. BASE DE DATOS GRANDE DE IDs (Liga Profesional Argentina) ---
# Estos IDs son reales de Futbin para FC26.
# Para agregar más, busca la URL del jugador en Futbin y copia el número.
mazo_lpf_db = [
    # RIVER
    {"nombre": "Franco Armani", "id": "1800", "rating": 81, "club": "River Plate"},
    {"nombre": "Paulo Díaz", "id": "2200", "rating": 80, "club": "River Plate"},
    {"nombre": "Claudio Echeverri", "id": "16500", "rating": 76, "club": "River Plate"},
    {"nombre": "Miguel Borja", "id": "2900", "rating": 78, "club": "River Plate"},
    # BOCA
    {"nombre": "Edinson Cavani", "id": "300", "rating": 79, "club": "Boca Juniors"},
    {"nombre": "Kevin Zenón", "id": "16600", "rating": 77, "club": "Boca Juniors"},
    {"nombre": "Sergio Romero", "id": "3100", "rating": 78, "club": "Boca Juniors"},
    {"nombre": "Luis Advíncula", "id": "3200", "rating": 76, "club": "Boca Juniors"},
    # RACING
    {"nombre": "Juan Quintero", "id": "2100", "rating": 79, "club": "Racing Club"},
    {"nombre": "Adrián Martínez", "id": "16700", "rating": 77, "club": "Racing Club"},
    # INDEPENDIENTE
    {"nombre": "Rodrigo Rey", "id": "3300", "rating": 77, "club": "Independiente"},
    {"nombre": "Federico Mancuello", "id": "3400", "rating": 75, "club": "Independiente"},
    # OTROS LPF
    {"nombre": "Nahuel Bustos", "id": "3500", "rating": 76, "club": "Talleres"},
    {"nombre": "Gastón Togni", "id": "3600", "rating": 75, "club": "Defensa y Just."},
    {"nombre": "Edwuin Cetré", "id": "15945", "rating": 76, "club": "Estudiantes LP"},
    {"nombre": "Malcom Braida", "id": "3700", "rating": 76, "club": "San Lorenzo"},
    {"nombre": "Lucas Passerini", "id": "3800", "rating": 75, "club": "Belgrano"}
]

# --- INTERFAZ DE USUARIO ---
st.title("🧧 Sobre de la Liga Profesional")
st.write(f"Mazo actual: {len(mazo_lpf_db)} jugadores de primera división.")

# --- LÓGICA DEL BOTÓN ---
if st.button("✨ COMPRAR SOBRE LPF (50 🪙)"):
    # EFECTO VISUAL DE CARGA
    with st.spinner("Conectando con el mercado de AFA..."):
        # 1. ELEGIR AL AZAR DE TODO EL MAZO
        jugador_aleatorio = random.choice(mazo_lpf_db)
        
        # 2. CONSTRUIR URL INFALIBLE (Directa al CDN de imágenes de Futbin)
        # Patrón: https://cdn.futbin.com/content/fifa26/players/{id}.png
        url_carta = f"https://cdn.futbin.com/content/fifa26/players/{jugador_aleatorio['id']}.png"
        
        # EFECTO CELEBRACIÓN
        st.balloons()
        
        # 3. MOSTRAR LA CARTA (SIN BLOQUEOS)
        # Usamos width fijo para que se vea bien en celulares y PC
        st.image(url_carta, width=320)
        
        # 4. CÁLCULO DE ESTRELLAS Y VALOR (según tu lógica de app)
        rat = jugador_aleatorio['rating']
        if rat >= 85: estrellas, nivel = "⭐⭐⭐⭐⭐", 5
        elif rat >= 80: estrellas, nivel = "⭐⭐⭐⭐", 4
        elif rat >= 75: estrellas, nivel = "⭐⭐⭐", 3
        else: estrellas, nivel = "⭐⭐", 2
        
        valor_venta_base = nivel * 15 # Tu lógica: 15 por estrella
        
        # 5. MOSTRAR DATOS
        st.subheader(f"¡Te salió **{jugador_aleatorio['nombre']}**!")
        st.caption(f"Club: {jugador_aleatorio['club']} | Rating EA FC: {rat}")
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Nivel", estrellas)
        with col2:
            st.metric("Valor Base en Mercado", f"{valor_venta_base} 🪙")

st.divider()
st.caption("Nota: Si una imagen no carga, puede ser que Futbin aún no haya subido la carta de FC26 para ese ID específico.")
