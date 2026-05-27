# =============================================================================
# ARCHIVO: operation_db.py
# PROPÓSITO: Contiene todas las operaciones CRUD contra la base de datos.
#
# ¿POR QUÉ EXISTE ESTE ARCHIVO?
#   Separa la lógica de acceso a datos de los endpoints HTTP (main.py).
#   Esto sigue el principio de Separación de Responsabilidades:
#   - main.py   → sabe de HTTP (rutas, status codes, errores HTTP)
#   - operation_db.py → sabe de la base de datos (SQLModel/SQLAlchemy)
#
# PATRÓN:
#   Cada función recibe una `session` de SQLModel y opera sobre los modelos.
#   Si la entidad no existe, devuelve None → main.py convierte eso en 404.
#
# ¿CÓMO ADAPTARLO A OTRO PROYECTO?
#   Renombra las funciones y los modelos (PokemonBase → ProductBase, etc.).
#   La lógica interna de session.add / commit / refresh se mantiene igual.
# =============================================================================

from sqlalchemy.exc import NoResultFound       # excepción cuando no hay resultado
from sqlmodel import Session, select           # Session: contexto de BD; select: consultas
from model import PokemonBase, PokemonID, PokemonUpdate  # modelos del proyecto


# ─── CREATE ──────────────────────────────────────────────────────────────────
# Recibe los datos sin id (PokemonBase), crea un registro en la BD y devuelve
# el objeto completo con el id generado por la base de datos.
# model_validate() convierte el objeto Pydantic a un objeto SQLModel para BD.
def create_pokemon_db(pokemon: PokemonBase, session: Session):
    new = PokemonID.model_validate(pokemon)  # convierte PokemonBase → PokemonID (modelo de tabla)
    session.add(new)      # agrega el objeto a la sesión (aún no se guarda en BD)
    session.commit()      # hace efectivo el INSERT en la BD
    session.refresh(new)  # recarga el objeto desde la BD para obtener el id autogenerado
    return new


# ─── READ ONE ────────────────────────────────────────────────────────────────
# Busca un registro por su id (llave primaria).
# get_one() lanza NoResultFound si no existe → se captura y devuelve None.
# main.py convierte None en HTTPException 404.
def find_one_pokemon_db(pokemon_id: int, session: Session):
    try:
        return session.get_one(PokemonID, pokemon_id)  # busca por llave primaria
    except NoResultFound:
        return None   # el endpoint interpretará esto como "no encontrado"


# ─── READ ALL ────────────────────────────────────────────────────────────────
# Devuelve todos los registros de la tabla.
# select(PokemonID) genera un SELECT * FROM pokemonid.
# session.exec() ejecuta la consulta y retorna un iterable de objetos PokemonID.
def all_pokemon_db(session: Session):
    statement = select(PokemonID)          # construye la consulta SQL
    results   = session.exec(statement)   # ejecuta y devuelve resultados
    return results


# ─── UPDATE (PATCH parcial) ───────────────────────────────────────────────────
# Actualiza solo los campos que llegaron en new_pokemon (los que no son None).
# exclude_unset=True es CLAVE: descarta los campos que el cliente no envió,
# así solo se modifican los campos que realmente llegaron en el PATCH.
def updated_pokemon_db(pokemon_id: int, new_pokemon: PokemonUpdate, session: Session):
    pokemon = find_one_pokemon_db(pokemon_id, session)
    if pokemon is None:
        return None   # no existe → el endpoint devolverá 404

    # model_dump(exclude_unset=True) → solo los campos que vinieron en el request
    pokemon_update = new_pokemon.model_dump(exclude_unset=True)
    pokemon.sqlmodel_update(pokemon_update)  # aplica los cambios al objeto en memoria
    session.add(pokemon)     # marca el objeto como modificado en la sesión
    session.commit()         # hace efectivo el UPDATE en la BD
    session.refresh(pokemon) # recarga el objeto con los datos definitivos de la BD
    return pokemon


# ─── DELETE ──────────────────────────────────────────────────────────────────
# Busca el registro, lo elimina de la BD y devuelve el objeto eliminado.
# Si no existe, get_one() lanza NoResultFound → se devuelve None → 404 en main.py.
def kill_one_pokemon_db(pokemon_id: int, session: Session):
    try:
        pokemon = session.get_one(PokemonID, pokemon_id)  # busca por id
        session.delete(pokemon)   # marca para eliminar
        session.commit()          # hace efectivo el DELETE
        return pokemon            # devuelve el objeto eliminado (útil para confirmación)
    except NoResultFound:
        return None
