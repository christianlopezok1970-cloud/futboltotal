# --- 6. LÓGICA DE JUEGO (RECONSTRUIDO) ---
st.markdown("### ⚽ VIRTUAL DT PRO")

c1, c2 = st.columns(2)
c1.metric("Presupuesto Actual", f"{int(monedas)} 🪙")

# --- NUEVO SISTEMA DE RESCATE: FICHAJE DE EMERGENCIA (ANTI-TRAMPA) ---
total_jugadores = len(titulares) + len(suplentes)
# Calculamos valor de reventa bajo para que no sea negocio vender el regalo
valor_club = sum([int(j[2]) * 15 for j in jugadores_db])

# Se activa si: No completa 11, No tiene 50 monedas, NO TIENE SUPLENTES y el club es pobre
if monedas < 50 and total_jugadores < 11 and len(suplentes) == 0 and (monedas + valor_club) < 50:
    st.error("🚨 CRISIS DE PLANTILLA: No tienes fondos para completar los 11 titulares.")
    
    posiciones_actuales = [j[1] for j in titulares]
    # Formación base para detectar el hueco
    formacion_ideal = ['ARQ', 'DEF', 'DEF', 'DEF', 'DEF', 'VOL', 'VOL', 'VOL', 'VOL', 'DEL', 'DEL']
    
    posicion_faltante = None
    temp_pos = posiciones_actuales.copy()
    for p in formacion_ideal:
        if p in temp_pos:
            temp_pos.remove(p)
        else:
            posicion_faltante = p
            break
            
    if posicion_faltante:
        with st.expander(f"SOLICITAR REFUERZO GRATUITO ({posicion_faltante})"):
            st.write(f"La liga te asignará un jugador de **Nivel 1** en la posición de **{posicion_faltante}** para que puedas competir.")
            if st.button("Fichar Refuerzo de Emergencia"):
                # Filtramos el Excel por posición y Nivel 1
                pool = df_base[(df_base['POS'] == posicion_faltante) & (df_base['Nivel'] == 1)]
                if pool.empty:
                    pool = df_base[df_base['POS'] == posicion_faltante].sort_values('Nivel')

                if not pool.empty:
                    n = pool.sample(n=1).iloc[0]
                    # Insertamos directamente como titular y forzamos Nivel 1
                    ejecutar_db("""INSERT INTO plantilla 
                                (usuario_id, jugador_nombre, posicion, nivel, equipo, score, es_titular) 
                                VALUES (?,?,?,1,?,?,1)""", 
                                (u_id, n['Jugador'], n['POS'], n['Equipo'], float(n['Score'])), 
                                commit=True)
                    st.success(f"¡{n['Jugador']} (Nivel 1) se ha unido al equipo!")
                    st.rerun()

# --- LÓGICA DE COBRO (Solo si hay 11 titulares) ---
if len(titulares) == 11:
    ganancia = sum([int((j[4]-64)*3) if j[4]>=65 else int(j[4]-65) for j in titulares])
    c2.markdown(f"**Balance Jornada:** {ganancia} 🪙")
    if 'c_cobro' not in st.session_state: st.session_state.c_cobro = False
    
    if not st.session_state.c_cobro:
        if c2.button("💰 COBRAR JORNADA", use_container_width=True):
            st.session_state.c_cobro = True
            st.rerun()
    else:
        if c2.button("⚠️ CONFIRMAR COBRO", type="primary", use_container_width=True):
            ejecutar_db("UPDATE usuarios SET monedas = monedas + ? WHERE id = ?", (ganancia, u_id), commit=True)
            st.session_state.c_cobro = False
            st.rerun()
        if c2.button("Cancelar"):
            st.session_state.c_cobro = False
            st.rerun()
else:
    c2.warning(f"Faltan {11 - len(titulares)} titulares para cobrar")

# --- OFICINA DE PRESTIGIO ---
with st.expander("💎 Oficina de Prestigio"):
    st.write(f"Prestigio: **{prestigio} pts**")
    if st.button(f"Comprar 1 Pto (500 🪙)", use_container_width=True):
        if monedas >= 500:
            ejecutar_db("UPDATE usuarios SET monedas = monedas - 500, prestigio = prestigio + 1 WHERE id = ?", (u_id,), commit=True)
            st.rerun()
        else: st.error("No tienes monedas suficientes.")
