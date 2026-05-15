# ParaSol Backend

Backend geoespacial para análisis climático y seguros paramétricos agrícolas sobre Avalanche.

---

# Objetivo

El backend procesa información geoespacial y satelital para detectar eventos climáticos que puedan activar seguros paramétricos automáticos.

Actualmente el sistema permite:

* recibir polígonos geográficos
* consultar datasets satelitales desde Google Earth Engine
* calcular lluvia acumulada
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
CHIRPS Dataset
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
│   └── chirps_provider.py
│
├── schemas/
│   └── rainfall.py
│
├── services/
│   └── rainfall_service.py
│
└── main.py
```

---

# Explicación de Carpetas

## api/routes

Contiene los endpoints HTTP del sistema.

Ejemplo actual:

```text
POST /rainfall/check
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

Responsabilidad:

* consultar datasets
* abstraer Earth Engine

Esto permite cambiar datasets sin romper services.

---

## schemas

Modelos Pydantic utilizados para validar requests.

Ejemplo actual:

```python
class RainfallRequest(BaseModel):
    coordinates: list
```

---

## services

Contiene la lógica de negocio y procesamiento geoespacial.

### rainfall_service.py

Responsabilidades:

* construir polígonos GIS
* consultar datasets climáticos
* calcular lluvia acumulada
* generar estadísticas regionales

---

## main.py

Punto de entrada principal del backend.

Responsabilidades:

* crear aplicación FastAPI
* registrar routers
* cargar inicialización global

---

# Flujo Actual

## 1. Cliente envía coordenadas

Ejemplo:

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
  ]
}
```

---

## 2. FastAPI recibe request

Endpoint:

```text
POST /rainfall/check
```

---

## 3. Service construye polígono

Se genera un objeto GIS real usando:

```python
ee.Geometry.Polygon()
```

---

## 4. Provider consulta CHIRPS

Dataset utilizado:

```text
UCSB-CHG/CHIRPS/DAILY
```

---

## 5. Earth Engine calcula lluvia acumulada

Proceso actual:

* selección banda precipitation
* suma temporal de imágenes
* reducción espacial sobre el polígono

---

## 6. Backend devuelve estadísticas

Ejemplo:

```json
{
  "precipitation": 823.41
}
```

---

# Logging

El backend utiliza logging centralizado.

Ejemplo:

```text
INFO - Checking rainfall
INFO - Rainfall calculation completed
```

---

# Estado Actual del Proyecto

Actualmente implementado:

* arquitectura modular FastAPI
* integración Earth Engine
* cálculo de lluvia acumulada
* separación routes/services/providers
* logging centralizado
* validación básica con Pydantic

---

# Próximos Pasos

## Corto plazo

* validación avanzada de GeoJSON
* manejo de excepciones
* response models
* Sentinel-1 fallback
* NDVI analysis
* análisis multitemporal

---

## Mediano plazo

* motor paramétrico
* triggers automáticos
* scoring climático
* integración blockchain Avalanche
* smart contract payouts

---

# Visión

El objetivo final es construir un motor paramétrico agrícola híbrido que combine:

* análisis satelital
* automatización climática
* blockchain
* pagos automáticos
* reducción de fraude
* infraestructura escalable

orientado a seguros agrícolas institucionales sobre Avalanche.
