import geopandas as gpd
import pandas as pd
import os
import logging

def generar_tabla_maestra(ruta_grid, rutas_datasets, carpeta_salida):
    """
    Cruza los datasets de puntos con el grid hexagonal y genera la tabla maestra.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    
    logging.info("Cargando el grid de hexágonos...")
    grid = gpd.read_file(ruta_grid)
    grid = grid.to_crs(epsg=4326) # Aseguramos sistema de coordenadas estándar

    grid = grid[['hex_id', 'geometry']]  # Eliminamos la información de los municipios y centroides aquí

    todos_los_puntos = []

    for nombre, ruta in rutas_datasets.items():
        if not os.path.exists(ruta):
            logging.warning(f"No se encontró '{ruta}'. Revisa el nombre.")
            continue
            
        logging.info(f"Procesando capa: {nombre}...")
        
        gdf_puntos = gpd.read_file(ruta)
        gdf_puntos = gdf_puntos.to_crs(epsg=4326)
        
        # El cruce espacial
        puntos_con_hex = gpd.sjoin(gdf_puntos, grid[['hex_id', 'geometry']], how="inner", predicate="within")
        
        if 'index_right' in puntos_con_hex.columns:
            puntos_con_hex = puntos_con_hex.drop(columns=['index_right'])
        
        todos_los_puntos.append(puntos_con_hex)

    if len(todos_los_puntos) > 0:
        logging.info("Construyendo la Tabla Maestra...")
        
        df_global = pd.concat(todos_los_puntos, ignore_index=True)
        conteos = df_global.groupby(['hex_id', 'tipo']).size().reset_index(name='cantidad')
        
        tabla_pivote = conteos.pivot(index='hex_id', columns='tipo', values='cantidad').fillna(0)
        tabla_pivote.columns = [f"q_{col}" for col in tabla_pivote.columns]
        tabla_pivote = tabla_pivote.reset_index()

        tabla_maestra = grid.merge(tabla_pivote, on='hex_id', how='left')
        
        columnas_q = [col for col in tabla_maestra.columns if col.startswith('q_')]
        tabla_maestra[columnas_q] = tabla_maestra[columnas_q].fillna(0)
        
        ruta_maestra = f"{carpeta_salida}/tabla_maestra.geojson"
        tabla_maestra.to_file(ruta_maestra, driver="GeoJSON")
        logging.info(f"✅ Tabla Maestra generada en: {ruta_maestra}")
        
        return tabla_maestra
    else:
        logging.error("No se procesó ningún archivo.")
        return None