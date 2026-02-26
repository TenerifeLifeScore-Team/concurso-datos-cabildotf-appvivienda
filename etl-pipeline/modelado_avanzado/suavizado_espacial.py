import pandas as pd
import geopandas as gpd
import logging

# Configuración de pesos
PESOS_KERNEL = {
    0: 1.0,   # Tú mismo
    1: 0.5,   # Vecinos directos (que te tocan)
    2: 0.25   # Vecinos de segunda línea
}

def aplicar_suavizado_espacial(ruta_entrada, ruta_salida):
    """
    Versión GEOMÉTRICA: Calcula vecinos por contacto físico (intersects), 
    independientemente del tipo de ID (H3 o HEX_XXXX).
    """
    logging.info(f"📍 Leyendo datos saturados desde: {ruta_entrada}")
    
    try:
        gdf = gpd.read_file(ruta_entrada)
    except Exception as e:
        logging.error(f"❌ Error leyendo archivo: {e}")
        return

    # 1. Asegurar ID
    if 'hex_id' not in gdf.columns:
        gdf = gdf.reset_index()
    if 'hex_id' not in gdf.columns:
        if 'index' in gdf.columns:
            gdf = gdf.rename(columns={'index': 'hex_id'})
        else:
            logging.error("❌ No encuentro columna 'hex_id'.")
            return

    # 2. Identificar columnas numéricas 'sat_'
    cols_a_suavizar = [c for c in gdf.columns if c.startswith('sat_')]
    logging.info(f"   Variables a suavizar: {len(cols_a_suavizar)}")

    # 3. Optimización: Diccionario de datos
    data_dict = gdf.set_index('hex_id')[cols_a_suavizar].to_dict(orient='index')

    # ========================================================
    # PASO CLAVE: CALCULAR VECINOS POR GEOMETRÍA (Espacial)
    # ========================================================
    logging.info("   🧩 Calculando mapa de vecindad (quién toca a quién)...")
    
    # Creamos un buffer diminuto para asegurar que si se tocan, se detecte la intersección
    # 0.00001 grados es aprox 1 metro. Suficiente para corregir micro-errores de la grid.
    gdf_buffer = gdf.copy()
    gdf_buffer['geometry'] = gdf_buffer.geometry.buffer(0.00001)
    
    # Hacemos un Join Espacial con sí mismo para ver quién toca a quién
    # Esto nos devuelve pares: (hex_id_izq, hex_id_der)
    join_vecinos = gpd.sjoin(gdf_buffer, gdf_buffer, how='inner', predicate='intersects')
    
    # Construimos el diccionario de adyacencia: { 'HEX_1': {'HEX_2', 'HEX_3'...} }
    adjacencia = {}
    for idx, row in join_vecinos.iterrows():
        # Recuperamos los IDs originales usando los índices que devuelve sjoin
        id_origen = row['hex_id_left']
        id_vecino = row['hex_id_right']
        
        if id_origen not in adjacencia:
            adjacencia[id_origen] = set()
        
        # Guardamos al vecino (excluyéndonos a nosotros mismos)
        if id_origen != id_vecino:
            adjacencia[id_origen].add(id_vecino)

    logging.info("   ✅ Mapa de vecindad construido. Aplicando suavizado...")

    # ========================================================
    # BUCLE DE SUAVIZADO
    # ========================================================
    nuevos_datos = []
    
    for i, row in gdf.iterrows():
        hex_actual = row['hex_id']
        acumulados = {col: 0.0 for col in cols_a_suavizar}
        
        # --- DEFINIR ANILLOS ---
        # Anillo 0: Nosotros
        vecinos_0 = {hex_actual}
        
        # Anillo 1: Vecinos directos (del mapa de adyacencia)
        vecinos_1 = adjacencia.get(hex_actual, set())
        
        # Anillo 2: Vecinos de mis vecinos (excluyendo a los de anillo 0 y 1)
        vecinos_2_raw = set()
        for v in vecinos_1:
            vecinos_de_v = adjacencia.get(v, set())
            vecinos_2_raw.update(vecinos_de_v)
            
        vecinos_2 = vecinos_2_raw - vecinos_1 - vecinos_0
        
        # --- APLICAR PESOS ---
        listas_anillos = [vecinos_0, vecinos_1, vecinos_2]
        
        for distancia, grupo_vecinos in enumerate(listas_anillos):
            peso = PESOS_KERNEL.get(distancia, 0)
            if peso == 0 or not grupo_vecinos: continue
            
            for vecino_id in grupo_vecinos:
                if vecino_id in data_dict:
                    vals = data_dict[vecino_id]
                    for col in cols_a_suavizar:
                        acumulados[col] += vals[col] * peso

        # Guardar
        fila_res = acumulados.copy()
        fila_res['hex_id'] = hex_actual
        nuevos_datos.append(fila_res)

    # ========================================================
    # GUARDADO
    # ========================================================
    if not nuevos_datos:
        logging.error("❌ Error CRÍTICO: No se generaron datos.")
        return

    df_suavizado = pd.DataFrame(nuevos_datos)
    
    # Merge seguro
    gdf_final = gdf[['hex_id', 'geometry']].merge(df_suavizado, on='hex_id', how='left')
    
    # Redondeo final
    for col in cols_a_suavizar:
        gdf_final[col] = gdf_final[col].fillna(0).round(3)
        
    logging.info(f"💾 Guardando tabla suavizada en: {ruta_salida}")
    gdf_final.to_file(ruta_salida, driver='GeoJSON')
    logging.info("✅ ¡Suavizado geométrico completado!")