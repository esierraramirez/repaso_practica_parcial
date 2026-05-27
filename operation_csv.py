# =============================================================================
# ARCHIVO: operation_csv.py
# PROPÓSITO: Operaciones CRUD sobre un archivo CSV (alternativa sin BD).
#
# ¿POR QUÉ EXISTE ESTE ARCHIVO?
#   Permite persistir datos usando un simple archivo .csv en lugar de una
#   base de datos relacional. Es útil para prototipos rápidos o proyectos
#   pequeños donde no se quiere configurar una BD.
#   NOTA: En el proyecto actual, los endpoints principales ya usan operation_db.py
#   (base de datos). Este archivo es la implementación CSV original, que quedó
#   como alternativa / referencia.
#
# ARCHIVO CSV GENERADO: pokedex.csv (en la raíz del proyecto)
# COLUMNAS: id, name, tipo, level
#
# ¿CÓMO ADAPTARLO A OTRO PROYECTO?
#   Cambia CSV_FILE, columns, y los modelos (PokemonBase/PokemonID) por los
#   de tu entidad. La lógica de leer/escribir CSV se puede reusar tal cual.
# =============================================================================

import os
import csv
from typing import Optional
from model import *   # importa PokemonBase, PokemonID, PokemonUpdate

# ─── Configuración del archivo CSV ───────────────────────────────────────────
CSV_FILE = "pokedex.csv"                   # nombre del archivo CSV en disco
columns  = ["id", "name", "tipo", "level"] # columnas = cabecera del CSV; deben coincidir con el modelo


# ─── UTILIDAD: Generar nuevo ID ───────────────────────────────────────────────
# Lee el CSV, obtiene el id máximo y retorna id_maximo + 1.
# Si el archivo no existe o está vacío, empieza desde 1.
# Esto simula el autoincrement de una BD relacional.
def newID():
    try:
        with open(CSV_FILE, mode="r", newline='') as csvfile:
            reader  = csv.DictReader(csvfile)
            max_id  = max(int(row['id']) for row in reader)
            return max_id + 1
    except (FileNotFoundError, csv.Error):
        return 1   # primera fila → id = 1


# ─── UTILIDAD: Guardar un pokemon con ID en el CSV ───────────────────────────
# Abre el CSV en modo "append" (agrega al final).
# Si el archivo no existía, escribe la cabecera primero.
# model_dump() convierte el objeto Pydantic a un diccionario {columna: valor}.
def savePokemonID(pokemon: PokemonID):
    pokedex_exists = os.path.exists(CSV_FILE)
    with open(CSV_FILE, "a+", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        if not pokedex_exists:
            writer.writeheader()         # escribe cabecera solo si el archivo es nuevo
        writer.writerow(pokemon.model_dump())   # escribe la fila de datos


# ─── CREATE ──────────────────────────────────────────────────────────────────
# Genera un nuevo id, construye un PokemonID y lo guarda en el CSV.
# **pokemon.model_dump() desempaqueta el dict del PokemonBase como kwargs.
def createPokemon(pokemon: PokemonBase):
    id          = newID()
    new_pokemon = PokemonID(id=id, **pokemon.model_dump())
    savePokemonID(new_pokemon)
    return new_pokemon


# ─── READ ALL ────────────────────────────────────────────────────────────────
# Lee todas las filas del CSV y las convierte en objetos PokemonID.
# DictReader devuelve cada fila como un dict {columna: valor}.
def showPokemons():
    with open(CSV_FILE) as csvfile:
        reader = csv.DictReader(csvfile)
        return [PokemonID(**row) for row in reader]   # list comprehension → lista de objetos


# ─── READ ONE ────────────────────────────────────────────────────────────────
# Recorre el CSV buscando la fila cuyo id coincida.
# Retorna el objeto o None si no existe.
def showPokemon(id: int):
    with open(CSV_FILE) as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            if int(row['id']) == id:
                return PokemonID(**row)
    # si llega aquí sin hacer return, Python devuelve None implícitamente


# ─── UPDATE ──────────────────────────────────────────────────────────────────
# Lee todos los pokemon, modifica el que coincide con el id y
# reescribe el CSV completo (no hay UPDATE parcial en CSV).
# model_copy(update=...) es la forma Pydantic de clonar con cambios.
def updatePokemon(id: int, pokemon: PokemonBase):
    pokemon_update: Optional[PokemonID] = None
    pokemons = showPokemons()
    for num, pokemon_ in enumerate(pokemons):
        if pokemon_.id == id:
            # clona el objeto aplicando los nuevos valores
            pokemons[num] = (pokemon_update) = pokemon_.model_copy(update=pokemon)
    # reescribe el CSV completo con la lista actualizada
    with open(CSV_FILE, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for pokemon_ in pokemons:
            writer.writerow(pokemon_.model_dump())
    if pokemon_update:
        return pokemon_update   # retorna el pokemon actualizado


# ─── DELETE ──────────────────────────────────────────────────────────────────
# Lee todos, omite el que tiene el id buscado, reescribe el CSV sin él.
# continue salta al siguiente ciclo sin escribir la fila que se va a eliminar.
def deletePokemon(id: int):
    pokemon_deleted: Optional[PokemonBase] = None
    pokemons = showPokemons()
    with open(CSV_FILE, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        for pokemon_ in pokemons:
            if pokemon_.id == id:
                pokemon_deleted = pokemon_
                continue         # no escribe esta fila → queda "eliminada"
            writer.writerow(pokemon_.model_dump())
    if pokemon_deleted:
        # devuelve PokemonBase (sin id) para el response_model del endpoint DELETE
        dict_pokemon_no_id = pokemon_deleted.model_dump()
        del dict_pokemon_no_id["id"]
        return PokemonBase(**dict_pokemon_no_id)










