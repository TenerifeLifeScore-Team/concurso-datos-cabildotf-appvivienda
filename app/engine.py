import pandas as pd
import numpy as np
import geopandas as gpd

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