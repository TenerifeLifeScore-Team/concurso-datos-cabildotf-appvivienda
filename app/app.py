import streamlit as st
import pydeck as pdk
from streamlit_option_menu import option_menu
from utils import *
from loaders import cargar_datos_mapa, cargar_puntos_maestros
from engine import calcular_lifescore_vectorial, calcular_lifescore_punto

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y CSS
# ==========================================
st.set_page_config(
    page_title="Tenerife LifeScore",
    page_icon="🏝️",
    layout="wide", 
    initial_sidebar_state="expanded"
)

# Cargamos el diccionario y la jerarquía desde utils.py
diccionario_config = cargar_configuracion()
jerarquia, mapa_traductor = obtener_jerarquia_categorias(diccionario_config)

# CSS INYECTADO: Sidebar 33%, sin scroll en main, y ajustando márgenes
st.markdown(
    """
    <style>
        /* Sidebar al 33% del ancho de la pantalla */
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 33vw;
            max-width: 33vw;
        }
        /* Eliminar el scroll vertical solo de la parte principal (derecha) */
        [data-testid="stMain"] {
            overflow-y: auto !important;
        }
        /* Reducir el espacio en blanco de arriba */
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 0rem !important;
            max-height: 100vh;
        }
        /* FORZAR ALTURA RESPONSIVA EN EL MAPA */
        /* Buscamos el contenedor específico de PyDeck en Streamlit */
        div[data-testid="stDeckGlJsonChart"] {
            /* Calcula: 100% de la altura de la ventana MENOS 180px (título + margen sup) */
            height: calc(100vh - 180px) !important; 
            
            /* Un mínimo por si acaso la pantalla es muy bajita */
            min-height: 500px !important;
        }
        
        /* Aseguramos que el 'canvas' interno también se estire */
        div[data-testid="stDeckGlJsonChart"] > div {
            height: 100% !important;
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. BARRA LATERAL (SIDEBAR) - Personalización
# ==========================================

with st.sidebar:

    st.title("Tenerife LifeScore")
    
    with st.form("formulario_parametros"):
        sliders_subgrupos = {}
        checks_actividades = {}

        # ["Servicios básicos", "Consumo y vida diaria", "Ocio y estilo de vida", "Restauración y socialización"]
        lista_macros = list(jerarquia.keys())
        tabs = st.tabs(lista_macros)

        for i, tab in enumerate(tabs):
            nombre_macro = lista_macros[i]
            grupos_de_esta_macro = jerarquia[nombre_macro]

            with tab:

                for grupo_slider, lista_nombres_ui in grupos_de_esta_macro.items():
                    
                    # Slider del subgrupo
                    sliders_subgrupos[grupo_slider] = st.slider(
                        grupo_slider, 
                        min_value=0, max_value=5, value=3, step=1,
                        key=f"slider_{grupo_slider}"
                    )

                    # Desplegable de checks
                    with st.expander(f"Filtros de {grupo_slider}"):
                        st.markdown("<small>Desmarca lo que no necesites:</small>", unsafe_allow_html=True)

                        for nombre_ui in lista_nombres_ui:
                            # Pintamos un único check por nombre agrupado (Ej: "Cafeterías")
                            estado_check = st.checkbox(
                                nombre_ui, 
                                value=True, 
                                key=f"check_{nombre_ui}_{grupo_slider}"
                            )

                            # TRADUCCIÓN: Propagamos el estado (True/False) a todas las actividades reales ocultas bajo ese nombre
                            for act_real in mapa_traductor[nombre_ui]:
                                checks_actividades[act_real] = estado_check
                    
                    st.markdown("<div style='margin-bottom: 15px;'></div>", unsafe_allow_html=True)

        st.divider()
        boton_calcular = st.form_submit_button("Calcular LifeScore 🚀", use_container_width=True, type="primary")

# ==========================================
# 3. NAVEGACIÓN SUPERIOR HORIZONTAL
# ==========================================
# Esto crea el menú bonito arriba del todo, usando la librería option_menu
seleccion_menu = option_menu(
    menu_title=None,  # No necesitamos título para el menú en sí
    options=["Visión general del modelo", "Zona específica"], 
    icons=["map", "pin-map-fill"],  # Iconos de Bootstrap
    default_index=0, 
    orientation="horizontal"
)

# ==========================================
# 4. CONTENIDO PRINCIPAL
# ==========================================
# En lugar de "with tab:", ahora usamos if/elif según lo que elija el usuario
if seleccion_menu == "Visión general del modelo":
    # 1. Cargar Datos (Cacheado)
    gdf_hexagons = cargar_datos_mapa()
    
    # INICIALIZACIÓN: Si no existe la variable en sesión, la creamos vacía
    if 'gdf_mapa_actual' not in st.session_state:
        st.session_state['gdf_mapa_actual'] = None

    # Contenedor principal
    if boton_calcular:
        with st.spinner("Calculando LifeScore para toda la isla... 🧮"):
            
            # A. PREPARAR INPUTS
            # Los diccionarios 'sliders_subgrupos' y 'checks_actividades' ya vienen rellenos del sidebar
            
            # B. LLAMAR AL MOTOR (ENGINE)
            gdf_resultado = calcular_lifescore_vectorial(
                gdf_hexagons, 
                diccionario_config, 
                sliders_subgrupos, 
                checks_actividades
            )
            
            # C. PREPARAR COLORES
            gdf_resultado["fill_color"] = gdf_resultado["score_final"].apply(obtener_color_por_score)
            
            # D. GUARDAR EN MEMORIA (PERSISTENCIA)
            st.session_state['gdf_mapa_actual'] = gdf_resultado
            
            #if boton_calcular:
            #    st.success("¡Mapa actualizado!")

    # ============================================================
    # PINTADO (RENDER) - FUERA DEL IF PARA QUE NO SE BORRE
    # ============================================================
    # Recuperamos los datos COMPLETOS de la memoria
    gdf_completo = st.session_state['gdf_mapa_actual']

    if gdf_completo is not None:
        
        # --------------------------------------------------------
        # PASO DE OPTIMIZACIÓN: EL FILTRO "DIETA"
        # --------------------------------------------------------
        # Solo pasamos a PyDeck las columnas que NECESITA para pintar.
        # Esto reduce el tamaño del JSON de 5MB a 200KB (vuela).
        if 'hex_id' not in gdf_completo.columns:     # <--- NUEVO
            gdf_completo = gdf_completo.reset_index() # <--- NUEVO

        cols_visualizacion = [
            "geometry",     # Obligatorio: Dónde está el hexágono
            "score_final",  # Para el Tooltip
            "fill_color",   # El color calculado
            "hex_id"        # Identificador (siempre útil tenerlo)
        ]
        
        # Creamos una copia ligera solo con lo necesario
        gdf_ligero = gdf_completo[cols_visualizacion].copy()
        
        # --------------------------------------------------------
        # CONFIGURACIÓN PYDECK
        # --------------------------------------------------------
        view_state = pdk.ViewState(
            latitude=28.30,     # Centro aprox de Tenerife
            longitude=-16.55,
            zoom=9,
            pitch=0,            # 0 para vista cenital (2D), 45 para 3D
        )

        layer_hexagonos = pdk.Layer(
            "GeoJsonLayer",
            data=gdf_ligero,      # USAMOS LA VERSIÓN LIGERA
            opacity=0.8,
            stroked=False,      # Sin bordes negros
            filled=True,
            get_fill_color="fill_color",
            pickable=True,
            auto_highlight=True,
        )

        tooltip = {
            # "html": "<b>Zona:</b> {hex_id}<br/><b>LifeScore:</b> {score_final}/10",
            "html": "<b>LifeScore:</b> {score_final}/10",
            "style": {"backgroundColor": "steelblue", "color": "white"}
        }

        r = pdk.Deck(
            layers=[layer_hexagonos],
            initial_view_state=view_state,
            tooltip=tooltip,
            map_style="mapbox://styles/mapbox/light-v9" 
        )

        # E. PINTAR FINALMENTE
        with st.spinner("Pintando el mapa... 🗺️"):
            st.pydeck_chart(r, width='stretch')
        
    else:
        # Si entras por primera vez y no se ha calculado nada (raro con la lógica actual, pero por seguridad)
        st.info("👈 Ajusta tus preferencias en el menú lateral y pulsa 'Calcular LifeScore'.")



elif seleccion_menu == "Zona específica":
    st.write("### Análisis de Zona al Detalle")
    st.markdown("""
        Escriba la dirección a mano o, para una **PRECISIÓN ABSOLUTA**, ingrese las coordenadas directamente (por ejemplo, copiándolas de Google Maps).
        * **Formato calle:** Calle Castillo 10, Santa Cruz
        * **Formato coordenadas:** `28.4668, -16.2499`
    """)
    
    col1, col2 = st.columns([3, 1])
    with col1:
        # El input ahora acepta las dos cosas
        direccion_input = st.text_input("📍 Buscar dirección o coordenadas (Lat, Lon)...")
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        boton_buscar = st.button("Escanear Zona 🎯", use_container_width=True)
        
    if boton_buscar and direccion_input:
        with st.spinner("Localizando el punto exacto..."):
            coords = obtener_coordenadas(direccion_input)
            
            if coords:
                lat, lon = coords
                st.success(f"¡Punto de anclaje fijado en Lat: {lat}, Lon: {lon}!")

                # --- EL RADAR EN ACCIÓN ---
                with st.spinner("Desplegando radar espacial y escaneando locales... 📡"):
                    # 1. Cargamos la munición (súper rápido gracias a la caché)
                    gdf_puntos = cargar_puntos_maestros()
                    
                    if gdf_puntos is not None:
                        # 2. Arrancamos el motor matemático
                        score_zona, conteo_zona = calcular_lifescore_punto(
                            lat=lat, 
                            lon=lon, 
                            gdf_puntos=gdf_puntos, 
                            diccionario_config=diccionario_config, 
                            sliders_usuario=sliders_subgrupos, 
                            checks_usuario=checks_actividades
                        )
                        
                        # 3. Pintamos los resultados en la web
                        st.divider()
                        st.markdown("### 🏆 Resultado del Análisis")
                        
                        # st.metric crea ese número gigante y bonito típico de los dashboards
                        st.metric(label="LifeScore de esta ubicación exacta", value=f"{score_zona} / 10")
                        
                        # 4. Desplegable de transparencia (Conteo Efectivo)
                        with st.expander("📊 Ver desglose de locales cercanos (Conteo Efectivo)"):
                            st.write("*Nota: Los valores incluyen la Prima de Proximidad (ej: un local a 100m vale 1.2).*")
                            
                            # Limpiamos los ceros y ordenamos de mayor a menor para que quede pro
                            conteo_limpio = {k: round(v, 2) for k, v in conteo_zona.items() if v > 0}
                            conteo_ordenado = dict(sorted(conteo_limpio.items(), key=lambda item: item[1], reverse=True))
                            
                            st.json(conteo_ordenado)

            else:
                st.error("No hemos podido localizar ese punto. Revisa la dirección o intenta usar coordenadas exactas separadas por una coma.")