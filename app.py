import streamlit as st
import random

# 1. Base de Datos de IDs (Futbin 26)
# He seleccionado algunos jugadores variados para tu mazo
jugadores_db = [
    {"nombre": "Edwuin Cetré", "id": "15945", "rating": 76},
    {"nombre": "Lionel Messi", "id": "1", "rating": 86},
    {"nombre": "Julián Álvarez", "id": "2121", "rating": 84},
    {"nombre": "Lautaro Martínez", "id": "2363", "rating": 88},
    {"nombre": "Rodrigo De Paul", "id": "2525", "rating": 84},
    {"nombre": "Enzo Fernández", "id": "16450", "rating": 82},
    {"nombre": "Nicolás Tagliafico", "id": "2700", "rating": 78},
    {"nombre": "Paulo Dybala", "id": "1900", "rating": 84},
    {"nombre": "Emi Martínez", "id": "2850", "rating": 85},
    {"nombre": "Alexis Mac Allister", "id": "16000", "rating": 82}
]

st.title("🧧 Sobre de Jugadores FC26")
st.write("Presiona el botón para obtener un jugador al azar de la base de datos de Futbin.")

# --- LÓGICA DEL JUEGO ---
if st.button("✨ ABRIR SOBRE AZAR"):
    # Elegimos un jugador aleatorio de nuestra lista
    jugador = random.choice(jugadores_db)
    
    # Construimos la URL infalible (directa al servidor de imágenes)
    url_carta = f"https://cdn.futbin.com/content/fifa26/players/{jugador['id']}.png"
    
    with st.spinner(f"Buscando a {jugador['nombre']}..."):
        st.balloons()
        
        # Mostramos la carta real
        st.image(url_carta, width=300)
        
        # Calculamos estrellas y valor según tu lógica
        rat = jugador['rating']
        if rat >= 85: estrellas, nivel = "⭐⭐⭐⭐⭐", 5
        elif rat >= 80: estrellas, nivel = "⭐⭐⭐⭐", 4
        elif rat >= 75: estrellas, nivel = "⭐⭐⭐", 3
        elif rat >= 70: estrellas, nivel = "⭐⭐", 2
        else: estrellas, nivel = "⭐", 1
        
        valor_base = nivel * 15 # Tu lógica de 15 por estrella
        
        # Interfaz de stats
        st.subheader(f"¡Te salió {jugador['nombre']}!")
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Calidad", estrellas)
        with col2:
            st.metric("Valor Base", f"{valor_base} 🪙")
            
        st.info(f"Rating oficial EA: {rat}")

st.divider()
st.caption("Nota: Si quieres agregar más jugadores, solo necesitas buscar su ID en la URL de Futbin y agregarlo a la lista 'jugadores_db'.")
