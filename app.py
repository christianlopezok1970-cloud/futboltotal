import streamlit as st
import random

# Configuración
st.set_page_config(page_title="EDLP Pack Opener", layout="centered")

# --- BASE DE DATOS DE ESTUDIANTES DE LA PLATA (Ejemplos del link que pasaste) ---
# Para que sean "todos", puedes seguir agregando IDs de esa lista de Futbin
mazo_edlp = [
    {"nombre": "Enzo Pérez", "id": "183894", "rat": 77},
    {"nombre": "Santiago Ascacíbar", "id": "235165", "rat": 77},
    {"nombre": "Guido Carrillo", "id": "208115", "rat": 76},
    {"nombre": "Edwuin Cetré", "id": "242426", "rat": 76},
    {"nombre": "José Sosa", "id": "163155", "rat": 75},
    {"nombre": "Federico Fernández", "id": "192362", "rat": 74},
    {"nombre": "Gastón Benedetti", "id": "273344", "rat": 73},
    {"nombre": "Eros Mancuso", "id": "268305", "rat": 73},
    {"nombre": "Tiago Palacios", "id": "258957", "rat": 72},
    {"nombre": "Matías Mansilla", "id": "261947", "rat": 72}
]

st.title("🇦🇹 Sobre de Estudiantes de La Plata")
st.write("Conectado a la base de datos de Futbin / EA Sports FC")

if st.button("✨ ABRIR SOBRE DEL PINCHA"):
    jugador = random.choice(mazo_edlp)
    
    # URL DIRECTA AL CDN (A veces los navegadores bloquean esto si viene de Streamlit)
    # Intentamos la versión oficial de EA que es más abierta:
    url_carta = f"https://www.futbin.com/content/fifa26/players/{jugador['id']}.png"
    
    with st.spinner(f"Abriendo sobre... ¡Salió {jugador['nombre']}!"):
        st.balloons()
        
        # MOSTRAR IMAGEN CON TRUCO DE CABECERAS
        # Si Streamlit no la muestra, usamos un contenedor HTML
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="{url_carta}" width="280" style="border-radius: 10px;" 
                onerror="this.onerror=null;this.src='https://selene.club/static/media/card-placeholder.png';">
            </div>
            """, 
            unsafe_allow_html=True
        )
        
        # Lógica de estrellas y valor base
        rating = jugador['rat']
        if rating >= 80: nivel = 4
        elif rating >= 75: nivel = 3
        else: nivel = 2
        
        valor = nivel * 15
        
        st.markdown(f"<h2 style='text-align: center;'>{jugador['nombre']}</h2>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Rating", rating)
        c2.metric("Nivel", f"{nivel} ⭐")
        c3.metric("Valor Base", f"{valor} 🪙")

st.info("Nota: Si la imagen se ve rota, es por la protección de Futbin. En la versión final de tu app, usaremos un Proxy de imágenes.")
