import pandas as pd
import random

class LigaManagerApp:
    def __init__(self, csv_url):
        # 1. Carga de Base de Datos (982 jugadores)
        try:
            self.df_base = pd.read_csv(csv_url)
            self.df_base.columns = [c.strip() for c in self.df_base.columns]
        except Exception as e:
            print(f"Error al conectar: {e}")
            self.df_base = pd.DataFrame()

        self.creditos = 0
        self.historial = []
        
        # 2. Plantilla 1-4-4-2 (Listado Superior)
        self.titulares = {
            'ARQ': [None],
            'DEF': [None, None, None, None],
            'VOL': [None, None, None, None],
            'DEL': [None, None]
        }
        # 3. Banco (Listado Inferior - Máx 25)
        self.suplentes = [] 

    # --- RULETA DE AZAR (50% 0, 25% +1, 20% -1, 5% +3) ---
    def girar_ruleta(self):
        opciones = [0, 1, -1, 3]
        pesos = [0.50, 0.25, 0.20, 0.05]
        resultado = random.choices(opciones, weights=pesos, k=1)[0]
        self.creditos += resultado
        # Registro con formato visual
        simbolo = "✨" if resultado > 0 else ("💀" if resultado < 0 else "💨")
        self.registrar_movimiento(f"{simbolo} Ruleta: {resultado}c (Total: {self.creditos}c)")
        return resultado

    # --- TIENDA CON DOBLE SEGURIDAD ---
    def comprar_pack(self, confirmacion=False):
        if not confirmacion: 
            return "⚠️ Debes confirmar la compra de 100 créditos."
        
        if self.creditos >= 100:
            if len(self.suplentes) + 2 > 25:
                return "❌ Banco lleno. Vende jugadores antes de comprar."
            
            self.creditos -= 100
            # Sorteo de la base de datos real
            nuevos = self.df_base.sample(n=2).to_dict('records')
            self.suplentes.extend(nuevos)
            
            for j in nuevos:
                self.registrar_movimiento(f"📦 Ojeo: {j['Jugador']} [{j['Equipo']}]")
            return "✅ Pack abierto con éxito."
        return "❌ Créditos insuficientes."

    # --- GESTIÓN DE POSICIONES (Mandar al Banco / Mandar a Titular) ---
    def mandar_a_titulares(self, index_suplente):
        jugador = self.suplentes[index_suplente]
        posicion = jugador['POS']
        
        # Buscar lugar vacío en la posición correspondiente
        if posicion in self.titulares:
            for i, slot in enumerate(self.titulares[posicion]):
                if slot is None:
                    self.titulares[posicion][i] = jugador
                    self.suplentes.pop(index_suplente)
                    self.registrar_movimiento(f"⬆️ {jugador['Jugador']} subió al 11 Titular.")
                    return True
            return f"❌ Ya tienes todos los slots de {posicion} ocupados."
        return "❌ Posición no reconocida."

    def mandar_al_banco(self, pos, index_titular):
        jugador = self.titulares[pos][index_titular]
        if jugador:
            if len(self.suplentes) < 25:
                self.suplentes.append(jugador)
                self.titulares[pos][index_titular] = None
                self.registrar_movimiento(f"⬇️ {jugador['Jugador']} regresó al Banco.")
                return True
            return "❌ Banco lleno, no puede bajar."
        return "❌ No hay nadie en esa posición."

    # --- VENTA CON DOBLE SEGURIDAD (20c x Estrella) ---
    def vender_suplente(self, index_suplente, confirmacion=False):
        if not confirmacion:
            return "⚠️ Confirmación requerida para vender."
        
        jugador = self.suplentes.pop(index_suplente)
        ganancia = jugador['Nivel'] * 20
        self.creditos += ganancia
        self.registrar_movimiento(f"💰 VENTA: {jugador['Jugador']} por {ganancia}c.")
        return ganancia

    def registrar_movimiento(self, texto):
        self.historial.append(texto)

    # --- RENDERIZADO DE INTERFAZ ---
    def mostrar_interfaz(self):
        print(f"\n{'='*70}")
        print(f"💰 CRÉDITOS: {self.creditos} | 👤 USUARIO: MANAGER_01")
        print(f"{'='*70}")
        
        print("\n🔝 LISTADO SUPERIOR (TITULARES 1-4-4-2)")
        for pos, lista in self.titulares.items():
            for i, j in enumerate(lista):
                if j:
                    estrellas = "⭐" * int(j['Nivel'])
                    print(f"   [{pos}] {j['Jugador']} | {j['Equipo']} | {estrellas} | Score: {j['Score']}")
                else:
                    print(f"   [{pos}] --- VACANTE ---")
        
        print("\n\n⏬ LISTADO INFERIOR (BANCO - MÁX 25)")
        for i, j in enumerate(self.suplentes):
            estrellas = "⭐" * int(j['Nivel'])
            print(f"   {i}. {j['Jugador']} ({j['POS']}) | {j['Equipo']} | {estrellas} | [BOTÓN VENDER]")

        print(f"\n{'*'*70}\n📜 HISTORIAL DE MOVIMIENTOS")
        for mov in self.historial[-4:]:
            print(f" > {mov}")
        print(f"{'*'*70}")

# --- INICIALIZACIÓN ---
URL_CSV = "https://docs.google.com/spreadsheets/d/e/2PACX-1vQ2VmykJ-6g-KVHVS3doLPVdxGA09KgOByjy67lnJW-VlJxLWgukpKAUM1PmeTOKbPtH1fNDSUyCBTO/pub?output=csv"
app = LigaManagerApp(URL_CSV)

# Ejemplo de uso:
# app.creditos = 100
# app.comprar_pack(confirmacion=True)
# app.mostrar_interfaz()
