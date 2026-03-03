import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
import logging

def calcular_grid_hexagonal(gdf, radio=500, porcentaje_tierra=0.45):
    """
    Genera una malla de hexágonos ajustada perfectamente a la isla,
    eliminando los que caen mayoritariamente en el mar y asignando municipio y centroide.
    """
    # 1. Convertimos a sistema métrico (UTM zona 28N)
    gdf_utm = gdf.to_crs(epsg=32628)
    
    # 2. Obtenemos los límites y añadimos margen
    xmin, ymin, xmax, ymax = gdf_utm.total_bounds
    margen = radio * 4
    xmin -= margen
    ymin -= margen
    xmax += margen
    ymax += margen
    
    # 3. Generamos los hexágonos
    ancho = radio * 2
    alto = np.sqrt(3) * radio
    
    cols = int((xmax - xmin) / (ancho * 0.75)) + 1
    filas = int((ymax - ymin) / alto) + 1
    
    poligonos = []
    logging.info(f"Generando grid base de aprox {cols}x{filas} celdas...")
    
    for c in range(cols):
        for f in range(filas):
            x_centro = xmin + c * ancho * 0.75
            y_centro = ymin + f * alto
            if c % 2 == 1:
                y_centro += alto / 2
            
            puntos = []
            for i in range(6):
                angulo_rad = np.pi / 180 * (60 * i)
                puntos.append((x_centro + radio * np.cos(angulo_rad),
                               y_centro + radio * np.sin(angulo_rad)))
            poligonos.append(Polygon(puntos))

    # 4. Crear GeoDataFrame base
    grid = gpd.GeoDataFrame({'geometry': poligonos}, crs="EPSG:32628")
    
    # 5. Filtramos hexágonos con un alto porcentaje de mar
    isla = gdf_utm.dissolve() 
    isla_geom = isla.geometry.iloc[0]
    
    logging.info("Filtrando celdas oceánicas (este proceso puede tardar varios segundos)")
    
    grid_toca = grid[grid.intersects(isla_geom)].copy()
    area_total_hex = grid_toca.geometry.area.iloc[0]
    grid_toca['area_tierra'] = grid_toca.geometry.intersection(isla_geom).area
    
    umbral_area = area_total_hex * porcentaje_tierra
    grid_final = grid_toca[grid_toca['area_tierra'] >= umbral_area].copy()
    grid_final = grid_final[['geometry']].reset_index(drop=True)

    grid_final['hex_id'] = [f"HEX_{str(i).zfill(4)}" for i in range(len(grid_final))]
    
    # 6. ENRIQUECIMIENTO: CENTROIDES Y MUNICIPIOS
    # Volvemos a GPS (Lat/Lon) primero para tener coordenadas estándar
    grid_final = grid_final.to_crs(epsg=4326)
    
    logging.info("Calculando centroides y asignando municipios...")
    
    # A) Calcular Centroides
    centroides = grid_final.geometry.centroid
    grid_final['centroide'] = [f"{round(y, 5)}, {round(x, 5)}" for y, x in zip(centroides.y, centroides.x)]
    
    # B) Asignar Municipio
    gdf_4326 = gdf.to_crs(epsg=4326)
    
    # Busca la columna del nombre del municipio en el geojson original
    # OJO: Pon aquí el nombre exacto de la columna si no es 'name' (ej: 'nombre', 'NAMEUNIT', etc.)
    col_muni = 'name' if 'name' in gdf_4326.columns else gdf_4326.columns[0]
    
    # Cruzamos usando los centroides para mayor precisión
    grid_puntos = grid_final.copy()
    grid_puntos['geometry'] = centroides
    
    cruce = gpd.sjoin(grid_puntos, gdf_4326[['geometry', col_muni]], how='left', predicate='within')
    
    # Evitamos duplicados por si un punto cae exactamente en la frontera
    cruce = cruce[~cruce.index.duplicated(keep='first')]
    grid_final['municipio'] = cruce[col_muni].fillna("Desconocido")
    
    # 7. ORDENAMOS COLUMNAS PARA QUE QUEDE LIMPIO
    columnas_ordenadas = ['hex_id', 'municipio', 'centroide', 'geometry']
    grid_final = grid_final[columnas_ordenadas]

    return grid_final