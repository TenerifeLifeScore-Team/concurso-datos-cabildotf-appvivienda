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
    """
    Toma el diccionario plano y lo organiza en: 
    Macro Categoría -> Grupo Slider -> Lista de Actividades
    """
    categorias_agrupadas = {}
    
    for actividad, valores in diccionario_config.items():
        macro = valores["macro_categoria"]
        grupo = valores["grupo_slider"]
        
        if macro not in categorias_agrupadas:
            categorias_agrupadas[macro] = {}
            
        if grupo not in categorias_agrupadas[macro]:
            categorias_agrupadas[macro][grupo] = []
            
        categorias_agrupadas[macro][grupo].append(actividad)
        
    return categorias_agrupadas
