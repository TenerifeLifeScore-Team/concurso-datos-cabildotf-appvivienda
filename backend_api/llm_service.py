import google.generativeai as genai
import os
from utils_ia import preparar_resumen_contexto
from dotenv import load_dotenv

# 1. Cargar variables de entorno del archivo .env
load_dotenv()

# 2. Leer la clave (Si no la encuentra, da error o usa un string vacío)
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("⚠️ ADVERTENCIA: No se encontró GEMINI_API_KEY en el archivo .env")

genai.configure(api_key=API_KEY)

def generar_resumen_ia(detalles_zona: dict, sliders_usuario: dict) -> str:
    try:
        # 1. Preparamos los datos limpios
        contexto = preparar_resumen_contexto(detalles_zona, sliders_usuario)
        
        # 2. Configuramos el modelo rápido (Flash es gratis y veloz)
        model = genai.GenerativeModel('models/gemini-flash-lite-latest')
        
        # 3. El Prompt Maestro
        prompt = f"""
        Eres un asesor inmobiliario experto en Tenerife.
        Usa estrictamente los siguientes datos para generar un micro-resumen (máximo 2 frases cortas).
        Solo las dos frases, tu resumen va a ir ubicado como resumen junto a una puntuación para una zona en concreto de la isla.
        
        DATOS:
        {contexto}
        
        OBJETIVO:
        Dime si es una buena zona para este usuario y destaca UN punto fuerte clave o UNA carencia crítica según sus gustos.
        Usa un tono cercano y que sea fácil de entender para el usuario. No menciones números exactos.
        """

        # 4. Llamada a la API
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        return "Disfruta de esta zona explorando sus servicios cercanos." # Fallback si la IA falla