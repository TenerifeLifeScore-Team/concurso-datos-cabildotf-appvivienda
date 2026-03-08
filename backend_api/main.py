import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional
from llm_service import generar_resumen_ia

from engine import calcular_lifescore, calcular_lifescore_punto
import loaders

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
gdf_puntos = None

# --- CARGA AL INICIO ---
@app.on_event("startup")
async def load_data():
    global memoria_config, memoria_df, gdf_puntos
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

    # 3. Cargar Puntos Maestros (Radar)
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

# Modelo nuevo para recibir coordenadas
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

    if 'color' not in df_resultado.columns:
         df_resultado['color'] = df_resultado['score_final'].apply(get_color)
    
    return df_resultado[['hex_id', 'score_final', 'color']].to_dict(orient="records")


@app.post("/calculate-point")
def get_point_score(prefs: PointPreferences):
    """
    Devuelve el Score INSTANTÁNEAMENTE. No llama a la IA.
    """
    if gdf_puntos is None:
        raise HTTPException(status_code=503, detail="Radar no cargado")
    
    score, conteo_final = calcular_lifescore_punto(
        prefs.lat, prefs.lon, gdf_puntos, memoria_config, prefs.sliders, prefs.checks
    )
    
    return {
        "score": score,
        "detalles": conteo_final
    }

# --- 2. ENDPOINT LENTO (SOLO IA) ---
@app.post("/explain-point")
def explain_point_score(prefs: PointPreferences):
    """
    Recalcula los datos y se los pasa a la IA. Tarda 2-3 segundos.
    """
    # Recalculamos los datos (es muy rápido, no importa hacerlo 2 veces)
    score, conteo_final = calcular_lifescore_punto(
        prefs.lat, prefs.lon, gdf_puntos, memoria_config, prefs.sliders, prefs.checks
    )
    
    if score == 0:
        return {"resumen_ia": "No hay datos suficientes en esta zona."}

    # Llamamos a la IA con el score para que ajuste el tono
    resumen = generar_resumen_ia(conteo_final, prefs.sliders, score)
    
    return {"resumen_ia": resumen}