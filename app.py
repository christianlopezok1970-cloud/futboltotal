import streamlit as st
import pandas as pd
import requests
from bs4 import BeautifulSoup
import random

# Configuración
st.set_page_config(page_title="SoFIFA LPF Pack Opener", layout="centered")

def obtener_mazo_lpf():
    """
    Entra a SoFIFA y extrae la lista completa de jugadores de la liga argentina.
    """
    url = "https://sofifa.com/league/353"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        jugadores = []
        # Buscamos la tabla de jugadores
        table = soup.find('table', {'class': 'table-hover'})
        rows = table.find_all('tr')[1:] # Saltamos el encabezado
        
        for row in rows:
            cols = row.find_all('td')
            if len(cols) > 1:
                # Extraer datos
                nombre_tag = cols[1].find('a', {'data-tooltip': True})
                nombre = nombre_tag.text if nombre_tag else "Jugador Desconocido"
                
                id_jugador = cols[1].find('img')['id'] if cols[1].find('img') else ""
                
                rating = int(cols[2].find('span').text) if cols[2].find('span') else 0
                
                club = cols[1].find('div', {'class': 'sub'}).find('a').text if cols[1].find('div', {'class': 'sub'}) else "Sin Club"
                
                jugadores.append({
                    "nombre": nombre,
                    "id": id_jugador,
                    "rating": rating,
                    "club": club
                })
        return jugadores
    except Exception as e:
        st.error(f"Error al conectar con SoFIFA: {e}")
        return []

# --- INTERFAZ ---
st.title("🇦🇷 Sobre Infinito: Liga Profesional")
st.write("Datos sincronizados en tiempo real con SoFIFA")

if st.button("✨ ABRIR SOBRE DE LA LIGA (50 🪙)"):
    with st.spinner("Buscando en la base de datos de la AFA..."):
        mazo = obtener_mazo_lpf()
        
        if mazo:
            jugador = random.choice(mazo)
            
            # Construir la URL de la imagen de SoFIFA
            # El patrón de SoFIFA es: https://cdn.sofifa.net/players/{id_corto}/{id_largo}/24_120.png
            # Para simplificar, usaremos un placeholder de carta si la imagen falla
            id_limpio = jugador['id'].zfill(6)
            url_foto = f"https://cdn.sofifa.net/players/{id_limpio[:3]}/{id_limpio[-3:]}/24_120.png"
            
            st.balloons()
            
            # Mostrar la carta
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # Intentamos mostrar la foto del jugador
                st.image(url_foto, width=150, caption=jugador['nombre'])
            
            with col2:
                st.subheader(jugador['nombre'])
                st.write(f"🏠 **Club:** {jugador['club']}")
                st.write(f"📊 **Rating:** {jugador['rating']}")
                
                # Tu lógica de niveles
                rat = jugador['rating']
                if rat >= 80: estrellas, nivel = "⭐⭐⭐⭐", 4
                elif rat >= 75: estrellas, nivel = "⭐⭐⭐", 3
                else: estrellas, nivel = "⭐⭐", 2
                
                st.metric("Nivel", estrellas)
                st.metric("Valor Venta", f"{nivel * 15} 🪙")
        else:
            st.warning("No se pudo cargar el mazo. Intenta de nuevo.")
