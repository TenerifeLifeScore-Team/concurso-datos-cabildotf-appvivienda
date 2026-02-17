import geopandas as gpd
import pandas as pd
import json
import logging

def aplicar_limites(ruta_maestra, ruta_diccionario, ruta_salida):
    logging.info("Cargando Tabla Maestra y Diccionario...")

    gdf = gpd.read_file(ruta_maestra)

    with open(ruta_diccionario, 'r', encoding='utf-8') as f:
        diccionario_config = json.load(f)

    logging.info("Aplicando límites de saturación a cada actividad...")

    columnas_q = [col for col in gdf.columns if col.startswith('q_')]
    actividades_procesadas = 0
    actividades_no_encontradas = []
    
    nuevas_columnas = {}

    for col_q in columnas_q:
        actividad = col_q.replace('q_', '')
        col_sat = f"sat_{actividad}"
        
        if actividad in diccionario_config:
            limite = diccionario_config[actividad]['limite']
            nuevas_columnas[col_sat] = gdf[col_q].clip(upper=limite)
            
            logging.info(f"   - {actividad}: Límite fijado en {limite}.")
            actividades_procesadas += 1
        else:
            actividades_no_encontradas.append(actividad)
            nuevas_columnas[col_sat] = gdf[col_q]

    gdf = pd.concat([gdf, pd.DataFrame(nuevas_columnas)], axis=1)

    if actividades_no_encontradas:
        logging.warning("Actividades en el mapa pero NO en el Excel:")
        for act in actividades_no_encontradas:
            logging.warning(f"   - {act} (Procesado sin límite)")

    gdf.to_file(ruta_salida, driver="GeoJSON")
    logging.info(f"Se han saturado {actividades_procesadas} actividades.")
    logging.info(f"✅ Tabla saturada guardada en: {ruta_salida}")
    
    return gdf