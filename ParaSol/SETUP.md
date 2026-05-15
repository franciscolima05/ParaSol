# Setup SQLAlchemy + PostgreSQL + PostGIS

## 1. Instalar PostgreSQL con PostGIS

**macOS (Homebrew):**
```bash
brew install postgresql postgis
brew services start postgresql
```

**Linux (Ubuntu):**
```bash
sudo apt install postgresql postgresql-contrib postgis
sudo systemctl start postgresql
```

## 2. Crear base de datos y extensión PostGIS

```bash
createdb parasol_db
psql parasol_db -c "CREATE EXTENSION postgis;"
```

## 3. Instalar dependencias Python

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
pip install -r requirements.txt
```

## 4. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con credenciales reales
```

## 5. Inicializar base de datos

```bash
python example_usage.py
```

## Estructura de archivos

```
ParaSol/
├── database.py           # Configuración de SQLAlchemy + engine
├── models.py             # Definición de modelos (SatelliteImage, SensorData)
├── example_usage.py      # Ejemplos de CRUD
├── requirements.txt      # Dependencias
└── .env.example          # Variables de entorno
```

## Comandos útiles

```bash
# Ver todas las tablas
psql parasol_db -c "\dt"

# Ver tabla de imágenes
psql parasol_db -c "SELECT id, name, source FROM satellite_images;"

# Query geoespacial (imágenes con menos del 10% nubosidad)
psql parasol_db -c "SELECT name, cloud_cover FROM satellite_images WHERE cloud_cover < 10;"
```

## Migrations (Alembic)

```bash
# Inicializar alembic
alembic init alembic

# Crear migración automática
alembic revision --autogenerate -m "Initial schema"

# Aplicar migraciones
alembic upgrade head
```
