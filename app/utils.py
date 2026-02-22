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
