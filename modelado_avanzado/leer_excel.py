import pandas as pd
import json


def generar_diccionario_desde_excel(ruta_excel):
    print(f"[INFO] Abriendo Excel: {ruta_excel}")
    
    # Leemos todas las hojas de golpe teniendo en cuenta donde están los registros
    xls = pd.read_excel(ruta_excel, sheet_name=None, header=1, usecols="B:E")
    
    diccionario_maestro = {}
    
    for nombre_hoja, df in xls.items():
        print(f"[INFO] Procesando hoja: {nombre_hoja}...")
        
        # 1. Eliminar la fila de "descripciones" 
        df = df.drop(index=0).reset_index(drop=True)
        
        # 2. Renombrar las columnas
        df.columns = ['grupo', 'actividad', 'peso', 'limite']
        
        # 3. Rellenar los huecos de las celdas combinadas del grupo
        df['grupo'] = df['grupo'].ffill()
        
        # 4. Limpiar filas vacías
        df = df.dropna(subset=['actividad'])
        
        # 5. Construir el diccionario actividad por actividad
        for _, fila in df.iterrows():
            actividad = str(fila['actividad']).strip()  # Limpiamos
            
            diccionario_maestro[actividad] = {
                "macro_categoria": nombre_hoja, # Ej: 'salud'
                "grupo_slider": str(fila['grupo']).strip(), # Ej: 'Salud vital'
                "peso": float(fila['peso']),
                "limite": float(fila['limite'])
            }
            
    return diccionario_maestro