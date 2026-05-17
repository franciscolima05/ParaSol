# ParaSol — Technical Integration README

> **Audiencia:** Equipo de desarrollo (Manu, Gonza, Joaco, Pancho)  
> **Objetivo:** Mapa técnico de qué está hardcodeado, qué falta conectar y qué hacer primero.  
> **Basado en:** código real de `frontend/`, `backend/`, `contracts/` — sin inventar features.

---

## 1. Overview del sistema

ParaSol es un protocolo de seguros paramétricos agrícolas compuesto por tres capas:

```
[AGRICULTOR / ASEGURADORA]
         ↓
   [FRONTEND — HTML + Vanilla JS]
         ↓
   [BACKEND — FastAPI + GEE]     ←→   [BLOCKCHAIN — Avalanche Fuji]
         ↓
   [PostgreSQL / PostGIS]
```

El frontend tiene **tres vistas para el agricultor** (`campo/`, `poliza/`, `historial/`) y **una vista para la aseguradora** (`aseguradora/`), más la **pitch page** (`spich/`).

El backend expone **5 endpoints satelitales reales** y tiene una **capa de dominio completa** (modelos, repositorios) que todavía no está conectada al frontend.

Los contratos están **deployados en Fuji Testnet** (`ParaSolPolicy`, `ParaSolPool`, `ParaSolEngine`) y el frontend los lee en modo read-only vía RPC público.

---

## 2. Arquitectura actual — cómo funciona hoy

### 2.1 Frontend `campo/` (dashboard del agricultor)

**Lo que funciona de verdad:**
- El usuario dibuja un polígono en Leaflet → se genera un GeoJSON.
- Se llama en paralelo a los 4 endpoints reales del backend: `/rainfall/check`, `/analysis/twi`, `/analysis/flood`, `/analysis/ndvi`.
- Las métricas se renderizan en las tarjetas satélitales.

**Lo que está hardcodeado:**
- El estado inicial del header: `ESTADO_CAMPO: MONITOREO_ACTIVO` y `COBERTURA: ACTIVA (100%)` son strings fijos.
- El `ID_LOTE: PAMPA_CORE_772` es un string hardcodeado en el HTML.
- La lógica de "comparativa histórica" en `updateProducerUI()` usa bases ficticias: `total_rainfall_mm / 600` y `ndvi_median / 0.5`. No existe ningún endpoint de históricos en el backend.
- La barra de progreso de póliza y el umbral del 15% de anegamiento están hardcodeados en el JS del frontend — no vienen del contrato.

### 2.2 Frontend `poliza/` (póliza NFT del agricultor)

**Completamente hardcodeado.** El `main.js` define un objeto `policy` con todos los datos del NFT (fieldHash, poolId, coverageUSDC, premiumUSDC, fechas, payoutPct) y un objeto `pool` con los datos del fondo, directamente en el JS. No hay ninguna llamada al contrato ni al backend.

```js
// poliza/main.js — todo esto es hardcoded
const policy = {
  fieldHash: "0x772a...",
  coverageUSDC: 5000000000,
  premiumUSDC: 450000000,
  payoutPct: 40
};
```

La guía de contratos (`contracts/README.md`) ya documenta exactamente cómo leer estos datos con `viem` usando `getPolicyDetails(tokenId)` y `percentagePaidOut(policyId)`. La conexión no está implementada.

### 2.3 Frontend `historial/`

**Completamente hardcodeado.** El array `MOCK_HISTORY` en `main.js` tiene dos registros fijos. La función `reloadAnalysis(id)` solo hace un `console.log`. No hay persistencia ni llamada a ningún endpoint.

### 2.4 Frontend `aseguradora/`

**Completamente hardcodeado.** Todos los KPIs (capital total, pólizas activas, superficie, payouts, distribución de riesgo, actividad on-chain) son valores fijos en el HTML. No existe ningún endpoint en el backend que agregue estos datos.

### 2.5 Backend

**Los 5 endpoints satelitales funcionan y están deployados en Render:**

| Endpoint | Estado | Dataset |
|---|---|---|
| `POST /rainfall/check` | ✅ Funciona | CHIRPS Daily |
| `POST /analysis/twi` | ✅ Funciona | USGS SRTM GL1 003 |
| `POST /analysis/flood` | ✅ Funciona | Sentinel-1 GRD |
| `POST /analysis/flood/debug` | ✅ Funciona | Sentinel-1 GRD |
| `POST /analysis/ndvi` | ✅ Funciona | Sentinel-2 SR |

**La capa de dominio existe pero no está conectada a ningún endpoint HTTP:**

Los modelos (`User`, `Field`, `Policy`, `PolicyPayout`, `LiquidityPool`, `ParametricEvent`), repositorios y la base de datos PostgreSQL/PostGIS están implementados pero no expuestos. Los archivos de servicios de dominio (`policyService.py`, `userService.py`, `poolService.py`, `parametricService.py`, `oracleService.py`) están **completamente vacíos**.

**El listener on-chain existe** (`src/listener.py`, `src/services/blockchain/`) pero no está integrado en el `app/main.py` de producción.

### 2.6 Contratos

Tres contratos deployados en Fuji Testnet:

- `ParaSolPolicy.sol` (ERC-721): mint de pólizas NFT, `getPolicyDetails()`.
- `ParaSolPool.sol`: gestión de capital USDC, `pools()`, `getAvailableCapital()`, `nextPoolId()`.
- `ParaSolEngine.sol`: oráculo + payout escalonado, `processParametricEvent()`, `percentagePaidOut()`.

Solo `POLICY_CONTRACT_ADDRESS` tiene dirección configurada. `POOL_CONTRACT_ADDRESS` y `ENGINE_CONTRACT_ADDRESS` están vacías en el README de contratos.

---

## 3. Problemas detectados

### 3.1 Frontend hardcodeado

| Archivo | Qué está hardcodeado | Reemplazo correcto |
|---|---|---|
| `campo/map.js` | Base histórica 600mm y NDVI 0.5 | Endpoint `/analysis/historical-baseline` (no existe) |
| `campo/map.js` | Umbral póliza 15% | `getPolicyDetails(tokenId).triggerSnapshotHash` → leer del contrato |
| `poliza/main.js` | Todos los datos de póliza y pool | `getPolicyDetails()` + `pools()` + `percentagePaidOut()` vía viem |
| `historial/main.js` | Array `MOCK_HISTORY` | Endpoint `GET /policies/{holderId}/events` (no existe) |
| `aseguradora/index.html` | Todos los KPIs de la aseguradora | Endpoints de agregación (no existen) |
| `campo/index.html` | `ID_LOTE: PAMPA_CORE_772` | Parámetro de sesión / URL |

### 3.2 Datos duplicados o inconsistentes

- El umbral de pago del 15% de anegamiento aparece hardcodeado en `campo/map.js` **y** en el HTML de `campo/index.html`, pero la fuente de verdad debería ser el `triggerSnapshotHash` del contrato.
- El `payoutPct: 40` en `poliza/main.js` contradice el `percentagePaidOut(policyId)` del `ParaSolEngine.sol`. Si el contrato dice otra cosa, la UI muestra datos incorrectos.
- Los datos del pool en `poliza/main.js` (`total_capital: 250000000000`, `locked: 84200000000`) no coinciden con los datos del `aseguradora/index.html` (que muestra 250,000 USDC disponibles pero calcula locked=137,700). La fuente única debería ser `pools(poolId)` del contrato.

### 3.3 Falta de integración backend ↔ frontend

El backend tiene una capa de dominio completa (6 modelos, 6 repositorios) que el frontend nunca consulta. No existen endpoints REST que expongan:
- Lista de pólizas por agricultor
- Estado de un evento paramétrico
- Historial de análisis satelitales por campo
- Métricas agregadas para la aseguradora

### 3.4 Falta de integración blockchain ↔ frontend

La guía en `contracts/README.md` documenta cómo usar `viem` para leer contratos, pero ninguna página del frontend implementa esa lectura. El frontend usa datos mock que deberían venir de:
- `ParaSolPolicy.getPolicyDetails(tokenId)` → datos de cobertura, fechas, fieldHash
- `ParaSolEngine.percentagePaidOut(policyId)` → tramo pagado real
- `ParaSolPool.pools(poolId)` → capital total, locked, paid_out
- Eventos `PolicyMinted`, `PayoutTriggered` → historial de actividad on-chain

### 3.5 Servicios de dominio vacíos

Los siguientes archivos existen pero están completamente vacíos:

```
src/services/policyService.py      ← vacío
src/services/userService.py        ← vacío
src/services/poolService.py        ← vacío
src/services/parametricService.py  ← vacío
src/services/oracleService.py      ← vacío
src/services/fieldService.py       ← vacío
```

Esto significa que aunque los repositorios están implementados, no hay ningún flujo de negocio orquestado: no se puede crear una póliza, registrar un evento paramétrico ni gatillar un payout desde el backend.

---

## 4. Flujo de datos ideal — target architecture

```
AGRICULTOR dibuja polígono en Leaflet
        ↓
Frontend envía GeoJSON + fechas
        ↓
Backend /analysis/* (GEE) → devuelve métricas satelitales
        ↓
Frontend muestra métricas + evalúa si umbral se cumple
        ↓ (si flood_detected && flooded_area_pct >= threshold)
Backend parametricService → crea ParametricEvent en DB
        ↓
Backend oracleService → firma ECDSA del payload_hash
        ↓
Backend blockchain/client.py → llama ParaSolEngine.processParametricEvent()
        ↓
Contrato verifica póliza activa + calcula tramo de payout
        ↓
Contrato emite PayoutTriggered → transfiere USDC al wallet del agricultor
        ↓
Backend events.py escucha PayoutTriggered → actualiza Policy.status en DB
        ↓
Frontend consulta GET /policies/{id} → muestra estado real
```

**Flujo de lectura de póliza:**

```
Frontend carga poliza/index.html con ?tokenId=1042
        ↓
viem.readContract(getPolicyDetails(1042))     → cobertura, fechas, fieldHash
viem.readContract(percentagePaidOut(1042))    → tramo pagado real
viem.readContract(pools(poolId))              → estado del fondo
        ↓
Frontend renderiza datos reales (no mock)
```

---

## 5. Tabla de endpoints faltantes o incompletos

### 5.1 Endpoints que existen y funcionan

| Método | Ruta | Estado |
|---|---|---|
| POST | `/rainfall/check` | ✅ Funciona |
| POST | `/analysis/twi` | ✅ Funciona |
| POST | `/analysis/flood` | ✅ Funciona |
| POST | `/analysis/flood/debug` | ✅ Funciona |
| POST | `/analysis/ndvi` | ✅ Funciona |

### 5.2 Endpoints que deben crearse (prioridad alta)

| Método | Ruta sugerida | Para quién | Datos fuente |
|---|---|---|---|
| GET | `/policies/{holder_address}` | Agricultor | DB + contrato |
| GET | `/policies/{token_id}/detail` | Agricultor | Contrato (viem) |
| GET | `/policies/{token_id}/events` | Historial | DB (parametric_events) |
| GET | `/pools/{pool_id}` | Aseguradora | Contrato (viem) |
| GET | `/insurer/dashboard` | Aseguradora | DB aggregate |
| POST | `/parametric/evaluate` | Interno | Backend → Engine.sol |

### 5.3 Endpoints que deben crearse (prioridad media)

| Método | Ruta sugerida | Para quién | Datos fuente |
|---|---|---|---|
| GET | `/analysis/historical-baseline` | Campo | DB o GEE histórico |
| GET | `/fields/{field_id}` | Campo | DB |
| POST | `/fields` | Registro de campo | DB |
| POST | `/policies` | Contratación | DB + contrato |

---

## 6. Estado de integración por módulo

### 6.1 Frontend

| Vista | Datos satelitales | Datos blockchain | Datos de DB | Estado global |
|---|---|---|---|---|
| `campo/` | ✅ Conectado (GEE real) | ❌ Sin integración | ❌ Sin integración | 🟡 Parcial |
| `poliza/` | — | ❌ Hardcodeado | ❌ Sin integración | 🔴 Mock total |
| `historial/` | — | ❌ Sin integración | ❌ Sin integración | 🔴 Mock total |
| `aseguradora/` | — | ❌ Sin integración | ❌ Sin integración | 🔴 Mock total |
| `spich/` | — | — | — | ✅ Solo presentación |

### 6.2 Backend

| Capa | Estado |
|---|---|
| Endpoints GEE (análisis satelital) | ✅ Implementados y deployados |
| Modelos de dominio (SQLAlchemy) | ✅ Implementados |
| Repositorios | ✅ Implementados |
| Servicios de dominio | ❌ Vacíos (archivos sin código) |
| Endpoints REST de dominio | ❌ No existen |
| Listener on-chain (events.py) | 🟡 Implementado, no integrado en main.py de prod |
| Wrappers de contratos (Web3.py) | 🟡 Implementados, sin flujo activo |
| oracleService (firma ECDSA) | ❌ Vacío |
| parametricService (evaluación de triggers) | ❌ Vacío |

### 6.3 Contratos

| Contrato | Deploy Fuji | Dirección configurada | Integración backend |
|---|---|---|---|
| `ParaSolPolicy.sol` | ✅ | ✅ `0xe7f172...` | 🟡 Listener parcial |
| `ParaSolPool.sol` | ✅ (pendiente confirmar) | ❌ Vacía en README | ❌ No integrado |
| `ParaSolEngine.sol` | ✅ (pendiente confirmar) | ❌ Vacía en README | ❌ No integrado |

---

## 7. Backlog técnico — tareas accionables

Las tareas están ordenadas por dependencia: cada bloque desbloquea el siguiente.

### Bloque A — Blockchain → Frontend (no requiere backend nuevo)

1. **`poliza/main.js`**: Reemplazar el objeto `policy` hardcodeado por llamadas `viem.readContract(getPolicyDetails(tokenId))` y `viem.readContract(percentagePaidOut(policyId))`.
2. **`poliza/main.js`**: Reemplazar el objeto `pool` por `viem.readContract(pools(poolId))`.
3. **`campo/map.js`**: Leer el umbral de pago (15%) del `trigger_snapshot` de la póliza activa del usuario, no del JS hardcodeado.
4. **`aseguradora/index.html`**: Leer datos on-chain de los pools con `nextPoolId()` + `pools(i)` para calcular capital total, locked, paid_out reales.

### Bloque B — Servicios de dominio del backend

5. **`policyService.py`**: Implementar `create_policy()`, `get_policy_by_holder()`, `on_policy_minted()` (callback del listener).
6. **`parametricService.py`**: Implementar `evaluate_field(field_id, analysis_results)` — decide si se crea un `ParametricEvent` basándose en los resultados de GEE.
7. **`oracleService.py`**: Implementar `sign_event(event_id)` — firma ECDSA del `payload_hash` con la clave privada del oráculo.
8. **`poolService.py`**: Implementar `get_pool_status(pool_id)` leyendo del contrato vía Web3.py.

### Bloque C — Nuevos endpoints REST

9. **`GET /policies/{token_id}/detail`**: Llama a `getPolicyDetails()` on-chain + `percentagePaidOut()` y devuelve JSON al frontend.
10. **`GET /policies/{holder_address}`**: Consulta DB para listar pólizas del agricultor.
11. **`GET /policies/{token_id}/events`**: Lista `ParametricEvent` de la DB para el historial.
12. **`GET /insurer/dashboard`**: Agrega datos de todos los pools + pólizas para la vista de aseguradora.

### Bloque D — Integración del listener on-chain

13. **`app/main.py`**: Agregar `POLICY_CONTRACT_ADDRESS`, `ENGINE_CONTRACT_ADDRESS` y `POOL_CONTRACT_ADDRESS` al `.env` de producción.
14. **`app/main.py`**: Activar `start_blockchain_listeners()` en `startup_event()` una vez configuradas las direcciones.
15. **`events.py`**: Agregar listener para el evento `PayoutTriggered` del Engine además del `Transfer` de Policy.

### Bloque E — Frontend historial (requiere C completado)

16. **`historial/main.js`**: Reemplazar `MOCK_HISTORY` por llamada a `GET /policies/{holder_address}/events`.
17. **`historial/main.js`**: Implementar `reloadAnalysis(id)` para relanzar el análisis GEE de un evento histórico.

---

## 8. Riesgos actuales

### 8.1 Inconsistencia de datos crítica

Los datos del pool son inconsistentes entre `poliza/main.js` y `aseguradora/index.html`. Hasta que ambas vistas lean del contrato, mostrarán números distintos para la misma póliza. **Riesgo de confusión durante la demo.**

### 8.2 Direcciones de contratos incompletas

`POOL_CONTRACT_ADDRESS` y `ENGINE_CONTRACT_ADDRESS` están vacías en el README de contratos. Si el Engine no tiene dirección configurada, el backend no puede ejecutar payouts on-chain. **Pendiente de confirmar con Gonza.**

### 8.3 Servicios de dominio vacíos bloquean el flujo completo

El pipeline `análisis GEE → ParametricEvent → firma ECDSA → payout on-chain` no puede ejecutarse porque `parametricService.py` y `oracleService.py` están vacíos. El backend puede detectar inundaciones pero no puede gatillar pagos automáticamente.

### 8.4 Latencia de GEE en demo en vivo

Los endpoints de GEE pueden tardar 15-45 segundos en responder. En una demo en vivo sin precarga, el jurado ve una pantalla de carga por ese tiempo. **Recomendación: preparar un polígono pre-analizado con resultados ya cacheados.**

### 8.5 Clave privada del oráculo en `.env`

`oracleService.py` deberá usar `PRIVATE_KEY` del `.env` para firmar eventos. En el estado actual esta clave no está siendo usada por ningún servicio activo, pero cuando se implemente hay que asegurar que nunca se exponga en logs ni en respuestas HTTP.

### 8.6 `policyPayoutRepository.py` duplica `parametricEventRepository.py`

El contenido de `src/repositories/policyPayoutRepository.py` es idéntico al de `parametricEventRepository.py` — parece un copy-paste incompleto. El repositorio real de `PolicyPayout` (con sus transiciones PENDING → SUBMITTED → CONFIRMED) no está implementado.

---

## 9. Próximos pasos recomendados

**Para el hackathon (impacto inmediato en la demo):**

1. Conectar `poliza/main.js` al contrato vía viem — reemplaza el mock más visible con datos reales en ~2 horas de trabajo.
2. Configurar `POOL_CONTRACT_ADDRESS` y `ENGINE_CONTRACT_ADDRESS` en el backend y confirmar que los tres contratos están deployados y verificados.
3. Preparar un polígono de demo pre-analizado para evitar latencia de GEE en vivo.

**Para la arquitectura completa (post-hackathon):**

4. Implementar `parametricService.py` como orquestador central que conecta GEE → DB → oráculo → contrato.
5. Crear los endpoints REST de dominio (Bloque C) para eliminar todos los mocks del frontend.
6. Corregir `policyPayoutRepository.py` que está duplicado con código incorrecto.
7. Activar el listener on-chain en producción una vez configuradas todas las direcciones de contratos.

---

*Generado a partir del código fuente real del repositorio. Las secciones marcadas como "pendiente de confirmar" requieren verificación directa con el responsable del componente.*