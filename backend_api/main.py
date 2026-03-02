import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from llm_service import generar_resumen_ia

# Importamos el motor (Añadimos calcular_lifescore_punto)
from engine import calcular_lifescore, calcular_lifescore_punto # <--- NUEVO
import loaders # <--- NUEVO (Necesario para cargar los puntos maestros)

app = FastAPI(title="Tenerife LifeScore API")

# Configuración de seguridad (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- RUTAS DE ARCHIVOS ---
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data-processed"
FILE_CONFIG = DATA_DIR / "diccionario_config.json"
FILE_DATA = DATA_DIR / "tabla_saturada_suavizada.geojson"

# Variables en memoria (Cache)
memoria_config = {}
memoria_df = None
gdf_puntos = None # <--- NUEVO (Variable para guardar el radar)

# --- CARGA AL INICIO ---
@app.on_event("startup")
async def load_data():
    global memoria_config, memoria_df, gdf_puntos # <--- NUEVO (Añadimos gdf_puntos al global)
    print("🚀 Iniciando Tenerife LifeScore API...")
    
    # 1. Cargar Configuración
    try:
        with open(FILE_CONFIG, "r", encoding="utf-8") as f:
            memoria_config = json.load(f)
        print(f"✅ Config cargada: {len(memoria_config)} actividades.")
    except Exception as e:
        print(f"❌ Error cargando config: {e}")

    # 2. Cargar Datos Suavizados (Hexágonos)
    try:
        print("⏳ Leyendo GeoJSON (esto puede tardar unos segundos)...")
        gdf = gpd.read_file(FILE_DATA)
        memoria_df = pd.DataFrame(gdf.drop(columns='geometry', errors='ignore'))
        
        if 'hex_id' in memoria_df.columns:
            memoria_df['hex_id'] = memoria_df['hex_id'].astype(str)
            
        print(f"✅ Datos cargados en RAM: {len(memoria_df)} hexágonos.")
    except Exception as e:
        print(f"❌ Error cargando datos hexágonos: {e}")

    # 3. Cargar Puntos Maestros (Radar) <--- BLOQUE NUEVO
    try:
        print("📡 Cargando sistema de radar...")
        gdf_puntos = loaders.cargar_puntos_maestros()
        if gdf_puntos is not None:
            print(f"✅ Radar activo: {len(gdf_puntos)} puntos de interés cargados.")
        else:
            print("⚠️ No se pudo cargar el radar (puntos_maestros.geojson).")
    except Exception as e:
        print(f"❌ Error cargando radar: {e}")

# --- MODELOS DE DATOS ---
class UserPreferences(BaseModel):
    sliders: Dict[str, float]
    checks: Optional[Dict[str, bool]] = {}

# Modelo nuevo para recibir coordenadas <--- NUEVO
class PointPreferences(UserPreferences):
    lat: float
    lon: float

# --- ENDPOINTS ---

@app.get("/")
def root():
    return {"status": "Online", "msg": "Bienvenido a la API de Tenerife LifeScore"}

@app.get("/config")
def get_config_structure():
    """
    Devuelve la jerarquía organizada para la UI.
    """
    temp_structure = {}
    
    for key, data in memoria_config.items():
        macro = data.get("macro_categoria", "Otros")
        grupo = data.get("grupo_slider", "General")
        nombre_ui = data.get("nombre_ui", key)
        
        if macro not in temp_structure:
            temp_structure[macro] = {}
        if grupo not in temp_structure[macro]:
            temp_structure[macro][grupo] = {}
        if nombre_ui not in temp_structure[macro][grupo]:
            temp_structure[macro][grupo][nombre_ui] = []
            
        temp_structure[macro][grupo][nombre_ui].append(key)
    
    resultado = {}
    for macro, grupos in temp_structure.items():
        resultado[macro] = {}
        for grupo, items_ui in grupos.items():
            lista_items = []
            for ui_label, internal_ids in items_ui.items():
                lista_items.append({
                    "label": ui_label,
                    "ids": internal_ids
                })
            
            lista_items.sort(key=lambda x: x["label"])
            resultado[macro][grupo] = lista_items
            
    return resultado

@app.post("/calculate")
def calculate_map(prefs: UserPreferences):
    """
    Calcula el mapa de calor (Hexágonos).
    """
    if memoria_df is None:
        raise HTTPException(status_code=503, detail="Datos no cargados aún")
        
    df_resultado = calcular_lifescore(
        memoria_df,
        memoria_config,
        prefs.sliders,
        prefs.checks
    )

    # Añadimos la función de color aquí mismo para el mapa global
    def get_color(s):
        if s >= 8: return "#2ECC71" # Verde
        if s >= 5: return "#F1C40F" # Amarillo
        return "#E74C3C" # Rojo

    # Si tu engine ya devuelve el color, perfecto. Si no, lo calculamos:
    if 'color' not in df_resultado.columns:
         df_resultado['color'] = df_resultado['score_final'].apply(get_color)
    
    return df_resultado[['hex_id', 'score_final', 'color']].to_dict(orient="records")


@app.post("/calculate-point")
def get_point_score(prefs: PointPreferences):
    """
    Recibe lat/lon y preferencias, devuelve Score exacto, detalles y el resumen de IA.
    """
    # Debug para confirmar en la terminal que estás en la versión correcta
    print("📢 DEBUG: ¡Calculando punto con IA!") 

    if gdf_puntos is None:
        raise HTTPException(status_code=503, detail="Radar no cargado (revisa logs del servidor)")
    
    # 1. Cálculo Matemático (Rápido)
    score, conteo_final = calcular_lifescore_punto(
        prefs.lat, 
        prefs.lon, 
        gdf_puntos, 
        memoria_config, 
        prefs.sliders, 
        prefs.checks
    )
    
    # 2. Cálculo Semántico (IA)
    # Valor por defecto por si no hay nada cerca o falla la IA
    resumen_texto = "Zona sin datos suficientes para análisis."
    
    # Solo llamamos a la IA si la zona tiene algo interesante (Score > 0)
    if score > 0:
        resumen_texto = generar_resumen_ia(conteo_final, prefs.sliders)
    
    # 3. Return con los 3 campos clave
    return {
        "score": score,
        "resumen_ia": resumen_texto, # <--- ¡ESTE ES EL CAMPO NUEVO!
        "detalles": {k: round(v, 2) for k, v in conteo_final.items() if v > 0}
    }