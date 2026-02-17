import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
radio_hexagono = 500  # Metros
porcentaje_minimo_tierra = 0.45  # 45% -> Si tiene menos de un 45% de tierra, lo elimina

def calcular_grid_hexagonal(gdf, radio):
    """
    Genera una malla de hexágonos ajustada perfectamente a la isla,
    eliminando los que caen mayoritariamente en el mar.
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
    
    # Sumamos +1 para asegurar que no se trunca la última fila/columna
    cols = int((xmax - xmin) / (ancho * 0.75)) + 1
    filas = int((ymax - ymin) / alto) + 1
    
    poligonos = []
    print(f"Generando grid base de aprox {cols}x{filas} celdas...")
    
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
    isla_geom = isla.geometry.iloc[0] # Geometría pura de la isla
    
    print("Filtrando celdas oceánicas")
    
    # A) Filtro rápido: Nos quedamos solo con los que al menos tocan la isla
    grid_toca = grid[grid.intersects(isla_geom)].copy()
    
    # B) Filtro fino: Calculamos cuánto del hexágono es tierra firme
    area_total_hex = grid_toca.geometry.area.iloc[0]
    
    # Calculamos la intersección real
    grid_toca['area_tierra'] = grid_toca.geometry.intersection(isla_geom).area
    
    # C) Aplicamos el umbral
    umbral_area = area_total_hex * porcentaje_minimo_tierra
    grid_final = grid_toca[grid_toca['area_tierra'] >= umbral_area].copy()
    
    # Limpiamos columnas extra
    grid_final = grid_final[['geometry']].reset_index(drop=True)
    
    # Volvemos a GPS (Lat/Lon)
    return grid_final.to_crs(epsg=4326)