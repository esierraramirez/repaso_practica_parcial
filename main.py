# =============================================================================
# ARCHIVO: main.py
# PROPÓSITO: Punto de entrada de la aplicación FastAPI.
#            Aquí se definen TODOS los endpoints (rutas HTTP) del proyecto.
#
# ¿POR QUÉ ES EL ARCHIVO PRINCIPAL?
#   FastAPI arranca leyendo este archivo. Contiene la instancia `app` que
#   Uvicorn ejecuta. Cada función decorada con @app.get / @app.post / etc.
#   es un endpoint HTTP que el cliente puede llamar.
#
# ESTRUCTURA DE IMPORTS:
#   - FastAPI, HTTPException, Request → núcleo del framework
#   - Session / SessionDep → manejo de BD (viene de db.py)
#   - JSONResponse / HTMLResponse → tipos de respuesta HTTP
#   - Jinja2Templates → motor de plantillas HTML
#   - utils → funciones auxiliares para manejo de imágenes
#   - model → los esquemas de datos (PokemonBase, PokemonID, PokemonUpdate)
#   - operation_csv → CRUD sobre archivo CSV (alternativa sin BD)
#   - operation_db → CRUD sobre base de datos relacional (activo)
#
# ORDEN RECOMENDADO DE ENDPOINTS:
#   1. Manejador global de errores
#   2. Endpoints de archivos/media
#   3. CRUD principal (POST, GET, PATCH, DELETE)
#   4. Endpoints HTML (vistas con plantillas)
#   5. Endpoint raíz "/"
# =============================================================================

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from sqlmodel import Session
from starlette.responses import JSONResponse
from db import create_all_tables, SessionDep
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from utils import (save_img_local, save_img_remote)
from model import PokemonBase, PokemonID, PokemonUpdate
from operation_csv import createPokemon, showPokemons, showPokemon, updatePokemon, deletePokemon
from operation_db import create_pokemon_db, find_one_pokemon_db, all_pokemon_db, updated_pokemon_db, kill_one_pokemon_db

# ─── Instancia de FastAPI ─────────────────────────────────────────────────────
# lifespan=create_all_tables → función que se ejecuta al ARRANCAR el servidor.
# create_all_tables (en db.py) crea las tablas en la BD si no existen.
app = FastAPI(lifespan=create_all_tables)

# ─── Motor de plantillas Jinja2 ───────────────────────────────────────────────
# Apunta a la carpeta "templates/" donde viven los archivos .html.
# Se usa en los endpoints que devuelven HTMLResponse con TemplateResponse().
templates = Jinja2Templates(directory="templates")


# =============================================================================
# MANEJADOR GLOBAL DE ERRORES HTTP
# =============================================================================
# Intercepta TODAS las HTTPException lanzadas en cualquier endpoint.
# Permite personalizar el formato del JSON de error en un solo lugar.
# Sin este handler, FastAPI devuelve {"detail": "..."} por defecto.
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"message": f"{exc.detail} Ooops. TODOOO fallo"}, )


# =============================================================================
# ENDPOINTS DE IMÁGENES
# =============================================================================

# ─── POST /image/local ───────────────────────────────────────────────────────
# Recibe una imagen via multipart/form-data y la guarda en disco local.
# UploadFile = File(...) indica que el campo "file" es OBLIGATORIO.
# save_img_local() valida el tipo y guarda; devuelve la ruta en disco.
@app.post("/image/local")
async def image_save(file: UploadFile = File(...)):
    path = save_img_local(file)
    return {"saved at": path}


# ─── POST /image/remote ──────────────────────────────────────────────────────
# Recibe una imagen y la sube a Supabase Storage (almacenamiento en la nube).
# Devuelve la URL pública del archivo en Supabase.
@app.post("/image/remote")
async def image_store(file: UploadFile = File(...)):
    url = save_img_remote(file)
    return {"saved at": url}


# =============================================================================
# CRUD PRINCIPAL (Base de datos)
# =============================================================================

# ─── POST /pokemon ────────────────────────────────────────────────────────────
# Crea un nuevo pokemon en la BD.
# response_model=PokemonID → FastAPI serializa la respuesta con ese schema.
# status_code=201 → HTTP "Created" (estándar REST para recursos creados).
# session: SessionDep → FastAPI inyecta la sesión de BD automáticamente.
@app.post("/pokemon", response_model=PokemonID, status_code=201)
async def catch_pokemon(pokemon: PokemonBase, session: SessionDep):
    return create_pokemon_db(pokemon, session)


##pokedex.append(pokemon)


# ─── GET /pokemon ─────────────────────────────────────────────────────────────
# Devuelve la lista completa de pokemons en formato JSON.
# response_model=list[PokemonID] → FastAPI valida que la respuesta sea lista.
@app.get("/pokemon", response_model=list[PokemonID])
async def show_all_pokemon(session: SessionDep):
    pokemons = all_pokemon_db(session)
    return pokemons


# ─── GET /pokemon/{id} ────────────────────────────────────────────────────────
# Devuelve un pokemon por su id en formato JSON.
# {id} es un path parameter; FastAPI lo convierte a int automáticamente.
# Si no existe → 404 Not Found.
@app.get("/pokemon/{id}", response_model=PokemonID)
async def show_pokemon(id: int, session: SessionDep):
    pokemon = find_one_pokemon_db(id, session)
    if not (pokemon):
        raise HTTPException(status_code=404, detail="Pokemon has not been caught")
    return pokemon


# ─── GET /pokemon_html/{id} ───────────────────────────────────────────────────
# Devuelve HTML renderizado con datos de UN pokemon.
# response_class=HTMLResponse → FastAPI sabe que la respuesta es HTML, no JSON.
# TemplateResponse pasa "pokemon_html" al template; en el HTML se usa {{ pokemon_html.name }}.
@app.get("/pokemon_html/{id}", response_class=HTMLResponse)
async def one_pokemon_html(request: Request, id: int, session: SessionDep):
    pokemon = find_one_pokemon_db(id, session)
    if not (pokemon):
        raise HTTPException(status_code=404, detail="Pokemon has not been caught")
    return templates.TemplateResponse("pokemons.html",
                                      {"request": request, "pokemon_html": pokemon})


# ─── GET /pokemons_html ───────────────────────────────────────────────────────
# Devuelve HTML renderizado con la lista completa de pokemons.
# El template pokemons.html itera sobre "pokemon_html" con un bucle Jinja2.
@app.get("/pokemons_html", response_class=HTMLResponse)
async def all_pokemon_html(request: Request, session: SessionDep):
    pokemons = all_pokemon_db(session)
    return templates.TemplateResponse("pokemons.html", {"request": request, "pokemon_html": pokemons})


# ─── PATCH /pokemon/{id} ─────────────────────────────────────────────────────
# Actualización PARCIAL: solo se modifican los campos que llegan en el body.
# PATCH ≠ PUT: PUT reemplaza todo el objeto; PATCH solo lo que cambió.
# PokemonUpdate tiene todos los campos opcionales para soportar actualizaciones parciales.
@app.patch("/pokemon/{id}", response_model=PokemonID)
async def update_pokemon(id: int, pokemon_update: PokemonUpdate, session: SessionDep):
    updated = updated_pokemon_db(id, pokemon_update, session)
    if not (updated):
        raise HTTPException(status_code=404, detail="Pokemon has not been evolved")
    return updated


# ─── DELETE /pokemon/{id} ─────────────────────────────────────────────────────
# Elimina un pokemon de la BD por su id.
# response_model=PokemonBase → devuelve el objeto eliminado sin id (confirmación).
@app.delete("/pokemon/{id}", response_model=PokemonBase)
async def delete_pokemon(id: int, session: SessionDep):
    deleted = kill_one_pokemon_db(id, session)
    if not (deleted):
        raise HTTPException(status_code=404, detail="Pokemon has not been caught")
    return deleted


# =============================================================================
# ENDPOINT RAÍZ (demo de HTML inline)
# =============================================================================
# Aqui empieza nuestro HTML 👨🏻‍💻

# ─── GET / ────────────────────────────────────────────────────────────────────
# Página de bienvenida con HTML escrito directamente en el código (inline).
# Útil para páginas muy simples o de prueba rápida.
# Para páginas más complejas usar templates/ con Jinja2 (como los endpoints de arriba).
@app.get("/", response_class=HTMLResponse)
async def root():
    contenido_html = """
    <html lang="en">
<head>
    <meta charset="UTF-8">
    <title>HTMLResponses-INTO-FASTAPI</title>
</head>
<body>
<h1>Nuestro HTML</h1>

<a href="http://sigmotoa.com">Visita mi sitio </a>
<br>
<br>
<a href="#algo"> Visitar algo</a>
<br>
<a href="formulario.html" target="_self">Ver Formulario</a>

<section id="algo">
    <p>Un parrafo</p>
</section>

<section id ="Carro">
    <p>Un carro F1</p>
    <img src="data:image/jpeg;base64,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" alt="Un carro formula 1 color naranja dando una curva" sizes="">
</section>

<footer>
    <p>lorem ipsum </p>

</footer>

</body>
</html>
    
    """
    return HTMLResponse(content=contenido_html, status_code=200)


# ─── GET /template ────────────────────────────────────────────────────────────
# Renderiza el template index.html (si existe en la carpeta templates/).
# NOTA: actualmente index.html no existe; créalo en templates/ cuando necesites
#       una landing page con Jinja2.
@app.get("/template", response_class=HTMLResponse)
async def htmltemplate(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


'''
# ─── Ejemplo de endpoint con parámetro en la ruta (comentado) ─────────────────
# Descomentar cuando se necesite un endpoint tipo "saludo personalizado".
# {name} es un path parameter que FastAPI pasa automáticamente como argumento.

@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}
'''
