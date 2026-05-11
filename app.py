import streamlit as st
import random
import time

st.set_page_config(page_title="LPF Chaos Engine", layout="wide")

# --- VARIABLES DE ENTRADA ---
st.title("🎲 Sandbox Engine: El Producto Edition")
st.sidebar.header("Variables del Clásico")

mi_club = st.sidebar.text_input("Tu Club", "Estudiantes LP")
rival_nombre = st.sidebar.text_input("Rival", "Gimnasia LP")
p_loc_ini = st.sidebar.slider(f"Poder {mi_club}", 100, 1000, 750)
p_riv_ini = st.sidebar.slider(f"Poder {rival_nombre}", 100, 1000, 720)

if st.button("🏁 INICIAR CAOS"):
    marcador_spot = st.empty()
    progreso = st.progress(0)
    col1, col2 = st.columns([2, 1])
    
    with col1: cronica = st.container(height=450)
    with col2: stats_vivas = st.empty()
    
    g_l, g_v = 0, 0
    p_l, p_r = float(p_loc_ini), float(p_riv_ini)

    for minuto in range(1, 96): # 90 min + descuento
        dado = random.randint(1, 1000)
        
        # --- PAUSAS DINÁMICAS ---
        if dado > 900: espera = 0.8 # Evento importante
        elif dado > 700: espera = 0.4 # Algo de acción
        else: espera = 0.05 # Relleno (vuela)
        time.sleep(espera)
        
        # --- UI UPDATE ---
        marcador_spot.markdown(f"<h1 style='text-align: center; color: white; background: #222; border-radius: 10px;'>{mi_club} {g_l} — {g_v} {rival_nombre}</h1>", unsafe_allow_html=True)
        progreso.progress(min(minuto / 90, 1.0))
        
        stats_vivas.markdown(f"**Energía {mi_club}:** {int(p_l)}⚡\n\n**Energía {rival_nombre}:** {int(p_r)}⚡")

        # --- LÓGICA DE VARIABLES (EL DADO DE 1000) ---
        
        # 1. EL "VAR" O PENAL (Evento raro: 1-15)
        if dado <= 15:
            equipo_fav = mi_club if random.random() > 0.5 else rival_nombre
            cronica.warning(f"📢 {minuto}' - ¡PENAL! El árbitro cobra falta en el área para {equipo_fav}.")
            time.sleep(1)
            if random.randint(1, 100) > 20: # 80% de chance de gol
                if equipo_fav == mi_club: g_l += 1
                else: g_v += 1
                cronica.error(f"⚽ {minuto}' - ¡GOL DE PENAL!")
                st.toast("¡GOL!")
            else:
                cronica.info(f"🧤 {minuto}' - ¡LO ATAJÓ! El arquero es héroe.")

        # 2. ACCIÓN DE GOL (Dado 930-1000: más chances)
        elif dado >= 930:
            # Duelo de dados (recalibrado para que sea más fácil meter gol)
            suerte_l = random.randint(1, 400)
            suerte_v = random.randint(1, 400)
            
            # El ataque local (p_l) contra defensa rival (p_r)
            if (p_l + suerte_l) > (p_r + suerte_v + 80): 
                g_l += 1
                cronica.error(f"⚽ {minuto}' - ¡GOOOOOL! Gran jugada colectiva de {mi_club}.")
                st.balloons()
            elif (p_r + suerte_v) > (p_l + suerte_l + 80):
                g_v += 1
                cronica.error(f"💀 {minuto}' - ¡GOL! {rival_nombre} aprovecha un descuido.")
            else:
                cronica.write(f"🧤 {minuto}' - ¡UHHHH! El palo salvó al arquero.")

        # 3. LESIÓN O ROJA (Dado 500-510)
        elif 500 <= dado <= 510:
            if random.random() > 0.5:
                cronica.warning(f"🟥 {minuto}' - ¡EXPULSIÓN! {mi_club} se queda con 10.")
                p_l -= 150 # Golpe duro al poder
            else:
                cronica.warning(f"🚑 {minuto}' - ¡Lesión! {rival_nombre} debe hacer un cambio obligado.")
                p_r -= 80

        # 4. RELLENO
        elif minuto % 15 == 0:
            cronica.write(f"⏱️ {minuto}' - El partido entra en una meseta.")

        # --- DESGASTE NATURAL ---
        p_l -= random.uniform(0.5, 1.2)
        p_r -= random.uniform(0.5, 1.2)

    st.success(f"Final del partido. Marcador: {g_l} - {g_v}")
