# =============================================================================
# ARCHIVO: pokemon_type.py
# PROPÓSITO: Define los tipos posibles para los elementos del proyecto.
#
# ¿POR QUÉ EXISTE ESTE ARCHIVO?
#   Centraliza los valores permitidos en un "Enum". Esto evita escribir strings
#   sueltos por todo el código (ej: "fuego", "agua") y previene errores de
#   tipeo. FastAPI y Pydantic lo usan para validar automáticamente que el valor
#   enviado en el JSON sea uno de los valores permitidos.
#
# ¿CÓMO ADAPTARLO A OTRO PROYECTO?
#   Renombra la clase y sus valores según las categorías de tu proyecto.
#   Ejemplo para una tienda: class Categoria(str, Enum): ROPA="ropa" etc.
# =============================================================================

from enum import Enum, auto   # Enum: clase base para enumeraciones de Python

# ─────────────────────────────────────────────────────────────────────────────
# CLASE: Tipo
# Hereda de (str, Enum) para que los valores sean cadenas de texto.
# Heredar de str es IMPORTANTE porque así FastAPI puede serializar el valor
# directamente a JSON sin conversión extra, y SQLModel lo guarda en la BD.
# ─────────────────────────────────────────────────────────────────────────────
class Tipo(str, Enum):
    # Cada línea = un valor válido.  Lado izquierdo = nombre Python, lado derecho = valor real en BD/JSON.
    HIERBA    = "hierba"      # ← cambia estos valores por los de tu dominio
    FUEGO     = "fuego"
    ELECTRICO = "electrico"
    NORMAL    = "normal"
    AGUA      = "AGUA"
