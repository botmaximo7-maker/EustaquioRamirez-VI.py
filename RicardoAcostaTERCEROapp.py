import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import random
import time
from scipy.optimize import milp, LinearConstraint, Bounds

# Configuración de la página web
st.set_page_config(page_title="Optimización del Hogar", layout="wide")

# --- CONTEXTO DEL PROBLEMA EN LA PARTE SUPERIOR ---
st.title("⚡ Optimización Eléctrica y de Calidad de Vida")

# Escenario 1: El problema base
with st.expander("📖 Caso 1: El Desafío Base (Maximizar el Bienestar)", expanded=False):
    st.info(
        "### 🎯 Balance General del Hogar\n"
        "Este sistema resuelve un problema de **Programación Lineal** para balancear el confort diario "
        "y el uso de electrodomésticos bajo restricciones económicas y energéticas estrictas.\n\n"
        "**¿Qué intenta resolver la aplicación?**\n"
        "1. **Objetivo Principal:** Encontrar cuántas horas al mes usar cada aparato para obtener la **máxima calidad de vida** "
        "posible (basada en la importancia asignada a cada uno).\n"
        "2. **Restricción de Presupuesto:** El costo total acumulado por el uso no debe superar el dinero mensual disponible.\n"
        "3. **Restricción Energética:** El consumo eléctrico total no puede exceder el límite de Watts para evitar sobrecargas."
    )

# Escenario 2: La crisis familiar
with st.expander("🚨 Caso 2: ¡Se mudó la suegra con la familia extendida!", expanded=True):
    st.warning(
        "### 📈 Crisis de Demanda Eléctrica y Financiera\n"
        "**El nuevo escenario:** La suegra, sus dos hijas y los hijos de sus hijas se han mudado a la casa de forma permanente. "
        "Al multiplicarse los habitantes (¡y debido a que no tienen cultura de ahorro!), el uso real "
        "de los electrodomésticos se ha disparado por completo.\n\n"
        "**Consecuencias en el sistema:**\n"
        "* **El problema:** Los mínimos de horas de uso que venías manejando quedaron obsoletos. Si mantienes el presupuesto de $15,000 "
        "y los 50,000 Watts, el algoritmo **fallará** porque el consumo vital de tanta gente supera los límites históricos.\n"
        "* **La solución interactiva:** Para resolver esta crisis familiar, debes usar la **barra lateral** para estirar el "
        "Presupuesto Máximo, ampliar los Watts permitidos y ajustar el piso mínimo de horas de aparatos críticos (como el lavarropas o la pava)."
    )

st.write("---")
st.write("💡 *Modifica los parámetros en la barra lateral para ajustar el sistema al nuevo escenario familiar.*")


# --- BARRA LATERAL: ENTRADA DE DATOS PRINCIPALES ---
st.sidebar.header("📊 Restricciones Globales")
limite_presupuesto = st.sidebar.number_input("Presupuesto Máximo ($)", value=15000, step=500)
limite_watts = st.sidebar.number_input("Consumo Máximo (Watts)", value=50000, step=1000)
min_aparatos = st.sidebar.number_input("Piso mínimo de conteo de aparatos", value=7.0, step=0.5, format="%.1f")

# Datos de los aparatos
aparatos = ["Pava", "Heladera", "Computadora", "Lavarropas", "Televisor", "Microondas", "Secador"]
valores_defecto = {
    "Pava": {"prioridad": 7, "costo": 150, "watts": 1200, "min_horas": 10},
    "Heladera": {"prioridad": 10, "costo": 80, "watts": 200, "min_horas": 30},
    "Computadora": {"prioridad": 8, "costo": 110, "watts": 150, "min_horas": 25},
    "Lavarropas": {"prioridad": 6, "costo": 200, "watts": 500, "min_horas": 8},
    "Televisor": {"prioridad": 4, "costo": 70, "watts": 100, "min_horas": 15},
    "Microondas": {"prioridad": 5, "costo": 180, "watts": 800, "min_horas": 6},
    "Secador": {"prioridad": 5, "costo": 250, "watts": 1500, "min_horas": 5}
}

st.sidebar.header("🔌 Configuración por Aparato")
datos_usuario = {}

for ap in aparatos:
    with st.sidebar.expander(f"Configurar {ap}"):
        prio = st.slider(f"Importancia (1-10) - {ap}", 1, 10, valores_defecto[ap]["prioridad"])
        costo = st.number_input(f"Costo por hora ($) - {ap}", value=valores_defecto[ap]["costo"])
        watts = st.number_input(f"Watts por hora - {ap}", value=valores_defecto[ap]["watts"])
        min_h = st.number_input(f"Mínimo horas al mes - {ap}", value=valores_defecto[ap]["min_horas"])
        
        datos_usuario[ap] = {"prio": prio, "costo": costo, "watts": watts, "min_h": min_h}


# --- 🎰 SECCIÓN AISLADA DE JUEGOS AL FINAL DE LA BARRA LATERAL ---
st.sidebar.markdown("---")
with st.sidebar.expander("🎰 Casino & Recreo (Minijuegos)", expanded=False):
    
    # --- 💰 ESTADO COMPARTIDO DE FICHAS ---
    if "bj_saldo" not in st.session_state:
        st.session_state.bj_saldo = 1000

    st.markdown(f"### 🏦 Billetera: **${st.session_state.bj_saldo}**")

    if st.session_state.bj_saldo <= 0:
        st.error("😢 Te quedaste sin fondos en el casino.")
        if st.button("💸 Pedir un Plan de Pago (+$500)", use_container_width=True):
            st.session_state.bj_saldo = 500
            st.rerun()

    st.markdown("---")

    # --- 🕹️ JUEGO 1: TRES EN RAYA ---
    st.subheader("🎮 Tres en Raya")

    if "tablero" not in st.session_state:
        st.session_state.tablero = [""] * 9
    if "turno" not in st.session_state:
        st.session_state.turno = "Jugador 1 (X)"
    if "ganador" not in st.session_state:
        st.session_state.ganador = None

    def verificar_ganador():
        t = st.session_state.tablero
        combinaciones = [
            [0, 1, 2], [3, 4, 5], [6, 7, 8],
            [0, 3, 6], [1, 4, 7], [2, 5, 8],
            [0, 4, 8], [2, 4, 6]
        ]
        for combo in combinaciones:
            if t[combo[0]] == t[combo[1]] == t[combo[2]] != "":
                return "Jugador 1" if t[combo[0]] == "X" else "Jugador 2"
        if "" not in t:
            return "Empate"
        return None

    if st.session_state.ganador:
        if st.session_state.ganador == "Empate":
            st.warning("¡Es un Empate! 🤝")
        else:
            st.success(f"🎉 ¡Ganó el {st.session_state.ganador}!")
    else:
        st.info(f"👉 Turno de: **{st.session_state.turno}**")

    cols_juego = st.columns(3)
    for i in range(9):
        with cols_juego[i % 3]:
            contenido = st.session_state.tablero[i]
            label_boton = contenido if contenido != "" else " "
            desactivado = contenido != "" or st.session_state.ganador is not None
            
            if st.button(label_boton, key=f"btn_{i}", disabled=desactivado, use_container_width=True):
                if st.session_state.turno == "Jugador 1 (X)":
                    st.session_state.tablero[i] = "X"
                    st.session_state.turno = "Jugador 2 (O)"
                else:
                    st.session_state.tablero[i] = "O"
                    st.session_state.turno = "Jugador 1 (X)"
                st.session_state.ganador = verificar_ganador()
                st.rerun()

    if st.button("🔄 Reiniciar Ta-Te-Ti", use_container_width=True):
        st.session_state.tablero = [""] * 9
        st.session_state.turno = "Jugador 1 (X)"
        st.session_state.ganador = None
        st.rerun()

    st.markdown("---")

    # --- 🃏 JUEGO 2: BLACKJACK ---
    st.subheader("🃏 Blackjack (21)")

    def crear_baraja():
        valores = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        return valores * 4

    def calcular_puntos(mano):
        puntos = 0
        ases = 0
        for carta in mano:
            if carta in ['J', 'Q', 'K']:
                puntos += 10
            elif carta == 'A':
                ases += 1
                puntos += 11
            else:
                puntos += int(carta)
        while puntos > 21 and ases:
            puntos -= 10
            ases -= 1
        return puntos

    if "bj_apuesta" not in st.session_state:
        st.session_state.bj_apuesta = 100

    if "bj_baraja" not in st.session_state:
        st.session_state.bj_baraja = crear_baraja()
        st.session_state.bj_jugador = []
        st.session_state.bj_casa = []
        st.session_state.bj_estado = "inicio"
        st.session_state.bj_msg = ""

    def iniciar_blackjack():
        st.session_state.bj_saldo -= st.session_state.bj_apuesta
        st.session_state.bj_baraja = crear_baraja()
        random.shuffle(st.session_state.bj_baraja)
        st.session_state.bj_jugador = [st.session_state.bj_baraja.pop(), st.session_state.bj_baraja.pop()]
        st.session_state.bj_casa = [st.session_state.bj_baraja.pop(), st.session_state.bj_baraja.pop()]
        st.session_state.bj_estado = "jugando"
        st.session_state.bj_msg = ""
        
        if calcular_puntos(st.session_state.bj_jugador) == 21:
            st.session_state.bj_estado = "terminado"
            ganancia = int(st.session_state.bj_apuesta * 2.5)
            st.session_state.bj_saldo += ganancia
            st.session_state.bj_msg = f"¡Blackjack Natural! Ganaste ${ganancia}! 🎉"

    if st.session_state.bj_estado == "inicio":
        if st.session_state.bj_saldo > 0:
            st.session_state.bj_apuesta = st.number_input(
                "Apuesta Blackjack:", min_value=10, max_value=st.session_state.bj_saldo, value=min(100, st.session_state.bj_saldo), step=10, key="apuesta_bj_val"
            )
            if st.button("🃏 Repartir Cartas", use_container_width=True):
                iniciar_blackjack()
                st.rerun()
    else:
        pts_jugador = calcular_puntos(st.session_state.bj_jugador)
        pts_casa = calcular_puntos(st.session_state.bj_casa)
        
        if st.session_state.bj_estado == "jugando":
            st.write(f"**Tu Mano:** {', '.join(st.session_state.bj_jugador)} (Pts: {pts_jugador})")
            st.write(f"**Casa:** {st.session_state.bj_casa[0]}, ❓")
        else:
            st.write(f"**Tu Mano:** {', '.join(st.session_state.bj_jugador)} (Pts: {pts_jugador})")
            st.write(f"**Casa:** {', '.join(st.session_state.bj_casa)} (Pts: {pts_casa})")

        if st.session_state.bj_estado == "jugando":
            col_bj1, col_bj2 = st.columns(2)
            with col_bj1:
                if st.button("🃏 Pedir", use_container_width=True, key="bj_pedir"):
                    st.session_state.bj_jugador.append(st.session_state.bj_baraja.pop())
                    if calcular_puntos(st.session_state.bj_jugador) > 21:
                        st.session_state.bj_estado = "terminado"
                        st.session_state.bj_msg = "❌ ¡Te pasaste de 21! Perdiste."
                    st.rerun()
            with col_bj2:
                if st.button("🛑 Plantarse", use_container_width=True, key="bj_plantar"):
                    st.session_state.bj_estado = "terminado"
                    while calcular_puntos(st.session_state.bj_casa) < 17:
                        st.session_state.bj_casa.append(st.session_state.bj_baraja.pop())
                    
                    final_jugador = calcular_puntos(st.session_state.bj_jugador)
                    final_casa = calcular_puntos(st.session_state.bj_casa)
                    
                    if final_casa > 21:
                        st.session_state.bj_saldo += st.session_state.bj_apuesta * 2
                        st.session_state.bj_msg = f"🎉 ¡La casa se pasó! Ganaste ${st.session_state.bj_apuesta}."
                    elif final_jugador > final_casa:
                        st.session_state.bj_saldo += st.session_state.bj_apuesta * 2
                        st.session_state.bj_msg = f"🎉 ¡Ganaste por puntos! Recibes ${st.session_state.bj_apuesta}."
                    elif final_jugador < final_casa:
                        st.session_state.bj_msg = "❌ Perdiste contra la casa."
                    else:
                        st.session_state.bj_saldo += st.session_state.bj_apuesta
                        st.session_state.bj_msg = "🤝 Es un empate (Push)."
                    st.rerun()
                    
        if st.session_state.bj_estado == "terminado":
            if "🎉" in st.session_state.bj_msg or "Blackjack" in st.session_state.bj_msg:
                st.success(st.session_state.bj_msg)
            elif "🤝" in st.session_state.bj_msg:
                st.warning(st.session_state.bj_msg)
            else:
                st.error(st.session_state.bj_msg)
                
            if st.button("🔄 Siguiente Mano", use_container_width=True, key="bj_reiniciar"):
                st.session_state.bj_estado = "inicio"
                st.rerun()

    st.markdown("---")

    # --- 🏇 JUEGO 3: CARRERA DE CABALLOS ---
    st.subheader("🏇 Hipódromo Virtual")

    caballos = {
        "Rayo McQueen (x2.0)": 2.0,
        "Usain Bolt (x3.5)": 3.5,
        "Galopante (x5.0)": 5.0,
        "Juan (x8.0)": 8.0
    }

    if "ch_apuesta" not in st.session_state:
        st.session_state.ch_apuesta = 50

    if st.session_state.bj_saldo > 0:
        caballo_elegido = st.selectbox("Elegí tu caballo:", list(caballos.keys()))
        st.session_state.ch_apuesta = st.number_input(
            "Monto a apostar (Carreras):", min_value=10, max_value=st.session_state.bj_saldo, value=min(50, st.session_state.bj_saldo), step=10, key="apuesta_ch_val"
        )
        
        if st.button("🏁 ¡Largar Carrera!", use_container_width=True):
            st.session_state.bj_saldo -= st.session_state.ch_apuesta
            
            barra_progreso = st.progress(0)
            estado_carrera = st.empty()
            
            for p in range(1, 101, 20):
                estado_carrera.text(f"🏇 ¡Están corriendo! Distancia: {p}%...")
                barra_progreso.progress(p)
                time.sleep(0.3)
                
            barra_progreso.empty()
            estado_carrera.empty()
            
            ganador = random.choice(list(caballos.keys()))
            
            if ganador == caballo_elegido:
                cuota = caballos[ganador]
                premio = int(st.session_state.ch_apuesta * cuota)
                st.session_state.bj_saldo += premio
                st.success(f"🏆 ¡Ganó {ganador}! ¡Acertaste y te llevas ${premio}! 🎉")
            else:
                st.error(f"❌ Ganó {ganador}. Tu caballo llegó último. Perdiste ${st.session_state.ch_apuesta}.")
            time.sleep(0.1)

    st.markdown("---")

    # --- 🎯 JUEGO 4: TIRO AL BLANCO ---
    st.subheader("🎯 Tiro al Blanco")

    if "tb_apuesta" not in st.session_state:
        st.session_state.tb_apuesta = 50

    if st.session_state.bj_saldo > 0:
        objetivo_usuario = st.slider("Alineá tu mira (Posición 1 a 5):", 1, 5, 3)
        st.session_state.tb_apuesta = st.number_input(
            "Monto a apostar (Tiro):", min_value=10, max_value=st.session_state.bj_saldo, value=min(50, st.session_state.bj_saldo), step=10, key="apuesta_tb_val"
        )
        
        if st.button("💥 ¡Fuego!", use_container_width=True):
            st.session_state.bj_saldo -= st.session_state.tb_apuesta
            
            mira = st.empty()
            for i in range(3):
                mira.text("🎯 Apuntando" + "." * (i + 1))
                time.sleep(0.2)
            mira.empty()
            
            blanco_real = random.randint(1, 5)
            
            if objetivo_usuario == blanco_real:
                premio = st.session_state.tb_apuesta * 3
                st.session_state.bj_saldo += premio
                st.success(f"🎯 ¡IMPACTO DIRECTO! El blanco estaba en la posición {blanco_real}. ¡Ganaste ${premio}!")
            elif abs(objetivo_usuario - blanco_real) == 1:
                st.session_state.bj_saldo += st.session_state.tb_apuesta
                st.warning(f"💥 ¡Casi! El blanco estaba en {blanco_real}. Le diste al borde y recuperás tu apuesta.")
            else:
                st.error(f"💨 ¡Errado! El blanco apareció en la posición {blanco_real}. Perdiste ${st.session_state.tb_apuesta}.")

    st.markdown("---")

    # --- 🥤 JUEGO 5: TRES VASOS Y UNA BOLITA ---
    st.subheader("🥤 ¿Dónde está la bolita?")

    if "tl_apuesta" not in st.session_state:
        st.session_state.tl_apuesta = 50

    if "tl_estado" not in st.session_state:
        st.session_state.tl_estado = "inicio"
    if "tl_bolita" not in st.session_state:
        st.session_state.tl_bolita = 1
    if "tl_msg" not in st.session_state:
        st.session_state.tl_msg = ""

    if st.session_state.bj_saldo > 0 or st.session_state.tl_estado != "inicio":
        if st.session_state.tl_estado == "inicio":
            st.session_state.tl_apuesta = st.number_input(
                "Monto a apostar (Vasos):", min_value=10, max_value=st.session_state.bj_saldo, value=min(50, st.session_state.bj_saldo), step=10, key="apuesta_tl_val"
            )
            if st.button("🃏 Mostrar Bolita y Mezclar", use_container_width=True):
                st.session_state.bj_saldo -= st.session_state.tl_apuesta
                st.session_state.tl_estado = "mezclando"
                st.rerun()

        if st.session_state.tl_estado == "mezclando":
            anim_vasos = st.empty()
            anim_vasos.markdown("### 🥤&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🥤&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🥤\n#### &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;🔴 (Acá está...)")
            time.sleep(0.6)
            for _ in range(3):
                anim_vasos.markdown("### 🔄 ¡Mezclando vasos rápidamente! 🔄")
                time.sleep(0.3)
            anim_vasos.empty()
            
            st.session_state.tl_bolita = random.randint(0, 2)
            st.session_state.tl_estado = "adivinar"
            st.rerun()

        if st.session_state.tl_estado == "adivinar":
            st.write("🔒 *La bolita ya está oculta. Elegí un vaso:*")
            cols_vasos = st.columns(3)
            for idx in range(3):
                with cols_vasos[idx]:
                    if st.button(f"🥤 Vaso {idx+1}", key=f"btn_vaso_{idx}", use_container_width=True):
                        if idx == st.session_state.tl_bolita:
                            premio = st.session_state.tl_apuesta * 3
                            st.session_state.bj_saldo += premio
                            st.session_state.tl_msg = f"🎉 ¡EXCELENTE VISTA! La bolita estaba en el Vaso {idx+1}. Ganaste ${premio}."
                        else:
                            st.session_state.tl_msg = f"❌ ¡Le erraste! Estaba en el Vaso {st.session_state.tl_bolita+1}. Perdiste ${st.session_state.tl_apuesta}."
                        st.session_state.tl_estado = "resultado"
                        st.rerun()

        if st.session_state.tl_estado == "resultado":
            vasos_dibujo = ["🥤", "🥤", "🥤"]
            vasos_dibujo[st.session_state.tl_bolita] = "🥤🔴"
            st.markdown(f"### {vasos_dibujo[0]} &nbsp;&nbsp;&nbsp;&nbsp; {vasos_dibujo[1]} &nbsp;&nbsp;&nbsp;&nbsp; {vasos_dibujo[2]}")
            
            if "🎉" in st.session_state.tl_msg:
                st.success(st.session_state.tl_msg)
            else:
                st.error(st.session_state.tl_msg)
                
            if st.button("🔄 Jugar otra vez", use_container_width=True, key="tl_reiniciar"):
                st.session_state.tl_estado = "inicio"
                st.rerun()

    st.markdown("---")

    # --- 🐦 JUEGO 6: FLAPPY BIRD ---
    st.subheader("🐦 Flappy Bird Arcade")
    st.write("Controles: **Espacio** o **Clic** para saltar.")

    flappy_bird_html = """
    <div style="text-align:center;">
        <canvas id="fbCanvas" width="240" height="300" style="border:2px solid #333; background:#70c5ce; border-radius:10px; cursor:pointer;"></canvas>
        <div style="font-family:sans-serif; font-size:14px; color:#555; margin-top:5px;">
            Puntaje: <span id="lblScore" style="font-weight:bold; color:#d9534f;">0</span>
        </div>
    </div>
    <script>
        const canvas = document.getElementById("fbCanvas"); const ctx = canvas.getContext("2d"); const scoreLabel = document.getElementById("lblScore");
        let bird = { x: 40, y: 140, radius: 10, velocity: 0, gravity: 0.25, jump: -4.5 };
        let pipes = []; let frame = 0; let score = 0; let gameOver = false; let gameStarted = false;
        function resetGame() { bird.y = 140; bird.velocity = 0; pipes = []; score = 0; frame = 0; gameOver = false; gameStarted = false; scoreLabel.innerText = "0"; }
        function spawnPipe() { let gap = 85; let minH = 30; let maxH = canvas.height - gap - minH; let h = Math.floor(Math.random()*(maxH-minH+1))+minH; pipes.push({ x: canvas.width, top: h, bottom: canvas.height-h-gap, passed: false }); }
        function loop() {
            ctx.fillStyle = "#70c5ce"; ctx.fillRect(0,0,canvas.width,canvas.height);
            if(gameStarted && !gameOver){ bird.velocity += bird.gravity; bird.y += bird.velocity; }
            if(bird.y+bird.radius >= canvas.height){ gameOver = true; }
            ctx.fillStyle = "#f0ad4e"; ctx.beginPath(); ctx.arc(bird.x, bird.y, bird.radius, 0, Math.PI*2); ctx.fill();
            if(gameStarted && !gameOver){ if(frame%90===0) spawnPipe(); frame++; }
            for(let i=pipes.length-1; i>=0; i--){
                if(gameStarted && !gameOver) pipes[i].x -= 2;
                ctx.fillStyle = "#5cb85c"; ctx.fillRect(pipes[i].x, 0, 35, pipes[i].top); ctx.fillRect(pipes[i].x, canvas.height-pipes[i].bottom, 35, pipes[i].bottom);
                if(bird.x+bird.radius > pipes[i].x && bird.x-bird.radius < pipes[i].x+35){
                    if(bird.y-bird.radius < pipes[i].top || bird.y+bird.radius > canvas.height-pipes[i].bottom) gameOver = true;
                }
                if(!pipes[i].passed && pipes[i].x+35 < bird.x){ pipes[i].passed = true; score++; scoreLabel.innerText = score; }
                if(pipes[i].x + 35 < 0) pipes.splice(i,1);
            }
            if(!gameStarted){ ctx.fillStyle="rgba(0,0,0,0.3)"; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.fillStyle="#fff"; ctx.font="14px sans-serif"; ctx.textAlign="center"; ctx.fillText("Clic para Volar", canvas.width/2, canvas.height/2); }
            else if(gameOver){ ctx.fillStyle="rgba(0,0,0,0.5)"; ctx.fillRect(0,0,canvas.width,canvas.height); ctx.fillStyle="#fff"; ctx.font="16px sans-serif"; ctx.textAlign="center"; ctx.fillText("GAME OVER", canvas.width/2, canvas.height/2); }
            requestAnimationFrame(loop);
        }
        function act(e){ if(e.type==='keydown' && e.code!=='Space')return; if(!gameStarted){gameStarted=true; bird.velocity=bird.jump;} else if(gameOver){resetGame();} else {bird.velocity=bird.jump;} }
        window.addEventListener("keydown", act); canvas.addEventListener("click", act);
        resetGame(); loop();
    </script>
    """
    components.html(flappy_bird_html, height=335)

    # --- 🐷 JUEGO 7: ANGRY BIRDS CLONE (NUEVO) ---
    st.markdown("---")
    st.subheader("🐷 Angry Birds Arcade")
    st.write("Arrastrá y soltá el pájaro rojo para derribar al chancho.")

    angry_birds_html = """
    <div style="text-align:center;">
        <canvas id="abCanvas" width="240" height="240" style="border:2px solid #333; background:#a2d2ff; border-radius:10px;"></canvas>
        <div style="font-family:sans-serif; font-size:14px; color:#555; margin-top:5px;">
            Derribos: <span id="lblAbScore" style="font-weight:bold; color:#5cb85c;">0</span>
        </div>
    </div>
    <script>
        const canvas = document.getElementById("abCanvas"); const ctx = canvas.getContext("2d"); const abScoreLabel = document.getElementById("lblAbScore");
        let sling = { x: 50, y: 160 };
        let bird = { x: 50, y: 160, vx: 0, vy: 0, radius: 10, isFlying: false, isDragging: false };
        let pig = { x: 190, y: 170, radius: 12, isHit: false };
        let abScore = 0;

        function resetRound() {
            bird.x = sling.x; bird.y = sling.y; bird.vx = 0; bird.vy = 0; bird.isFlying = false; bird.isDragging = false;
            pig.x = 150 + Math.random() * 60; pig.y = 170; pig.isHit = false;
        }

        canvas.addEventListener("mousedown", (e) => {
            if (bird.isFlying) return;
            const rect = canvas.getBoundingClientRect(); const mx = e.clientX - rect.left; const my = e.clientY - rect.top;
            if (Math.hypot(mx - bird.x, my - bird.y) < 20) { bird.isDragging = true; }
        });

        canvas.addEventListener("mousemove", (e) => {
            if (!bird.isDragging) return;
            const rect = canvas.getBoundingClientRect(); const mx = e.clientX - rect.left; const my = e.clientY - rect.top;
            let dist = Math.min(Math.hypot(mx - sling.x, my - sling.y), 40);
            let angle = Math.atan2(my - sling.y, mx - sling.x);
            bird.x = sling.x + dist * Math.cos(angle); bird.y = sling.y + dist * Math.sin(angle);
        });

        canvas.addEventListener("mouseup", (e) => {
            if (!bird.isDragging) return;
            bird.isDragging = false; bird.isFlying = true;
            bird.vx = (sling.x - bird.x) * 0.15; bird.vy = (sling.y - bird.y) * 0.15;
        });

        function abLoop() {
            ctx.fillStyle = "#a2d2ff"; ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.fillStyle = "#875a36"; ctx.fillRect(0, 180, canvas.width, 60); // Piso
            ctx.strokeStyle = "#53351d"; ctx.lineWidth = 4; ctx.beginPath(); ctx.moveTo(sling.x, sling.y); ctx.lineTo(sling.x, 180); ctx.stroke(); // Resortera
            
            if (bird.isFlying) {
                bird.vy += 0.15; bird.x += bird.vx; bird.y += bird.vy;
                if (bird.y > 170 || bird.x > canvas.width || bird.x < 0) { setTimeout(resetRound, 1000); bird.isFlying = false; }
            }
            
            // Colisión con Chancho
            if (!pig.isHit && Math.hypot(bird.x - pig.x, bird.y - pig.y) < (bird.radius + pig.radius)) {
                pig.isHit = true; abScore++; abScoreLabel.innerText = abScore;
            }

            // Dibujar Pájaro (Rojo)
            ctx.fillStyle = "#d9534f"; ctx.beginPath(); ctx.arc(bird.x, bird.y, bird.radius, 0, Math.PI*2); ctx.fill();
            // Dibujar Chancho (Verde)
            if (!pig.isHit) { ctx.fillStyle = "#5cb85c"; ctx.beginPath(); ctx.arc(pig.x, pig.y, pig.radius, 0, Math.PI*2); ctx.fill(); }

            requestAnimationFrame(abLoop);
        }
        resetRound(); abLoop();
    </script>
    """
    components.html(angry_birds_html, height=275)

    # --- SISTEMA DE CANJE UNIFICADO ---
    st.markdown("---")
    if "fb_record_actual" not in st.session_state:
        st.session_state.fb_record_actual = 0

    puntos_a_reclamar = st.number_input("Puntos de Arcade a canjear:", min_value=0, value=0, step=1, key="arcade_canje")
    if st.button("💰 Cobrar Fichas de Arcade", use_container_width=True):
        if puntos_a_reclamar > 0:
            ganancia_fb = puntos_a_reclamar * 50
            st.session_state.bj_saldo += ganancia_fb
            if puntos_a_reclamar > st.session_state.fb_record_actual:
                st.session_state.fb_record_actual = puntos_a_reclamar
            st.success(f"¡Reclamaste ${ganancia_fb} fichas!")
            st.rerun()


# --- PROCESAMIENTO DE LOS DATOS DE OPTIMIZACIÓN ---
c = [-datos_usuario[ap]["prio"] for ap in aparatos]
conteo_coefs = [1.0, 1.0, 1.5, 1.2, 1.3, 1.0, 1.1]

A = [
    conteo_coefs,
    [datos_usuario[ap]["costo"] for ap in aparatos],
    [datos_usuario[ap]["watts"] for ap in aparatos]
]

bl = [min_aparatos, -np.inf, -np.inf]
bu = [np.inf, limite_presupuesto, limite_watts]

constraints = LinearConstraint(A, bl, bu)

limite_inferior = [datos_usuario[ap]["min_h"] for ap in aparatos]
limite_superior = [np.inf] * 7
bounds = Bounds(limite_inferior, limite_superior)

res = milp(
    c=c,
    constraints=constraints,
    bounds=bounds,
    integrality=[0] * 7
)

# --- MOSTRAR RESULTADOS PRINCIPALES ---
col1, col2 = st.columns(2)

with col1:
    st.subheader("📌 Resultados de la Optimización")
    if res.success:
        st.success(f"¡Calidad de Vida Máxima Lograda! = {-res.fun:.2f} puntos")
        
        resultados_tabla = {
            "Aparato": aparatos,
            "Horas recomendadas al mes": [f"{val:.2f} hs" for val in res.x]
        }
        st.table(resultados_tabla)
    else:
        st.error("❌ No se encontró solución. Con tanta gente en la casa, los mínimos configurados superan el presupuesto o los Watts disponibles. ¡Sube los límites en la barra lateral!")

with col2:
    st.subheader("📊 Verificación de Restricciones")
    if res.success:
        tot_aparatos = sum(A[0][i] * res.x[i] for i in range(7))
        tot_dinero = sum(A[1][i] * res.x[i] for i in range(7))
        tot_watts = sum(A[2][i] * res.x[i] for i in range(7))
        
        st.metric(label="Total Aparatos Conectados (Mínimo: " + str(min_aparatos) + ")", value=f"{tot_aparatos:.2f}")
        st.metric(label="Gasto Mensual Total (Máximo: $" + str(limite_presupuesto) + ")", value=f"${tot_dinero:.2f}")
        st.metric(label="Consumo de Potencia Total (Máximo: " + str(limite_watts) + " W)", value=f"{tot_watts:.2f} W")


