# --- 7. INTERFAZ PRINCIPAL ---
st.title("⚽ AFA Manager Pro 2026")

# Listado Superior: Titulares (Ahora más compacto)
st.subheader("🔝 Once Titular (1-4-4-2)")
if st.session_state.titulares:
    ordenar_titulares()
    df_t = pd.DataFrame(st.session_state.titulares)
    df_t['Rareza'] = df_t['Nivel'].apply(formato_nivel)
    
    # Cambiamos st.table por st.dataframe para que sea chico y uniforme
    st.dataframe(
        df_t[['POS', 'Jugador', 'Equipo', 'Rareza', 'Score']], 
        use_container_width=True, 
        hide_index=True,
        height=422 # Altura fija para que no sea gigante (aprox 11 filas)
    )
    
    quitar = st.selectbox("Mandar al banco:", [j['Jugador'] for j in st.session_state.titulares], key="q_tit")
    if st.button("Bajar al banco ⬇️"):
        idx = next(i for i, j in enumerate(st.session_state.titulares) if j['Jugador'] == quitar)
        st.session_state.suplentes.append(st.session_state.titulares.pop(idx))
        st.rerun()
else: 
    st.info("Armá tu equipo con los suplentes.")

st.divider()

# Listado Inferior: Suplentes
st.subheader("⏬ Banco de Suplentes")
if st.session_state.suplentes:
    df_s = pd.DataFrame(st.session_state.suplentes)
    df_s['Rareza'] = df_s['Nivel'].apply(formato_nivel)
    
    # Mantenemos st.dataframe pero ajustamos altura para uniformidad
    st.dataframe(
        df_s[['Jugador', 'POS', 'Rareza', 'Equipo']], 
        use_container_width=True, 
        hide_index=True,
        height=300 # Un poco más chico que el titular
    )

    c1, c2 = st.columns(2)
    # ... (el resto de los botones de Subir y Vender se mantienen igual)
