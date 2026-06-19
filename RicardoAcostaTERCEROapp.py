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


# --- BARRA LATERAL: ENTRADA DE DATOS ---
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


# --- 💰 ESTADO COMPARTIDO DE FICHAS ---
if "bj_saldo" not in st.session_state:
    st.session_state.bj_saldo = 1000

st.sidebar.markdown("---")
st.sidebar.markdown(f"### 🏦 Billetera del Casino: **${st.session_state.bj_saldo}**")

if st.session_state.bj_saldo <= 0:
    st.sidebar.error("😢 Te quedaste sin fondos en el casino.")
    if st.sidebar.button("💸 Pedir un Plan de Pago (+$500)", use_container_width=True):
        st.session_state.bj_saldo = 500
        st.rerun()


# --- 🕹️ JUEGO 1: TRES EN RAYA ---
st.sidebar.header("🎮 Tres en Raya")

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
        st.sidebar.warning("¡Es un Empate! 🤝")
    else:
        st.sidebar.success(f"🎉 ¡Ganó el {st.session_state.ganador}!")
else:
    st.sidebar.info(f"👉 Turno de: **{st.session_state.turno}**")

cols_juego = st.sidebar.columns(3)
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

if st.sidebar.button("🔄 Reiniciar Ta-Te-Ti", use_container_width=True):
    st.session_state.tablero = [""] * 9
    st.session_state.turno = "Jugador 1 (X)"
    st.session_state.ganador = None
    st.rerun()


# --- 🃏 JUEGO 2: BLACKJACK ---
st.sidebar.markdown("---")
st.sidebar.header("🃏 Blackjack (21)")

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
        st.session_state.bj_apuesta = st.sidebar.number_input(
            "Apuesta Blackjack:", min_value=10, max_value=st.session_state.bj_saldo, value=min(100, st.session_state.bj_saldo), step=10, key="apuesta_bj_val"
        )
        if st.sidebar.button("🃏 Repartir Cartas", use_container_width=True):
            iniciar_blackjack()
            st.rerun()
else:
    pts_jugador = calcular_puntos(st.session_state.bj_jugador)
    pts_casa = calcular_puntos(st.session_state.bj_casa)
    
    if st.session_state.bj_estado == "jugando":
        st.sidebar.write(f"**Tu Mano:** {', '.join(st.session_state.bj_jugador)} (Pts: {pts_jugador})")
        st.sidebar.write(f"**Casa:** {st.session_state.bj_casa[0]}, ❓")
    else:
        st.sidebar.write(f"**Tu Mano:** {', '.join(st.session_state.bj_jugador)} (Pts: {pts_jugador})")
        st.sidebar.write(f"**Casa:** {', '.join(st.session_state.bj_casa)} (Pts: {pts_casa})")

    if st.session_state.bj_estado == "jugando":
        col_bj1, col_bj2 = st.sidebar.columns(2)
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
            st.sidebar.success(st.session_state.bj_msg)
        elif "🤝" in st.session_state.bj_msg:
            st.sidebar.warning(st.session_state.bj_msg)
        else:
            st.sidebar.error(st.session_state.bj_msg)
            
        if st.sidebar.button("🔄 Siguiente Mano", use_container_width=True, key="bj_reiniciar"):
            st.session_state.bj_estado = "inicio"
            st.rerun()


# --- 🏇 JUEGO 3: CARRERA DE CABALLOS ---
st.sidebar.markdown("---")
st.sidebar.header("🏇 Hipódromo Virtual")

caballos = {
    "Rayo McQueen (x2.0)": 2.0,
    "Usain Bolt (x3.5)": 3.5,
    "Galopante (x5.0)": 5.0,
    "Juan (x8.0)": 8.0
}

if "ch_apuesta" not in st.session_state:
    st.session_state.ch_apuesta = 50

if st.session_state.bj_saldo > 0:
    caballo_elegido = st.sidebar.selectbox("Elegí tu caballo:", list(caballos.keys()))
    st.session_state.ch_apuesta = st.sidebar.number_input(
        "Monto a apostar (Carreras):", min_value=10, max_value=st.session_state.bj_saldo, value=min(50, st.session_state.bj_saldo), step=10, key="apuesta_ch_val"
    )
    
    if st.sidebar.button("🏁 ¡Largar Carrera!", use_container_width=True):
        st.session_state.bj_saldo -= st.session_state.ch_apuesta
        
        # Simulación animada de carrera
        barra_progreso = st.sidebar.progress(0)
        estado_carrera = st.sidebar.empty()
        
        for p in range(1, 101, 20):
            estado_carrera.text(f"🏇 ¡Están corriendo! Distancia: {p}%...")
            barra_progreso.progress(p)
            time.sleep(0.3)
            
        barra_progreso.empty()
        estado_carrera.empty()
        
        # Definir ganador aleatorio
        ganador = random.choice(list(caballos.keys()))
        
        if ganador == caballo_elegido:
            cuota = caballos[ganador]
            premio = int(st.session_state.ch_apuesta * cuota)
            st.session_state.bj_saldo += premio
            st.sidebar.success(f"🏆 ¡Ganó {ganador}! ¡Acertaste y te llevas ${premio}! 🎉")
        else:
            st.sidebar.error(f"❌ Ganó {ganador}. Tu caballo llegó último. Perdiste ${st.session_state.ch_apuesta}.")
        time.sleep(0.1)


# --- 🎯 JUEGO 4: TIRO AL BLANCO ---
st.sidebar.markdown("---")
st.sidebar.header("🎯 Tiro al Blanco")

if "tb_apuesta" not in st.session_state:
    st.session_state.tb_apuesta = 50

if st.session_state.bj_saldo > 0:
    objetivo_usuario = st.sidebar.slider("Alineá tu mira (Posición 1 a 5):", 1, 5, 3)
    st.session_state.tb_apuesta = st.sidebar.number_input(
        "Monto a apostar (Tiro):", min_value=10, max_value=st.session_state.bj_saldo, value=min(50, st.session_state.bj_saldo), step=10, key="apuesta_tb_val"
    )
    
    if st.sidebar.button("💥 ¡Fuego!", use_container_width=True):
        st.session_state.bj_saldo -= st.session_state.tb_apuesta
        
        # Efecto de apuntado rápido
        mira = st.sidebar.empty()
        for i in range(3):
            mira.text("🎯 Apuntando" + "." * (i + 1))
            time.sleep(0.2)
        mira.empty()
        
        # Posición real del blanco
        blanco_real = random.randint(1, 5)
        
        if objetivo_usuario == blanco_real:
            # Recompensa base por acertar en el blanco (Triple)
            premio = st.session_state.tb_apuesta * 3
            st.session_state.bj_saldo += premio
            st.sidebar.success(f"🎯 ¡IMPACTO DIRECTO! El blanco estaba en la posición {blanco_real}. ¡Ganaste ${premio}!")
        elif abs(objetivo_usuario - blanco_real) == 1:
            # Rozó el blanco, devuelve la apuesta
            st.session_state.bj_saldo += st.session_state.tb_apuesta
            st.sidebar.warning(f"💥 ¡Casi! El blanco estaba en {blanco_real}. Le diste al borde y recuperás tu apuesta.")
        else:
            st.sidebar.error(f"💨 ¡Errado! El blanco apareció en la posición {blanco_real}. Perdiste ${st.session_state.tb_apuesta}.")


# --- 🥤 JUEGO 5: TRES VASOS Y UNA BOLITA (TRILEROS) ---
st.sidebar.markdown("---")
st.sidebar.header("🥤 ¿Dónde está la bolita?")

if "tl_apuesta" not in st.session_state:
    st.session_state.tl_apuesta = 50

if "tl_estado" not in st.session_state:
    st.session_state.tl_estado = "inicio"  # inicio, mezclando, adivinar, resultado
if "tl_bolita" not in st.session_state:
    st.session_state.tl_bolita = 1
if "tl_msg" not in st.session_state:
    st.session_state.tl_msg = ""

if st.session_state.bj_saldo > 0 or st.session_state.tl_estado != "inicio":
    if st.session_state.tl_estado == "inicio":
        st.session_state.tl_apuesta = st.sidebar.number_input(
            "Monto a apostar (Vasos):", min_value=10, max_value=st.session_state.bj_saldo, value=min(50, st.session_state.bj_saldo), step=10, key="apuesta_tl_val"
        )
        if st.sidebar.button("🃏 Mostrar Bolita y Mezclar", use_container_width=True):
            st.session_state.bj_saldo -= st.session_state.tl_apuesta
            st.session_state.tl_estado = "mezclando"
            st.rerun()

    if st.session_state.tl_estado == "mezclando":
        anim_vasos = st.sidebar.empty()
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
        st.sidebar.write("🔒 *La bolita ya está oculta. Elegí un vaso:*")
        cols_vasos = st.sidebar.columns(3)
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
        st.sidebar.markdown(f"### {vasos_dibujo[0]} &nbsp;&nbsp;&nbsp;&nbsp; {vasos_dibujo[1]} &nbsp;&nbsp;&nbsp;&nbsp; {vasos_dibujo[2]}")
        
        if "🎉" in st.session_state.tl_msg:
            st.sidebar.success(st.session_state.tl_msg)
        else:
            st.sidebar.error(st.session_state.tl_msg)
            
        if st.sidebar.button("🔄 Jugar otra vez", use_container_width=True, key="tl_reiniciar"):
            st.session_state.tl_estado = "inicio"
            st.rerun()


# --- 🐦 JUEGO 6: FLAPPY BIRD EN HTML5 / JS ---
st.sidebar.markdown("---")
st.sidebar.header("🐦 Flappy Bird Arcadé")
st.sidebar.write("Controles: **Espacio** o **Clic** para saltar.")

# Componente de juego interactivo incrustado en HTML5 Canvas
flappy_bird_html = """
<div style="text-align:center;">
    <canvas id="fbCanvas" width="260" height="320" style="border:2px solid #333; background:#70c5ce; border-radius:10px; cursor:pointer;"></canvas>
    <div style="font-family:sans-serif; font-size:14px; color:#555; margin-top:5px;">
        Puntaje Actual: <span id="lblScore" style="font-weight:bold; color:#d9534f;">0</span>
    </div>
</div>

<script>
    const canvas = document.getElementById("fbCanvas");
    const ctx = canvas.getContext("2d");
    const scoreLabel = document.getElementById("lblScore");

    // Parámetros físicos del juego
    let bird = { x: 40, y: 150, radius: 10, velocity: 0, gravity: 0.25, jump: -4.6 };
    let pipes = [];
    let frame = 0;
    let score = 0;
    let gameOver = false;
    let gameStarted = false;

    function resetGame() {
        bird.y = 150; bird.velocity = 0;
        pipes = []; score = 0; frame = 0;
        gameOver = false; gameStarted = false;
        scoreLabel.innerText = "0";
    }

    function spawnPipe() {
        let gap = 90;
        let minHeight = 40;
        let maxHeight = canvas.height - gap - minHeight;
        let height = Math.floor(Math.random() * (maxHeight - minHeight + 1)) + minHeight;
        pipes.push({ x: canvas.width, top: height, bottom: canvas.height - height - gap, passed: false });
    }

    function loop() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Fondo cielo simple
        ctx.fillStyle = "#70c5ce";
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Lógica física del ave
        if (gameStarted && !gameOver) {
            bird.velocity += bird.gravity;
            bird.y += bird.velocity;
        }

        // Límites de pantalla
        if (bird.y + bird.radius >= canvas.height) { bird.y = canvas.height - bird.radius; gameOver = true; }
        if (bird.y - bird.radius <= 0) { bird.y = bird.radius; bird.velocity = 0; }

        // Dibujar Ave (Un círculo amarillo simpático)
        ctx.fillStyle = "#f0ad4e";
        ctx.beginPath(); ctx.arc(bird.x, bird.y, bird.radius, 0, Math.PI * 2); ctx.fill();
        // Ojito
        ctx.fillStyle = "#000";
        ctx.beginPath(); ctx.arc(bird.x + 4, bird.y - 3, 2, 0, Math.PI * 2); ctx.fill();
        // Pico
        ctx.fillStyle = "#d9534f";
        ctx.beginPath(); ctx.moveTo(bird.x + 9, bird.y - 2); ctx.lineTo(bird.x + 15, bird.y); ctx.lineTo(bird.x + 9, bird.y + 4); ctx.fill();

        // Generación y movimiento de cañerías
        if (gameStarted && !gameOver) {
            if (frame % 100 === 0) spawnPipe();
            frame++;
        }

        for (let i = pipes.length - 1; i >= 0; i--) {
            if (gameStarted && !gameOver) pipes[i].x -= 1.8;

            // Dibujar caño superior
            ctx.fillStyle = "#5cb85c";
            ctx.fillRect(pipes[i].x, 0, 40, pipes[i].top);
            ctx.lineWidth = 2; ctx.strokeStyle = "#3e8f3e";
            ctx.strokeRect(pipes[i].x, 0, 40, pipes[i].top);

            // Dibujar caño inferior
            ctx.fillRect(pipes[i].x, canvas.height - pipes[i].bottom, 40, pipes[i].bottom);
            ctx.strokeRect(pipes[i].x, canvas.height - pipes[i].bottom, 40, pipes[i].bottom);

            // Verificar colisiones
            if (bird.x + bird.radius > pipes[i].x && bird.x - bird.radius < pipes[i].x + 40) {
                if (bird.y - bird.radius < pipes[i].top || bird.y + bird.radius > canvas.height - pipes[i].bottom) {
                    gameOver = true;
                }
            }

            // Sumar puntos al pasar el obstáculo
            if (!pipes[i].passed && pipes[i].x + 40 < bird.x) {
                pipes[i].passed = true;
                score++;
                scoreLabel.innerText = score;
                // Enviamos de vuelta el puntaje a Streamlit en tiempo real
                window.parent.postMessage({type: 'score_update', value: score}, '*');
            }

            if (pipes[i].x + 40 < 0) pipes.splice(i, 1);
        }

        // Pantallas informativas superpuestas
        if (!gameStarted) {
            ctx.fillStyle = "rgba(0,0,0,0.4)"; ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.fillStyle = "#fff"; ctx.font = "bold 16px sans-serif"; ctx.textAlign = "center";
            ctx.fillText("Hacé Clic o Espacio", canvas.width/2, canvas.height/2 - 10);
            ctx.fillText("¡Para Volar!", canvas.width/2, canvas.height/2 + 15);
        } else if (gameOver) {
            ctx.fillStyle = "rgba(0,0,0,0.6)"; ctx.fillRect(0,0,canvas.width,canvas.height);
            ctx.fillStyle = "#fff"; ctx.font = "bold 20px sans-serif"; ctx.textAlign = "center";
            ctx.fillText("GAME OVER 💥", canvas.width/2, canvas.height/2 - 15);
            ctx.font = "14px sans-serif";
            ctx.fillText("Clic para reiniciar", canvas.width/2, canvas.height/2 + 15);
        }

        requestAnimationFrame(loop);
    }

    // Manejadores de eventos de acción (Salto)
    function handleAction(e) {
        if (e.type === 'keydown' && e.code !== 'Space') return;
        if(e.type === 'keydown') e.preventDefault(); // Evitar scroll con espacio
        
        if (!gameStarted) { gameStarted = true; bird.velocity = bird.jump; }
        else if (gameOver) { resetGame(); }
        else { bird.velocity = bird.jump; }
    }

    window.addEventListener("keydown", handleAction);
    canvas.addEventListener("click", handleAction);

    resetGame();
    loop();
</script>
"""

# Inicializamos estados para transferir puntos del Canvas a Streamlit
if "fb_record_actual" not in st.session_state:
    st.session_state.fb_record_actual = 0

# Renderizamos el Widget del juego
components.html(flappy_bird_html, height=365)

# Input oculto/simulado que puede usarse para reclamar recompensas de fichas basados en tu habilidad
st.sidebar.write(f"🏆 *Tu mejor puntaje en esta sesión:* **{st.session_state.fb_record_actual} puntos**")

col_fb1, col_fb2 = st.sidebar.columns(2)
with col_fb1:
    puntos_a_reclamar = st.number_input("Puntaje a canjear:", min_value=0, value=0, step=1, key="fb_canje")
with col_fb2:
    st.write("##")
    if st.button("💰 Cobrar Fichas", use_container_width=True):
        if puntos_a_reclamar > 0:
            # Recompensa: $50 por cada caño superado
            ganancia_fb = puntos_a_reclamar * 50
            st.session_state.bj_saldo += ganancia_fb
            if puntos_a_reclamar > st.session_state.fb_record_actual:
                st.session_state.fb_record_actual = puntos_a_reclamar
            st.sidebar.success(f"¡Reclamaste ${ganancia_fb} fichas!")
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

# --- MOSTRAR RESULTADOS ---
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


