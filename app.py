import streamlit as st
import random
import time

st.set_page_config(page_title="Sandbox LPF", layout="wide")

# --- INTERFAZ ---
st.title("⚽ Simulador de Gestión Dinámica")
st.sidebar.header("Ajustes del Encuentro")

mi_club = st.sidebar.text_input("Tu Club", "Estudiantes LP")
rival_nombre = st.sidebar.text_input("Rival", "Gimnasia LP")

# Sliders para el poder
p_loc_ini = st.sidebar.slider(f"Poder {mi_club}", 100, 1000, 750)
p_riv_ini = st.sidebar.slider(f"Poder {rival_nombre}", 100, 1000, 720)

if st.button("🏟️ EMPEZAR SIMULACIÓN"):
    marcador_spot = st.empty()
    progreso = st.progress(0)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        cronica = st.container(height=450)
    with col2:
        stats_vivas = st.empty()
    
    g_l, g_v = 0, 0
    p_l, p_r = float(p_loc_ini), float(p_riv_ini)

    for minuto in range(1, 91):
        # 🎲 EL DADO DE 1000 CARAS
        dado = random.randint(1, 1000)
        
        # --- LÓGICA DE TIEMPO (Pausas dinámicas) ---
        if dado >= 850:
            espera = 1.2  # Pausa larga para eventos importantes
        else:
            espera = 0.15 # Minutos de relleno pasan rápido
        
        time.sleep(espera) 
        
        # --- ACTUALIZAR PANTALLA ---
        marcador_spot.markdown(f"<h1 style='text-align: center; color: #FF4B4B;'>{mi_club} {g_l} — {g_v} {rival_nombre}</h1>", unsafe_allow_html=True)
        progreso.progress(minuto / 90)
        
        stats_vivas.markdown(f"""
        ### Estado actual
        **{mi_club}**: {int(p_l)} pts  
        **{rival_nombre}**: {int(p_r)} pts
        ---
        *El cansancio reduce el poder cada minuto.*
        """)

        # --- EVENTOS ---
        if dado < 850:
            # Solo escribimos en la crónica cada tanto para no scrolear infinito
            if minuto % 10 == 0:
                cronica.write(f"⏱️ {minuto}' - El partido se juega lejos de las áreas.")
        
        elif 850 <= dado < 960:
            cronica.warning(f"⚠️ {minuto}' - ¡Peligro! El azar genera una aproximación clara.")
            
        else: # EL DADO TIRÓ CHANCE DE GOL (961-1000)
            # Duelo de dados finales
            tiro_l = p_l + random.randint(1, 300)
            tiro_v = p_r + random.randint(1, 300)
            
            if tiro_l > tiro_v + 150:
                g_l += 1
                cronica.error(f"⚽ {minuto}' - ¡GOOOOOL DE {mi_club.upper()}!")
                st.balloons()
                time.sleep(2) # Pausa de festejo
            elif tiro_v > tiro_l + 150:
                g_v += 1
                cronica.error(f"💀 {minuto}' - ¡GOL DE {rival_nombre.upper()}!")
                time.sleep(2) # Pausa de lamento
            else:
                cronica.info(f"🧤 {minuto}' - ¡TREMENDO! El arquero evita el gol en la línea.")
                time.sleep(1)

        # Desgaste
        p_l -= 0.6
        p_r -= 0.6

    st.success("🏁 Partido Finalizado.")
