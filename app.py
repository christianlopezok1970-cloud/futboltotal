import streamlit as st

# Configuración de la página
st.set_page_config(page_title="FC26 Card Opener", layout="centered")

st.title("🧧 Apertura de Sobre: FC26")
st.write("Este sistema conecta directamente con el servidor de imágenes de Futbin.")

# Datos de ejemplo (Esto lo podrías tener en una lista después)
id_cetre = "15945"
nombre_jugador = "Edwuin Cetré"
rating_jugador = 76

# --- LÓGICA DEL BOTÓN ---
if st.button(f"✨ ABRIR SOBRE: {nombre_jugador}"):
    # Construimos la URL directa a la imagen del servidor de Futbin
    # El patrón siempre es: https://cdn.futbin.com/content/fifa26/players/{id}.png
    url_carta = f"https://cdn.futbin.com/content/fifa26/players/{id_cetre}.png"
    
    with st.spinner("Trayendo carta desde el servidor..."):
        # Efectos visuales
        st.balloons()
        
        # Mostramos la imagen directamente
        # Usamos use_container_width=False para que no se deforme la carta
        st.image(url_carta, width=350)
        
        # Información complementaria
        st.success(f"¡Has obtenido a **{nombre_jugador}**!")
        
        # Sistema de estrellas basado en tu lógica (75-81 = 3 estrellas)
        estrellas = "⭐ ⭐ ⭐"
        valor_venta = 45 # 3 estrellas * 15 monedas
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Calidad", estrellas)
        with col2:
            st.metric("Valor de Venta", f"{valor_venta} 🪙")

st.divider()
st.caption("Nota: Este método es infalible porque no requiere 'scrapear' la web, solo llama a la imagen por su ID.")
