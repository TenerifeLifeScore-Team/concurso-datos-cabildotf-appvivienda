import streamlit as st
import pydeck as pdk
from streamlit_option_menu import option_menu
from utils import *
from loaders import cargar_datos_mapa
from engine import calcular_lifescore_vectorial

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
            overflow: hidden !important;
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
                        min_value=1, max_value=10, value=5, step=1,
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
    
    # Verificación de seguridad
    if gdf_hexagons.empty:
        st.error("⚠️ No se pudo cargar el mapa base (GeoJSON). Revisa 'loaders.py'.")
        st.stop()

    # Contenedor principal
    # Botón de calcular del sidebar
    if boton_calcular:
        with st.spinner("Calculando LifeScore para toda la isla... 🧮"):
            
            # A. PREPARAR INPUTS
            # Los diccionarios 'sliders_subgrupos' y 'checks_actividades' ya vienen rellenos del sidebar
            
            # B. LLAMAR AL MOTOR (ENGINE)
            # Esto nos devuelve el GeoDataFrame con la columna 'score_final'
            gdf_resultado = calcular_lifescore_vectorial(
                gdf_hexagons, 
                diccionario_config, 
                sliders_subgrupos, 
                checks_actividades
            )
            
            # C. PREPARAR COLORES PARA PYDECK
            # PyDeck necesita una columna con lista [R, G, B]. La creamos al vuelo.
            # Usamos una lambda para aplicar la función de colores fila a fila.
            gdf_resultado["fill_color"] = gdf_resultado["score_final"].apply(obtener_color_por_score)
            
            # D. CONFIGURAR EL MAPA (PYDECK)
            view_state = pdk.ViewState(
                latitude=28.30,     # Centro aprox de Tenerife
                longitude=-16.55,
                zoom=9,
                pitch=0,            # 0 para vista cenital (2D), 45 para 3D
            )

            layer_hexagonos = pdk.Layer(
                "GeoJsonLayer",
                data=gdf_resultado,
                opacity=0.8,
                stroked=False,      # Sin bordes negros para que se vea más limpio
                filled=True,
                extruded=False,     # Ponlo a True si quieres que los hexágonos tengan altura
                get_fill_color="fill_color", # Usamos la columna que acabamos de crear
                pickable=True,      # Para que funcione el tooltip al pasar el ratón
            )

            # Tooltip: Qué sale al pasar el ratón
            tooltip = {
                "html": "<b>LifeScore:</b> {score_final}/10",
                "style": {"backgroundColor": "steelblue", "color": "white"}
            }

            r = pdk.Deck(
                layers=[layer_hexagonos],
                initial_view_state=view_state,
                tooltip=tooltip,
                map_style="mapbox://styles/mapbox/light-v9" # O 'road', 'dark', etc.
            )

            # E. PINTAR FINALMENTE
            st.pydeck_chart(r, use_container_width=True)
            
            # F. Métrica resumen (Opcional pero útil)
            # mejor_zona = gdf_resultado['score_final'].max()
            # st.success(f"✅ Mapa actualizado. La puntuación máxima encontrada es **{mejor_zona}/100**.")
            
    else:
        st.info("👈 Ajusta tus preferencias en el menú lateral y pulsa 'Calcular LifeScore'.")




elif seleccion_menu == "Zona específica":
    st.write("Introduce una dirección para ver qué servicios tienes a tu alrededor.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("📍 Buscar dirección o barrio...")
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("Buscar", use_container_width=True)
        
    st.info("👆 Aquí saldrán las métricas específicas del hexágono seleccionado.")