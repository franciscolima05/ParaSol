# ParaSol Backend

Backend geoespacial para análisis climático y seguros paramétricos agrícolas sobre Avalanche.

---

# Objetivo

El backend procesa información geoespacial y satelital para detectar eventos climáticos que puedan activar seguros paramétricos automáticos.

Actualmente el sistema permite:

* recibir polígonos geográficos
* consultar datasets satelitales desde Google Earth Engine
* calcular lluvia acumulada y serie diaria de precipitación
* calcular TWI (Topographic Wetness Index) para detectar zonas vulnerables a anegamiento
* obtener estadísticas climáticas sobre una región
* exponer endpoints HTTP mediante FastAPI

---

# Arquitectura Actual

```text
Client
   ↓
FastAPI API
   ↓
Services Layer
   ↓
Providers Layer
   ↓
Google Earth Engine
   ↓
CHIRPS Dataset / SRTM DEM
```

---

# Stack Tecnológico

| Componente          | Tecnología          |
| ------------------- | ------------------- |
| API                 | FastAPI             |
| Geoprocesamiento    | Google Earth Engine |
| Lenguaje            | Python 3.14         |
| Validación de datos | Pydantic            |
| Logging             | logging             |
| Dataset climático   | CHIRPS Daily        |
| Dataset topográfico | USGS SRTM GL1 003   |

---

# Estructura del Proyecto

```text
app/
├── api/
│   └── routes/
│       └── analysis.py
│
├── core/
│   ├── earth_engine.py
│   └── logger.py
│
├── providers/
│   ├── chirps_provider.py
│   └── dem_provider.py
│
├── schemas/
│   └── rainfall.py
│
├── services/
│   ├── rainfall_service.py
│   └── twi_service.py
│
└── main.py
```

---

# Explicación de Carpetas

## api/routes

Contiene los endpoints HTTP del sistema.

Endpoints actuales:

```text
POST /rainfall/check
POST /analysis/twi
POST /analysis/ndvi
```

Responsabilidades:

* recibir requests
* validar entrada
* delegar lógica a services

---

## core

Infraestructura global del backend.

### earth_engine.py

Inicializa Google Earth Engine.

### logger.py

Configuración centralizada de logs.

---

## providers

Capa de acceso a fuentes externas.

Actualmente:

* CHIRPS rainfall dataset
* Sentinel-2 NDVI
* USGS SRTM DEM

Responsabilidad:

* consultar datasets
* abstraer Earth Engine
* desacoplar providers del motor de negocio

Esto permite cambiar datasets sin romper services.

---

## schemas

Modelos Pydantic utilizados para validar requests.

```python
class RainfallRequest(BaseModel):
    coordinates: list
    start_date: str
    end_date: str
```

---

## services

Contiene la lógica de negocio y procesamiento geoespacial.

### rainfall_service.py

Responsabilidades:

* construir polígonos GIS
* consultar CHIRPS dataset
* calcular lluvia acumulada total
* calcular estadísticas espaciales
* detectar baja cobertura espacial
* calcular píxeles efectivos utilizados
* generar serie diaria de precipitación

### twi_service.py

Responsabilidades:

* construir polígonos GIS
* consultar DEM (SRTM 30m)
* calcular pendiente en radianes
* calcular TWI sobre el polígono
* retornar promedio y máximo de TWI

### ndvi_service.py

Responsabilidades:

* consultar Sentinel-2
* calcular NDVI
* aplicar filtros de nubosidad
* calcular métricas vegetativas
* clasificar estado vegetativo

---

## main.py

Punto de entrada principal del backend.

Responsabilidades:

* crear aplicación FastAPI
* registrar routers
* cargar inicialización global

---

# Flujo Actual

## Endpoint: POST /rainfall/check

### 1. Cliente envía coordenadas y fechas

```json
{
  "coordinates": [
    [
      [-60.326698, -38.198767],
      [-60.306698, -38.198767],
      [-60.306698, -38.178767],
      [-60.326698, -38.178767],
      [-60.326698, -38.198767]
    ]
  ],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

---

### 2. Service construye polígono y consulta CHIRPS

```python
ee.Geometry.Polygon()
ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
```

Dataset utilizado:

| Dataset      | Resolución    | Tipo                           |
| ------------ | ------------- | ------------------------------ |
| CHIRPS Daily | ~5.5 km/pixel | precipitación diaria satelital |

---

### 3. Backend calcula estadísticas espaciales diarias

Para cada imagen diaria el backend:

* calcula promedio espacial de precipitación
* calcula máximo espacial
* calcula mínimo espacial
* calcula percentil 95 espacial
* calcula cantidad efectiva de píxeles utilizados

La reducción espacial se realiza utilizando la resolución nativa del dataset CHIRPS obtenida automáticamente desde Earth Engine.

Ejemplo:

```python
native_scale = image.projection().nominalScale()
```

---

### 4. Validación de confiabilidad espacial

El backend detecta automáticamente si el polígono cubre muy pocos píxeles CHIRPS.

Esto es importante porque:

* CHIRPS posee resolución relativamente baja (~5 km)
* polígonos pequeños pueden generar estadísticas poco robustas
* percentiles espaciales pueden perder validez con pocos píxeles

El sistema devuelve:

```json
{
  "low_confidence": true,
  "confidence_reasons": [
    "polygon covers too few CHIRPS pixels"
  ]
}
```

Esto permite exponer incertidumbre estadística de forma transparente para aplicaciones institucionales y seguros paramétricos.

---

### 5. Backend devuelve estadísticas climáticas

```json
{
  "low_confidence": true,
  "confidence_reasons": [
    "polygon covers too few CHIRPS pixels"
  ],

  "total_rainfall_mm": 70.2,

  "max_observed_mm": 44.66,

  "unit": "mm",

  "dataset": "UCSB-CHG/CHIRPS/DAILY",

  "spatial_resolution_km": 5,

  "native_scale_meters": 5565.97,

  "period": {
    "start": "2013-04-01",
    "end": "2013-04-04"
  },

  "series": [
    {
      "date": "2013-04-01",

      "mean_mm": 38.45,

      "max_mm": 44.66,

      "min_mm": 28.62,

      "p95_mm": 44.66,

      "effective_pixels": 2
    }
  ]
}
```

---

### Interpretación de Métricas CHIRPS

| Campo                 | Qué representa                               |
| --------------------- | -------------------------------------------- |
| `total_rainfall_mm`   | lluvia acumulada del período                 |
| `max_observed_mm`     | máximo extremo observado dentro del polígono |
| `mean_mm`             | promedio espacial regional                   |
| `max_mm`              | pixel con mayor precipitación                |
| `min_mm`              | pixel con menor precipitación                |
| `p95_mm`              | percentil 95 espacial de precipitación       |
| `effective_pixels`    | cantidad de píxeles utilizados               |
| `low_confidence`      | indica baja robustez estadística             |
| `native_scale_meters` | resolución real utilizada                    |

---

## CHIRPS — Consideraciones Técnicas

CHIRPS es un dataset satelital de precipitación diseñado para monitoreo climático y agrícola.

Ventajas:

* cobertura histórica extensa
* resolución diaria
* buena estabilidad temporal
* ampliamente utilizado en climatología y agricultura

Limitaciones:

* resolución espacial moderada (~5 km)
* no detecta inundación directa
* puede suavizar eventos muy localizados
* polígonos pequeños pueden utilizar pocos píxeles

Por esta razón el backend implementa:

* detección automática de baja cobertura espacial
* exposición de incertidumbre
* validación de píxeles efectivos
* estadísticas espaciales robustas

---

## Endpoint: POST /analysis/twi

### 1. Cliente envía polígono

```json
{
  "polygon": {
    "coordinates": [
      [
        [-60.326698, -38.198767],
        [-60.306698, -38.198767],
        [-60.306698, -38.178767],
        [-60.326698, -38.178767],
        [-60.326698, -38.198767]
      ]
    ]
  }
}
```

### 2. Service calcula TWI desde DEM SRTM (30m)

* pendiente en radianes
* acumulación de flujo aproximada por convolución
* TWI = ln(flow_acc / tan(slope))
* reducción espacial sobre el polígono

### 3. Backend devuelve estadísticas topográficas

```json
{
  "status": "ok",
  "message": "TWI calculado",
  "data": {
    "avg_twi": 8.897949874733417,
    "max_twi": 11.952496185564904
  }
}
```

### Interpretación del TWI

| TWI   | Interpretación               |
| ----- | ---------------------------- |
| < 6   | zona alta, drena bien        |
| 6 - 9 | zona intermedia              |
| > 9   | zona baja, acumula agua      |
| > 11  | muy vulnerable a anegamiento |

---

## Endpoint: POST /analysis/ndvi

### 1. Cliente envía polígono y período

```json
{
  "coordinates": [
    [
      [-58.0200, -34.9300],
      [-57.9000, -34.9300],
      [-57.9000, -35.0200],
      [-58.0200, -35.0200],
      [-58.0200, -34.9300]
    ]
  ],
  "start_date": "2025-01-01",
  "end_date": "2025-12-31"
}
```

---

### 2. Service consulta Sentinel-2 y calcula NDVI

```python
(COPERNICUS/S2_SR_HARMONIZED)
```

El backend:

* aplica filtros de nubosidad
* calcula NDVI
* calcula estadísticas vegetativas
* clasifica vigor vegetal

---

### 3. Backend devuelve métricas vegetativas

```json
{
  "low_confidence": false,

  "period": {
    "start": "2025-01-01",
    "end": "2025-12-31"
  },

  "ndvi": {
    "ndvi_mean": 0.4149,
    "ndvi_min": 0.1691,
    "ndvi_max": 0.8538,
    "ndvi_median": 0.4004,
    "image_count": 59
  },

  "classification": {
    "label": "moderate_crop",
    "description": "Cultivo en desarrollo o pastizal",
    "value": 0.4149
  },

  "dataset": "COPERNICUS/S2_SR_HARMONIZED",

  "resolution_meters": 10
}
```

---

### Interpretación NDVI

| NDVI      | Interpretación                  |
| --------- | ------------------------------- |
| < 0.2     | suelo desnudo                   |
| 0.2 - 0.4 | vegetación baja                 |
| 0.4 - 0.6 | cultivo moderado                |
| 0.6 - 0.8 | cultivo vigoroso                |
| > 0.8     | vegetación extremadamente densa |

---

# Datos que ofrece el Backend

## /rainfall/check

| Campo               | Qué representa            |
| ------------------- | ------------------------- |
| `total_rainfall_mm` | lluvia acumulada          |
| `max_observed_mm`   | máximo extremo detectado  |
| `series`            | estadísticas diarias      |
| `effective_pixels`  | píxeles utilizados        |
| `low_confidence`    | baja robustez estadística |

---

## /analysis/twi

| Campo     | Qué representa               |
| --------- | ---------------------------- |
| `avg_twi` | humedad topográfica promedio |
| `max_twi` | zona más vulnerable          |

---

## /analysis/ndvi

| Campo            | Qué representa              |
| ---------------- | --------------------------- |
| `ndvi_mean`      | vigor vegetativo promedio   |
| `ndvi_max`       | máximo vigor observado      |
| `image_count`    | imágenes válidas utilizadas |
| `classification` | clasificación agronómica    |

---

# Logging

El backend utiliza logging centralizado.

Ejemplo:

```text
INFO - comprobando la lluvia
INFO - serie diaria calculada: 365 días
INFO - calculo de lluvia completado
```

---

# Fundamento Agronómico de los Umbrales

Basado en literatura del INTA y AAPRESID para cultivos de la región pampeana:

| Cultivo | Días anegado | Pérdida estimada       |
| ------- | ------------ | ---------------------- |
| Soja    | < 2 días     | sin consecuencias      |
| Soja    | 3 días       | ~20% rendimiento       |
| Soja    | 4+ días      | reducción de rinde     |
| Soja    | 7+ días      | daño severo            |
| Maíz    | 2-4 días     | sin pérdida apreciable |
| Maíz    | > 4 días     | daño según etapa       |

---

# Pipeline de Detección de Pérdida de Cosecha

El objetivo del sistema es combinar múltiples fuentes satelitales:

```text
CHIRPS      → cuánto llovió
DEM + TWI   → dónde podría acumularse agua
Sentinel-1  → si realmente hubo inundación
NDVI        → si el cultivo sufrió daño
```

Esto permite reducir:

* falsos positivos
* fraude
* errores climáticos
* payouts incorrectos

---

# Estado Actual del Proyecto

Actualmente implementado:

* arquitectura modular FastAPI
* integración Earth Engine
* análisis CHIRPS
* análisis TWI
* análisis NDVI
* estadísticas espaciales
* manejo de incertidumbre
* validación de píxeles efectivos
* logging centralizado
* separación routes/services/providers

---

# Próximos Pasos

## Corto plazo

* Sentinel-1 SAR
* detección real de inundación
* NDVI temporal pre/post evento
* manejo avanzado de excepciones
* response models tipados

## Mediano plazo

* motor paramétrico multi-fuente
* triggers automáticos
* scoring climático
* integración Avalanche
* smart contract payouts
* hashes verificables de evidencia

---

# Visión

El objetivo final es construir un motor paramétrico agrícola híbrido que combine:

* análisis satelital multi-fuente
* umbrales agronómicos validados
* automatización climática
* blockchain Avalanche
* payouts automáticos
* reducción de fraude
* auditoría verificable
* infraestructura escalable

orientado a seguros agrícolas institucionales sobre Avalanche.
