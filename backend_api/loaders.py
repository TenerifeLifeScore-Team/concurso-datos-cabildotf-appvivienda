import geopandas as gpd
import pandas as pd
import json
import os

# Ruta base donde están tus datos procesados
DATA_PATH = "data-processed"

def cargar_puntos_maestros():
    """Carga el GeoJSON de puntos (hospitales, bares, etc.) para el radar."""
    path = os.path.join(DATA_PATH, "puntos_maestros.geojson")
    if os.path.exists(path):
        return gpd.read_file(path)
    return None

def cargar_datos_mapa():
    """Carga el grid de hexágonos saturado para el mapa global."""
    path = os.path.join(DATA_PATH, "tabla_saturada_suavizada.geojson")
    if os.path.exists(path):
        return gpd.read_file(path)
    return None

def cargar_configuracion():
    """Carga el diccionario de pesos y categorías."""
    path = os.path.join(DATA_PATH, "diccionario_config.json")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)