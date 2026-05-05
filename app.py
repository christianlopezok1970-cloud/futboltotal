# --- 3. LOGIN Y GESTIÓN DE SESIÓN ---
with st.sidebar:
    st.title("🏆 Futbol Total")
    agente = st.text_input("Usuario").strip()
    clave = st.text_input("Clave", type="password").strip()

if not agente or not clave:
    st.info("Ingresa para gestionar tu equipo.")
    st.stop()

# Cargar datos del usuario
user_data = ejecutar_db("SELECT id, presupuesto FROM usuarios WHERE nombre = ?", (agente,))

if not user_data:
    ejecutar_db("INSERT INTO usuarios (nombre, password, presupuesto, prestigio) VALUES (?, ?, 2500000, 10)", (agente, clave), commit=True)
    st.rerun()

u_id, presupuesto_db = user_data[0]

# USAMOS SESSION_STATE para que el descuento sea instantáneo en la pantalla
if 'presupuesto' not in st.session_state:
    st.session_state.presupuesto = presupuesto_db

# --- 4. MERCADO (CON DESCUENTO GARANTIZADO) ---
df_j = cargar_jugadores()

# Mostrar el presupuesto de la sesión (el que se descuenta en vivo)
st.sidebar.metric("Presupuesto Disponible", f"€ {st.session_state.presupuesto:,.0f}")

with st.expander("🔍 BUSCAR Y FICHAR"):
    seleccion = st.selectbox("Mercado de Pases", [""] + df_j['Display'].tolist())
    
    if seleccion:
        jug = df_j[df_j['Display'] == seleccion].iloc[0]
        nombre_j = jug.iloc[0]
        costo = int(jug['ValorNum'])
        
        st.info(f"Costo: € {costo:,}")
        
        if st.button("CONFIRMAR OPERACIÓN"):
            # 1. Verificar duplicados en la base de datos
            existe = ejecutar_db("SELECT id FROM cartera WHERE nombre_jugador = ?", (nombre_j,))
            
            if existe:
                st.error(f"⚠️ {nombre_j} ya ha sido fichado por otro usuario.")
            elif st.session_state.presupuesto < costo:
                st.error("❌ No tienes suficiente dinero.")
            else:
                # --- OPERACIÓN CRÍTICA ---
                # A. Descontar en la Base de Datos
                ejecutar_db("UPDATE usuarios SET presupuesto = presupuesto - ? WHERE id = ?", (costo, u_id), commit=True)
                
                # B. Registrar Jugador
                ejecutar_db("INSERT INTO cartera (usuario_id, nombre_jugador, club, posicion, estado) VALUES (?,?,?,?,?)", 
                            (u_id, nombre_j, jug.iloc[1], jug['Posicion'], "Suplente"), commit=True)
                
                # C. Actualizar Memoria de Streamlit (esto asegura que el número baje en pantalla)
                st.session_state.presupuesto -= costo
                
                st.success(f"¡{nombre_j} fichado por € {costo:,}!")
                st.balloons()
                st.rerun()
