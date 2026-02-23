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
    max_posible_teorico = 0.0  # <--- AQUÍ ACUMULAREMOS LA PUNTUACIÓN PERFECTA
    
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
        max_valor_real = columna_datos.max()
        
        # Si nadie en la isla tiene esto, no suma puntos a nadie, 
        # PERO tampoco debería sumar al teórico (porque es imposible conseguirlo)
        if max_valor_real == 0:
            continue
            
        # --- NORMALIZACIÓN INTERNA (0.0 a 1.0) ---
        # El mejor hexágono en ESTA actividad tendrá un 1.0
        columna_normalizada = columna_datos / max_valor_real
        
        # --- FACTORES ---
        peso_base = config['peso']       # Importancia fija (Excel)
        grupo = config['grupo_slider']
        val_slider = sliders_usuario.get(grupo, 3) 
        
        # Factor usuario (1 a 5) -> (0.2 a 1.0)
        factor_usuario = val_slider / 5.0
        
        # --- CÁLCULO DE PUNTOS REALES ---
        puntos_actividad = columna_normalizada * peso_base * factor_usuario
        score_acumulado += puntos_actividad
        
        # --- CÁLCULO DEL MÁXIMO TEÓRICO ---
        # Si un hexágono tuviera un 1.0 en esta actividad, sumaría esto:
        puntos_perfectos_actividad = 1.0 * peso_base * factor_usuario
        max_posible_teorico += puntos_perfectos_actividad

    # 3. Normalización Final ABSOLUTA (0 - 10)
    # Dividimos lo que tiene el hexágono entre lo MÁXIMO que se podría tener
    if max_posible_teorico > 0:
        score_final = (score_acumulado / max_posible_teorico) * 10
    else:
        score_final = score_acumulado 

    gdf_result['score_final'] = score_final.round(2) # 2 decimales para más precisión
    
    return gdf_result