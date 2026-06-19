import streamlit as st
import numpy as np
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


# --- 🕹️ JUEGO: TRES EN RAYA (AL FINAL DE LA BARRA LATERAL) ---
st.sidebar.markdown("---")
st.sidebar.header("🎮 Tres en Raya (Para pasar el rato)")

# Inicializar variables del juego en el estado de la sesión
if "tablero" not in st.session_state:
    st.session_state.tablero = [""] * 9
if "turno" not in st.session_state:
    st.session_state.turno = "Jugador 1 (X)"
if "ganador" not in st.session_state:
    st.session_state.ganador = None

def verificar_ganador():
    t = st.session_state.tablero
    combinaciones = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # Horizontales
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # Verticales
        [0, 4, 8], [2, 4, 6]             # Diagonales
    ]
    for combo in combinaciones:
        if t[combo[0]] == t[combo[1]] == t[combo[2]] != "":
            return "Jugador 1" if t[combo[0]] == "X" else "Jugador 2"
    if "" not in t:
        return "Empate"
    return None

# Mostrar el turno actual o el resultado
if st.session_state.ganador:
    if st.session_state.ganador == "Empate":
        st.sidebar.warning("¡Es un Empate! 🤝")
    else:
        st.sidebar.success(f"🎉 ¡Ganó el {st.session_state.ganador}!")
else:
    st.sidebar.info(f"👉 Turno de: **{st.session_state.turno}**")

# Dibujar la cuadrícula del tablero utilizando columnas de Streamlit
cols_juego = st.sidebar.columns(3)
for i in range(9):
    with cols_juego[i % 3]:
        contenido = st.session_state.tablero[i]
        label_boton = contenido if contenido != "" else " "
        
        # Desactivar botón si ya se jugó o si hay un ganador
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

# Botón para reiniciar el juego
if st.sidebar.button("🔄 Reiniciar Partida", use_container_width=True):
    st.session_state.tablero = [""] * 9
    st.session_state.turno = "Jugador 1 (X)"
    st.session_state.ganador = None
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
        st.metric(label="Consumo de Potencia Total (Máximo: " + str(limite_watts) + " W)", value=f"{tot_watts:.2f} Watts")
       
