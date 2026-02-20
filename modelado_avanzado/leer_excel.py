import pandas as pd
import logging

def generar_diccionario_desde_excel(ruta_excel):
    logging.info(f"Abriendo Excel: {ruta_excel}")

    # 1. Configuración de pestañas
    # Definimos cómo queremos agrupar los sliders en la Sidebar
    PESTANAS = {
        "Servicios básicos": [
            "Salud vital", "Salud especializada", "Educación", "Transporte público", "Mascotas"
        ],
        "Consumo y vida diaria": [
            "Alimentación y Despensa", "Cuidado Personal y Salud", 
            "Hogar y Bricolaje", "Moda y Shopping"
        ],
        "Ocio y estilo de vida": [
            "Cultura", "Ocio, Hobbies y Tecnología", "Mascotas"
        ],
        "Restauración y socialización": [
            "Cafeterías y Mañaneo", "Casual, Fast Food y Bares de Paso", 
            "Gastronomía y Guachinches", "Vida Nocturna y Copas"
        ]
    }

    # Creamos un "Mapa Inverso" para buscar rápido:
    # { 'Salud vital': 'Servicios básicos', 'Cultura': 'Ocio y estilo de vida', ... }
    mapa_grupo_a_pestana = {}
    for pestana, lista_grupos in PESTANAS.items():
        for grupo in lista_grupos:
            mapa_grupo_a_pestana[grupo] = pestana
    
    # Leemos todas las hojas de golpe
    xls = pd.read_excel(ruta_excel, sheet_name=None, header=1, usecols="B:E")
    
    diccionario_maestro = {}
    
    for nombre_hoja, df in xls.items():
        logging.info(f"Procesando hoja: {nombre_hoja}...")
        
        # Limpieza básica del DataFrame
        df = df.drop(index=0).reset_index(drop=True)
        df.columns = ['grupo', 'actividad', 'peso', 'limite']
        df['grupo'] = df['grupo'].ffill()
        df = df.dropna(subset=['actividad'])
        
        for _, fila in df.iterrows():
            actividad = str(fila['actividad']).strip()
            grupo_actual = str(fila['grupo']).strip()
            
            # Comprobación solo de seguridad (no va a pasar)
            macro_asignada = mapa_grupo_a_pestana.get(grupo_actual, "Otros")
            
            diccionario_maestro[actividad] = {
                "macro_categoria": macro_asignada, # Ahora esto es 'Servicios básicos', etc.
                "grupo_slider": grupo_actual,
                "peso": float(fila['peso']),
                "limite": float(fila['limite'])
            }
            
    return diccionario_maestro