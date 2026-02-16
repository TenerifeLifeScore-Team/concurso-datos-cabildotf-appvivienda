import geopandas as gpd
import pandas as pd
import os

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS
# ==========================================
ARCHIVO_GRID = "data-clean/grid_tenerife.geojson" # Tu grid ya generado
CARPETA_SALIDA = "data-clean"
os.makedirs(CARPETA_SALIDA, exist_ok=True)

# Pon aquí el nombre EXACTO de tus archivos limpios
RUTAS_DATASETS = {
    "movilidad": "data-clean/movilidad.geojson",
    "comercio": "data-clean/comercio.geojson",
    "salud": "data-clean/salud.geojson",
    "restauracion": "data-clean/restauracion.geojson",
    "educacion": "data-clean/educacion.geojson"
}

# ==========================================
# 2. CARGAR EL TABLERO (GRID)
# ==========================================
print("🗺️ Cargando el grid de hexágonos...")
grid = gpd.read_file(ARCHIVO_GRID)

# Creamos la columna ID
if 'hex_id' not in grid.columns:
    grid['hex_id'] = [f"HEX_{str(i).zfill(4)}" for i in range(len(grid))]
    # Guardamos el grid actualizado con los IDs para no perderlos
    grid.to_file(ARCHIVO_GRID, driver="GeoJSON")
    print("   ✅ Columna 'hex_id' generada y guardada en el grid.")

# Aseguramos sistema de coordenadas estándar
grid = grid.to_crs(epsg=4326)

# ==========================================
# 3. CRUCE ESPACIAL (SPATIAL JOIN)
# ==========================================
todos_los_puntos = []

for nombre, ruta in RUTAS_DATASETS.items():
    if not os.path.exists(ruta):
        print(f"⚠️ OMITIDO: No se encontró '{ruta}'. Revisa el nombre.")
        continue
        
    print(f"🔄 Procesando capa: {nombre}...")
    
    # Cargar los puntos limpios
    gdf_puntos = gpd.read_file(ruta)
    gdf_puntos = gdf_puntos.to_crs(epsg=4326)
    
    # El cruce: Asignar a cada punto el hex_id donde cae
    # predicate="within" significa "el punto está DENTRO del hexágono"
    puntos_con_hex = gpd.sjoin(gdf_puntos, grid[['hex_id', 'geometry']], how="inner", predicate="within")
    
    # Limpiar columnas temporales del join
    if 'index_right' in puntos_con_hex.columns:
        puntos_con_hex = puntos_con_hex.drop(columns=['index_right'])
        
    # Guardar este dataset actualizado (para que tengáis el dato si el usuario hace click en un punto)
    ruta_salida_puntos = f"{CARPETA_SALIDA}/{nombre}_hex.geojson"
    puntos_con_hex.to_file(ruta_salida_puntos, driver="GeoJSON")
    
    # Lo guardamos en la lista global para la tabla maestra
    todos_los_puntos.append(puntos_con_hex)

# ==========================================
# 4. CREAR LA TABLA MAESTRA DE CONTEOS
# ==========================================
if len(todos_los_puntos) > 0:
    print("\n📊 Construyendo la Tabla Maestra...")
    
    # Juntamos todas las categorías
    df_global = pd.concat(todos_los_puntos, ignore_index=True)
    
    # Contamos cuántos elementos hay por hexágono y por grupo_slider
    conteos = df_global.groupby(['hex_id', 'tipo']).size().reset_index(name='cantidad')
    
    # Pivotamos: Pasamos de filas a columnas
    tabla_pivote = conteos.pivot(index='hex_id', columns='tipo', values='cantidad').fillna(0)
    
    # Añadimos un prefijo para que quede claro (ej: q_Farmacias)
    # Le pongo 'q_' porque en vuestra fórmula la cantidad real se llama q_j
    tabla_pivote.columns = [f"q_{col}" for col in tabla_pivote.columns]
    tabla_pivote = tabla_pivote.reset_index()

    # Unimos los conteos con los polígonos del grid
    tabla_maestra = grid.merge(tabla_pivote, on='hex_id', how='left')
    
    # Los hexágonos que se quedaron vacíos tendrán NaN, los pasamos a 0
    columnas_q = [col for col in tabla_maestra.columns if col.startswith('q_')]
    tabla_maestra[columnas_q] = tabla_maestra[columnas_q].fillna(0)
    
    # Guardar resultado final
    ruta_maestra = f"{CARPETA_SALIDA}/tabla_maestra.geojson"
    tabla_maestra.to_file(ruta_maestra, driver="GeoJSON")
    print(f"🚀 ¡ÉXITO! Tabla Maestra generada en: {ruta_maestra}")
else:
    print("❌ No se procesó ningún archivo. Revisa las rutas.")