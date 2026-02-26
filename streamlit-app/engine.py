import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

def calcular_lifescore_vectorial(gdf_saturado, diccionario_config, sliders_usuario, checks_usuario):
    """
    Calcula el LifeScore respetando la jerarquía:
    1. Score Categoría (0-10) = (Puntos Reales / Puntos Ideales)
    2. LifeScore Global (0-10) = Media Ponderada de Categorías según Sliders
    """
    # 1. Copia de seguridad para no tocar el original
    gdf_result = gdf_saturado.copy()
    
    # Estructura temporal para guardar numeradores y denominadores POR GRUPO
    # Ejemplo: {'Salud': {'puntos': [0, 5, ...], 'ideal': [10, 10, ...]}, ...}
    grupos_calc = {}

    # -------------------------------------------------------------
    # FASE 1: CÁLCULO POR CATEGORÍAS (MICRO)
    # -------------------------------------------------------------
    for actividad, config in diccionario_config.items():
        
        # A. Si el usuario desmarcó el Checkbox, ignoramos esta actividad completamente
        # (Esto es la Normalización Dinámica: desaparece del numerador y del denominador)
        if not checks_usuario.get(actividad, True):
            continue
            
        nombre_col = f"sat_{actividad}"
        
        # B. Verificaciones
        if nombre_col not in gdf_result.columns:
            continue
            
        # C. Datos del Config
        grupo = config['grupo_slider']  # Ej: "Salud", "Ocio"
        peso_experto = config['peso']   # Ej: 10, 9, 5...
        max_cap = config['limite']     # El tope teórico (Ej: 3 farmacias)
        
        # D. Inicializar grupo si no existe
        if grupo not in grupos_calc:
            grupos_calc[grupo] = {
                'numerador': np.zeros(len(gdf_result)),
                'denominador': 0.0 # Es un escalar, porque el ideal es igual para todos
            }
        
        # E. CÁLCULO MATEMÁTICO (El Corazón del Modelo)
        # Numerador: Cuánto tienes * Importancia
        # Usamos la columna ya saturada (que viene con valores entre 0 y max_cap)
        puntos_reales = gdf_result[nombre_col] * peso_experto
        
        # Denominador: Cuánto deberías tener para ser perfecto * Importancia
        # Usamos max_cap porque es el estándar de calidad, no el máximo encontrado
        puntos_ideales = max_cap * peso_experto
        
        # Acumulamos en su cajita correspondiente
        grupos_calc[grupo]['numerador'] += puntos_reales
        grupos_calc[grupo]['denominador'] += puntos_ideales

    # -------------------------------------------------------------
    # FASE 2: AGREGACIÓN GLOBAL (MACRO) - CORREGIDA
    # -------------------------------------------------------------
    
    numerador_global = np.zeros(len(gdf_result))
    denominador_global = 0.0
    
    # Iteramos sobre los grupos (Salud, Ocio, Movilidad...)
    for grupo, valores in grupos_calc.items():
        
        # 1. Calcular Nota de la Categoría (0 a 10)
        # ---------------------------------------------------------
        if valores['denominador'] > 0:
            # Aquí es donde se define el 0-10 interno
            score_categoria = (valores['numerador'] / valores['denominador']) * 10
        else:
            score_categoria = 0.0
            
        # CLIP DE SEGURIDAD: Por si acaso en el Excel pusiste un peso mal y sale un 11
        score_categoria = np.clip(score_categoria, 0, 10)
        
        # Guardamos la nota parcial para debugar
        gdf_result[f'score_{grupo}'] = score_categoria.round(2)
        
        # 2. Aplicar el Slider del Usuario (Ponderación Global)
        # ---------------------------------------------------------
        # Recuperamos el valor del slider (1, 2, 3, 4 o 5)
        # Si el usuario no lo ha tocado, asumimos 3 (medio)
        peso_slider = sliders_usuario.get(grupo, 3) 
        
        # ACUMULACIÓN PONDERADA
        numerador_global += score_categoria * peso_slider
        denominador_global += peso_slider
        
    # -------------------------------------------------------------
    # FASE 3: SCORE FINAL (DIVISIÓN OBLIGATORIA)
    # -------------------------------------------------------------
    
    if denominador_global > 0:
        # La magia: Dividimos por la suma de los sliders
        score_final = numerador_global / denominador_global
    else:
        score_final = 0.0
        
    # CLIP FINAL DE SEGURIDAD (Para dormir tranquilo)
    # Esto corta cualquier decimal loco tipo 10.00001 a 10.0
    gdf_result['score_final'] = np.clip(score_final, 0, 10).round(2)
    
    return gdf_result



def obtener_multiplicador(d):
    """Aplica la prima de proximidad y el decaimiento por distancia en metros."""
    if d <= 150: return 1.2
    elif d <= 500: return 0.8
    elif d <= 1000: return 0.5
    elif d <= 2500: return 0.25
    elif d <= 5000: return 0.1
    else: return 0.0


def calcular_conteo_efectivo(lat, lon, gdf_puntos):
    """
    Proyecta el punto, escanea las distancias a todos los locales 
    y devuelve un diccionario con el q_j (Conteo Efectivo) aplicando pesos.
    """
    # 1. Proyectamos
    punto_wgs84 = gpd.GeoSeries([Point(lon, lat)], crs="EPSG:4326")
    punto_metric = punto_wgs84.to_crs(epsg=32628).iloc[0]

    # 2. Medimos distancias
    df_distancias = gdf_puntos[['actividad']].copy()
    df_distancias['distancia'] = gdf_puntos.geometry.distance(punto_metric)

    # 3. Aplicamos la Prima de Proximidad
    df_distancias['peso_distancia'] = df_distancias['distancia'].apply(obtener_multiplicador)

    # 4. Agrupamos y devolvemos el diccionario
    df_utiles = df_distancias[df_distancias['peso_distancia'] > 0]
    return df_utiles.groupby('actividad')['peso_distancia'].sum().to_dict()


# SEGUNDA FUNCIONALIDAD #

def calcular_lifescore_punto(lat, lon, gdf_puntos, diccionario_config, sliders_usuario, checks_usuario):
    """
    Recibe el Conteo Efectivo de un punto y aplica la fórmula del modelo 
    (límites, pesos y sliders) para devolver el LifeScore final (0-10).
    """
    
    # --- DELEGAMOS EL TRABAJO ESPACIAL ---
    conteo_efectivo = calcular_conteo_efectivo(lat, lon, gdf_puntos)

    # -------------------------------------------------------------
    # FASE 1: CÁLCULO POR CATEGORÍAS (MICRO)
    # -------------------------------------------------------------
    grupos_calc = {}

    for actividad, config in diccionario_config.items():
        if not checks_usuario.get(actividad, True):
            continue

        grupo = config['grupo_slider']
        peso_experto = config['peso']
        max_cap = config['limite']

        if grupo not in grupos_calc:
            grupos_calc[grupo] = {'numerador': 0.0, 'denominador': 0.0}

        # B. SATURACIÓN: min(q_j, L_j)
        cantidad_real = conteo_efectivo.get(actividad, 0.0)
        cantidad_saturada = min(cantidad_real, max_cap)

        puntos_reales = cantidad_saturada * peso_experto
        puntos_ideales = max_cap * peso_experto

        grupos_calc[grupo]['numerador'] += puntos_reales
        grupos_calc[grupo]['denominador'] += puntos_ideales

    # -------------------------------------------------------------
    # FASE 2: AGREGACIÓN GLOBAL (MACRO)
    # -------------------------------------------------------------
    numerador_global = 0.0
    denominador_global = 0.0

    for grupo, valores in grupos_calc.items():
        if valores['denominador'] > 0:
            score_categoria = (valores['numerador'] / valores['denominador']) * 10
        else:
            score_categoria = 0.0
            
        score_categoria = np.clip(score_categoria, 0, 10)
        peso_slider = sliders_usuario.get(grupo, 3)
        
        numerador_global += score_categoria * peso_slider
        denominador_global += peso_slider

    # -------------------------------------------------------------
    # FASE 3: SCORE FINAL
    # -------------------------------------------------------------
    if denominador_global > 0:
        score_final = numerador_global / denominador_global
    else:
        score_final = 0.0

    score_final = np.clip(score_final, 0, 10)
    
    # -------------------------------------------------------------
    # FASE 4: LIMPIEZA VISUAL PARA LA WEB
    # -------------------------------------------------------------
    conteo_final = {}
    for actividad, valor in conteo_efectivo.items():
        if actividad in diccionario_config and checks_usuario.get(actividad, True):
            conteo_final[actividad] = valor

    return round(score_final, 2), conteo_final