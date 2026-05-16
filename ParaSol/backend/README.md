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
* USGS SRTM DEM

Responsabilidad:

* consultar datasets
* abstraer Earth Engine

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
* calcular promedio diario de precipitación
* generar serie diaria de precipitación

### twi_service.py

Responsabilidades:

* construir polígonos GIS
* consultar DEM (SRTM 30m)
* calcular pendiente en radianes
* calcular TWI sobre el polígono
* retornar promedio y máximo de TWI

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

### 2. Service construye polígono y consulta CHIRPS

```python
ee.Geometry.Polygon()
ee.ImageCollection("UCSB-CHG/CHIRPS/DAILY")
```

### 3. Backend calcula serie diaria y estadísticas

* una imagen por día → reducción espacial sobre el polígono
* suma total del período
* promedio diario

### 4. Backend devuelve estadísticas

```json
{
  "total_rainfall_mm": 765.86,
  "unit": "mm",
  "period": {
    "start": "2024-01-01",
    "end": "2024-12-31"
  },
  "series": [
    {"date": "2024-01-01", "precipitation_mm": 2.3},
    {"date": "2024-01-02", "precipitation_mm": 0.0}
  ]
}
```

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

| TWI       | Interpretación                        |
| --------- | ------------------------------------- |
| < 6       | zona alta, drena bien                 |
| 6 - 9     | zona intermedia                       |
| > 9       | zona baja, acumula agua               |
| > 11      | muy vulnerable a anegamiento          |

---

# Datos que ofrece el Backend

## /rainfall/check

| campo                 | qué es                                |
| --------------------- | ------------------------------------- |
| `total_rainfall_mm`   | cuánto llovió en todo el período      |
| `unit`                | unidad de medida (mm)                 |
| `period`              | el rango de fechas consultado         |
| `series`              | lluvia real de cada día               |

## /analysis/twi

| campo       | qué es                                          |
| ----------- | ----------------------------------------------- |
| `avg_twi`   | humedad topográfica promedio del polígono        |
| `max_twi`   | zona más vulnerable dentro del polígono         |

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

| Cultivo | Días anegado      | Pérdida estimada              |
| ------- | ----------------- | ----------------------------- |
| Soja    | < 2 días          | sin consecuencias             |
| Soja    | 3 días (temprana) | ~20% rendimiento              |
| Soja    | 4+ días           | reducción población + rinde   |
| Soja    | 7+ días           | daño severo observable        |
| Maíz    | 2-4 días          | sin pérdida apreciable        |
| Maíz    | > 4 días          | daño según etapa fenológica   |

---

# Estado Actual del Proyecto

Actualmente implementado:

* arquitectura modular FastAPI
* integración Earth Engine
* cálculo de lluvia acumulada y serie diaria (CHIRPS)
* cálculo de TWI para detección de zonas vulnerables (SRTM)
* separación routes / services / providers
* logging centralizado
* validación con Pydantic (coordenadas + fechas dinámicas)

---

# Pipeline de Detección de Pérdida de Cosecha

El objetivo del sistema es combinar cuatro fuentes para validar pérdida de cultivo:

```text
CHIRPS      → cuánto llovió
DEM + TWI   → dónde se acumularía el agua
Sentinel-1  → si realmente se acumuló
NDVI        → si el cultivo se dañó
```

---

# Próximos Pasos

## Corto plazo

* Sentinel-1 — detección de anegamiento real
* NDVI — análisis de daño en vegetación (pre vs post evento)
* manejo de excepciones
* response models con Pydantic

## Mediano plazo

* motor paramétrico — combina las cuatro fuentes con umbrales INTA
* triggers automáticos por cultivo y etapa fenológica
* scoring climático con niveles de severidad
* integración blockchain Avalanche
* smart contract payouts

---

# Visión

El objetivo final es construir un motor paramétrico agrícola híbrido que combine:

* análisis satelital multi-fuente
* umbrales agronómicos validados (INTA / AAPRESID)
* automatización climática
* blockchain Avalanche
* pagos automáticos escalonados por severidad
* reducción de fraude mediante hash de polígono y firma de oráculo
* infraestructura escalable

orientado a seguros agrícolas institucionales sobre Avalanche.