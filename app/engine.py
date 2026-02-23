import pandas as pd
import numpy as np
import geopandas as gpd

def calcular_lifescore_vectorial(gdf_saturado, diccionario_config, sliders_usuario, checks_usuario):
    """
    Calcula el LifeScore sobre un GeoDataFrame.
    
    Args:
        gdf_saturado (gpd.GeoDataFrame): Tabla con geometría y cols 'sat_...'
        diccionario_config (dict): Configuración que leemos del Excel.
        sliders_usuario (dict): {Grupo: 1-10}
        checks_usuario (dict): {actividad_original: True/False}
    
    Returns:
        gpd.GeoDataFrame: Copia con columna 'score_final' y geometría lista para pintar.
    """
    # 1. Trabajamos sobre copia para no alterar el caché
    gdf_result = gdf_saturado.copy()
    
    # Vector de ceros para acumular puntos
    score_acumulado = np.zeros(len(gdf_result))
    
    # 2. Iteramos sobre las actividades del DICCIONARIO (nuestra verdad)
    for actividad_tecnica, config in diccionario_config.items():
        
        # A. Construimos el nombre de la columna en el GeoJSON
        # La estructura es: "sat_" + nombre actividad
        columna_geojson = f"sat_{actividad_tecnica}"
        
        # B. Verificaciones de seguridad
        # 1. ¿El usuario la ha activado?
        if not checks_usuario.get(actividad_tecnica, True):
            continue
        
        # 2. ¿Existe esa columna 'sat_...' en el archivo?
        if columna_geojson not in gdf_result.columns:
            # Si no existe, la saltamos silenciosamente (o loggeamos warning)
            continue
            
        # C. Obtenemos factores (Peso * Slider)
        peso_base = config['peso']       # Ponderación del experto
        grupo = config['grupo_slider']   # Ej: "Salud vital"
        val_slider = sliders_usuario.get(grupo, 5) # 1 a 10
        
        # Normalizamos slider (1 -> 0.1, 10 -> 1.0)
        factor_usuario = val_slider / 10.0
        
        # D. CÁLCULO VECTORIAL
        # Sumamos: (Cantidad Saturada * Peso * Importancia)
        score_acumulado += gdf_result[columna_geojson] * peso_base * factor_usuario

    # 3. Normalización (0 - 100)
    max_score = score_acumulado.max()
    
    if max_score > 0:
        score_final = (score_acumulado / max_score) * 100
    else:
        score_final = score_acumulado # Todo ceros
        
    # Añadimos la columna al GeoDataFrame
    gdf_result['score_final'] = score_final.round(1)
    
    # Devolvemos el GeoDataFrame completo (con geometry)
    # para que PyDeck o Folium puedan pintarlo.
    return gdf_result