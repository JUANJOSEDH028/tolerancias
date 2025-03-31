import streamlit as st
import numpy as np
import math
import pandas as pd

# Función para calcular la tolerancia del sensor para temperatura
def calcular_tolerancia_sensor_temp(rango_min, rango_max):
    temperatura_maxima = max(abs(rango_min), abs(rango_max))
    return 0.15 + 0.0020 * temperatura_maxima

# Función metrológica que calcula la incertidumbre y combina las tolerancias de todos los componentes.
# Para sensores que no sean de temperatura se usa el valor de tolerancia_sensor_input ingresado por el usuario.
def calcular_tolerancia_metrologica(errores, incertidumbre_patron, rango_calibrado,
                                    tolerancia_transmisor, tolerancia_plc, tolerancia_pantalla,
                                    sensor_type, tolerancia_sensor_input=None):
    desviacion_estandar = np.std(errores, ddof=1)
    incertidumbre_combinada = math.sqrt(desviacion_estandar**2 + incertidumbre_patron**2)
    incertidumbre_expandida = 2 * incertidumbre_combinada
    tolerancia_estricta = incertidumbre_expandida
    tolerancia_practica = round(incertidumbre_expandida + 0.05, 2)
    
    rango_min, rango_max = rango_calibrado
    span = abs(rango_max - rango_min)
    tolerancia_porcentaje = (incertidumbre_expandida / span) * 100

    # Para sensores de temperatura se calcula automáticamente; para otros se usa el valor ingresado.
    if sensor_type == 'temperatura':
        tolerancia_sensor = calcular_tolerancia_sensor_temp(rango_min, rango_max)
    else:
        if tolerancia_sensor_input is None:
            tolerancia_sensor = 0.5  # valor por defecto si no se ingresa nada
        else:
            tolerancia_sensor = tolerancia_sensor_input

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

# Clase para el cálculo normativo
class SensorCalibrationAnalyzer:
    def __init__(self, tipo_sensor, unidades):
        self.tipo_sensor = tipo_sensor
        self.unidades = unidades
        self.parametros_normativos = {
            'temperatura': {
                'clase_precision': {'alta': 0.1, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.15,
                'factor_compensacion': 0.0020
            },
            'presion': {
                'clase_precision': {'alta': 0.1, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.20,
                'factor_compensacion': 0.0025
            },
            'caudal': {
                'clase_precision': {'alta': 0.2, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.25,
                'factor_compensacion': 0.0030
            },
            'velocidad': {
                'clase_precision': {'alta': 0.1, 'estandar': 0.5, 'baja': 1.0},
                'factor_base_tolerancia': 0.18,
                'factor_compensacion': 0.0015
            }
        }
    
    def calcular_tolerancia_transmision(self, rango_calibrado, datos_calibracion, clase_precision='estandar', mostrar_detalles=False):
        if datos_calibracion.empty:
            raise ValueError("No se proporcionaron datos de calibración")
        
        puntos_calibracion = datos_calibracion['valor_medido']
        errores = datos_calibracion['error']
        error_medio = np.mean(errores)
        error_maximo = np.max(np.abs(errores))
        desviacion_estandar = np.std(errores)
        
        params = self.parametros_normativos.get(self.tipo_sensor, self.parametros_normativos['temperatura'])
        rango_min, rango_max = rango_calibrado
        rango_medicion = rango_max - rango_min
        
        precision_base = params['clase_precision'].get(clase_precision, 0.5)
        factor_base = params['factor_base_tolerancia']
        factor_compensacion = params['factor_compensacion'] * max(abs(rango_min), abs(rango_max))
        tolerancia_transmision = factor_base + factor_compensacion
        
        error_maximo_permitido_porcentual = precision_base
        error_maximo_permitido_unidades = (error_maximo_permitido_porcentual / 100) * rango_medicion
        porcentaje_tolerancia = (tolerancia_transmision / rango_medicion) * 100
        incertidumbre_combinada = math.sqrt(desviacion_estandar**2)
        incertidumbre_expandida = 2 * incertidumbre_combinada
        
        resultados = {
            'tipo_sensor': self.tipo_sensor,
            'unidades': self.unidades,
            'rango_calibrado': f"{rango_min} - {rango_max} {self.unidades}",
            'clase_precision': clase_precision,
            'error_medio': round(error_medio, 4),
            'error_maximo_medido': round(error_maximo, 4),
            'error_maximo_permitido_porcentual': round(error_maximo_permitido_porcentual, 2),
            'error_maximo_permitido_unidades': round(error_maximo_permitido_unidades, 4),
            'desviacion_estandar_error': round(desviacion_estandar, 4),
            'tolerancia_transmision': round(tolerancia_transmision, 4),
            'porcentaje_tolerancia': round(porcentaje_tolerancia, 2),
            'incertidumbre_combinada': round(incertidumbre_combinada, 4),
            'incertidumbre_expandida': round(incertidumbre_expandida, 4)
        }
        
        if mostrar_detalles:
            detalles = {
                'puntos_calibracion': list(puntos_calibracion),
                'errores': list(errores),
                'error_medio': round(error_medio, 4),
                'error_maximo': round(error_maximo, 4),
                'desviacion_estandar': round(desviacion_estandar, 4),
                'precision_base': precision_base,
                'factor_base': factor_base,
                'factor_compensacion': factor_compensacion,
                'rango_medicion': rango_medicion,
                'error_maximo_permitido_unidades': round(error_maximo_permitido_unidades, 4),
                'porcentaje_tolerancia': round(porcentaje_tolerancia, 2)
            }
            resultados['detalles'] = detalles
        
        return resultados

# --- Interfaz en Streamlit ---
st.title("Analizador Integrado de Tolerancia de Transmisión de Sensores")

# Selección de tipo de sensor
sensor_options = {
    "Temperatura": ("temperatura", "°C"),
    "Presión": ("presion", "in/W"),
    "Caudal": ("caudal", "m³/h"),
    "Velocidad": ("velocidad", "rpm")
}
sensor_elegido = st.selectbox("Seleccione el tipo de sensor", list(sensor_options.keys()))
tipo_sensor, unidades = sensor_options[sensor_elegido]

# Rango de calibración
st.subheader("Rango de Calibración")
rango_min = st.number_input(f"Ingrese límite inferior del rango ({unidades})", value=0.0)
rango_max = st.number_input(f"Ingrese límite superior del rango ({unidades})", value=100.0)

# Clase de precisión
st.subheader("Clase de Precisión")
precision_map = {"Alta precisión": "alta", "Precisión estándar": "estandar", "Baja precisión": "baja"}
clase_precision_elegida = st.selectbox("Seleccione la clase de precisión", list(precision_map.keys()))
clase_precision = precision_map[clase_precision_elegida]

# Datos de calibración
st.subheader("Datos de Calibración")
st.write("Ingrese los datos en el formato: **valor_medido,error** (una línea por dato)")
calibracion_text = st.text_area("Datos de calibración", height=150, placeholder="Ejemplo:\n25.0,0.2\n30.0,-0.1")

# Parámetros adicionales para el cálculo metrológico
st.subheader("Parámetros Metrológicos Adicionales")
incertidumbre_patron = st.number_input("Incertidumbre del patrón (°C)", value=0.1, step=0.01)
tolerancia_transmisor = st.number_input("Tolerancia del transmisor (°C)", value=0.2, step=0.01)
tolerancia_plc = st.number_input("Tolerancia de la tarjeta PLC (°C)", value=0.1, step=0.01)
tolerancia_pantalla = st.number_input("Tolerancia de la pantalla (°C)", value=0.05, step=0.01)

# Si el sensor no es de temperatura, se solicita la tolerancia del sensor como constante
if tipo_sensor != 'temperatura':
    tolerancia_sensor_input = st.number_input("Ingrese la tolerancia del sensor (constante, °C)", value=0.5, step=0.01)
else:
    tolerancia_sensor_input = None

# Opción para mostrar cálculos intermedios del método normativo
mostrar_detalles = st.checkbox("Mostrar cálculos intermedios (Normativo)")

if st.button("Calcular Tolerancia de Transmisión"):
    if not calibracion_text.strip():
        st.error("Por favor, ingrese los datos de calibración.")
    else:
        try:
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
                
                # Cálculo normativo
                analizador_normativo = SensorCalibrationAnalyzer(tipo_sensor, unidades)
                resultados_normativos = analizador_normativo.calcular_tolerancia_transmision(
                    (rango_min, rango_max), df_calibracion, clase_precision, mostrar_detalles
                )
                
                # Cálculo metrológico (se usa el valor de tolerancia_sensor_input para no temperatura)
                resultados_metrologicos = calcular_tolerancia_metrologica(
                    errores=df_calibracion['error'].to_numpy(),
                    incertidumbre_patron=incertidumbre_patron,
                    rango_calibrado=(rango_min, rango_max),
                    tolerancia_transmisor=tolerancia_transmisor,
                    tolerancia_plc=tolerancia_plc,
                    tolerancia_pantalla=tolerancia_pantalla,
                    sensor_type=tipo_sensor,
                    tolerancia_sensor_input=tolerancia_sensor_input
                )
                
                st.subheader("Resultados Normativos")
                for clave, valor in resultados_normativos.items():
                    if clave != "detalles":
                        st.write(f"**{clave.replace('_',' ').capitalize()}**: {valor}")
                if mostrar_detalles and "detalles" in resultados_normativos:
                    with st.expander("Ver cálculos intermedios (Normativo)"):
                        for det_key, det_val in resultados_normativos["detalles"].items():
                            st.write(f"**{det_key.replace('_',' ').capitalize()}**: {det_val}")
                
                st.subheader("Resultados Metrológicos")
                for clave, valor in resultados_metrologicos.items():
                    st.write(f"**{clave}**: {valor}")
                    
        except Exception as e:
            st.error(f"Error en el análisis: {e}")

