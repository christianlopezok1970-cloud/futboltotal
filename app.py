import streamlit as st
import random

# CONFIGURACIÓN
st.set_page_config(page_title="LPF Pack Opener", page_icon="⚽")

# --- BASE DE DATOS LOCAL (Aquí metes a todos los que quieras) ---
# He incluido una lista representativa de la Liga Profesional Argentina
mazo_lpf = [
    # ESTUDIANTES LP
    {"n": "Enzo Pérez", "id": "183894", "r": 77, "c": "Estudiantes LP"},
    {"n": "Santiago Ascacíbar", "id": "235165", "r": 77, "c": "Estudiantes LP"},
    {"n": "Edwuin Cetré", "id": "242426", "r": 76, "c": "Estudiantes LP"},
    {"n": "Guido Carrillo", "id": "208115", "r": 76, "c": "Estudiantes LP"},
    # RIVER
    {"n": "Franco Armani", "id": "193080", "r": 81, "c": "River Plate"},
    {"n": "Miguel Borja", "id": "205362", "r": 78, "c": "River Plate"},
    {"n": "Claudio Echeverri", "id": "275916", "r": 74, "c": "River Plate"},
    # BOCA
    {"n": "Edinson Cavani", "id": "179813", "r": 79, "c": "Boca Juniors"},
    {"n": "Kevin Zenón", "id": "262854", "r": 77, "c": "Boca Juniors"},
    {"n": "Luis Advíncula", "id": "203019", "r": 76, "c": "Boca Juniors"},
    # RACING
    {"n": "Juanfer Quintero", "id": "202548", "r": 79, "c": "Racing Club"},
    {"n": "Maravilla Martínez", "id": "274643", "r": 77, "c": "Racing Club"},
    # TALLERES / SAN LORENZO / OTROS
    {"n": "Guido Herrera", "id": "235213", "r": 77, "c": "Talleres"},
    {"n": "Adam Bareiro", "n2": "River Plate", "id": "244675", "r": 77, "c": "San Lorenzo"},
    {"n": "Nahuel Losada", "id": "260123", "r": 76, "c": "Belgrano"}
]

def obtener_imagen(player_id):
    """
    Construye la URL de la imagen usando el CDN de SoFIFA, que es más estable.
    """
    # Formato de URL de SoFIFA: id con ceros a la izquierda
    id_str = str(player_id).zfill(6)
    return f"https://cdn.sofifa.net/players/{id_str[:3]}/{id_str[-3:]}/24_120.png"

# --- INTERFAZ ---
st.title("🇦🇷 Sobre de la Liga Profesional")
st.write(f"Jugadores disponibles en el mazo: {len(mazo_lpf)}")

if st.button("✨ ABRIR SOBRE (50 🪙)"):
    # Selección aleatoria
    j = random.choice(mazo_lpf)
    
    # Lógica de estrellas (15 monedas por estrella)
    if j['r'] >= 80: estrellas, nivel = "⭐⭐⭐⭐", 4
    elif j['r'] >= 75: estrellas, nivel = "⭐⭐⭐", 3
    else: estrellas, nivel = "⭐⭐", 2
    
    valor_venta = nivel * 15

    # Mostrar resultado
    with st.spinner("¡Abriendo sobre!"):
        st.balloons()
        
        # Usamos columnas para diseño limpio
        col1, col2 = st.columns([1, 1.5])
        
        with col1:
            # Intentamos cargar la imagen de SoFIFA
            st.image(obtener_imagen(j['id']), width=150)
            
        with col2:
            st.header(j['n'])
            st.write(f"🏠 **Club:** {j['c']}")
            st.write(f"📊 **Rating:** {j['r']}")
            st.metric("Nivel", estrellas)
            st.metric("Valor Venta", f"{valor_venta} 🪙")
            
        st.success(f"¡Has fichado a {j['n']}!")

st.divider()
st.info("Para que aparezcan 'todos' los jugadores, simplemente debemos seguir alimentando la lista 'mazo_lpf' con los nombres e IDs de SoFIFA.")
