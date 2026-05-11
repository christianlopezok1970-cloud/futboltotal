import streamlit as st
import random
import time

st.title("🎲 Sandbox Engine: Minuto a Minuto Realista")

# Configuración inicial
poder_actual = st.sidebar.slider("Poder inicial del equipo", 500, 1000, 750)
rival_poder = 720

if st.button("🎬 INICIAR PARTIDO"):
    cronica = st.container(height=450)
    marcador = st.empty()
    
    goles_l, goles_v = 0, 0
    
    # Simulación de 90 minutos (paso de 1 en 1 o 5 en 5)
    for minuto in range(1, 91):
        time.sleep(0.1) # Velocidad de la simulación
        
        # 1. EL DADO DE ACCIÓN (1000 caras)
        dado = random.randint(1, 1000)
        
        # 2. EFECTO FATIGA: El poder baja un poquito cada minuto
        poder_actual -= 0.5 
        
        # 3. LÓGICA DE EVENTOS (El "Embudo" de probabilidades)
        
        # RANGO DE NADA: Del 1 al 850 (85% de los minutos no pasa nada)
        if dado < 850:
            # Solo mostramos mensaje en minutos clave para no saturar
            if minuto % 10 == 0:
                cronica.write(f"⏱️ {minuto}' - Juego trabado en el mediocampo...")
            continue # Salta al siguiente minuto sin hacer nada
            
        # RANGO DE PELIGRO: Del 851 al 980 (Aproximaciones)
        elif 851 <= dado <= 980:
            if random.random() > 0.5:
                cronica.write(f"⚠️ {minuto}' - ¡Aviso de {st.session_state.get('club_nombre', 'Local')}! Remate desviado.")
            else:
                cronica.write(f"⚠️ {minuto}' - Centro peligroso del rival que despeja la defensa.")
        
        # RANGO DE GOL: Del 981 al 1000 (Solo el 2% de los minutos son chances claras)
        else:
            # Aquí choca el poder contra el azar
            ataque = poder_actual + random.randint(1, 200)
            defensa = rival_poder + random.randint(1, 200)
            
            if ataque > defensa:
                goles_l += 1
                cronica.write(f"⚽ **{minuto}' - ¡GOOOOOOL!** Jugada magistral de contraataque.")
                st.balloons()
            else:
                cronica.write(f"🧤 {minuto}' - ¡Era el gol! Pero el arquero rival tuvo una reacción heróica.")

        # Actualizar marcador en tiempo real
        marcador.metric("MARCADOR", f"{goles_l} - {goles_v}", delta=f"Poder: {int(poder_actual)}")

    st.success(f"Final del partido: {goles_l} - {goles_v}")
