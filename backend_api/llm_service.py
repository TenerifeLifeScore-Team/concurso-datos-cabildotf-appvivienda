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

def generar_resumen_ia(detalles_zona: dict, sliders_usuario: dict, score: float) -> str:
    try:
        # 1. Preparamos los datos limpios
        contexto = preparar_resumen_contexto(detalles_zona, sliders_usuario)
        
        # 2. Configuramos el modelo rápido (Flash es gratis y veloz)
        model = genai.GenerativeModel('models/gemini-flash-lite-latest')

        instruccion_tono = ""
        if score >= 6:
            instruccion_tono = "La puntuación es EXCELENTE. Sé entusiasta y felicita al usuario por la elección."
        elif score >= 3:
            instruccion_tono = "La puntuación es MEDIA/ACEPTABLE. Sé equilibrado: destaca lo bueno pero menciona lo que falta sin ser dramático."
        else:
            instruccion_tono = "La puntuación es BAJA/MALA. Sé empático pero realista. Advierte educadamente de que esta zona no cumple sus expectativas principales."
        
        # 3. El Prompt Maestro
        prompt = f"""
        Eres un asesor inmobiliario experto en Tenerife.
        Usa estrictamente los siguientes datos para generar un micro-resumen (máximo 2 frases cortas).
        Solo las dos frases, tu resumen va a ir ubicado como resumen junto a una puntuación para una zona en concreto de la isla.
        
        DATOS TÉCNICOS:
        - Puntuación de compatibilidad calculada: {score}/10.
        - Perfil y Entorno:
        {contexto}
        
        INSTRUCCIONES DE TONO:
        {instruccion_tono}.
        Esta es una app para el cabildo, por lo que siempre debes ser algo optimista, pero también realista.
        
        OBJETIVO:
        Escribe un micro-resumen (máximo 2 frases) justificando la puntuación.
        Céntrate en la relación entre lo que el usuario pide y lo que hay (o lo que falta).
        No menciones la nota numérica en el texto, solo explica el porqué.
        Usa un tono cercano y que sea fácil de entender para el usuario.
        """

        # 4. Llamada a la API
        response = model.generate_content(prompt)
        return response.text.strip()
        
    except Exception as e:
        print(f"❌ Error IA: {e}")
        return "Disfruta de esta zona explorando sus servicios cercanos." # Fallback si la IA falla