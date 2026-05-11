
import streamlit as st
import random
import time

if st.button("🏁 INICIAR PARTIDO"):
    # --- Todo esto debe tener 4 espacios de sangría ---
    marcador = st.empty()
    progreso = st.progress(0)
    cronica = st.container()
    
    g_l, g_v = 0, 0
    p_l, p_r = float(p_loc_ini), float(p_riv_ini)
    
    # El 'for' debe estar alineado con 'marcador', 'progreso', etc.
    for minuto in range(1, 96):
        dado = random.randint(1, 1000)
        
        # --- Lo que está dentro del 'for' tiene 8 espacios (4 del if + 4 del for) ---
        if dado > 940:
            time.sleep(1.2)
        else:
            time.sleep(0.05)
            
        marcador.markdown(f"<h1 style='text-align: center;'>{mi_club} {g_l} — {g_v} {rival}</h1>", unsafe_allow_html=True)
        progreso.progress(min(minuto / 90, 1.0))

        if dado > 940:
            ataque = p_l + random.randint(1, 500)
            defensa = p_r + random.randint(1, 500)
            
            if ataque > (defensa + 130):
                g_l += 1
                cronica.error(f"⚽ **{minuto}' - ¡GOOOOOL!** {mi_club} aprovecha un hueco.")
            elif defensa > (ataque + 130):
                g_v += 1
                cronica.error(f"💀 **{minuto}' - ¡GOL!** {rival} golpea de contra.")
            else:
                cronica.info(f"🧤 **{minuto}' - ¡CERCA!** El arquero desvía al córner.")
