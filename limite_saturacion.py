import geopandas as gpd
import json
import os

# ==========================================
# 1. CONFIGURACIÓN DE RUTAS
# ==========================================
ARCHIVO_MAESTRO = "data-clean/TABLA_MAESTRA.geojson"
ARCHIVO_DICCIONARIO = "data-clean/diccionario_config.json"
CARPETA_SALIDA = "data-clean"

# ==========================================
# 2. CARGAR DATOS
# ==========================================
print("📥 Cargando Tabla Maestra y Diccionario...")

# Cargar la tabla con los conteos reales (q_j)
gdf = gpd.read_file(ARCHIVO_MAESTRO)

# Cargar el diccionario que acabamos de crear
with open(ARCHIVO_DICCIONARIO, 'r', encoding='utf-8') as f:
    diccionario_config = json.load(f)

# ==========================================
# 3. APLICAR LÓGICA DE SATURACIÓN: min(q_j, L_j)
# ==========================================
print("\n🧮 Aplicando límites de saturación a cada actividad...")

# Buscamos todas las columnas que empiezan por 'q_' (los conteos reales)
columnas_q = [col for col in gdf.columns if col.startswith('q_')]

actividades_procesadas = 0
actividades_no_encontradas = []

for col_q in columnas_q:
    # Extraemos el nombre exacto de la actividad (quitando el 'q_')
    actividad = col_q.replace('q_', '')
    
    # Buscamos esta actividad en nuestro diccionario JSON
    if actividad in diccionario_config:
        # Extraemos su límite (L_j)
        limite = diccionario_config[actividad]['limite']
        
        # Creamos la nueva columna saturada usando .clip() -> equivalente a min(q_j, L_j)
        col_sat = f"sat_{actividad}"
        gdf[col_sat] = gdf[col_q].clip(upper=limite)
        
        print(f"   ✔️ {actividad}: Límite fijado en {limite}.")
        actividades_procesadas += 1
    else:
        # Si por algún motivo hay una actividad en el mapa que no está en el Excel
        actividades_no_encontradas.append(actividad)
        # La dejamos igual por defecto, pero avisamos
        gdf[f"sat_{actividad}"] = gdf[col_q]

# Mostrar advertencias si las hay
if actividades_no_encontradas:
    print(f"\n⚠️ AVISO: Las siguientes actividades están en el mapa pero NO en tu Excel:")
    for act in actividades_no_encontradas:
        print(f"   - {act} (Se ha procesado sin límite)")

# ==========================================
# 4. LIMPIEZA Y GUARDADO
# ==========================================
# Guardamos la tabla con las nuevas columnas 'sat_'
ruta_salida = f"{CARPETA_SALIDA}/tabla_saturada.geojson"
gdf.to_file(ruta_salida, driver="GeoJSON")

print(f"\n🚀 ¡ÉXITO! Se han saturado {actividades_procesadas} actividades.")
print(f"💾 Tabla saturada guardada en: {ruta_salida}")