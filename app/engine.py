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
    # 1. Copia de seguridad
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
            continue
            
        # --- DATOS CRUDOS ---
        columna_datos = gdf_result[columna_geojson]
        
        # === EL TRUCO MAESTRO: NORMALIZACIÓN ===
        # Buscamos el valor máximo de ESTA actividad en toda la isla
        max_valor_columna = columna_datos.max()
        
        # Si nadie en toda la isla tiene esta actividad, pasamos
        if max_valor_columna == 0:
            continue
            
        # Convertimos los datos a una escala 0.0 - 1.0
        # Ahora 1 museo vale tanto como 200 cafeterías (ambos son el "máximo" en su categoría)
        columna_normalizada = columna_datos / max_valor_columna
        
        # --- FACTORES ---
        peso_base = config['peso']       # Importancia fija (Excel)
        grupo = config['grupo_slider']
        val_slider = sliders_usuario.get(grupo, 3) 
        
        # Hacemos que el slider sea más agresivo (potencia)
        # Slider 1 -> x0.2 | Slider 5 -> x1.0
        factor_usuario = val_slider / 5.0
        
        # --- CÁLCULO VECTORIAL ---
        # Usamos la columna NORMALIZADA en vez de la original
        puntos_actividad = columna_normalizada * peso_base * factor_usuario
        
        score_acumulado += puntos_actividad

    # 3. Normalización Final (0 - 10)
    max_score_total = score_acumulado.max()
    
    if max_score_total > 0:
        score_final = (score_acumulado / max_score_total) * 10
    else:
        score_final = score_acumulado 

    gdf_result['score_final'] = score_final.round(2) # 2 decimales para más precisión
    
    return gdf_result