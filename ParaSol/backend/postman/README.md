# Postman — ParaSol Backend

Collection lista para importar a Postman con casos de prueba reales contra los
endpoints geoespaciales del backend.

---

## Cómo importar

1. Abrir Postman → **Import** → seleccionar `ParaSol.postman_collection.json`.
2. La variable `{{baseUrl}}` viene seteada en `http://localhost:8000`. Si tu
   FastAPI corre en otro puerto, editar la variable de colección.
3. Levantar el backend:

   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

4. Asegurarse de tener Earth Engine autenticado en la máquina (Application
   Default Credentials o `earthengine authenticate`).

---

## Requests incluidos

| # | Request                                                | Endpoint                |
| - | ------------------------------------------------------ | ----------------------- |
| 1 | Health check                                           | `GET /`                 |
| 2 | Rainfall check — CHIRPS (Salado 2017)                  | `POST /rainfall/check`  |
| 3 | TWI — SRTM (Salado 2017)                               | `POST /analysis/twi`    |
| 4 | Flood detection — Sentinel-1 (Salado 2017) **PRIMARY** | `POST /analysis/flood`  |
| 5 | Flood detection — Sentinel-1 (Idai 2019) sanity check  | `POST /analysis/flood`  |
| 6 | Flood detection — orbit auto                           | `POST /analysis/flood`  |

---

## Caso primario: Inundación cuenca del Salado (2017)

Durante el verano 2016-2017 la cuenca del Salado bonaerense sufrió una crue
extraordinaria que dejó más de 1 millón de hectáreas anegadas y afectó
cosechas de soja y maíz en la zona núcleo.

**Polígono de prueba.** ~7 km × 6 km de campos rurales cerca de 25 de Mayo,
provincia de Buenos Aires. Esquinas en EPSG:4326:

```
SW: -60.20, -35.48
NE: -60.13, -35.42
```

**Ventanas temporales.**

| Ventana    | Período                  | Por qué                                                   |
| ---------- | ------------------------ | --------------------------------------------------------- |
| Pre-evento | 2016-11-15 → 2016-12-31  | Primavera seca previa, baseline de suelo "normal"         |
| Post-evento| 2017-02-15 → 2017-03-31  | Pico de la crue, después de las lluvias extremas de enero |

**Resultados esperados (orden de magnitud).**

* `pre_event.scene_count`  ≥ 3
* `post_event.scene_count` ≥ 4
* `pre_event.vv_mean_db`   ≈ −9 a −12 dB (suelo seco / cultivo)
* `post_event.vv_mean_db`  ≈ −14 a −18 dB (anegamiento parcial)
* `delta_vv_db`            negativo, ≈ −3 a −6 dB
* `new_flooded_area_pct`   varios % (depende del recorte exacto)

Si `new_flooded_area_pct` > 0 con `delta_vv_db` claramente negativo, el
pipeline está validando correctamente el anegamiento.

---

## Sanity check: Ciclón Idai (Mozambique, 2019)

Sirve como **prueba de control**. Es el caso canónico de UN-SPIDER y Google
Earth Engine para flood detection con Sentinel-1, sobre la zona de Buzi
(Mozambique) post-ciclón Idai del 14-15 de marzo de 2019.

Si este request devuelve un `new_flooded_area_pct` significativo y el
argentino no, el problema no está en el código sino en cobertura S1 sobre
ese polígono / fechas.

---

## Interpretación rápida del backscatter VV

| VV (dB)    | Superficie                              |
| ---------- | --------------------------------------- |
| > -10      | suelo seco, vegetación densa            |
| -10 a -15  | suelo húmedo, cultivo                   |
| -15 a -17  | transición / cultivo anegado            |
| < -17      | superficie de agua libre                |

`flood_threshold_db` (default −17.0) es el umbral que separa "agua" de
"no agua". Se puede ajustar:

* terrenos muy planos / barros → bajar a −15 dB
* zonas con mucha rugosidad o vegetación post-evento → bajar a −18 dB

---

## Troubleshooting

* **`scene_count = 0` en post-evento.** Probar la otra pasada orbital
  (`ASCENDING` / `DESCENDING`) o ampliar la ventana temporal a 30-45 días.
* **Latencia alta (> 30 s).** Earth Engine procesa on-the-fly. Para
  polígonos grandes conviene reducir el área o aumentar `scale` en
  `flood_service.py`.
* **`ee.ee_exception.EEException: Not signed up for Earth Engine`.**
  Falta autenticación en la máquina. Correr `earthengine authenticate`.
