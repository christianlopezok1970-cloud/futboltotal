import streamlit as st
import random

# --- 1. BASE DE DATOS LOCAL (El listado que "vive" en el código) ---
# Aquí puedes meter cientos de jugadores siguiendo este formato.
# Los IDs son los que aparecen en la URL de Futbin.
lista_estudiantes = [
    {"nombre": "Enzo Pérez", "id": "183894", "rat": 77},
    {"nombre": "Santiago Ascacíbar", "id": "235165", "rat": 77},
    {"nombre": "Guido Carrillo", "id": "208115", "rat": 76},
    {"nombre": "Edwuin Cetré", "id": "242426", "rat": 76},
    {"nombre": "José Sosa", "id": "163155", "rat": 75},
    {"nombre": "Federico Fernández", "id": "192362", "rat": 74},
    {"nombre": "Luciano Lollo", "id": "192361", "rat": 73},
    {"nombre": "Gastón Benedetti", "id": "273344", "rat": 73},
    {"nombre": "Eros Mancuso", "id": "268305", "rat": 73},
    {"nombre": "Tiago Palacios", "id": "258957", "rat": 72},
    {"nombre": "Matías Mansilla", "id": "261947", "rat": 72},
    {"nombre": "Javier Correa", "id": "222452", "rat": 74}
]

# --- 2. FUNCIÓN PARA MOSTRAR LA CARTA (TRUCO ANTIBLOQUEO) ---
def mostrar_carta(player_id):
    # Usamos una URL de servidor de imágenes que suele tener menos bloqueos
    # o el CDN directo.
    url = f"https://www.futbin.com/content/fifa26/players/{player_id}.png"
    
    # Este HTML ayuda a que el navegador cargue la imagen ignorando algunas restricciones
    st.markdown(
        f"""
        <div style="display: flex; justify-content: center;">
            <img src="{url}" width="300" style="filter: drop-shadow(0px 10px 15px rgba(0,0,0,0.5));">
        </div>
        """, 
        unsafe_allow_html=True
    )

# --- 3. INTERFAZ ---
st.title("🇦🇹 Pack Opener: Estudiantes LP")

if st.button("🧧 ABRIR SOBRE (50 🪙)"):
    # Elegir al azar de la lista interna
    jugador = random.choice(lista_estudiantes)
    
    # Procesar lógica de niveles (15 monedas por estrella)
    # Ejemplo: 75+ = 3 estrellas (45 coins), 80+ = 4 estrellas (60 coins)
    if jugador['rat'] >= 80: estrellas, nivel = "⭐⭐⭐⭐", 4
    elif jugador['rat'] >= 75: estrellas, nivel = "⭐⭐⭐", 3
    else: estrellas, nivel = "⭐⭐", 2
    
    valor_venta = nivel * 15
    
    # Mostrar resultados
    with st.spinner("¡Cargando carta...!"):
        st.balloons()
        mostrar_carta(jugador['id'])
        
        st.markdown(f"<h2 style='text-align: center;'>{jugador['nombre']}</h2>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        col1.metric("Rating", jugador['rat'])
        col1.write(f"Calidad: {estrellas}")
        
        col2.metric("Valor Mercado", f"{valor_venta} 🪙")
        col2.info(f"Nivel de carta: {nivel}")
