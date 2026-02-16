import pandas as pd
import json

# ==========================================
# 1. CONFIGURACIÓN
# ==========================================
ARCHIVO_EXCEL = "recursos/Tipos de actividades - TenerifeLifeScore.xlsx" # Pon el nombre real
ARCHIVO_JSON_SALIDA = "data-clean/diccionario_config.json"

def generar_diccionario_desde_excel(ruta_excel):
    print(f"📂 Abriendo Excel: {ruta_excel}")
    
    # Leemos TODAS las hojas de golpe. sheet_name=None devuelve un diccionario de DataFrames
    # header=1 significa que la FILA 2 de Excel tiene los nombres de las columnas (índice 1)
    # usecols="B:E" coge exactamente las columnas que nos importan
    xls = pd.read_excel(ruta_excel, sheet_name=None, header=1, usecols="B:E")
    
    diccionario_maestro = {}
    
    for nombre_hoja, df in xls.items():
        print(f"   📖 Procesando hoja: {nombre_hoja}...")
        
        # 1. Eliminar la fila de "descripciones" 
        # (Al poner header=1, la fila 3 del Excel es ahora la fila 0 de nuestro DataFrame)
        df = df.drop(index=0).reset_index(drop=True)
        
        # 2. Renombrar las columnas para que sea súper fácil programar con ellas
        df.columns = ['grupo', 'actividad', 'peso', 'limite']
        
        # 3. LA MAGIA: Rellenar los huecos de las celdas combinadas del grupo
        # Copia "Salud vital" hacia abajo hasta que encuentre "Salud especializada"
        df['grupo'] = df['grupo'].ffill()
        
        # 4. Limpiar filas vacías (por si el Excel tiene formato más abajo pero sin datos)
        df = df.dropna(subset=['actividad'])
        
        # 5. Construir el diccionario actividad por actividad
        for _, fila in df.iterrows():
            # Limpiamos espacios extra en los nombres con .strip() por si acaso
            actividad = str(fila['actividad']).strip()
            
            diccionario_maestro[actividad] = {
                "macro_categoria": nombre_hoja, # Ej: 'salud'
                "grupo_slider": str(fila['grupo']).strip(), # Ej: 'Salud vital'
                "peso": float(fila['peso']),
                "limite": float(fila['limite'])
            }
            
    return diccionario_maestro

# ==========================================
# 2. EJECUCIÓN
# ==========================================
if __name__ == "__main__":
    try:
        diccionario = generar_diccionario_desde_excel(ARCHIVO_EXCEL)
        
        # Guardar el resultado en un JSON para que los demás scripts lo lean al instante
        with open(ARCHIVO_JSON_SALIDA, 'w', encoding='utf-8') as f:
            json.dump(diccionario, f, ensure_ascii=False, indent=4)
            
        print(f"\n🚀 ¡ÉXITO! Se han procesado {len(diccionario)} actividades.")
        print(f"💾 Diccionario guardado en: {ARCHIVO_JSON_SALIDA}")
        
        # Imprimir una de prueba para confirmar que está perfecto
        print("\n🔍 Prueba de lectura (ej. 'farmacia'):")
        print(json.dumps(diccionario.get('farmacia', '⚠️ No encontrada'), indent=4, ensure_ascii=False))
        
    except Exception as e:
        print(f"❌ ERROR: {e}")