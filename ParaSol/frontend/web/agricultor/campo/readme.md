# ParaSol Terminal — GeoSpatial Operations Interface

## Descripción General
**ParaSol Terminal** es una interfaz de precisión geoespacial diseñada para el ecosistema de seguros paramétricos agrícolas sobre la blockchain **Avalanche**. Esta interfaz transforma la complejidad del análisis satelital en una experiencia de usuario intuitiva, permitiendo la delimitación de parcelas y la consulta en tiempo real de métricas climáticas críticas.

El sistema actúa como el puente entre el mundo físico (campos agrícolas) y el mundo digital (smart contracts), proporcionando la "verdad técnica" necesaria para disparar pagos automáticos sin intervención humana.

---

## Perfil de Usuario: ¿Para quién es esta interfaz?


### 1. El Agricultor (User-Centric)
*   **Transparencia Total**: El agricultor puede ver exactamente qué datos está leyendo el satélite sobre su campo.
*   **Autogestión**: Permite dibujar su propia parcela y verificar si las condiciones para un payout (pago de seguro) se han cumplido.
*   **Simplicidad**: No necesita entender de coordenadas complejas o JSON; las herramientas de dibujo y las tarjetas de colores (verde/rojo) le indican el estado de su cultivo.

---

## Características Técnicas

### 1. Motor Geoespacial
*   **Leaflet Engine**: Implementación ligera y eficiente para el renderizado de mapas.
*   **Esri World Imagery**: Capa satelital de alta resolución para identificación visual de cultivos.
*   **Leaflet Draw + Turf.js**: Herramientas de dibujo con cálculo de área en hectáreas (ha) con precisión decimal.

### 2. Integración Satelital (Render API)
La interfaz se conecta con el backend de ParaSol en Render para procesar:
*   **CHIRPS**: Lluvia acumulada y picos de precipitación.
*   **SRTM (TWI)**: Índice de humedad topográfica para detectar zonas de acumulación de agua.
*   **Sentinel-2 (NDVI)**: Índice de vegetación para evaluar el vigor y daño del cultivo.
*   **Sentinel-1 (SAR)**: Radar de apertura sintética para detección de inundaciones (incluso con nubes).

### 3. UX/UI Agro-Tech
*   **Estética Dark/Tech**: Diseño optimizado para terminales de campo, reduciendo la fatiga visual.
*   **Scanline Overlay**: Efecto visual de "escaneo satelital" que refuerza la naturaleza técnica del sistema.
*   **Feedback en Tiempo Real**: Indicadores de carga ("SCANNING...", "LOADING...") que mantienen al usuario informado sobre el estado de las peticiones asíncronas.

---

## Flujo de Operación

1.  **Selección**: El usuario localiza su campo y utiliza la herramienta de **Pentágono** o **Rectángulo** para delimitar la parcela.
2.  **Validación**: El sistema calcula automáticamente el área y genera el **GeoJSON** en el panel de control.
3.  **Análisis**: Se seleccionan las fechas de interés y se presiona **"ANALIZAR CAMPO"**.
4.  **Resultado**: Las tarjetas del **STEP_02** se actualizan con datos reales. Si se detecta una inundación, se activa una alerta visual pulsante.
5.  **Blockchain Ready**: El GeoJSON validado queda listo para ser vinculado a una póliza NFT en Avalanche.

---

## Stack Tecnológico
*   **Frontend**: HTML5, CSS3 (Tailwind CSS), Vanilla JavaScript.
*   **Mapas**: Leaflet.js, Leaflet.draw.
*   **Geoprocesamiento**: Turf.js.
*   **Backend**: FastAPI (Python) desplegado en Render.
*   **Datasets**: Google Earth Engine (CHIRPS, Sentinel, SRTM).

---

**ParaSol Terminal** — *Transformando el riesgo climático en código ejecutable.*
