from groq import Groq
import os
from utils_ia import preparar_resumen_contexto
from dotenv import load_dotenv

# 1. Cargar variables de entorno del archivo .env
load_dotenv()

# 2. Leer la clave de Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️ ADVERTENCIA: No se encontró GROQ_API_KEY en el archivo .env")

# 3. Inicializar el cliente de Groq
client = Groq(api_key=GROQ_API_KEY)

def generar_resumen_ia(detalles_zona: dict, sliders_usuario: dict, score: float) -> str:
    try:
        # 1. Preparamos los datos limpios (se mantiene igual)
        contexto = preparar_resumen_contexto(detalles_zona, sliders_usuario)
        
        # 2. Lógica de tonos (se mantiene igual)
        instruccion_tono = ""
        if score <= 1.5:
            instruccion_tono = "La puntuación es BAJA. Sé empático pero realista. Advierte educadamente de que esta zona no cumple sus expectativas principales."
        elif score <= 4:
            instruccion_tono = "La puntuación es MEDIA/ACEPTABLE. Sé equilibrado: destaca lo bueno pero menciona lo que falta sin ser dramático."
        elif score <= 7:
            instruccion_tono = "La puntuación es ACEPTABLE. Sé equilibrado y algo optimista: destaca lo bueno pero menciona lo que falta sin ser dramático."
        elif score >= 8.5:
            instruccion_tono = "La puntuación es MUY ACEPTABLE. Sé equilibrado y optimista: destaca lo bueno y menciona algo que puede faltar pero que es mínimo."
        else:
            instruccion_tono = "La puntuación es EXCELENTE. Sé positivo y habla bien de la ubicación."
        
        # 3. Separamos tu Prompt Maestro en Sistema y Usuario
        mensaje_sistema = """
        Eres un asesor inmobiliario experto en Tenerife.
        Esta es una app para el Cabildo de Tenerife, por lo que siempre debes ser algo optimista, pero también realista.
        Tu objetivo es escribir un micro-resumen (2 frases muy cortas) justificando la puntuación de una zona.
        Céntrate en la relación entre lo que el usuario pide y lo que hay (o lo que falta) A GRANDES RASGOS.
        No menciones la nota numérica en el texto, solo explica el porqué.
        Usa un tono cercano y que sea fácil de entender para el usuario, dirigiéndote en segunda persona tuteando al usuario que busca información en esa zona.
        Solo debes devolver las dos frases del resumen, nada de introducciones ni saludos.
        Es muy importante que te centres en el perfil del usuario y que lo compares con las cosas que hay, y explicando la puntuación obtenida.
        
        """

        mensaje_usuario = f"""
        DATOS TÉCNICOS:
        - Puntuación de compatibilidad calculada: {score}/10.
        - Perfil y Entorno:
        {contexto}
        
        INSTRUCCIONES DE TONO:
        {instruccion_tono}
        
        Por favor, genera el micro-resumen ahora:
        """

        # 4. Llamada a la API de Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": mensaje_sistema.strip()},
                {"role": "user", "content": mensaje_usuario.strip()}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7, # Creatividad balanceada
            max_tokens=150,  # Límite para que no se enrolle
        )
        
        # 5. Extraemos el texto de la respuesta
        return chat_completion.choices[0].message.content.strip()
        
    except Exception as e:
        print(f"❌ Error IA (Groq): {e}")
        return "Disfruta de esta zona explorando sus servicios cercanos." # Fallback si la IA falla