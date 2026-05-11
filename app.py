import streamlit as st
import random
import time

# --- AJUSTE DE "LA MANO DEL DIOS AZAR" ---
# Subimos la valla para que no sea un festival de goles constante
def simular_clásico():
    st.title("⚽ Sandbox LPF: Calibración Realista")
    
    # Sidebar
    mi_club = st.sidebar.text_input("Tu Club", "Estudiantes LP")
    rival = st.sidebar.text_input("Rival", "Gimnasia LP")
    p_l = st.sidebar.slider(f"Poder {mi_club}", 100, 1000, 750)
    p_r = st.sidebar.slider(f"Poder {rival}", 100, 1000, 720)

    if st.button("🏟️ JUGAR PARTIDO"):
        cronica = st.container(height=400)
        marcador = st.empty()
        g_l, g_v = 0, 0
        
        for min in range(1, 95):
            dado = random.randint(1, 1000)
            
            # --- TIEMPO DINÁMICO ---
            # Si pasa algo, frenamos. Si no, vuela.
            time.sleep(0.5 if dado > 940 else 0.02)
            
            # --- EVENTO DE GOL (955-1000: Menos chances que antes) ---
            if dado > 955: 
                # Duelo: Poder + Dado de 500 caras
                # Aumentamos la diferencia necesaria a 120 para que sea gol
                ataque = p_l + random.randint(1, 500)
                defensa = p_r + random.randint(1, 500)
                
                if ataque > (defensa + 120):
                    g_l += 1
                    cronica.error(f"⚽ {min}' - ¡GOOOL! {mi_club} rompe el arco.")
                elif defensa > (ataque + 120):
                    g_v += 1
                    cronica.error(f"💀 {min}' - ¡GOL! Silencio en el estadio, anotó {rival}.")
                else:
                    frases_ataje = ["¡La sacó el arquero!", "¡Pegó en el travesaño!", "¡Casi! Se va por un pelo."]
                    cronica.info(f"🧤 {min}' - {random.choice(frases_ataje)}")

            # --- EVENTO DE PENAL (Más raro: 1-5) ---
            elif dado <= 5:
                cronica.warning(f"📢 {min}' - ¡PENAL! Tensión absoluta...")
                time.sleep(1)
                if random.random() > 0.25: # 75% gol
                    g_l += 1
                    cronica.error(f"⚽ {min}' - ¡ADENTRO! No perdonó de penal.")
                else:
                    cronica.info(f"🧤 {min}' - ¡LO ERRÓ! La tiró a la tribuna.")

            # --- RELLENO ---
            elif min % 20 == 0:
                cronica.write(f"⏱️ {min}' - El partido está muy cerrado en el medio.")

            # Actualizar marcador
            marcador.markdown(f"### {mi_club} {g_l} - {g_v} {rival}")

        st.success("🏁 Final del partido.")

simular_clásico()
