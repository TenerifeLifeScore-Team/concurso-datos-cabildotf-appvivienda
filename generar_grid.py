import geopandas as gpd
from shapely.geometry import Polygon
import numpy as np
import matplotlib.pyplot as plt

# --- CONFIGURACIÓN ---
radio_hexagono = 500  # Metros (Cuanto más pequeño, más precisión, pero más lento)
archivo_municipios = "data-raw/municipios-tenerife.geojson"

def calcular_grid_hexagonal(gdf, radio):
    """
    Genera una malla de hexágonos que cubre toda la geometría de la isla.
    """
    # 1. Convertimos a sistema métrico (UTM zona 28N) para medir en metros
    # Usamos EPSG:32628 que es la proyección estándar para Canarias
    gdf_utm = gdf.to_crs(epsg=32628)
    
    # 2. Obtenemos los límites de la isla
    xmin, ymin, xmax, ymax = gdf_utm.total_bounds
    
    # 3. Generamos los hexágonos matemáticamente
    ancho = radio * 2
    alto = np.sqrt(3) * radio
    
    cols = int((xmax - xmin) / (ancho * 0.75))
    filas = int((ymax - ymin) / alto)
    
    poligonos = []
    
    print(f"Generando grid de aprox {cols}x{filas} celdas...")
    
    for c in range(cols):
        for f in range(filas):
            x_centro = xmin + c * ancho * 0.75 # Desplazamiento horizontal
            y_centro = ymin + f * alto
            if c % 2 == 1:
                y_centro += alto / 2
            
            # Crear hexágono
            puntos = []
            for i in range(6):
                angulo_rad = np.pi / 180 * (60 * i)
                puntos.append((x_centro + radio * np.cos(angulo_rad),
                               y_centro + radio * np.sin(angulo_rad)))
            poligonos.append(Polygon(puntos))

    # 4. Crear GeoDataFrame con los hexágonos
    grid = gpd.GeoDataFrame({'geometry': poligonos}, crs="EPSG:32628")
    
    # 5. FILTRADO: Nos quedamos solo con los hexágonos que caen DENTRO de Tenerife
    # Unimos todos los municipios en una sola forma (la isla entera)
    isla = gdf_utm.dissolve() 
    
    print("Recortando el grid a la forma de la isla (esto puede tardar unos segundos)...")
    # Filtramos los hexágonos que tocan la isla
    grid_final = gpd.sjoin(grid, isla, how="inner", predicate="intersects")
    
    # Limpiamos columnas extra generadas por el sjoin
    grid_final = grid_final[['geometry']].reset_index(drop=True)
    
    # Volvemos a coordenadas GPS (Lat/Lon) para el futuro mapa web
    return grid_final.to_crs(epsg=4326)

# --- EJECUCIÓN ---
try:
    print("Cargando mapa de municipios...")
    municipios = gpd.read_file(archivo_municipios)
    
    # Generar el grid
    mi_grid = calcular_grid_hexagonal(municipios, radio_hexagono)
    
    print(f"[EXITO] Hemos dividido Tenerife en {len(mi_grid)} sectores hexagonales.")
    
    # Guardar el resultado para no tener que calcularlo siempre
    ruta_salida = "data/grid_tenerife.geojson"
    mi_grid.to_file(ruta_salida, driver="GeoJSON")
    print(f"Guardado en '{ruta_salida}'")

    # --- VISUALIZACIÓN RÁPIDA ---
    print("Generando imagen previa...")
    fig, ax = plt.subplots(figsize=(10, 10))
    municipios.plot(ax=ax, color='lightgrey', edgecolor='white')
    mi_grid.plot(ax=ax, facecolor="none", edgecolor="blue", linewidth=0.3)
    plt.title(f"Tenerife dividido en {len(mi_grid)} sectores")
    plt.show()

except Exception as e:
    print(f"[ERROR] {e}")
    print("Asegurate de que el archivo 'municipios-tenerife.geojson' esta en la carpeta data/")