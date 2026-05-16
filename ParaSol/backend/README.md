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
POST /analysis/flood
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
* Sentinel-1 GRD (SAR)

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

### flood_service.py

Responsabilidades:

* construir polígonos GIS
* consultar Sentinel-1 GRD (VV, IW, 10m) en una ventana pre y otra post evento
* aplicar speckle filter (focal_median) sobre el composite mediana de cada ventana
* aplicar umbral de backscatter en dB para clasificar agua
* calcular % de área inundada en el post-evento
* calcular % de área NUEVA inundada (cambio neto pre → post)
* devolver delta de backscatter VV en dB

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

## Endpoint: POST /analysis/flood

Detección de anegamiento real con **Sentinel-1 SAR**.

El radar atraviesa nubes y funciona de noche, por lo que es la fuente
correcta cuando hay nubosidad alta o el evento ocurre fuera del horario
diurno. El servicio compara el backscatter VV pre vs post sobre el
mismo polígono y misma pasada orbital.

### 1. Cliente envía polígono y ventanas pre/post evento

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
  },
  "pre_event":  { "start_date": "2024-01-01", "end_date": "2024-01-20" },
  "post_event": { "start_date": "2024-02-01", "end_date": "2024-02-15" },
  "orbit": "DESCENDING",
  "flood_threshold_db": -17.0,
  "min_flooded_area_pct": 5.0
}
```

`orbit`, `flood_threshold_db` y `min_flooded_area_pct` son opcionales.
Si no se fija `orbit`, el service elige automáticamente la pasada con
más escenas en el post-evento. `min_flooded_area_pct` (default 5%) es
el umbral binario por escena para considerarla "anegada" — subir para
cultivos tolerantes, bajar para sensibles.

### 2. Service procesa con Earth Engine

* filtra `COPERNICUS/S1_GRD` por VV / IW / 10m / mismo `relativeOrbitNumber_start`
* construye composites:
  * **pre = median()** — baseline robusto del estado seco típico
  * **post = min()** — captura el píxel más oscuro de cada lugar a lo largo
    del período post, exponiendo eventos cortos que la mediana ahogaría
* aplica focal_median (despeckle) sobre cada composite
* aplica el umbral en dB para clasificar agua
* análisis adicional escena por escena para `flood_detected` y `flood_days`

### 3. Backend devuelve estadísticas SAR

```json
{
  "status": "ok",
  "message": "Detección de anegamiento completada",
  "pre_event": {
    "period": { "start_date": "2024-01-01", "end_date": "2024-01-20" },
    "scene_count": 5,
    "vv_mean_db": -10.42
  },
  "post_event": {
    "period": { "start_date": "2024-02-01", "end_date": "2024-02-15" },
    "scene_count": 4,
    "vv_mean_db": -16.18
  },
  "orbit_used": "DESCENDING",
  "flood_threshold_db": -17.0,
  "min_flooded_area_pct": 5.0,
  "flooded_area_pct": 23.41,
  "new_flooded_area_pct": 19.07,
  "delta_vv_db": -5.76,
  "flood_detected": true,
  "flood_days": 32,
  "scenes": [
    { "date": "2024-02-03", "new_flooded_pct": 18.42, "flooded": true },
    { "date": "2024-02-15", "new_flooded_pct": 21.07, "flooded": true },
    { "date": "2024-03-06", "new_flooded_pct": 11.34, "flooded": true },
    { "date": "2024-03-18", "new_flooded_pct": 2.11, "flooded": false }
  ]
}
```

### Interpretación del backscatter VV

| VV (dB)      | Superficie                                  |
| ------------ | ------------------------------------------- |
| > -10        | suelo seco, vegetación densa                |
| -10 a -15    | suelo húmedo, cultivo                       |
| -15 a -17    | transición / cultivo anegado                |
| < -17        | superficie de agua libre                    |

| Métrica                 | Qué representa                                        |
| ----------------------- | ----------------------------------------------------- |
| `flooded_area_pct`      | % del polígono clasificado como agua en el post       |
| `new_flooded_area_pct`  | % que pasó de NO-agua (pre) a agua (post) — efecto neto del evento |
| `delta_vv_db`           | caída de backscatter medio. Más negativo = más agua   |
| `flood_detected`        | `true` si al menos una escena post supera `min_flooded_area_pct` vs baseline |
| `flood_days`            | span en días entre la primera y la última escena anegada |
| `scenes`                | detalle por escena (fecha, % nuevo-inundado, flag binaria) |

`new_flooded_area_pct` es la métrica clave para el motor paramétrico:
descuenta cuerpos de agua permanentes (lagunas, cauces) y aísla el
cambio atribuible al evento. `flood_detected` + `flood_days` son los
disparadores binarios y la duración que se ata al payout.

**Nota sobre `flood_days`.** Sentinel-1 revisita cada ~6–12 días, por
lo que `flood_days` no es una medición diaria sino el *span* entre la
primera y la última escena que cumplió el umbral dentro del
`post_event`. Es la métrica honesta dada la cadencia del sensor.

**Por qué pre = median y post = min.** El motor paramétrico tiene que
ser robusto a dos situaciones contrapuestas:

* **Eventos largos** (Pakistán Sindh 2022 — anegamiento por semanas).
  Cualquier reducer captura la señal. La mediana es fina.
* **Eventos cortos** (Ciclón Idai 2019 — peak de 1–2 días, drena
  rápido). Si solo una escena post está bajo agua y las siguientes
  están secas, la mediana por píxel devuelve "seco" — ahoga el peak.
  Por eso al post se le aplica `min()`: para cada píxel toma su
  momento más oscuro durante el período post, exponiendo agua aunque
  haya durado un solo barrido. Es el approach estándar de UN-SPIDER
  para flood detection con SAR.

Al pre se le mantiene la mediana porque ahí queremos el estado seco
"típico" como baseline — no el peor caso (que podría incluir lluvias
puntuales que contaminarían la referencia).

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

## /analysis/flood

| campo                   | qué es                                                  |
| ----------------------- | ------------------------------------------------------- |
| `pre_event.vv_mean_db`  | backscatter VV medio antes del evento (referencia seca) |
| `post_event.vv_mean_db` | backscatter VV medio después del evento                 |
| `flooded_area_pct`      | % de área inundada total en el post-evento              |
| `new_flooded_area_pct`  | % de área NUEVA inundada atribuible al evento           |
| `delta_vv_db`           | caída del backscatter medio (post - pre)                |
| `orbit_used`            | pasada orbital utilizada (ASCENDING / DESCENDING)       |
| `flood_detected`        | booleano — hubo o no anegamiento real atribuible al evento |
| `flood_days`            | duración del anegamiento detectable (en días)           |
| `scenes`                | observaciones por escena                                |

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
* detección de anegamiento real con Sentinel-1 SAR (pre vs post evento)
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

* NDVI (Sentinel-2) — análisis de daño en vegetación (pre vs post evento)
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