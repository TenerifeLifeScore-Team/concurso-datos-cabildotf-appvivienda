import streamlit as st
from streamlit_option_menu import option_menu

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA Y CSS
# ==========================================
st.set_page_config(
    page_title="Tenerife LifeScore",
    page_icon="🏝️",
    layout="wide", 
    initial_sidebar_state="expanded"
)

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
        /* Aniquilar el espacio superior oculto de la barra lateral */
        [data-testid="stSidebarHeader"] {
            padding: 0 !important;
            height: 2rem !important;
            min-height: 0 !important;
        }
        [data-testid="stSidebarUserContent"] {
            padding-top: 0 !important; 
        }
    </style>
    """,
    unsafe_allow_html=True,
)

# ==========================================
# 2. BARRA LATERAL (SIDEBAR) - Personalización
# ==========================================
with st.sidebar:
    st.title("⚙️ Personalización")
    st.markdown("Ajusta tus preferencias para encontrar tu zona ideal.")
    st.divider()

    # --- EJEMPLO DE UN GRUPO (Salud) ---
    st.subheader("🏥 Salud Vital")
    
    peso_salud = st.slider(
        "Importancia de la Salud", 
        min_value=1, max_value=10, value=8, step=1,
        help="1 = Nada importante, 10 = Imprescindible"
    )
    
    with st.expander("Ver opciones avanzadas 🔽"):
        st.markdown("<small>Desmarca lo que no necesites:</small>", unsafe_allow_html=True)
        chk_farmacia = st.checkbox("Farmacias", value=True)
        chk_centro_salud = st.checkbox("Centros de Salud", value=True)
        chk_hospital = st.checkbox("Servicios Hospitalarios", value=True)

    st.divider()
    
    st.button("Calcular LifeScore 🚀", use_container_width=True, type="primary")

# ==========================================
# 3. NAVEGACIÓN SUPERIOR HORIZONTAL
# ==========================================
# Esto crea el menú bonito arriba del todo
seleccion_menu = option_menu(
    menu_title=None,  # No necesitamos título para el menú en sí
    options=["Visión general del modelo", "Zona específica"], 
    icons=["map", "pin-map-fill"],  # Iconos de Bootstrap
    default_index=0, 
    orientation="horizontal"
)

# ==========================================
# 4. CONTENIDO PRINCIPAL (Lógica del Menú)
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