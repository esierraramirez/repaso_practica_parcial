# =============================================================================
# ARCHIVO: model.py
# PROPÓSITO: Define los modelos de datos (esquemas) del proyecto.
#
# ¿POR QUÉ EXISTE ESTE ARCHIVO?
#   Aquí viven las "formas" de los datos: qué campos tiene cada entidad,
#   qué tipo es cada campo y qué reglas de validación aplican.
#   SQLModel une Pydantic (validación) + SQLAlchemy (base de datos) en una
#   sola clase, por eso con el mismo modelo validamos el JSON de entrada
#   Y mapeamos la tabla en la base de datos.
#
# JERARQUÍA DE CLASES (patrón recomendado con SQLModel):
#
#   PokemonBase          ← Campos comunes, SIN id, SIN table=True
#       └── PokemonID    ← Agrega el id; con table=True crea la tabla en BD
#       └── PokemonUpdate← Solo para PATCH; todos los campos son opcionales
#
# ¿CÓMO ADAPTARLO A OTRO PROYECTO?
#   Renombra las clases (ej: ProductBase, ProductID, ProductUpdate).
#   Ajusta los campos según tu entidad y sus validaciones.
# =============================================================================

from pokemon_type import *             # importa el Enum Tipo (y cualquier otro Enum que agregues)
from sqlmodel import SQLModel, Field   # SQLModel = base de todos los modelos
from typing import Optional            # Optional permite valores None en campos


# ─────────────────────────────────────────────────────────────────────────────
# CLASE BASE: PokemonBase
# Contiene los campos de negocio (sin id).
# Se usa como: cuerpo del POST, base para PokemonID y PokemonUpdate.
# NO tiene table=True → NO crea tabla en la BD.
# ─────────────────────────────────────────────────────────────────────────────
class PokemonBase(SQLModel):
    # Field(default=...) define el valor por defecto si el cliente no lo envía.
    name:  str | None  = Field(default=None)            # nombre del pokemon
    tipo:  Tipo | None = Field(default=Tipo.NORMAL)     # tipo (viene del Enum Tipo)
    level: int | None  = Field(default=None)            # nivel numérico


# ─────────────────────────────────────────────────────────────────────────────
# CLASE DE BASE DE DATOS: PokemonID
# Hereda todos los campos de PokemonBase y agrega el campo `id`.
# table=True  → SQLModel crea (o mapea) la tabla "pokemonid" en la BD.
# primary_key=True → el campo `id` es la llave primaria; la BD lo autogenera.
# ─────────────────────────────────────────────────────────────────────────────
class PokemonID(PokemonBase, table=True):
    id: int | None = Field(default=None, primary_key=True)  # autogenerado por la BD


# ─────────────────────────────────────────────────────────────────────────────
# CLASE DE ACTUALIZACIÓN: PokemonUpdate
# Se usa EXCLUSIVAMENTE en el endpoint PATCH (actualización parcial).
# Todos los campos son opcionales (None) para que el cliente envíe solo
# los campos que quiere cambiar sin necesidad de mandar el objeto completo.
# min_length / max_length / gt / le = validaciones automáticas de Pydantic.
# ─────────────────────────────────────────────────────────────────────────────
class PokemonUpdate(PokemonBase):
    name:  str | None = Field(None, min_length=4, max_length=50)  # entre 4 y 50 caracteres
    level: int | None = Field(None, gt=0, le=100)                 # entre 1 y 100
