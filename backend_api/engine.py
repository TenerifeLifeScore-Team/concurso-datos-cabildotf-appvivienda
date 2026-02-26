import pandas as pd
import numpy as np

def calcular_lifescore(df_suavizado, diccionario_config, sliders_usuario, checks_usuario):
    """
    Calcula el LifeScore vectorial optimizado para la API.
    df_suavizado: DataFrame de Pandas (sin geometría) con columnas 'sat_...'
    """
    # Trabajamos sobre una copia ligera
    df_result = df_suavizado.copy()
    
    # Acumuladores para la media ponderada global
    numerador_global = np.zeros(len(df_result))
    denominador_global = 0.0

    # Agrupamos cálculos por grupo del slider (Ej: "Salud", "Ocio")
    grupos_calc = {}

    # --- FASE 1: CÁLCULO MICRO (Por actividad) ---
    for actividad_key, config in diccionario_config.items():
        # 1. Filtro Checkbox: Si el usuario lo desactivó, saltamos
        if not checks_usuario.get(actividad_key, True):
            continue
            
        # 2. Verificar columna (Ej: "sat_Guagua")
        nombre_col = f"sat_{actividad_key}"
        if nombre_col not in df_result.columns:
            continue
            
        grupo = config.get('grupo_slider', 'Otros')
        peso_experto = config.get('peso', 1.0)
        limite_teorico = config.get('limite', 1.0) # El "ideal"

        if grupo not in grupos_calc:
            grupos_calc[grupo] = {
                'numerador': np.zeros(len(df_result)),
                'denominador': 0.0
            }
        
        # Puntos Reales vs Ideales
        # Usamos los datos suavizados que ya vienen en el geojson
        valor_suavizado = df_result[nombre_col]
        
        grupos_calc[grupo]['numerador'] += valor_suavizado * peso_experto
        grupos_calc[grupo]['denominador'] += limite_teorico * peso_experto

    # --- FASE 2: CÁLCULO MACRO (Por Grupo) ---
    for grupo, valores in grupos_calc.items():
        # Nota del grupo (0 a 10)
        if valores['denominador'] > 0:
            score_grupo = (valores['numerador'] / valores['denominador']) * 10
        else:
            score_grupo = 0.0
            
        score_grupo = np.clip(score_grupo, 0, 10)
        
        # Ponderación del Usuario (Slider 0-5)
        peso_usuario = sliders_usuario.get(grupo, 3.0) # Default 3
        
        numerador_global += score_grupo * peso_usuario
        denominador_global += peso_usuario

    # --- FASE 3: SCORE FINAL ---
    if denominador_global > 0:
        score_final = numerador_global / denominador_global
    else:
        score_final = np.zeros(len(df_result))
        
    # Guardamos resultado
    df_result['score_final'] = np.clip(score_final, 0, 10).round(2)
    
    # Generamos color Hex para el mapa
    df_result['color'] = df_result['score_final'].apply(obtener_color_hex)
    
    # Devolvemos solo lo necesario: ID, Nota y Color
    return df_result[['hex_id', 'score_final', 'color']]

def obtener_color_hex(score):
    """
    Convierte score (0-10) a Hex string #RRGGBB usando tu gradiente
    Rojo -> Naranja -> Amarillo -> Verde -> Azul
    """
    val = max(0, min(10, float(score)))
    
    # Definición de colores clave (RGB)
    c_rojo = np.array([255, 60, 60])
    c_naranja = np.array([255, 160, 0])
    c_amarillo = np.array([255, 220, 0])
    c_verde = np.array([50, 200, 80])
    c_azul = np.array([0, 110, 255])
    
    rgb = np.array([0, 0, 0])

    if val <= 1.5:
        f = val / 1.5
        rgb = c_rojo + (c_naranja - c_rojo) * f
    elif val <= 4.0:
        f = (val - 1.5) / 2.5
        rgb = c_naranja + (c_amarillo - c_naranja) * f
    elif val <= 7.0:
        f = (val - 4.0) / 3.0
        rgb = c_amarillo + (c_verde - c_amarillo) * f
    else:
        f = (val - 7.0) / 3.0
        rgb = c_verde + (c_azul - c_verde) * f
        
    return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]), int(rgb[1]), int(rgb[2]))