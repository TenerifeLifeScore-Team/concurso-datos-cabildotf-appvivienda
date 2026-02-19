import streamlit as st

# ==========================================
# 1. CONFIGURACIÓN DE LA PÁGINA
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
        /* 1. Sidebar al 33% del ancho de la pantalla (vw = viewport width) */
        [data-testid="stSidebar"][aria-expanded="true"] {
            min-width: 33vw;
            max-width: 33vw;
        }

        /* 2. Eliminar el scroll vertical solo de la parte principal (derecha) */
        [data-testid="stMain"] {
            overflow: hidden !important;
        }
        
        /* 3. Reducir el espacio en blanco de arriba para aprovechar la pantalla completa */
        .block-container {
            padding-top: 2rem !important;
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
# 3. CONTENIDO PRINCIPAL (TABS)
# ==========================================
# Fíjate que hemos borrado el st.title() y el st.markdown() que había aquí.

# Creamos las dos pestañas superiores
tab1, tab2 = st.tabs(["🗺️ Visión general del modelo", "📍 Zona específica"])

with tab1:
    # Ajustamos la altura del contenedor para que ocupe casi toda la pantalla visible
    # Cuando metamos el mapa real (ej. Folium o Pydeck), le diremos que use el 100% del alto
    st.info("👈 El panel izquierdo ocupa ahora un 33%. Intenta hacer scroll hacia abajo aquí: ¡está bloqueado! Como una app real.")
    st.container(height=650, border=True)

with tab2:
    st.header("Análisis de tu Zona")
    st.write("Introduce una dirección para ver qué servicios tienes a tu alrededor.")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.text_input("📍 Buscar dirección o barrio...")
    with col2:
        # Añadimos un poco de margen para alinear el botón con la caja de texto
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("Buscar", use_container_width=True)