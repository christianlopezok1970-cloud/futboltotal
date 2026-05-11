import streamlit as st
import random

# Configuración de estilo para que la carta se vea genial
st.markdown("""
    <style>
    .card-container {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        border: 2px solid #e03131;
    }
    </style>
    """, unsafe_allow_html=True)

# 1. LISTADO INTERNO (La base de datos que vive en tu código)
# Estos son los IDs reales de EA para Estudiantes de LP
mazo_estudiantes = [
    {"n": "Enzo Pérez", "id": "183894", "r": 77},
    {"n": "Santiago Ascacíbar", "id": "235165", "r": 77},
    {"n": "Edwuin Cetré", "id": "242426", "r": 76},
    {"n": "Guido Carrillo", "id": "208115", "r": 76},
    {"n": "José Sosa", "id": "163155", "r": 75},
    {"n": "Federico Fernández", "id": "192362", "r": 74},
    {"n": "Gastón Benedetti", "id": "273344", "r": 73},
    {"n": "Eros Mancuso", "id": "268305", "r": 73},
    {"n": "Tiago Palacios", "id": "258957", "r": 72},
    {"n": "Matías Mansilla", "id": "261947", "r": 72}
]

st.title("🇦🇹 Pincha Pack Opener")

if st.button("✨ ABRIR SOBRE DE ESTUDIANTES"):
    jugador = random.choice(mazo_estudiantes)
    
    # ESTRATEGIA DEFINITIVA: Usar el render de cartas de EA
    # Esta URL es la que usan las aplicaciones oficiales, es la más estable.
    url_foto = f"https://ratings-images-prod.asindcontent.g3.easports.com/FC25/full/player-portraits/p{jugador['id']}.png"
    
    with st.spinner("¡Buscando en el Country de City Bell...!"):
        st.balloons()
        
        # Usamos un contenedor visual
        st.markdown(f"""
            <div class="card-container">
                <img src="{url_foto}" width="200" style="margin-bottom: 10px;">
                <h2 style="color: #333;">{jugador['n']}</h2>
                <p style="font-size: 20px; color: #666;">Rating: <b>{jugador['r']}</b></p>
            </div>
        """, unsafe_allow_html=True)
        
        # Tu lógica de negocio para Futbol Total - Pro
        rat = jugador['r']
        nivel = 3 if rat >= 75 else 2
        valor = nivel * 15
        
        col1, col2 = st.columns(2)
        col1.metric("Calidad", f"{nivel} ⭐")
        col2.metric("Valor Mercado", f"{valor} 🪙")

st.info("Nota: Si la imagen no aparece, es porque EA cambió el ID para FC26. En ese caso, usamos un generador de cartas local.")
