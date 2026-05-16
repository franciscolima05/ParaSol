# ParaSol Backend

Backend geoespacial para análisis climático y seguros paramétricos agrícolas sobre Avalanche.

---

## Objetivo

El backend procesa información geoespacial y satelital para detectar eventos climáticos que puedan activar seguros paramétricos automáticos sobre la red Avalanche.

El sistema permite:

- recibir polígonos geográficos de parcelas agrícolas
- consultar datasets satelitales desde Google Earth Engine
- calcular lluvia acumulada y serie diaria de precipitación (CHIRPS)
- calcular TWI (Topographic Wetness Index) para detectar zonas vulnerables a anegamiento
- detectar inundaciones reales con Sentinel-1 SAR (pre vs post evento)
- calcular NDVI (Sentinel-2) para evaluar daño en vegetación
- exponer endpoints HTTP mediante FastAPI
- persistir datos de pólizas, eventos paramétricos y pagos en PostgreSQL/PostGIS
- escuchar eventos on-chain del smart contract para sincronizar la base de datos

---

## Arquitectura

```text
Client
   ↓
FastAPI API
   ↓
Services Layer
   ↓
Providers Layer          Repositories Layer
   ↓                            ↓
Google Earth Engine       PostgreSQL / PostGIS
   ↓
CHIRPS / SRTM / Sentinel-1 / Sentinel-2
```

---

## Stack Tecnológico

| Componente           | Tecnología                    |
| -------------------- | ----------------------------- |
| API                  | FastAPI                       |
| Geoprocesamiento     | Google Earth Engine           |
| Lenguaje             | Python 3.14                   |
| Validación de datos  | Pydantic                      |
| Base de datos        | PostgreSQL + PostGIS          |
| ORM                  | SQLAlchemy + GeoAlchemy2      |
| Blockchain           | Web3.py + Avalanche Fuji      |
| Logging              | logging                       |
| Dataset climático    | CHIRPS Daily                  |
| Dataset topográfico  | USGS SRTM GL1 003             |
| Dataset SAR          | Copernicus Sentinel-1 GRD     |
| Dataset vegetación   | Copernicus Sentinel-2 SR      |

---

## Estructura del Proyecto

```text
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── analysis.py
│   │
│   ├── core/
│   │   ├── earth_engine.py
│   │   └── logger.py
│   │
│   ├── providers/
│   │   ├── chirps_provider.py
│   │   ├── dem_provider.py
│   │   └── sentinel1_provider.py
│   │
│   ├── schemas/
│   │   ├── rainfall.py
│   │   └── sentinel.py
│   │
│   ├── services/
│   │   ├── rainfall_service.py
│   │   ├── twi_service.py
│   │   ├── flood_service.py
│   │   ├── flood_debug_service.py
│   │   └── ndvi_service.py
│   │
│   └── main.py
│
└── src/
    ├── database.py
    │
    ├── models/
    │   ├── __init__.py
    │   ├── User.py
    │   ├── Field.py
    │   ├── Policy.py
    │   ├── PolicyPayout.py
    │   ├── LiquidityPool.py
    │   └── ParametricEvent.py
    │
    ├── repositories/
    │   ├── __init__.py
    │   ├── userRepository.py
    │   ├── fieldRepository.py
    │   ├── policyRepository.py
    │   ├── policyPayoutRepository.py
    │   ├── liquidityPoolRepository.py
    │   └── parametricEventRepository.py
    │
    └── services/
        ├── userService.py
        ├── fieldService.py
        ├── policyService.py
        ├── parametricService.py
        ├── poolService.py
        ├── oracleService.py
        └── blockchain/
            ├── client.py
            ├── events.py
            ├── engine_contracts.py
            └── pool_contract.py
```

---

## Explicación de Capas

### app/ — Capa Geoespacial

Contiene toda la lógica de análisis satelital. Es la capa que interactúa con Google Earth Engine.

#### app/api/routes

Endpoints HTTP del sistema. Reciben requests, validan entrada y delegan a services.

Endpoints actuales:

```text
POST /rainfall/check
POST /analysis/twi
POST /analysis/flood
POST /analysis/flood/debug
POST /analysis/ndvi
```

#### app/core

Infraestructura global del backend.

- `earth_engine.py` — inicializa y mantiene la sesión con Google Earth Engine
- `logger.py` — configuración centralizada de logs

#### app/providers

Capa de acceso a datasets satelitales. Abstrae Earth Engine para que los services no dependan del dataset específico.

- `chirps_provider.py` — CHIRPS Daily (precipitación)
- `dem_provider.py` — USGS SRTM GL1 003 (topografía)
- `sentinel1_provider.py` — Copernicus S1 GRD (SAR, detección de inundación)

#### app/schemas

Modelos Pydantic para validación de requests y responses.

#### app/services

Lógica de negocio geoespacial y procesamiento satelital.

- `rainfall_service.py` — lluvia acumulada, serie diaria, estadísticas espaciales CHIRPS
- `twi_service.py` — TWI desde DEM SRTM para detección de zonas vulnerables
- `flood_service.py` — detección de anegamiento con Sentinel-1 SAR (pre vs post evento)
- `flood_debug_service.py` — diagnóstico de cobertura de escenas Sentinel-1
- `ndvi_service.py` — NDVI desde Sentinel-2, clasificación vegetativa

---

### src/ — Capa de Dominio y Persistencia

Contiene los modelos de negocio, repositorios de base de datos y la integración con la blockchain.

#### src/database.py

Configuración de SQLAlchemy con PostgreSQL/PostGIS. Expone `session_scope()` como context manager para gestión de transacciones.

#### src/models/

Modelos SQLAlchemy que representan las entidades del dominio.

| Modelo            | Descripción                                                         |
| ----------------- | ------------------------------------------------------------------- |
| `User`            | Agricultor con smart account ERC-4337. No necesita entender crypto. |
| `Field`           | Parcela agrícola con geometría PostGIS y `polygon_hash` anti-fraude |
| `Policy`          | Póliza paramétrica materializada como NFT ERC-721 en Avalanche      |
| `PolicyPayout`    | Tramo de pago escalonado (leve 25% / moderado 50% / severo 75%)     |
| `LiquidityPool`   | Pool de capital USDC que respalda las pólizas on-chain              |
| `ParametricEvent` | Evento climático detectado por el motor, firmado por el oráculo     |

#### src/repositories/

Capa de acceso a datos. Cada módulo expone funciones puras que reciben una `Session` y operan sobre un único modelo. La gestión de transacciones queda en manos del caller.

#### src/services/

Lógica de negocio de dominio: creación de usuarios, pólizas, eventos paramétricos, gestión de pools.

#### src/services/blockchain/

Integración con Avalanche Fuji.

- `client.py` — singleton Web3, firma y difusión de transacciones
- `events.py` — listener de eventos on-chain (polling de bloques en thread daemon)
- `engine_contracts.py` — wrappers de `ParaSolPolicy.sol` y `ParaSolEngine.sol`
- `pool_contract.py` — wrapper de `ParaSolPool.sol`

---

## Sincronización On-Chain

El backend implementa un sistema de **event listening** para sincronizar la base de datos con el estado real del smart contract.

### Flujo

```text
Smart Contract deployado
        ↓
emite Transfer(from=0x0, tokenId, holder)   ← mint de la póliza NFT
        ↓
backend escucha con web3.py (polling cada 3s)
        ↓
policyService.on_policy_minted()
        ↓
llena nft_token_id + mint_tx_hash + block_number en DB
policy.status → ACTIVE
```

### Activación

El listener se activa automáticamente al startup si `POLICY_CONTRACT_ADDRESS` está configurado en el entorno. Si no está configurado (contrato aún no deployado), el backend funciona normalmente sin el listener.

```python
# app/main.py
@app.on_event("startup")
def startup_event():
    init_ee()
    if os.getenv("POLICY_CONTRACT_ADDRESS"):
        start_blockchain_listeners()
```

Esto permite desarrollar y testear el backend sin depender del contrato deployado.

---

## Campos On-Chain y Ciclo de Vida

Los campos on-chain de `Policy` y `PolicyPayout` comienzan en `NULL` y se llenan a medida que avanza el ciclo de vida. El `status` siempre indica en qué etapa está cada objeto.

### Policy

```text
QUOTED → PENDING_PAYMENT → ACTIVE → PARTIAL_PAID → SETTLED
                                  ↘ UNDER_REVIEW ↗
```

| Campo                 | Cuándo se llena                          |
| --------------------- | ---------------------------------------- |
| `nft_contract_address`| al configurar `POLICY_CONTRACT_ADDRESS`  |
| `nft_token_id`        | al confirmar el mint on-chain            |
| `mint_tx_hash`        | al confirmar el mint on-chain            |
| `activated_at`        | junto con el mint                        |

### PolicyPayout

```text
PENDING → SUBMITTED → CONFIRMED
```

| Campo          | Cuándo se llena                          |
| -------------- | ---------------------------------------- |
| `tx_hash`      | al enviar la tx al smart contract        |
| `block_number` | al confirmar la tx on-chain              |
| `submitted_at` | al llamar `mark_submitted()`             |
| `paid_at`      | al confirmar la tx on-chain              |

---

## Endpoints Satelitales

### POST /rainfall/check

Calcula lluvia acumulada y serie diaria sobre un polígono.

**Request:**
```json
{
  "coordinates": [[[-60.326698, -38.198767], [-60.306698, -38.198767],
                   [-60.306698, -38.178767], [-60.326698, -38.178767],
                   [-60.326698, -38.198767]]],
  "start_date": "2024-01-01",
  "end_date": "2024-12-31"
}
```

**Response:**
```json
{
  "total_rainfall_mm": 765.86,
  "max_observed_mm": 44.66,
  "unit": "mm",
  "dataset": "UCSB-CHG/CHIRPS/DAILY",
  "native_scale_meters": 5565.97,
  "low_confidence": false,
  "confidence_reasons": [],
  "period": { "start": "2024-01-01", "end": "2024-12-31" },
  "series": [
    { "date": "2024-01-01", "mean_mm": 2.3, "max_mm": 3.1,
      "min_mm": 1.8, "p95_mm": 3.0, "effective_pixels": 4 }
  ]
}
```

**Métricas:**

| Campo               | Qué representa                          |
| ------------------- | --------------------------------------- |
| `total_rainfall_mm` | lluvia acumulada del período            |
| `max_observed_mm`   | máximo extremo detectado                |
| `effective_pixels`  | píxeles CHIRPS utilizados               |
| `low_confidence`    | baja robustez estadística (poco cob.) |
| `native_scale_meters` | resolución real del dataset           |

---

### POST /analysis/twi

Calcula el Topographic Wetness Index sobre un polígono desde el DEM SRTM 30m.

**Request:**
```json
{
  "polygon": {
    "coordinates": [[[-60.326698, -38.198767], [-60.306698, -38.198767],
                     [-60.306698, -38.178767], [-60.326698, -38.178767],
                     [-60.326698, -38.198767]]]
  }
}
```

**Response:**
```json
{
  "status": "ok",
  "message": "TWI calculado",
  "data": { "avg_twi": 8.89, "max_twi": 11.95 }
}
```

**Interpretación:**

| TWI    | Interpretación               |
| ------ | ---------------------------- |
| < 6    | zona alta, drena bien        |
| 6 - 9  | zona intermedia              |
| > 9    | zona baja, acumula agua      |
| > 11   | muy vulnerable a anegamiento |

---

### POST /analysis/flood

Detección de anegamiento real con **Sentinel-1 SAR**. El radar atraviesa nubes y funciona de noche. Compara backscatter VV pre vs post sobre el mismo polígono y mismo track orbital.

**Request:**
```json
{
  "polygon": { "coordinates": [[...]] },
  "pre_event":  { "start_date": "2024-01-01", "end_date": "2024-01-20" },
  "post_event": { "start_date": "2024-02-01", "end_date": "2024-02-15" },
  "orbit": "DESCENDING",
  "flood_threshold_db": -17.0,
  "min_flooded_area_pct": 5.0
}
```

`orbit`, `flood_threshold_db` y `min_flooded_area_pct` son opcionales.

**Response:**
```json
{
  "status": "ok",
  "flooded_area_pct": 23.41,
  "new_flooded_area_pct": 19.07,
  "delta_vv_db": -5.76,
  "flood_detected": true,
  "flood_days": 32,
  "scenes": [
    { "date": "2024-02-03", "new_flooded_pct": 18.42, "flooded": true }
  ]
}
```

**Interpretación del backscatter VV:**

| VV (dB)    | Superficie                        |
| ---------- | --------------------------------- |
| > -10      | suelo seco, vegetación densa      |
| -10 a -15  | suelo húmedo, cultivo             |
| -15 a -17  | transición / cultivo anegado      |
| < -17      | superficie de agua libre          |

**Por qué pre = median y post = min:**
El pre usa mediana para obtener un baseline seco robusto. El post usa min() para capturar el peak de inundación incluso en eventos cortos que drenan antes de la siguiente revisita de Sentinel-1 (~6-12 días). Es el approach estándar de UN-SPIDER para flood detection con SAR.

---

### POST /analysis/ndvi

Calcula NDVI desde Sentinel-2 con filtro de nubosidad y clasificación vegetativa.

**Response:**
```json
{
  "low_confidence": false,
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

**Interpretación NDVI:**

| NDVI      | Interpretación              |
| --------- | --------------------------- |
| < 0.2     | suelo desnudo               |
| 0.2 - 0.4 | vegetación baja             |
| 0.4 - 0.6 | cultivo moderado            |
| 0.6 - 0.8 | cultivo vigoroso            |
| > 0.8     | vegetación extremadamente densa |

---

## Pipeline de Detección de Pérdida de Cosecha

El motor paramétrico combina cuatro fuentes satelitales para validar pérdida de cultivo y reducir falsos positivos:

```text
CHIRPS      → cuánto llovió
DEM + TWI   → dónde se acumularía el agua topográficamente
Sentinel-1  → si realmente hubo inundación (SAR atraviesa nubes)
NDVI        → si el cultivo sufrió daño vegetativo
```

La coincidencia de múltiples fuentes reduce fraude, errores climáticos y payouts incorrectos.

---

## Fundamento Agronómico

Basado en literatura del INTA y AAPRESID para cultivos de la región pampeana:

| Cultivo | Días anegado | Pérdida estimada            |
| ------- | ------------ | --------------------------- |
| Soja    | < 2 días     | sin consecuencias           |
| Soja    | 3 días       | ~20% de rendimiento         |
| Soja    | 4+ días      | reducción de población + rinde |
| Soja    | 7+ días      | daño severo observable      |
| Maíz    | 2-4 días     | sin pérdida apreciable      |
| Maíz    | > 4 días     | daño según etapa fenológica |

---

## Anti-Fraude

El sistema implementa múltiples mecanismos para garantizar integridad:

- **`polygon_hash`** — SHA-256 del GeoJSON normalizado del polígono. Si la geometría se modifica después de emitida la póliza, el hash cambia y se detecta.
- **`payload_hash`** — SHA-256 determinístico de la query + fórmula + datos satelitales. El smart contract puede recomputarlo para verificar reproducibilidad: mismo polígono + período + dataset → mismo hash.
- **`terms_hash`** — SHA-256 del `trigger_snapshot` inmutable. Congela las condiciones de la póliza al momento de emisión.
- **`signature`** — firma ECDSA del oráculo sobre el `payload_hash`.
- **`basis_risk_flag`** — se activa cuando las fuentes satelitales disienten, mandando el evento a revisión manual antes de gatillar el payout.

---

## Variables de Entorno

```env
# Base de datos
DATABASE_URL=postgresql://user:password@localhost:5432/parasol_db

# Blockchain — Avalanche Fuji
AVALANCHE_FUJI_RPC=https://api.avax-test.network/ext/bc/C/rpc
PRIVATE_KEY=0x...
CHAIN_ID=43113

# Contratos (se completan al deployar)
POLICY_CONTRACT_ADDRESS=0x...
ENGINE_CONTRACT_ADDRESS=0x...
POOL_CONTRACT_ADDRESS=0x...
```

Si `POLICY_CONTRACT_ADDRESS` no está configurado, el backend inicia sin el listener on-chain. Al deployar el contrato se agrega la dirección al `.env` y se reinicia el backend.

---

## Estado Actual

Implementado:

- arquitectura modular FastAPI con separación routes / services / providers
- integración Google Earth Engine
- análisis CHIRPS (lluvia acumulada, serie diaria, estadísticas espaciales, detección de baja cobertura)
- análisis TWI desde DEM SRTM
- detección de anegamiento con Sentinel-1 SAR (pre vs post, análisis por escena)
- análisis NDVI desde Sentinel-2 con clasificación vegetativa
- logging centralizado
- modelos de dominio completos (User, Field, Policy, PolicyPayout, LiquidityPool, ParametricEvent)
- repositorios con funciones de ciclo de vida y transiciones de estado
- integración Web3.py con Avalanche Fuji
- wrappers de smart contracts (Pool, Policy, Engine)
- listener de eventos on-chain para sincronización automática de DB

---

## Próximos Pasos

### Corto plazo

- implementar `parametricService.py` con motor de evaluación de triggers
- implementar `oracleService.py` con firma ECDSA de eventos
- manejo avanzado de excepciones en endpoints
- response models tipados con Pydantic en todos los endpoints

### Mediano plazo

- motor paramétrico multi-fuente con umbrales INTA por cultivo y etapa fenológica
- scoring climático con niveles de severidad (leve / moderado / severo)
- triggers automáticos → payout on-chain
- NDVI temporal pre/post evento para confirmar daño vegetativo
- infraestructura de auditoría verificable on-chain

---

## Visión

Motor paramétrico agrícola híbrido que combina análisis satelital multi-fuente con umbrales agronómicos validados, automatización climática, blockchain Avalanche y pagos automáticos escalonados por severidad, orientado a seguros agrícolas institucionales con auditoría verificable y reducción de fraude.