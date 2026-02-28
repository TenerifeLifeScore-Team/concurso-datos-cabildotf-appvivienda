import logging
import json
import shutil
from pathlib import Path
import geopandas as gpd

# Importaciones locales
from modelado_avanzado.generar_tabla_maestra import generar_tabla_maestra
from modelado_avanzado.aplicar_limites import aplicar_limites
from modelado_avanzado.generar_grid import calcular_grid_hexagonal
from modelado_avanzado.leer_excel import generar_diccionario_desde_excel
from modelado_avanzado.suavizado_espacial import aplicar_suavizado_espacial
from modelado_avanzado.unificar_puntos import generar_puntos_maestros

# Configuración de Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)

def replicar_archivo(ruta_origen: Path, carpetas_destino: list):
    """
    Copia un archivo generado en la ruta origen al resto de carpetas destino.
    Evita copiar sobre sí mismo si la carpeta origen está en la lista.
    """
    if not ruta_origen.exists():
        logging.error(f"Error: No se encuentra el archivo origen {ruta_origen}")
        return

    nombre_archivo = ruta_origen.name

    for carpeta in carpetas_destino:
        # Evitar copiar si la carpeta destino es la misma que la origen
        if carpeta.resolve() == ruta_origen.parent.resolve():
            continue

        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_final = carpeta / nombre_archivo
        shutil.copy2(ruta_origen, ruta_final)
        logging.info(f"Replicado en: {ruta_final}")

def main():
    logging.info("=== INICIANDO PIPELINE DE DATOS LIFESCORE ===")

    # --- CONFIGURACIÓN DE RUTAS ---
    DIR_ETL = Path(__file__).resolve().parent
    RAIZ_PROYECTO = DIR_ETL.parent

    # Directorios Input
    DIR_CLEAN = DIR_ETL / "data-clean"
    DIR_RAW = DIR_ETL / "data-raw"
    DIR_REC = DIR_ETL / "recursos"

    # Directorios Output (Principal y Secundarios)
    # Definimos la primera carpeta como la "Principal" donde se generan los cálculos
    DIR_APP_WEB = RAIZ_PROYECTO / "streamlit-app" / "data-processed"
    DIR_API_MOVIL = RAIZ_PROYECTO / "backend_api" / "data-processed"
    
    DIR_PRINCIPAL = DIR_APP_WEB
    LISTA_DESTINOS = [DIR_APP_WEB, DIR_API_MOVIL]

    # Archivos Input
    ruta_excel = DIR_REC / "Tipos de actividades - TenerifeLifeScore.xlsx"
    ruta_municipios = DIR_RAW / "municipios-tenerife.geojson"
    rutas_datasets = {
        "movilidad": str(DIR_CLEAN / "movilidad.geojson"),
        "comercio": str(DIR_CLEAN / "comercio.geojson"),
        "salud": str(DIR_CLEAN / "salud.geojson"),
        "restauracion": str(DIR_CLEAN / "restauracion.geojson"),
        "educacion": str(DIR_CLEAN / "educacion.geojson"),
        "naturaleza": str(DIR_CLEAN / "naturaleza.geojson"),
        "deporte": str(DIR_CLEAN / "deportes_y_ocio.geojson")
    }

    # Asegurar existencia carpeta principal
    DIR_PRINCIPAL.mkdir(parents=True, exist_ok=True)

    # --- FASE 0: GRID HEXAGONAL ---
    logging.info("--- FASE 0: CREANDO TABLERO HEXAGONAL ---")
    
    gdf_municipios = gpd.read_file(ruta_municipios)
    grid_resultante = calcular_grid_hexagonal(
        gdf=gdf_municipios, 
        radio=500, 
        porcentaje_tierra=0.45
    )
    
    ruta_grid_main = DIR_PRINCIPAL / "grid_tenerife.geojson"
    grid_resultante.to_file(ruta_grid_main, driver="GeoJSON")
    logging.info(f"Grid generado en: {ruta_grid_main}")
    
    replicar_archivo(ruta_grid_main, LISTA_DESTINOS)


    # --- FASE 1: DICCIONARIO ---
    logging.info("--- FASE 1: CONSTRUYENDO DICCIONARIO ---")
    
    diccionario = generar_diccionario_desde_excel(ruta_excel=str(ruta_excel))
    
    ruta_diccionario_main = DIR_PRINCIPAL / "diccionario_config.json"
    with open(ruta_diccionario_main, 'w', encoding='utf-8') as f:
        json.dump(diccionario, f, ensure_ascii=False, indent=4)
    logging.info(f"Diccionario guardado en: {ruta_diccionario_main}")
    
    replicar_archivo(ruta_diccionario_main, LISTA_DESTINOS)

    # --- FASE 1.5: Unificar todos los puntos limpios para el Radar de la App Web ---
    logging.info("--- FASE 1.5: GENERANDO MEGA-TABLA DE PUNTOS (RADAR) ---")
    ruta_puntos_maestros_main = DIR_PRINCIPAL / "puntos_maestros.geojson"
    
    # 2. Ejecutamos la función (Calculamos una sola vez)
    generar_puntos_maestros(
        carpeta_clean=DIR_CLEAN,      # Usamos la variable DIR_CLEAN que definimos arriba
        ruta_salida=str(ruta_puntos_maestros_main)
    )
    logging.info(f"Puntos maestros generados en: {ruta_puntos_maestros_main}")
    
    # 3. Replicamos el archivo a la carpeta de la API/Backend
    replicar_archivo(ruta_puntos_maestros_main, LISTA_DESTINOS)

    # --- FASE 2: TABLA MAESTRA ---
    logging.info("--- FASE 2: CREANDO TABLA MAESTRA ---")
    
    # Nota: generar_tabla_maestra guarda el archivo internamente en carpeta_salida
    generar_tabla_maestra(
        ruta_grid=str(ruta_grid_main),
        rutas_datasets=rutas_datasets,
        carpeta_salida=str(DIR_PRINCIPAL)
    )
    
    # Asumimos que la función genera este nombre de archivo
    ruta_maestra_main = DIR_PRINCIPAL / "tabla_maestra.geojson"
    logging.info(f"Tabla maestra generada en: {ruta_maestra_main}")
    
    replicar_archivo(ruta_maestra_main, LISTA_DESTINOS)


    # --- FASE 3: SATURACIÓN (LÍMITES) ---
    logging.info("--- FASE 3: APLICANDO LÍMITES MATEMÁTICOS ---")
    
    ruta_saturada_main = DIR_PRINCIPAL / "tabla_saturada.geojson"
    
    aplicar_limites(
        ruta_maestra=str(ruta_maestra_main),
        ruta_diccionario=str(ruta_diccionario_main),
        ruta_salida=str(ruta_saturada_main)
    )
    logging.info(f"Saturación aplicada en: {ruta_saturada_main}")
    
    replicar_archivo(ruta_saturada_main, LISTA_DESTINOS)


    # --- FASE 4: SUAVIZADO ESPACIAL ---
    logging.info("--- FASE 4: APLICANDO SUAVIZADO ESPACIAL ---")
    
    ruta_suavizada_main = DIR_PRINCIPAL / "tabla_saturada_suavizada.geojson"
    
    aplicar_suavizado_espacial(
        ruta_entrada=str(ruta_saturada_main),
        ruta_salida=str(ruta_suavizada_main)
    )
    logging.info(f"Suavizado final guardado en: {ruta_suavizada_main}")
    
    replicar_archivo(ruta_suavizada_main, LISTA_DESTINOS)

    logging.info("=== PIPELINE COMPLETADO CON EXITO ===")

if __name__ == "__main__":
    main()