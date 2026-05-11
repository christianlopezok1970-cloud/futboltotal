# 90 minutos de pura adrenalina selectiva
    # CAMBIAMOS 'min' por 'minuto'
    for minuto in range(1, 96):
        dado = random.randint(1, 1000)
        
        # --- VELOCIDAD ---
        if dado > 940:
            time.sleep(1.2)
        else:
            time.sleep(0.05)
            
        # --- ACTUALIZAR UI ---
        marcador.markdown(f"<h1 style='text-align: center;'>{mi_club} {g_l} — {g_v} {rival}</h1>", unsafe_allow_html=True)
        
        # Ahora min() funciona perfecto porque no está 'pisada'
        progreso.progress(min(minuto / 90, 1.0))

        # --- LÓGICA DE EVENTOS (FILTRADO) ---
        if dado > 940:
            # Acordate de cambiar 'min' por 'minuto' en todos los f-strings de abajo
            ataque = p_l + random.randint(1, 500)
            defensa = p_r + random.randint(1, 500)
            
            if ataque > (defensa + 130):
                g_l += 1
                cronica.error(f"⚽ **{minuto}' - ¡GOOOOOL!** {mi_club} aprovecha un hueco.")
