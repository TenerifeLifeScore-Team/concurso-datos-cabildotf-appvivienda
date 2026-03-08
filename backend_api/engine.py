import geopandas as gpd
import numpy as np
from shapely.geometry import Point

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


# SEGUNDA FUNCIONALIDAD #
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