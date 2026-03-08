# 📍 Tenerife LifeScore

**Tenerife LifeScore** es una solución tecnológica avanzada diseñada para ayudar a los ciudadanos a encontrar su lugar ideal para vivir en la isla de Tenerife. Utilizando el poder de los **Datos Abiertos** y la **Inteligencia Artificial**, la aplicación analiza miles de puntos de datos para puntuar cada rincón de la isla según las necesidades reales de cada persona.

---

## 📸 Capturas de Pantalla

| Pantalla de Carga | Mapa de Calor | Mi Zona | Análisis con IA |
| :---: | :---: | :---: | :---: |
| <img width="216" height="480" alt="Pantalla de Carga" src="https://github.com/user-attachments/assets/43249853-490b-4b25-8c49-1a9ca85a0fe2" /> | <img width="216" height="480" alt="Mapa de Calor" src="https://github.com/user-attachments/assets/90b68b6f-8f13-4b3e-ae03-12ee474e6db7" /> | <img width="216" height="480" alt="Mi Zona" src="https://github.com/user-attachments/assets/37e677f0-cdf7-4c75-9f74-9a78b239076e" /> | <img width="216" height="480" alt="Análisis con IA" src="https://github.com/user-attachments/assets/4618403f-a28c-4d41-8f8e-e863d9c1d33a" /> |
---

## ✨ Características Principales

* **Visualización Geoespacial:** Mapa de calor interactivo basado en hexágonos que representa la calidad de vida en tiempo real.
* **Perfiles de Usuario:** Ajustes automáticos para estudiantes, familias, perfiles activos y más.
* **Análisis Inteligente (IA):** Generación de informes detallados sobre los pros y contras de cada zona usando modelos de lenguaje (LLM).
* **9 Conjuntos de Datos Abiertos:** Integración directa con el portal de datos del Cabildo (transporte, educación, salud, ocio, naturaleza, etc.).
* **Accesibilidad Total:** Cumplimiento de la normativa WCAG 2.1 AA, compatible con TalkBack y VoiceOver.

---

## 📂 Estructura del Proyecto

El repositorio está organizado como un monorepositorio que cubre todo el ciclo de vida del dato:

```text
.
├── 📱 mobile_app/         # Frontend desarrollado en Flutter (Android/iOS)
├── ⚙️ backend_api/        # API en Python para el cálculo de scores y servicio de IA
├── 🧪 etl-pipeline/       # Procesamiento de datos crudos (GeoJSON) y modelado
├── 📊 streamlit-app/      # Dashboard web interno para validación de datos
├── 📦 entregables/        # Archivos finales compilados (APK e IPA)
└── 📄 README.md           # El archivo que estás leyendo ahora mismo

```

---

## 🛠️ Stack Tecnológico

* **Frontend:** [Flutter](https://flutter.dev/) - Multiplataforma y alto rendimiento.
* **Backend:** [Python](https://www.python.org/) - Procesamiento lógico y API.
* **IA:** Integración de LLM para análisis semántico de barrios.
* **Geodatos:** [GeoJSON](https://geojson.org/) para la gestión de capas espaciales.
* **Datos:** Portal de [Datos Abiertos del Cabildo de Tenerife](https://datos.tenerife.es/).

---

## 🤝 Créditos

Desarrollado por el **Tenerife LifeScore Team** para el II Concurso de Datos Abiertos del Cabildo de Tenerife (2026).

* **Alejandro Delgado**
* **Aythami Lorenzo**
* **Tomas Santana**
