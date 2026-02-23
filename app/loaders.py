import streamlit as st
import geopandas as gpd
import os

PATH_DATOS = "tabla_saturada.geojson"

@st.cache_data
def cargar_datos_mapa():
    """
    Carga el GeoJSON con la geometría y los datos saturados.
    Devuelve un GeoDataFrame.
    """
    if not os.path.exists(PATH_DATOS):
        st.error()
        return gpd.GeoDataFrame()

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