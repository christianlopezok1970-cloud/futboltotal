# --- 4. MERCADO Y COMPRAS (SIN DUPLICADOS Y CON DESCUENTO REAL) ---
df_j = cargar_jugadores()
st.sidebar.metric("Presupuesto Disponible", f"€ {presupuesto:,.0f}")

with st.expander("🔍 BUSCAR Y FICHAR"):
    seleccion = st.selectbox("Mercado de Pases", [""] + df_j['Display'].tolist())
    if seleccion:
        jug = df_j[df_j['Display'] == seleccion].iloc[0]
        nombre_jugador = jug.iloc[0]
        costo = jug['ValorNum']
        
        st.info(f"Costo de fichaje: € {costo:,}")
        
        if st.button("CONFIRMAR OPERACIÓN"):
            # 1. Verificar si el jugador ya es propiedad de ALGUIEN
            duplicado = ejecutar_db("SELECT usuario_id FROM cartera WHERE nombre_jugador = ?", (nombre_jugador,))
            
            if duplicado:
                st.error(f"⚠️ El jugador {nombre_jugador} ya pertenece a otro equipo. No puede haber duplicados.")
            elif presupuesto < costo:
                st.error("❌ Fondos insuficientes para completar este fichaje.")
            else:
                # 2. PROCESO DE COMPRA (Restar dinero e insertar jugador)
                # Restamos el dinero al usuario en la tabla 'usuarios'
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (costo, u_id), commit=True)
                
                # Registramos al jugador en su 'cartera'
                ejecutar_db("""INSERT INTO cartera (usuario_id, nombre_jugador, club, posicion, estado) 
                               VALUES (?,?,?,?,?)""", 
                            (u_id, nombre_jugador, jug.iloc[1], jug['Posicion'], "Suplente"), commit=True)
                
                st.success(f"✅ ¡Fichaje estrella! {nombre_jugador} se ha unido a tu club.")
                st.balloons()
                st.rerun()
