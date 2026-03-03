import logging
import os
import geopandas as gpd
import pandas as pd

def generar_tabla_maestra(ruta_grid, rutas_datasets, carpeta_salida, ruta_municipios): # <--- Añadimos parámetro
    """
    Cruza los datasets de puntos con el grid hexagonal, calcula centroides 
    y asigna el municipio correspondiente.
    """
    os.makedirs(carpeta_salida, exist_ok=True)
    
    logging.info("Cargando el grid de hexágonos y calculando centroides...")
    grid = gpd.read_file(ruta_grid)
    grid = grid.to_crs(epsg=4326) 

    # 1. CÁLCULO DE CENTROIDES Y COORDENADAS
    # Calculamos el punto central exacto de cada hexágono
    centroides = grid.geometry.centroid
    grid['centroide'] = [f"{round(y, 5)}, {round(x, 5)}" for y, x in zip(centroides.y, centroides.x)]

    # 2. REVERSE GEOCODING LOCAL (Asignar Municipio)
    logging.info("Asignando municipio a cada hexágono...")
    try:
        gdf_muni = gpd.read_file(ruta_municipios).to_crs(epsg=4326)
        
        columna_nombre_municipio = 'NOMBRE' if 'NOMBRE' in gdf_muni.columns else gdf_muni.columns[0]
        
        grid_puntos = grid.copy()
        grid_puntos['geometry'] = centroides
        
        cruce_muni = gpd.sjoin(grid_puntos, gdf_muni[['geometry', columna_nombre_municipio]], how="left", predicate="within")
        
        # Le pasamos el nombre al grid original
        grid['municipio'] = cruce_muni[columna_nombre_municipio].fillna("Desconocido")
        
    except Exception as e:
        logging.error(f"⚠️ No se pudo asignar municipio: {e}")
        grid['municipio'] = "Desconocido"

    # 3. CRUCE CON DATASETS DE ACTIVIDADES
    todos_los_puntos = []

    for nombre, ruta in rutas_datasets.items():
        if not os.path.exists(ruta):
            logging.warning(f"No se encontró '{ruta}'. Revisa el nombre.")
            continue
            
        logging.info(f"Procesando capa: {nombre}...")
        
        gdf_puntos = gpd.read_file(ruta)
        gdf_puntos = gdf_puntos.to_crs(epsg=4326)
        
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

        # Al hacer el merge, 'grid' ya tiene las columnas 'latitud', 'longitud' y 'municipio'
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