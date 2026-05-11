import streamlit as st
import requests
from bs4 import BeautifulSoup

# Configuración visual
st.set_page_config(page_title="Futbin Card Opener", page_icon="⚽")

def obtener_datos_futbin(url):
    """
    Función que 'scrapea' Futbin para obtener la imagen y el nombre del jugador.
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 1. Extraer la URL de la imagen de la carta
        # Buscamos la etiqueta img que contiene la carta
        img_tag = soup.find('img', {'id': 'player_card'})
        image_url = img_tag['src'] if img_tag else None
        
        # 2. Extraer el Rating (como ejemplo de dato extra)
        rating_tag = soup.find('div', {'class': 'pcdisplay-rat'})
        rating = rating_tag.text.strip() if rating_tag else "S/N"
        
        return image_url, rating
    except Exception as e:
        return None, str(e)

# --- INTERFAZ DE USUARIO ---
st.title("🧧 Apertura de Sobre Especial")
st.write("Presiona el botón para conectar con el mercado de Futbin y traer la carta.")

# Link de ejemplo (Cetré)
url_cetre = "https://www.futbin.com/26/player/15945/edwuin-cetre"

if st.button("✨ ABRIR SOBRE: EDWUIN CETRÉ"):
    with st.spinner("Conectando con servidores de EA/Futbin..."):
        img_url, rat = obtener_datos_futbin(url_cetre)
        
        if img_url:
            # Mostramos la carta
            st.balloons() # Efecto de celebración
            
            col1, col2 = st.columns([1, 2])
            with col1:
                st.image(img_url, caption=f"Rating Oficial: {rat}")
            
            with col2:
                st.success("¡Jugador obtenido correctamente!")
                st.metric(label="Valor Base", value=f"{int(rat) * 1.5} 🪙") # Ejemplo de cálculo
                st.write("**Datos de Futbin:**")
                st.info(f"ID del Jugador: 15945")
        else:
            st.error("No se pudo obtener la carta. Verifica la conexión o el link.")

# Instrucciones para el usuario
st.divider()
st.caption("Este código utiliza Web Scraping para traer contenido dinámico desde Futbin.com")
