import streamlit as st
import json
import pandas as pd
import geopandas as gpd
from pathlib import Path

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
    # Puedes ajustar estos números si quieres tonos más pastel o neón
    c_rojo     = [255, 60, 60]    # 0.0 (Malo)
    c_amarillo = [255, 210, 0]    # 3.3 (Regular)
    c_verde    = [50, 200, 80]    # 6.6 (Bueno)
    c_azul     = [0, 110, 255]    # 10.0 (Excelente)

    # 3. Función auxiliar para mezclar dos colores
    def mezclar(color_inicio, color_fin, factor):
        # factor va de 0.0 a 1.0
        r = int(color_inicio[0] + (color_fin[0] - color_inicio[0]) * factor)
        g = int(color_inicio[1] + (color_fin[1] - color_inicio[1]) * factor)
        b = int(color_inicio[2] + (color_fin[2] - color_inicio[2]) * factor)
        return [r, g, b]

    # 4. Lógica de tramos (Interpolación)
    rgb = [0, 0, 0]

    if val <= 3.33:
        # Tramo: Rojo -> Amarillo
        factor = val / 3.33
        rgb = mezclar(c_rojo, c_amarillo, factor)
        
    elif val <= 6.66:
        # Tramo: Amarillo -> Verde
        factor = (val - 3.33) / 3.33
        rgb = mezclar(c_amarillo, c_verde, factor)
        
    else:
        # Tramo: Verde -> Azul
        factor = (val - 6.66) / 3.34
        rgb = mezclar(c_verde, c_azul, factor)

    # 5. Añadimos transparencia (Alpha) al final
    # 160 es semi-transparente (0-255)
    return rgb # + [160]