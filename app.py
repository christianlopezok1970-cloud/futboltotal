import streamlit as st
import random
import time

# --- CONFIGURACIÓN DE INTERFAZ ---
st.set_page_config(page_title="Argentina Sandbox Engine", layout="wide")

st.title("🎲 Motor de Azar: El Dado de 1000 Caras")
st.sidebar.header("Configuración del Sandbox")

# --- VARIABLES DE ENTRADA ---
club_local = st.sidebar.text_input("Tu Club", "Estudiantes LP")
rival = st.sidebar.text_input("Rival", "Gimnasia LP")
poder_local = st.sidebar.slider("Poder de tu plantel (1-1000)", 100, 1000, 750)
poder_rival = st.sidebar.slider("Poder del rival (1-1000)", 100, 1000, 720)

# --- EL MOTOR DEL PARTIDO ---
if st.button("🚀 INICIAR SIMULACIÓN DE PARTIDO"):
    st.divider()
    
    col1, col2 = st.columns([2, 1])
    
    goles_local = 0
    goles_rival = 0
    minuto = 0
    
    with col1:
        st.subheader(f"🏟️ Crónica en vivo: {club_local} vs {rival}")
        contenedor_cronica = st.container(height=400)
        
    with col2:
        st.subheader("📊 Marcador")
        pizarra = st.empty() # Espacio dinámico para el resultado
        grafico_azar = st.empty() # Espacio para ver las tiradas del dado
        historial_dados = []

    # BUCLE DE TIEMPO (Sandbox sim)
    for t in range(9): # 9 bloques de 10 minutos
        minuto += 10
        time.sleep(0.8) # Para darle suspenso
        
        # EL DADO DE 1000 CARAS RODANDO
        dado_local = random.randint(1, 1000)
        dado_rival = random.randint(1, 1000)
        
        # EL "AZAR PURO" (Eventos aleatorios fuera de rating)
        evento_azar = random.randint(1, 1000)
        
        # LÓGICA DE EVENTOS
        msg = ""
        # 1. Probabilidad de Gol Local
        # (Rating + Dado) vs (Rating + Dado)
        if (poder_local + dado_local) > (poder_rival + dado_rival + 400):
            goles_local += 1
            msg = f"⚽ **{minuto}' - ¡GOOOL DE {club_local.upper()}!** Una jugada magistral (Dado: {dado_local})"
        
        # 2. Probabilidad de Gol Rival
        elif (poder_rival + dado_rival) > (poder_local + dado_local + 400):
            goles_rival += 1
            msg = f"💀 **{minuto}' - Gol de {rival}.** Error defensivo fatal (Dado Rival: {dado_rival})"
            
        # 3. El Dado de Crisis (Eventos Extraños)
        elif evento_azar < 50:
            msg = f"🟥 {minuto}' - ¡ROJA! El azar decidió que tu central perdió los estribos."
            poder_local -= 100 # El sandbox se modifica en vivo
        
        elif evento_azar > 980:
            msg = f"🏥 {minuto}' - Lesión fortuita. Se retira tu figura entre lágrimas."
            poder_local -= 50
        
        else:
            frases_relleno = ["Pelea en el medio campo.", "Pase impreciso.", "Cánticos en la tribuna.", "El técnico da indicaciones."]
            msg = f"⏱️ {minuto}' - {random.choice(frases_relleno)} (Dados: {dado_local} vs {dado_rival})"

        # ACTUALIZAR INTERFAZ
        contenedor_cronica.write(msg)
        pizarra.metric("RESULTADO", f"{goles_local} - {goles_rival}")
        
        # Visualizar el azar
        historial_dados.append(dado_local)
        grafico_azar.line_chart(historial_dados)

    # RESULTADO FINAL
    if goles_local > goles_rival:
        st.success(f"¡FINAL! {club_local} ganó por la mística del dado.")
    elif goles_local < goles_rival:
        st.error(f"¡FINAL! El azar hundió a {club_local}.")
    else:
        st.warning("¡FINAL! Empate técnico en el arenero.")
