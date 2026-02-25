import streamlit as st
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderUnavailable
import re

RAIZ = Path(__file__).parent.parent

@st.cache_data
def cargar_configuracion():
    """Carga el diccionario en caché para no leer el JSON constantemente."""
    ruta_json = RAIZ / "data-proccesed" / "diccionario_config.json"
    with open(ruta_json, "r", encoding="utf-8") as f:
        diccionario = json.load(f)
    return diccionario

@st.cache_data
def obtener_jerarquia_categorias(diccionario_config):

    jerarquia_web = {}
    mapa_traductor = {}

    for actividad, valor in diccionario_config.items():

        macro = valor["macro_categoria"]
        grupo_slider = valor["grupo_slider"]
        nombre_ui = valor["nombre_ui"]

        if macro not in jerarquia_web:
            jerarquia_web[macro] = {}
        if grupo_slider not in jerarquia_web[macro]:
            jerarquia_web[macro][grupo_slider] = set()
        jerarquia_web[macro][grupo_slider].add(nombre_ui)

        if nombre_ui not in mapa_traductor:
            mapa_traductor[nombre_ui] = []
        mapa_traductor[nombre_ui].append(actividad)

    for macro in jerarquia_web:
        for grupo in jerarquia_web[macro]:
            jerarquia_web[macro][grupo] = sorted(list(jerarquia_web[macro][grupo]))

    return jerarquia_web, mapa_traductor     


def obtener_color_por_score_discreto(score):
    """
    Devuelve un color RGB según la nota (0-100).
    Rojo (0) -> Amarillo (50) -> Verde (100)
    """
    if score < 20:
        return [255, 0, 0, 160]      # Rojo fuerte
    elif score < 40:
        return [255, 128, 0, 160]    # Naranja
    elif score < 60:
        return [255, 255, 0, 160]    # Amarillo
    elif score < 80:
        return [128, 255, 0, 160]    # Verde claro
    else:
        return [0, 255, 0, 160]      # Verde puro


def obtener_color_por_score(score):
    """
    Genera un gradiente suave interpolando colores.
    Escala 0-10: Rojo -> Amarillo -> Verde -> Azul
    """
    # 1. Aseguramos que el score esté entre 0 y 10
    val = max(0, min(10, float(score)))

    # 2. Definimos los colores clave [R, G, B]
    c_rojo     = [255, 60, 60]    # 0.0 (Crítico)
    c_naranja  = [255, 160, 0]    # 1.5 (Ya tienes algo)
    c_amarillo = [255, 220, 0]    # 4.0 (Aceptable)
    c_verde    = [50, 200, 80]    # 7.0 (Bueno)
    c_azul     = [0, 110, 255]    # 10.0 (Top)

    # 3. Función auxiliar para mezclar dos colores
    def mezclar(color_inicio, color_fin, factor):
        # factor va de 0.0 a 1.0
        r = int(color_inicio[0] + (color_fin[0] - color_inicio[0]) * factor)
        g = int(color_inicio[1] + (color_fin[1] - color_inicio[1]) * factor)
        b = int(color_inicio[2] + (color_fin[2] - color_inicio[2]) * factor)
        return [r, g, b]

    # 4. Lógica de tramos (Interpolación)
    rgb = [0, 0, 0]

    # TRAMO 1: Salida rápida del rojo (0.0 a 1.5)
    # En cuanto tienes un poco de puntuación, te vas al naranja
    if val <= 1.5:
        factor = val / 1.5
        rgb = mezclar(c_rojo, c_naranja, factor)
    
    # TRAMO 2: Naranja a Amarillo (1.5 a 4.0)
    elif val <= 4.0:
        factor = (val - 1.5) / 2.5
        rgb = mezclar(c_naranja, c_amarillo, factor)
        
    # TRAMO 3: Amarillo a Verde (4.0 a 7.0)
    elif val <= 7.0:
        factor = (val - 4.0) / 3.0
        rgb = mezclar(c_amarillo, c_verde, factor)
        
    # TRAMO 4: Verde a Azul (7.0 a 10.0)
    else:
        factor = (val - 7.0) / 3.0
        rgb = mezclar(c_verde, c_azul, factor)

    # 5. Añadimos transparencia (Alpha) al final
    # 160 es semi-transparente (0-255)
    return rgb # + [160]


@st.cache_data(show_spinner=False)
def obtener_coordenadas(input_usuario):

    if not input_usuario or str(input_usuario).strip() == "":
        return None
        
    input_limpio = str(input_usuario).strip()
    res = son_coordenadas(input_limpio)

    if res is not None:
        return res

    geolocator = Nominatim(user_agent="Tenerife_LifeScore_App")
    direccion_completa = f"{input_limpio}, Tenerife, Canarias, España"
    
    try:
        location = geolocator.geocode(direccion_completa, timeout=10)
        if location:
            return (location.latitude, location.longitude)
        return None
            
    except (GeocoderTimedOut, GeocoderUnavailable):
        return None


def son_coordenadas(input_usuario):
    
    patron = r"^\s*\(?\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)?\s*$"
    
    match = re.match(patron, input_usuario)
    
    if match:
        # Extraemos los dos números que Regex ha capturado
        lat = float(match.group(1))
        lon = float(match.group(2))
        
        # Última comprobación matemática de seguridad
        if -90 <= lat <= 90 and -180 <= lon <= 180:
            return (lat, lon)
            
    return None
