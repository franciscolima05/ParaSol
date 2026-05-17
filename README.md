# Relatório de Análisis del Repositorio ParaSol

## 1. Introducción

Este informe presenta un análisis detallado del repositorio de GitHub `ParaSol`[](https://github.com/franciscolima05/ParaSol), un proyecto enfocado en infraestructura para seguros agrícolas. El objetivo es comprender la arquitectura, las tecnologías empleadas y la funcionalidad general del sistema.

## 2. Visión General del Proyecto

ParaSol es un proyecto desarrollado para el Hackathon Avalanche LATAM, con el propósito de crear una infraestructura para seguros agrícolas paramétricos. Utiliza datos geoespaciales y satelitales para detectar eventos climáticos que pueden activar automáticamente los seguros. El proyecto está compuesto por tres componentes principales: contratos inteligentes (smart contracts), un backend geoespacial y un frontend (dApp).

## 3. Análisis Técnico

### 3.1. Smart Contracts (Solidity + Foundry)

La sección de contratos inteligentes (`contracts/`) está implementada en **Solidity** y utiliza la herramienta **Foundry** para desarrollo, pruebas y despliegue. La estructura incluye:

*   `contracts/src/core/ParaSolPool.sol`: Este es el contrato principal, `ParaSolPool`, que gestiona los pools de capital para los seguros. Permite la creación de pools, el financiamiento de los mismos con tokens USDC, el bloqueo de capital y la ejecución de pagos. El contrato es `Ownable`, lo que significa que posee un propietario que puede definir el contrato `engine` responsable de ejecutar los pagos. Las funcionalidades principales incluyen:
    *   `createPool`: Crea un nuevo pool de seguros con un nombre específico.
    *   `fundPool`: Permite que los usuarios depositen USDC en un pool.
    *   `lockCapital`: Bloquea una cantidad de capital en un pool, generalmente para cubrir un seguro.
    *   `executePayout`: Realiza el pago de un seguro a un agricultor, deduciendo el valor del capital bloqueado y total del pool. Esta función solo puede ser llamada por el contrato `engine`.
    *   `getAvailableCapital`: Retorna el capital disponible en un pool (total - bloqueado).

### 3.2. Backend (Python + FastAPI + PostgreSQL/PostGIS)

El backend (`backend/`) es un servicio geoespacial desarrollado en **Python** utilizando el framework **FastAPI**. Es responsable de procesar información geoespacial y satelital para detectar eventos climáticos. Las principales características y tecnologías incluyen:

*   **Objetivo**: Procesar datos geoespaciales y satelitales para detectar eventos climáticos que activan seguros paramétricos automáticos.
*   **Funcionalidades Actuales**:
    *   Recibir polígonos geográficos.
    *   Consultar datasets satelitales de Google Earth Engine.
    *   Calcular lluvia acumulada y serie diaria de precipitación.
    *   Calcular TWI (Topographic Wetness Index) para detectar zonas vulnerables a inundaciones.
    *   Obtener estadísticas climáticas sobre una región.
    *   Exponer endpoints HTTP vía FastAPI.
*   **Arquitectura**: Cliente → FastAPI API → Services Layer → Providers Layer → Google Earth Engine → CHIRPS Dataset / SRTM DEM.
*   **Stack Tecnológico**:
    *   API: FastAPI
    *   Geoprocesamiento: Google Earth Engine
    *   Lenguaje: Python 3.14
    *   Validación de datos: Pydantic
    *   Logging: `logging` estándar de Python
    *   Datasets: CHIRPS Daily (climático), USGS SRTM GL1 003 (topográfico).
*   **Estructura de Carpetas**:
    *   `app/api/routes`: Define los endpoints HTTP (ej. `/rainfall/check`, `/analysis/twi`).
    *   `app/core`: Contiene infraestructura global, como la inicialización de Google Earth Engine y configuración de logs.
    *   `app/providers`: Capa de acceso a fuentes externas de datos (ej. `chirps_provider.py`, `dem_provider.py`).
    *   `app/schemas`: Modelos de datos para validación (ej. `rainfall.py`).
    *   `app/services`: Lógica de negocio (ej. `rainfall_service.py`, `twi_service.py`).
    *   `database.py`: Configuración de SQLAlchemy + engine para PostgreSQL/PostGIS.
    *   `models.py`: Definición de modelos de datos (ej. `SatelliteImage`, `SensorData`).
    *   `example_usage.py`: Ejemplos de operaciones CRUD.
    *   `requirements.txt`: Lista de dependencias Python.
    *   `.env.example`: Ejemplo de variables de entorno.


## 4. Conclusión

El proyecto ParaSol presenta una solución robusta y bien estructurada para seguros agrícolas paramétricos, integrando tecnologías de blockchain (Avalanche, Solidity), procesamiento geoespacial (Python, FastAPI, Google Earth Engine) y una interfaz de usuario moderna (Next.js, TypeScript). La modularidad de la arquitectura, con una clara separación entre contratos, backend y frontend, facilita el desarrollo y el mantenimiento. El uso de herramientas como Foundry para smart contracts y FastAPI para el backend demuestra una elección de tecnologías eficientes y escalables. El enfoque en datos geoespaciales para activar seguros es una aplicación innovadora de la tecnología blockchain en el sector agrícola.

## Demostración de Backend y Blockchain

[![Demo ParaSol](https://img.youtube.com/vi/TU_VIDEO_ID/maxresdefault.jpg)](https://www.youtube.com/watch?v=ly-qBHOm1_U)
