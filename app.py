import streamlit as st
import numpy as np
import math
import pandas as pd

class SensorCalibrationAnalyzer:
    def __init__(self, tipo_sensor, unidades):
        """
        Inicializar analizador de calibración de sensores.
        
        :param tipo_sensor: Tipo de sensor 
        :param unidades: Unidades de medida del sensor
        """
        self.tipo_sensor = tipo_sensor
        self.unidades = unidades
        
        # Configuraciones según normas internacionales
        self.parametros_normativos = {
            'temperatura': {
                'clase_precision': {
                    'alta': 0.1,     # Alta precisión
                    'estandar': 0.5, # Precisión estándar
                    'baja': 1.0      # Baja precisión
                },
                'factor_base_tolerancia': 0.15,
                'factor_compensacion': 0.0020
            },
            'presion': {
                'clase_precision': {
                    'alta': 0.1,
                    'estandar': 0.5,
                    'baja': 1.0
                },
                'factor_base_tolerancia': 0.20,
                'factor_compensacion': 0.0025
            },
            'caudal': {
                'clase_precision': {
                    'alta': 0.2,
                    'estandar': 0.5,
                    'baja': 1.0
                },
                'factor_base_tolerancia': 0.25,
                'factor_compensacion': 0.0030
            },
            'velocidad': {
                'clase_precision': {
                    'alta': 0.1,
                    'estandar': 0.5,
                    'baja': 1.0
                },
                'factor_base_tolerancia': 0.18,
                'factor_compensacion': 0.0015
            }
        }
    
    def calcular_tolerancia_transmision(self, rango_calibrado, datos_calibracion, clase_precision='estandar'):
        """
        Calcular la tolerancia de transmisión basada en datos de calibración.
        
        :param rango_calibrado: Rango de calibración (tupla de min y max)
        :param datos_calibracion: DataFrame con datos de calibración
        :param clase_precision: Nivel de precisión del instrumento
        :return: Diccionario de métricas de tolerancia
        """
        # Validar datos de calibración
        if datos_calibracion.empty:
            raise ValueError("No se proporcionaron datos de calibración")
        
        # Extraer puntos de calibración
        puntos_calibracion = datos_calibracion['valor_medido']
        errores = datos_calibracion['error']
        
        # Cálculo de estadísticas de error
        error_medio = np.mean(errores)
        error_maximo = np.max(np.abs(errores))
        desviacion_estandar = np.std(errores)
        
        # Cálculo de tolerancia base
        params = self.parametros_normativos.get(self.tipo_sensor, 
                                                self.parametros_normativos['temperatura'])
        rango_min, rango_max = rango_calibrado
        rango_medicion = rango_max - rango_min
        
        # Parámetros de precisión según normas
        precision_base = params['clase_precision'].get(clase_precision, 0.5)
        
        # Cálculo de tolerancia de transmisión
        factor_base = params['factor_base_tolerancia']
        factor_compensacion = params['factor_compensacion'] * max(abs(rango_min), abs(rango_max))
        tolerancia_transmision = factor_base + factor_compensacion
        
        # Cálculo de error máximo permitido en unidades físicas
        error_maximo_permitido_porcentual = precision_base
        error_maximo_permitido_unidades = (error_maximo_permitido_porcentual / 100) * rango_medicion
        
        # Porcentaje de tolerancia
        porcentaje_tolerancia = (tolerancia_transmision / rango_medicion) * 100
        
        # Cálculo de incertidumbre
        incertidumbre_combinada = math.sqrt(desviacion_estandar**2)
        incertidumbre_expandida = 2 * incertidumbre_combinada  # Factor de cobertura k=2
        
        return {
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

# Interfaz de usuario en Streamlit

st.title("Analizador de Tolerancia de Transmisión de Sensores")

# Selección de tipo de sensor
sensor_options = {
    "Temperatura": ("temperatura", "°C"),
    "Presión": ("presion", "in/W"),
    "Caudal": ("caudal", "m³/h"),
    "Velocidad": ("velocidad", "rpm")
}
sensor_elegido = st.selectbox("Seleccione el tipo de sensor", list(sensor_options.keys()))
tipo_sensor, unidades = sensor_options[sensor_elegido]

# Ingreso del rango de calibración
st.subheader("Rango de Calibración")
rango_min = st.number_input(f"Ingrese límite inferior del rango ({unidades})", value=0.0)
rango_max = st.number_input(f"Ingrese límite superior del rango ({unidades})", value=100.0)

# Selección de clase de precisión
st.subheader("Clase de Precisión")
precision_map = {
    "Alta precisión": "alta",
    "Precisión estándar": "estandar",
    "Baja precisión": "baja"
}
clase_precision_elegida = st.selectbox("Seleccione la clase de precisión", list(precision_map.keys()))
clase_precision = precision_map[clase_precision_elegida]

# Ingreso de datos de calibración
st.subheader("Datos de Calibración")
st.write("Ingrese los datos de calibración en el siguiente formato:")
st.write("**valor_medido,error** (separados por coma) y una línea por cada dato.")
calibracion_text = st.text_area("Datos de calibración", height=150, placeholder="Ejemplo:\n25.0,0.2\n30.0,-0.1")

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
                # Crear instancia del analizador
                analizador = SensorCalibrationAnalyzer(tipo_sensor, unidades)
                # Calcular tolerancia de transmisión
                resultados = analizador.calcular_tolerancia_transmision((rango_min, rango_max), df_calibracion, clase_precision)
                
                st.subheader("Resultados de Análisis de Tolerancia")
                for clave, valor in resultados.items():
                    st.write(f"**{clave.replace('_',' ').capitalize()}**: {valor}")
        except Exception as e:
            st.error(f"Error en el análisis: {e}")
