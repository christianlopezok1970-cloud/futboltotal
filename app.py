import streamlit as st
import random
import time

# 1. CONFIGURACIÓN DE LA PÁGINA
st.set_page_config(page_title="Sandbox LPF", layout="centered")

st.title("🏟️ Argentina Football Sandbox")
st.caption("Motor de azar de 1000 caras - Versión: Gestión de Crisis")

# 2. ENTRADAS DE DATOS (SIDEBAR)
# Definimos las variables antes del botón para que el código las reconozca
st.sidebar.header("Configuración del Clásico")
mi_club = st.sidebar.text_input("Tu Club", "Estudiantes LP")
rival = st.sidebar.text_input("Rival", "Gimnasia LP")

p_loc_ini = st.sidebar.slider(f"Poder {mi_club}", 100, 1000, 750)
p_riv_ini = st.sidebar.slider(f"Poder {rival}", 100, 1000, 720)

# 3. LÓGICA DEL PARTIDO
if st.button("🏁 INICIAR SIMULACIÓN"):
    # Espacios dinámicos en la interfaz
    marcador = st.empty()
    progreso = st.progress(0)
    cronica = st.container()
    
    # Inicializamos variables internas del partido
    g_l, g_v = 0, 0
    p_l = float(p_loc_ini)
    p_r = float(p_riv_ini)
    
    # Bucle de 90 minutos (más tiempo extra aleatorio)
    tiempo_total = 90 + random.randint(3, 6)
    
    for minuto in range(1, tiempo_total + 1):
        # El dado de 1000 caras
        dado = random.randint(1, 1000)
        
        # --- CONTROL DE VELOCIDAD ---
        if dado > 940:
            time.sleep(1.0) # Pausa para leer evento
        else:
            time.sleep(0.03) # El resto del tiempo vuela
            
        # --- ACTUALIZAR MARCADOR Y BARRA ---
        marcador.markdown(f"""
            <div style="text-align: center; background-color: #1e1e1e; padding: 20px; border-radius: 10px; border: 2px solid #ff4b4b;">
                <h1 style="color: white; margin: 0;">{mi_club} {g_l} — {g_v} {rival}</h1>
                <p style="color: #888; margin: 0;">Minuto {minuto}</p>
            </div>
            """, unsafe_allow_html=True)
        
        progreso.progress(min(minuto / 90, 1.0))

        # --- MOTOR DE EVENTOS (FILTRADO) ---
        
        # A. CHANCE DE GOL (Dado 941-1000)
        if dado > 940:
            ataque = p_l + random.randint(1, 500)
            defensa = p_r + random.randint(1, 500)
            
            # Diferencial de 135 para realismo (pocos goles, mucha tensión)
            if ataque > (defensa + 135):
                g_l += 1
                cronica.error(f"⚽ **{minuto}' - ¡GOOOOOL!** {mi_club} sacudió la red tras una gran jugada.")
                st.toast(f"¡GOL DE {mi_club.upper()}!")
            elif defensa > (ataque + 135):
                g_v += 1
                cronica.error(f"💀 **{minuto}' - ¡GOL!** {rival} aprovecha un contraataque letal.")
            else:
                frases_atajada = ["¡Casi! El remate se va besando el palo.", "¡Espectacular! El arquero vuela y salva el gol.", "¡Travesaño! El estadio es un suspiro."]
                cronica.info(f"🧤 **{minuto}' - {random.choice(frases_atajada)}**")

        # B. INCIDENTES (Dado 500-505)
        elif 500 <= dado <= 505:
            if random.random() > 0.5:
                cronica.warning(f"🟥 **{minuto}' - ¡EXPULSIÓN!** El árbitro saca la roja directa.")
                p_l -= 120 # Perder un jugador baja mucho el poder
            else:
                cronica.warning(f"🚑 **{minuto}' - ¡LESIÓN!** El partido se detiene por un jugador caído.")
                p_r -= 60

        # C. EL "VAR" / PENAL (Dado 777)
        elif dado == 777:
            equipo_penal = mi_club if random.random() > 0.5 else rival
            cronica.warning(f"📢 **{minuto}' - ¡PENAL!** El VAR confirma falta para {equipo_penal}.")
            time.sleep(1.5)
            if random.random() > 0.25: # 75% de probabilidad
                if equipo_penal == mi_club: g_l += 1
                else: g_v += 1
                cronica.error(f"🎯 **{minuto}' - ¡GOL DE PENAL!** Definición con clase.")
            else:
                cronica.info(f"❌ **{minuto}' - ¡LO ERRÓ!** La pelota salió desviada.")

        # --- DESGASTE DE ENERGÍA ---
        p_l -= 0.5
        p_r -= 0.5

    st.success(f"🏁 Final del partido en el Estadio Virtual. Marcador definitivo: {g_l} - {g_v}")
