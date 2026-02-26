import logging
from pathlib import Path
import geopandas as gpd
import json
import shutil

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


def guardar_en_ambos(gdf, nombre_archivo, lista_carpetas): # <--- NUEVO ARGUMENTO AQUÍ
    """
    Guarda un GeoDataFrame en todas las carpetas que le pasemos en la lista.
    """
    print(f"--- Guardando: {nombre_archivo} ---")
    
    for carpeta in lista_carpetas: # <--- USAMOS EL ARGUMENTO AQUÍ
        # 1. Crea la carpeta si no existe
        carpeta.mkdir(parents=True, exist_ok=True)
        
        # 2. Define la ruta completa
        ruta_final = carpeta / nombre_archivo
        
        # 3. Guarda el archivo
        # (Ajusta el driver si usas otro formato, ej: GPKG)
        gdf.to_file(ruta_final, driver="GeoJSON") 
        print(f"✅ Guardado en: {ruta_final}")


def main():
    logging.info("=== INICIANDO PIPELINE DE DATOS LIFESCORE ===")

    # --- DEFINICIÓN DE RUTAS (SOLO UNA VEZ Y BIEN HECHA) ---
    
    # 1. Dónde está este script ahora mismo (etl-pipeline)
    DIR_ETL = Path(__file__).resolve().parent
    
    # 2. La raíz del proyecto (para poder bajar a otras carpetas)
    RAIZ_PROYECTO = DIR_ETL.parent

    # 3. Carpetas de ORIGEN (Input)
    CARPETA_CLEAN = DIR_ETL / "data-clean"
    CARPETA_RAW = DIR_ETL / "data-raw"
    CARPETA_REC = DIR_ETL / "recursos"

    # 4. Carpetas de DESTINO (Output) - LISTA MAESTRA
    # Aquí defines todos los sitios donde quieres que aparezcan los archivos
    CARPETAS_DESTINO = [
        RAIZ_PROYECTO / "streamlit-app" / "data-proccesed",  # Tu app vieja
        RAIZ_PROYECTO / "backend_api" / "data-processed"     # Tu nueva API
    ]

    # --- RUTAS DE ARCHIVOS DE ENTRADA ---
    ruta_excel = CARPETA_REC / "Tipos de actividades - TenerifeLifeScore.xlsx"
    ruta_municipios = CARPETA_RAW / "municipios-tenerife.geojson"

    # Diccionario de datasets limpios (Inputs)
    rutas_datasets = {
        "movilidad": str(CARPETA_CLEAN / "movilidad.geojson"),
        "comercio": str(CARPETA_CLEAN / "comercio.geojson"),
        "salud": str(CARPETA_CLEAN / "salud.geojson"),
        "restauracion": str(CARPETA_CLEAN / "restauracion.geojson"),
        "educacion": str(CARPETA_CLEAN / "educacion.geojson")
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
    
    # Guardamos el resultado en las rutas
    for carpeta in CARPETAS_DESTINO:
        carpeta.mkdir(parents=True, exist_ok=True) # Crea la carpeta si no existe
        ruta_final = carpeta / "grid_tenerife.geojson"
        
        grid_resultante.to_file(ruta_final, driver="GeoJSON")
        logging.info(f"✅ Grid guardado en: {ruta_final}")

    # PASO 1: Generar Diccionario desde Excel
    print()
    logging.info("--- FASE 1: CONSTRUYENDO DICCIONARIO DESDE EXCEL ---")
    
    # Ejecutamos tu función que lee las pestañas del Excel
    diccionario = generar_diccionario_desde_excel(ruta_excel=str(ruta_excel))
    
    # Guardamos el diccionario en formato JSON para que el Paso 3 lo pueda leer
    for carpeta in CARPETAS_DESTINO:
        carpeta.mkdir(parents=True, exist_ok=True)
        ruta_final = carpeta / "diccionario_config.json"
        
        with open(ruta_final, 'w', encoding='utf-8') as f:
            json.dump(diccionario, f, ensure_ascii=False, indent=4)
        logging.info(f"✅ Diccionario guardado en: {ruta_final}")


    # PASO 2: Cruzar Puntos con Hexágonos
    print()
    logging.info("--- FASE 2: CREANDO TABLA MAESTRA ---")
    # Estrategia: Generamos en la PRIMERA carpeta y copiamos a las demás
    carpeta_principal = CARPETAS_DESTINO[0] # Usamos la de Streamlit como base
    resto_carpetas = CARPETAS_DESTINO[1:]   # El resto (Backend API, etc.)

    # 1. Generamos el archivo original una sola vez
    # Nota: ruta_grid ahora debe apuntar a un archivo que exista. 
    # Como acabamos de guardar el grid en la carpeta principal, usamos esa ruta.
    ruta_grid_principal = carpeta_principal / "grid_tenerife.geojson"

    generar_tabla_maestra(
        ruta_grid=str(ruta_grid_principal),
        rutas_datasets=rutas_datasets,
        carpeta_salida=str(carpeta_principal)
    )
    logging.info(f"✅ Tabla maestra generada en: {carpeta_principal}")

    # 2. Copiamos el resultado a las otras carpetas (backend_api)
    nombre_archivo_generado = "tabla_maestra.geojson" # Asegúrate que tu función genera este nombre
    origen = carpeta_principal / nombre_archivo_generado

    for carpeta_destino in resto_carpetas:
        carpeta_destino.mkdir(parents=True, exist_ok=True)
        destino = carpeta_destino / nombre_archivo_generado
        
        shutil.copy2(origen, destino)
        logging.info(f"✅ Copia de tabla maestra creada en: {destino}")


    ruta_maestra_main = carpeta_principal / "tabla_maestra.geojson"
    ruta_diccionario_main = carpeta_principal / "diccionario_config.json"
    ruta_saturada_main = carpeta_principal / "tabla_saturada.geojson"
    ruta_suavizada_main = carpeta_principal / "tabla_saturada_suavizada.geojson"


    # --- FASE 3: APLICAR SATURACIÓN ---
    logging.info("--- FASE 3: APLICANDO LÍMITES MATEMÁTICOS ---")
    
    # 1. Ejecutamos la función SOLO en la carpeta principal
    aplicar_limites(
        ruta_maestra=str(ruta_maestra_main),      # Leemos de la principal
        ruta_diccionario=str(ruta_diccionario_main), # Leemos config de la principal
        ruta_salida=str(ruta_saturada_main)       # Guardamos en la principal
    )
    logging.info(f"✅ Saturación aplicada en: {ruta_saturada_main}")

    # 2. Copiamos el resultado (tabla_saturada) al resto de carpetas
    for carpeta in resto_carpetas:
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / "tabla_saturada.geojson"
        shutil.copy2(ruta_saturada_main, destino)
        logging.info(f"   ↳ Copiado a: {destino}")


    # --- FASE 4: SUAVIZADO ESPACIAL (Gaussiano) ---
    logging.info("--- FASE 4: APLICANDO SUAVIZADO ESPACIAL (VECINOS) ---")

    # 1. Ejecutamos la función SOLO en la carpeta principal
    aplicar_suavizado_espacial(
        ruta_entrada=str(ruta_saturada_main),   # Leemos el output de la fase 3
        ruta_salida=str(ruta_suavizada_main)    # Guardamos el definitivo en la principal
    )
    logging.info(f"✅ Suavizado aplicado en: {ruta_suavizada_main}")

    # 2. Copiamos el resultado final al resto de carpetas
    for carpeta in resto_carpetas:
        carpeta.mkdir(parents=True, exist_ok=True)
        destino = carpeta / "tabla_saturada_suavizada.geojson"
        shutil.copy2(ruta_suavizada_main, destino)
        logging.info(f"   ↳ Copiado a: {destino}")
    
    logging.info("======== PIPELINE COMPLETADO CON ÉXITO ========")

if __name__ == "__main__":
    main()