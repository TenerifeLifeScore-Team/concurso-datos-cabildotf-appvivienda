import pandas as pd
import geopandas as gpd
import logging
from pathlib import Path

def generar_puntos_maestros(carpeta_clean, ruta_salida):
    """
    Lee todos los GeoJSON de la carpeta data-clean, los unifica en un solo 
    GeoDataFrame y los guarda listos para el 'Radar' de la aplicación web.
    """
    archivos_geojson = list(Path(carpeta_clean).glob("*.geojson"))
    
    if not archivos_geojson:
        logging.error("❌ No se encontraron archivos GeoJSON en data-clean.")
        return
        
    lista_gdfs = []
    
    for ruta in archivos_geojson:
        logging.info(f"📍 Leyendo puntos de: {ruta.name}")
        try:
            gdf = gpd.read_file(ruta)
            
            # Asegurarnos de que tienen la columna 'actividad'
            if 'tipo' not in gdf.columns:
                logging.warning(f"⚠️ El archivo {ruta.name} no tiene columna 'actividad'. Se saltará.")
                continue
                
            # Solo necesitamos la geometría y la actividad para el radar
            gdf = gdf[['tipo', 'geometry']]
            gdf = gdf.rename(columns={'tipo': 'actividad'})
            lista_gdfs.append(gdf)
            
        except Exception as e:
            logging.error(f"❌ Error al leer {ruta.name}: {e}")
            
    if lista_gdfs:
        # Unimos todos los puntos en un solo mapa
        gdf_maestro = gpd.GeoDataFrame(pd.concat(lista_gdfs, ignore_index=True))
        
        # OBLIGATORIO: Proyectar a EPSG:32628 (Canarias) para medir en METROS
        if gdf_maestro.crs is None or gdf_maestro.crs.to_string() != "EPSG:32628":
            logging.info("🌍 Proyectando al sistema métrico de Canarias (EPSG:32628)...")
            # Si viene sin CRS, asumimos que es WGS84 (GPS normal)
            if gdf_maestro.crs is None:
                gdf_maestro.set_crs(epsg=4326, inplace=True)
            gdf_maestro = gdf_maestro.to_crs(epsg=32628)
            
        # Guardamos el super-archivo
        logging.info(f"💾 Guardando Mega-Tabla de Puntos ({len(gdf_maestro)} locales) en: {ruta_salida}")
        gdf_maestro.to_file(ruta_salida, driver="GeoJSON")
        logging.info("✅ Puntos maestros generados con éxito.")
    else:
        logging.error("❌ No se pudo generar la tabla maestra de puntos.")