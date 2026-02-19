import streamlit as st
from streamlit_option_menu import option_menu
from utils import cargar_configuracion, obtener_jerarquia_categorias

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
jerarquia = obtener_jerarquia_categorias(diccionario_config)

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
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. BARRA LATERAL (SIDEBAR) - Personalización
# ==========================================

with st.sidebar:

    st.title("⚙️ Personaliza tu LifeScore")

    # Abrimos el formulario para que no recalcule hasta pulsar el botón
    with st.form("formulario_parametros"):
        sliders_subgrupos = {}
        checks_actividades = {}

        # Generación dinámica leyendo la jerarquía importada
        for macro_categoria, grupos in jerarquia.items():
            st.markdown(f"### {macro_categoria}")
            for grupo_slider, lista_actividades in grupos.items():
                sliders_subgrupos[grupo_slider] = st.slider(
                    f"Importancia de: {grupo_slider}", 
                    min_value=1, max_value=10, value=5, step=1
                )

                with st.expander(f"Filtros de {grupo_slider} 🔽"):
                    st.markdown("<small>Desmarca lo que no necesites:</small>", unsafe_allow_html=True)
                    for actividad in lista_actividades:
                        checks_actividades[actividad] = st.checkbox(actividad.title(), value=True)
        
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
    st.container(height=300, border=True)
    st.info("👆 Aquí se pintará el mapa interactivo completo de Tenerife.")

elif seleccion_menu == "Zona específica":
    st.write("Introduce una dirección para ver qué servicios tienes a tu alrededor.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("📍 Buscar dirección o barrio...")
    with col2:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("Buscar", use_container_width=True)
        
    st.info("👆 Aquí saldrán las métricas específicas del hexágono seleccionado.")