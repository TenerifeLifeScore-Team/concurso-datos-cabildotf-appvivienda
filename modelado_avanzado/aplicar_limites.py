import geopandas as gpd
import json
import logging

def aplicar_limites(ruta_maestra, ruta_diccionario, ruta_salida):
    """
    Lee la tabla maestra y aplica los límites de saturación desde el JSON.
    """
    logging.info("📥 Cargando Tabla Maestra y Diccionario...")

    gdf = gpd.read_file(ruta_maestra)

    with open(ruta_diccionario, 'r', encoding='utf-8') as f:
        diccionario_config = json.load(f)

    logging.info("🧮 Aplicando límites de saturación a cada actividad...")

    columnas_q = [col for col in gdf.columns if col.startswith('q_')]
    actividades_procesadas = 0
    actividades_no_encontradas = []

    for col_q in columnas_q:
        actividad = col_q.replace('q_', '')
        
        if actividad in diccionario_config:
            limite = diccionario_config[actividad]['limite']
            col_sat = f"sat_{actividad}"
            gdf[col_sat] = gdf[col_q].clip(upper=limite)
            
            logging.info(f"   ✔️ {actividad}: Límite fijado en {limite}.")
            actividades_procesadas += 1
        else:
            actividades_no_encontradas.append(actividad)
            gdf[f"sat_{actividad}"] = gdf[col_q]

    if actividades_no_encontradas:
        logging.warning("⚠️ AVISO: Actividades en el mapa pero NO en el Excel:")
        for act in actividades_no_encontradas:
            logging.warning(f"   - {act} (Procesado sin límite)")

    # Guardado
    gdf.to_file(ruta_salida, driver="GeoJSON")
    logging.info(f"🚀 ¡ÉXITO! Se han saturado {actividades_procesadas} actividades.")
    logging.info(f"💾 Tabla saturada guardada en: {ruta_salida}")
    
    return gdf