# =============================================================================
# ARCHIVO: db.py
# PROPÓSITO: Configurar y proveer la conexión a la base de datos.
#
# ¿POR QUÉ EXISTE ESTE ARCHIVO?
#   Separa toda la lógica de conexión del resto del código.
#   Aquí se crea el "engine" (motor de BD), se crean las tablas al inicio
#   y se provee la sesión a los endpoints mediante inyección de dependencias.
#
# FLUJO:
#   1. Carga las variables de entorno desde .env
#   2. Crea el engine con la URL de la BD (Neon/PostgreSQL por defecto)
#   3. create_all_tables() se ejecuta al iniciar FastAPI (lifespan)
#   4. get_session() provee una sesión por cada request HTTP
#   5. SessionDep es un alias tipado para inyectar la sesión en los endpoints
#
# ¿CÓMO ADAPTARLO A OTRO PROYECTO?
#   - Para SQLite local: cambia engine = create_engine(sqlite_url)
#   - Para otro proveedor: pon la URL en el .env bajo DATABASE_URL
#   - Si cambias los modelos, create_all_tables creará las nuevas tablas solas.
# =============================================================================

import os

from sqlmodel import Session, create_engine, SQLModel   # SQLModel: ORM + validación
from typing import Annotated                             # para el alias SessionDep
from fastapi import Depends, FastAPI                     # Depends: inyección de dependencias
from dotenv import load_dotenv                           # carga el archivo .env

# ─── Carga de variables de entorno ───────────────────────────────────────────
# load_dotenv() lee el archivo .env en la raíz del proyecto.
# Las variables quedan disponibles como os.getenv("NOMBRE").
# NUNCA pongas credenciales directamente en el código → úsalas solo desde .env
load_dotenv()

# ─── URL de la base de datos ─────────────────────────────────────────────────
# Se obtiene desde el archivo .env. Ejemplo de .env:
#   DATABASE_URL=postgresql+psycopg2://usuario:contraseña@host/nombre_bd
neon_url_db = os.getenv("DATABASE_URL")

# Alternativa local SQLite (útil para desarrollo sin base de datos externa):
sqlite_name = "pokemondb.sqlite3"          # nombre del archivo SQLite local
sqlite_url  = f"sqlite:///{sqlite_name}"   # URL de conexión SQLite

# ─── Motor de base de datos (engine) ─────────────────────────────────────────
# El engine es el objeto principal de SQLAlchemy/SQLModel que gestiona el pool
# de conexiones. Se crea UNA SOLA VEZ al cargar el módulo.
# Para usar SQLite en lugar de Neon: engine = create_engine(sqlite_url)
engine = create_engine(neon_url_db)


# ─── Lifespan: crear tablas al arrancar el servidor ──────────────────────────
# Esta función se pasa a FastAPI(lifespan=...) en main.py.
# Se ejecuta UNA SOLA VEZ cuando el servidor inicia.
# SQLModel.metadata.create_all() revisa todos los modelos con table=True
# y crea las tablas en la BD si no existen. Si ya existen, no las toca.
def create_all_tables(app: FastAPI):
    SQLModel.metadata.create_all(engine)   # crea tablas si no existen
    yield                                  # el servidor queda en "pausa" aquí; al apagar continúa


# ─── Proveedor de sesiones (get_session) ─────────────────────────────────────
# Generador que crea UNA sesión por cada request HTTP y la cierra al finalizar.
# El bloque "with Session(engine) as session" garantiza que la sesión
# se cierre aunque ocurra una excepción (manejo seguro de recursos).
def get_session():
    with Session(engine) as session:
        yield session   # FastAPI inyecta este objeto en los endpoints


# ─── Dependencia tipada (SessionDep) ─────────────────────────────────────────
# Alias que combina el tipo Session con la dependencia Depends(get_session).
# Se usa en los parámetros de los endpoints así:
#   async def mi_endpoint(session: SessionDep):
# FastAPI inyecta automáticamente la sesión correcta en cada llamada.
SessionDep = Annotated[Session, Depends(get_session)]
