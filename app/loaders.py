import streamlit as st
import geopandas as gpd
import os
from pathlib import Path

UBICACION_ACTUAL = Path(__file__).parent

# 2. Subimos un nivel (.parent) para ir a la raíz del proyecto
# Y desde ahí entramos a 'data-proccesed'
# OJO: Mantengo tu nombre "data-proccesed" (con dos c), si la cambias, cámbialo aquí también.
PATH_DATOS = UBICACION_ACTUAL.parent / "data-proccesed" / "tabla_saturada_suavizada.geojson"

@st.cache_data(show_spinner=False)
def cargar_datos_mapa():
    """
    Carga el GeoJSON con la geometría y los datos saturados.
    Devuelve un GeoDataFrame.
    """
    try:
        # Usamos GeoPandas para leer el fichero espacial
        gdf = gpd.read_file(PATH_DATOS)
        
        # Nos aseguramos de que los NaNs sean 0 para el cálculo matemático
        # (Solo en las columnas numéricas para no romper la geometría)
        cols_numericas = gdf.select_dtypes(include=['number']).columns
        gdf[cols_numericas] = gdf[cols_numericas].fillna(0)
        
        # Establecemos el índice
        if 'hex_id' in gdf.columns:
            gdf.set_index('hex_id', inplace=True)
            
        return gdf

    except Exception as e:
        st.error(f"Error cargando el GeoJSON: {e}")
        return gpd.GeoDataFrame()


# Definimos la ruta de la nueva mega-tabla
PATH_PUNTOS = UBICACION_ACTUAL.parent / "data-proccesed" / "puntos_maestros.geojson"

@st.cache_data(show_spinner=False)
def cargar_puntos_maestros():
    """
    Carga el GeoJSON con todos los locales de la isla.
    Lo mantiene en la memoria RAM (caché) para que el radar sea rapidísimo.
    """
    try:
        # Usamos GeoPandas para leer los puntos
        gdf_puntos = gpd.read_file(PATH_PUNTOS)
        
        # Por seguridad extrema, confirmamos que está en metros (EPSG:32628)
        if gdf_puntos.crs is None or gdf_puntos.crs.to_string() != "EPSG:32628":
            if gdf_puntos.crs is None:
                gdf_puntos.set_crs(epsg=4326, inplace=True)
            gdf_puntos = gdf_puntos.to_crs(epsg=32628)
            
        return gdf_puntos

    except Exception as e:
        st.error(f"❌ Error al cargar los puntos maestros: {e}")
        return None
