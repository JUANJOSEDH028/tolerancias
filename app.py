import streamlit as st
import numpy as np
import math
import pandas as pd

def calcular_tolerancia_sensor(rango_min, rango_max, sensor_type, tolerancia_sensor_input=None):
    # Para temperatura se calcula automáticamente; para otros se usa el valor ingresado
    if sensor_type == "temperatura":
        return 0.15 + 0.0020 * max(abs(rango_min), abs(rango_max))
    else:
        return tolerancia_sensor_input if tolerancia_sensor_input is not None else 0.5

def calcular_tolerancia_metrologica(errores, incertidumbre_patron, rango_calibrado,
                                    tolerancia_transmisor, tolerancia_plc, tolerancia_pantalla,
                                    sensor_type, tolerancia_sensor_input=None):
    # Cálculo de la desviación estándar (usando ddof=1 para muestras)
    desviacion_estandar = np.std(errores, ddof=1)
    # Incertidumbre combinada según GUM
    incertidumbre_combinada = math.sqrt(desviacion_estandar**2 + incertidumbre_patron**2)
    # Incertidumbre expandida (k=2 ~95% de confianza)
    incertidumbre_expandida = 2 * incertidumbre_combinada
    tolerancia_estricta = incertidumbre_expandida
    # Ajuste práctico: se suma un margen fijo de 0.05 °C
    tolerancia_practica = round(incertidumbre_expandida + 0.05, 2)
    
    rango_min, rango_max = rango_calibrado
    span = abs(rango_max - rango_min)
    tolerancia_porcentaje = (incertidumbre_expandida / span) * 100
    
    # Tolerancia del sensor: calculada automáticamente para temperatura o ingresada para otros
    tolerancia_sensor = calcular_tolerancia_sensor(rango_min, rango_max, sensor_type, tolerancia_sensor_input)
    
    # Combinación en cuadratura de todas las tolerancias de la cadena
    tolerancia_total = math.sqrt(
        tolerancia_sensor**2 +
        tolerancia_transmisor**2 +
        tolerancia_plc**2 +
        tolerancia_pantalla**2
    )
    
    return {
        "Tolerancia basada en incertidumbre expandida (°C)": round(tolerancia_estricta, 4),
        "Tolerancia con ajuste práctico (°C)": tolerancia_practica,
        "Tolerancia en porcentaje del rango calibrado (%)": round(tolerancia_porcentaje, 2),
        "Tolerancia total considerando todos los componentes (°C)": round(tolerancia_total, 2)
    }

# --- Interfaz en Streamlit ---
st.title("Analizador Metrológico de Tolerancia de Transmisión de Sensores")

# Selección de tipo de sensor
sensor_options = {
    "Temperatura": "temperatura",
    "Presión": "presion",
    "Caudal": "caudal",
    "Velocidad": "velocidad"
}
sensor_elegido = st.selectbox("Seleccione el tipo de sensor", list(sensor_options.keys()))
sensor_type = sensor_options[sensor_elegido]
unidad = "°C" if sensor_type == "temperatura" else ("bar" if sensor_type == "presion" else ("m³/h" if sensor_type == "caudal" else "rpm"))

# Rango de calibración
st.subheader("Rango de Calibración")
rango_min = st.number_input(f"Ingrese límite inferior del rango ({unidad})", value=0.0)
rango_max = st.number_input(f"Ingrese límite superior del rango ({unidad})", value=100.0)

# Datos de calibración
st.subheader("Datos de Calibración")
st.write("Ingrese los datos en el formato: **valor_medido,error** (una línea por dato)")
calibracion_text = st.text_area("Datos de calibración", height=150, placeholder="Ejemplo:\n25.0,0.2\n30.0,-0.1")

# Parámetros metrológicos adicionales
st.subheader("Parámetros Metrológicos Adicionales")
incertidumbre_patron = st.number_input("Incertidumbre del patrón (°C)", value=0.1, step=0.01)
tolerancia_transmisor = st.number_input("Tolerancia del transmisor (°C)", value=0.2, step=0.01)
tolerancia_plc = st.number_input("Tolerancia de la tarjeta PLC (°C)", value=0.1, step=0.01)
tolerancia_pantalla = st.number_input("Tolerancia de la pantalla (°C)", value=0.05, step=0.01)

# Para sensores distintos de temperatura, se solicita la tolerancia del sensor como constante
if sensor_type != "temperatura":
    tolerancia_sensor_input = st.number_input("Ingrese la tolerancia del sensor (constante, °C)", value=0.5, step=0.01)
else:
    tolerancia_sensor_input = None

if st.button("Calcular Tolerancia de Transmisión"):
    if not calibracion_text.strip():
        st.error("Por favor, ingrese los datos de calibración.")
    else:
        datos = []
        for linea in calibracion_text.splitlines():
            linea = linea.strip()
            if linea:
                partes = linea.split(',')
                if len(partes) != 2:
                    st.error("Cada línea debe contener dos valores separados por coma.")
                    break
                valor_medido, error = map(float, partes)
                datos.append({'valor_medido': valor_medido, 'error': error})
        if not datos:
            st.error("No se procesaron datos válidos.")
        else:
            df_calibracion = pd.DataFrame(datos)
            resultados = calcular_tolerancia_metrologica(
                errores=df_calibracion['error'].to_numpy(),
                incertidumbre_patron=incertidumbre_patron,
                rango_calibrado=(rango_min, rango_max),
                tolerancia_transmisor=tolerancia_transmisor,
                tolerancia_plc=tolerancia_plc,
                tolerancia_pantalla=tolerancia_pantalla,
                sensor_type=sensor_type,
                tolerancia_sensor_input=tolerancia_sensor_input
            )
            st.subheader("Resultados Metrológicos")
            for clave, valor in resultados.items():
                st.write(f"**{clave}**: {valor}")

