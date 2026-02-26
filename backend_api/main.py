import json
import geopandas as gpd
import pandas as pd
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Dict, List, Optional

# Importamos el motor
from engine import calcular_lifescore

app = FastAPI(title="Tenerife LifeScore API")

# Configuración de seguridad (CORS) para permitir acceso desde el móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # En producción se puede restringir, en dev dejamos todo abierto
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

# --- CARGA AL INICIO ---
@app.on_event("startup")
async def load_data():
    global memoria_config, memoria_df
    print("🚀 Iniciando Tenerife LifeScore API...")
    
    # 1. Cargar Configuración
    try:
        with open(FILE_CONFIG, "r", encoding="utf-8") as f:
            memoria_config = json.load(f)
        print(f"✅ Config cargada: {len(memoria_config)} actividades.")
    except Exception as e:
        print(f"❌ Error cargando config: {e}")

    # 2. Cargar Datos Suavizados
    try:
        print("⏳ Leyendo GeoJSON (esto puede tardar unos segundos)...")
        # Leemos el GeoJSON completo
        gdf = gpd.read_file(FILE_DATA)
        
        # TRUCO DE RENDIMIENTO:
        # Convertimos a Pandas DataFrame normal eliminando la geometría.
        # La API no necesita saber dónde está el hexágono, solo su ID y sus datos.
        # El móvil ya sabe dónde pintarlo.
        memoria_df = pd.DataFrame(gdf.drop(columns='geometry', errors='ignore'))
        
        # Asegurarnos de que 'hex_id' es string para evitar problemas de JSON
        if 'hex_id' in memoria_df.columns:
            memoria_df['hex_id'] = memoria_df['hex_id'].astype(str)
            
        print(f"✅ Datos cargados en RAM: {len(memoria_df)} hexágonos.")
    except Exception as e:
        print(f"❌ Error cargando datos: {e}")

# --- MODELOS DE DATOS ---
class UserPreferences(BaseModel):
    sliders: Dict[str, float] # Ej: {"Salud": 4.5, "Ocio": 2.0}
    checks: Optional[Dict[str, bool]] = {} # Ej: {"farmacia": True}

# --- ENDPOINTS ---

@app.get("/")
def root():
    return {"status": "Online", "msg": "Bienvenido a la API de Tenerife LifeScore"}

@app.get("/config")
def get_config_structure():
    """
    Devuelve la estructura para construir la UI en Flutter:
    { "Salud": ["Hospitales", "Farmacias"], ... }
    """
    jerarquia = {}
    for key, data in memoria_config.items():
        grupo = data.get("grupo_slider", "Otros")
        nombre_ui = data.get("nombre_ui", key)
        
        if grupo not in jerarquia:
            jerarquia[grupo] = set()
        jerarquia[grupo].add(nombre_ui)
    
    # Convertimos sets a listas ordenadas
    return {k: sorted(list(v)) for k, v in jerarquia.items()}

@app.post("/calculate")
def calculate_map(prefs: UserPreferences):
    """
    Recibe preferencias, calcula scores y devuelve colores por hexágono.
    """
    if memoria_df is None:
        raise HTTPException(status_code=503, detail="Datos no cargados aún")
        
    # Ejecutamos el motor matemático
    df_resultado = calcular_lifescore(
        memoria_df,
        memoria_config,
        prefs.sliders,
        prefs.checks
    )
    
    # Convertimos a diccionario para JSON
    # Orient='records' crea una lista de objetos: [{...}, {...}]
    return df_resultado.to_dict(orient="records")