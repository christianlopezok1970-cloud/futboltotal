import streamlit as st
import random
import time

st.set_page_config(page_title="Sandbox Solo Eventos", layout="centered")

st.title("🏟️ Simulación LPF: Modo Crónica Clave")
st.caption("Solo verás los eventos que cambian el destino del partido.")

# --- SIDEBAR ---
mi_club = st.sidebar.text_input("Tu Club", "Estudiantes LP")
rival = st.sidebar.text_input("Rival", "Gimnasia LP")
p_l = st.sidebar.slider(f"Poder {mi_club}", 100, 1000, 750)
p_r = st.sidebar.slider(f"Poder {rival}", 100, 1000, 720)

if st.button("🏁 INICIAR PARTIDO"):
    marcador = st.empty()
    progreso = st.progress(0)
    # Contenedor vacío para la crónica
    cronica = st.container()
    
    g_l, g_v = 0, 0
    
    # 90 minutos de pura adrenalina selectiva
    for min in range(1, 96):
        dado = random.randint(1, 1000)
        
        # --- VELOCIDAD ---
        # Si no pasa nada, el tiempo vuela. Si hay evento, pausamos para leer.
        if dado > 940:
            time.sleep(1.2)
        else:
            time.sleep(0.05)
            
        # --- ACTUALIZAR UI ---
        marcador.markdown(f"<h1 style='text-align: center;'>{mi_club} {g_l} — {g_v} {rival}</h1>", unsafe_allow_html=True)
        progreso.progress(min(min / 90, 1.0))

        # --- LÓGICA DE EVENTOS (FILTRADO) ---
        
        # 1. EVENTO DE GOL O ATAJADA (940-1000)
        if dado > 940:
            ataque = p_l + random.randint(1, 500)
            defensa = p_r + random.randint(1, 500)
            
            # Diferencial de 130 para hacerlo más difícil y realista
            if ataque > (defensa + 130):
                g_l += 1
                cronica.error(f"⚽ **{min}' - ¡GOOOOOL!** {mi_club} aprovecha un hueco y define cruzado.")
                st.toast(f"¡GOL DE {mi_club.upper()}!")
            elif defensa > (ataque + 130):
                g_v += 1
                cronica.error(f"💀 **{min}' - ¡GOL!** {rival} golpea de contraataque.")
            else:
                cronica.info(f"🧤 **{min}' - ¡CERCA!** El arquero desvía al córner un remate venenoso.")

        # 2. EVENTOS DISRUPTIVOS (Roja o Lesión rara: 500-505)
        elif 500 <= dado <= 505:
            if random.random() > 0.5:
                cronica.warning(f"🟥 **{min}' - ¡EXPULSIÓN!** El árbitro no duda y saca la roja.")
            else:
                cronica.warning(f"🚑 **{min}' - ¡CAMBIO OBLIGADO!** Un jugador cae desplomado por un tirón.")

        # 3. PENALES (Rarísimo: 777)
        elif dado == 777:
            cronica.warning(f"📢 **{min}' - ¡PENAL!** Una mano en el área cambia todo el panorama.")
            time.sleep(1)
            if random.random() > 0.3:
                g_l += 1
                cronica.error(f"⚽ **{min}' - ¡DENTRO!** Ejecución perfecta desde los doce pasos.")
            else:
                cronica.info(f"🧤 **{min}' - ¡AFUERA!** El remate besó el poste y salió.")

        # --- AQUÍ NO HAY ELSE ---
        # Si el dado no entra en estos rangos, Streamlit no escribe nada.
        # El tiempo simplemente corre.

    st.success("🏁 Final del partido. ¡Gracias por usar el Sandbox!")
