import streamlit as st
import random
import time

st.set_page_config(page_title="LPF Sandbox", layout="wide")

st.title("⚽ Simulación de Partido: Azar Total")

# --- SIDEBAR: CONFIGURACIÓN ---
st.sidebar.header("Ajustes del Sandbox")
mi_club = st.sidebar.text_input("Tu Club", "Estudiantes LP")
rival_nombre = st.sidebar.text_input("Rival", "Gimnasia LP")

col_prev_1, col_prev_2 = st.sidebar.columns(2)
poder_local_ini = col_prev_1.number_input(f"Poder {mi_club}", 100, 1000, 750)
poder_rival_ini = col_prev_2.number_input(f"Poder {rival_nombre}", 100, 1000, 720)

# --- ESPACIO DE JUEGO ---
if st.button("🏟️ PITAZO INICIAL"):
    # Contenedores para que la info no salte
    marcador_spot = st.empty()
    progreso_tiempo = st.progress(0)
    
    col1, col2 = st.columns([2, 1])
    with col1:
        cronica = st.container(height=400)
    with col2:
        st.write("📊 **Estado de los Planteles**")
        stats_vivas = st.empty()
    
    goles_l, goles_v = 0, 0
    p_local = float(poder_local_ini)
    p_rival = float(poder_rival_ini)

    # --- MOTOR DE 90 MINUTOS ---
    for min in range(1, 92):
        # Velocidad de los minutos (ajustable para realismo)
        time.sleep(0.08) 
        
        # 1. ACTUALIZAR INTERFAZ (Marcador y Barras)
        marcador_spot.markdown(f"<h1 style='text-align: center;'>{mi_club} {goles_l} - {goles_v} {rival_nombre}</h1>", unsafe_allow_html=True)
        progreso_tiempo.progress(min / 90 if min <= 90 else 1.0)
        
        stats_vivas.markdown(f"""
            **{mi_club}**: {int(p_local)} ⚡  
            **{rival_nombre}**: {int(p_rival)} ⚡
        """)

        # 2. EL DADO DE 1000 CARAS (Acción General)
        dado = random.randint(1, 1000)
        
        # 3. LÓGICA DE MINUTO A MINUTO
        
        # 🟢 NADA PASA (85% de probabilidad)
        if dado < 850:
            if min % 15 == 0: # Solo avisar cada tanto para no aburrir
                cronica.write(f"⏱️ {min}' - Mucha fricción en el medio. Nadie cede espacio.")
        
        # 🟡 PELIGRO (10% de probabilidad)
        elif 850 <= dado < 950:
            if random.random() > 0.5:
                cronica.write(f"⚠️ {min}' - ¡Llegó el Pincha! Pero el remate salió desviado.")
            else:
                cronica.write(f"⚠️ {min}' - El rival presiona alto, casi recuperan en el área.")
        
        # 🔴 CHANCE CLARA / GOL (5% de probabilidad)
        else:
            # Choque de Dados Individuales + Poder
            tiro_l = p_local + random.randint(1, 200)
            tiro_v = p_rival + random.randint(1, 200)
            
            if tiro_l > tiro_v + 100:
                goles_l += 1
                cronica.write(f"⚽ **{min}' - ¡GOOOOOL DE {mi_club.upper()}!**")
                st.toast("¡GOL!")
            elif tiro_v > tiro_l + 100:
                goles_v += 1
                cronica.write(f"💀 **{min}' - ¡GOL DE {rival_nombre.upper()}!**")
            else:
                cronica.write(f"🧤 {min}' - ¡Atajadón! Se salvaron de milagro.")

        # 4. DESGASTE FÍSICO (Sandbox)
        # El equipo local se cansa un poco más si va ganando (presión)
        p_local -= random.uniform(0.1, 0.5)
        p_rival -= random.uniform(0.1, 0.5)

    st.success("🏁 Final del encuentro.")
