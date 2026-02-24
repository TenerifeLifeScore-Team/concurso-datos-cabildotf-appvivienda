import logging
from pathlib import Path
import geopandas as gpd
import json

# Importamos las funciones puras desde la carpeta modelado_avanzado
from modelado_avanzado.generar_tabla_maestra import generar_tabla_maestra
from modelado_avanzado.aplicar_limites import aplicar_limites
from modelado_avanzado.generar_grid import calcular_grid_hexagonal
from modelado_avanzado.leer_excel import generar_diccionario_desde_excel
from modelado_avanzado.suavizado_espacial import aplicar_suavizado_espacial

# 1. Configurar el Logging global
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def main():
    logging.info("=== INICIANDO PIPELINE DE DATOS LIFESCORE ===")

    # 2. Definir las rutas
    RAIZ = Path(__file__).parent
    CARPETA_CLEAN = RAIZ / "data-clean"
    CARPETA_PRO = RAIZ / "data-proccesed"
    CARPETA_RAW = RAIZ / "data-raw"
    CARPETA_REC = RAIZ / "recursos"

    # Rutas de archivos que ccamos a usar
    ruta_excel = CARPETA_REC / "Tipos de actividades - TenerifeLifeScore.xlsx"
    ruta_municipios = CARPETA_RAW / "municipios-tenerife.geojson"

    # Rutas específicas de archivos que vamos a guardar
    ruta_grid = CARPETA_PRO / "grid_tenerife.geojson"
    ruta_diccionario = CARPETA_PRO / "diccionario_config.json"
    ruta_tabla_maestra = CARPETA_PRO / "tabla_maestra.geojson"
    ruta_tabla_saturada = CARPETA_PRO / "tabla_saturada.geojson"
    ruta_tabla_suavizada = CARPETA_PRO / "tabla_saturada_suavizada.geojson"

    # Diccionario de datasets limpios para pasarle al Script 2
    rutas_datasets = {
        "movilidad": str(CARPETA_CLEAN / "movilidad.geojson"),
        "comercio": str(CARPETA_CLEAN / "comercio.geojson"),
        "salud": str(CARPETA_CLEAN / "salud.geojson"),
        "restauracion": str(CARPETA_CLEAN / "restauracion.geojson"),
        "educacion": str(CARPETA_CLEAN / "educacion.geojson"),
        "naturaleza": str(CARPETA_CLEAN / "naturaleza.geojson"),
        "deporte": str(CARPETA_CLEAN / "deportes_y_ocio.geojson")
    }

    # =================
    # --- EJECUCIÓN ---
    # =================

    # PASO 0: Crear el Grid Hexagonal
    print()
    logging.info("--- FASE 0: CREANDO TABLERO HEXAGONAL ---")
    
    # Cargamos el mapa base de los municipios
    logging.info("Cargando mapa base de municipios...")
    gdf_municipios = gpd.read_file(ruta_municipios)
    
    # Ejecutamos la función con los parámetros consensuados (MODIFICAR AQUÍ SI NECESARIO)
    grid_resultante = calcular_grid_hexagonal(gdf=gdf_municipios, radio=500, porcentaje_tierra=0.45)
    
    # Guardamos el resultado en la ruta
    grid_resultante.to_file(ruta_grid, driver="GeoJSON")
    logging.info(f"✅ Grid generado y guardado en: {ruta_grid}")


    # PASO 1: Generar Diccionario desde Excel
    print()
    logging.info("--- FASE 1: CONSTRUYENDO DICCIONARIO DESDE EXCEL ---")
    
    # Ejecutamos tu función que lee las pestañas del Excel
    diccionario = generar_diccionario_desde_excel(ruta_excel=str(ruta_excel))
    
    # Guardamos el diccionario en formato JSON para que el Paso 3 lo pueda leer
    with open(ruta_diccionario, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=4)
    logging.info(f"✅ Diccionario guardado en: {ruta_diccionario}")


    # PASO 2: Cruzar Puntos con Hexágonos
    print()
    logging.info("--- FASE 2: CREANDO TABLA MAESTRA ---")
    generar_tabla_maestra(
        ruta_grid=str(ruta_grid),
        rutas_datasets=rutas_datasets,
        carpeta_salida=str(CARPETA_PRO)
    )


    # PASO 3: Aplicar Saturación
    print()
    logging.info("--- FASE 3: APLICANDO LÍMITES MATEMÁTICOS ---")
    aplicar_limites(
        ruta_maestra=str(ruta_tabla_maestra),
        ruta_diccionario=str(ruta_diccionario),
        ruta_salida=str(ruta_tabla_saturada)
    )

    # PASO 4: Suavizado Espacial (Gaussiano)
    print()
    logging.info("--- FASE 4: APLICANDO SUAVIZADO ESPACIAL (VECINOS) ---")
    aplicar_suavizado_espacial(
        ruta_entrada=str(ruta_tabla_saturada), # Leemos el output de la fase anterior
        ruta_salida=str(ruta_tabla_suavizada)  # Guardamos el archivo definitivo
    )
    
    logging.info("======== PIPELINE COMPLETADO CON ÉXITO ========")

if __name__ == "__main__":
    main()