# =============================================================================
# ARCHIVO: utils.py
# PROPÓSITO: Funciones de utilidad para manejo de archivos e imágenes.
#
# ¿POR QUÉ EXISTE ESTE ARCHIVO?
#   Concentra las funciones auxiliares que no pertenecen ni a la lógica de
#   negocio ni a los endpoints HTTP. Siguiendo el principio de separación de
#   responsabilidades, main.py solo orquesta; utils.py hace el trabajo pesado.
#
# FUNCIONES:
#   - save_img_local()  → guarda la imagen en disco local (carpeta files/img/)
#   - supabase_client() → crea y devuelve el cliente de Supabase (Storage)
#   - save_img_remote() → sube la imagen al bucket de Supabase Storage
#
# VARIABLES DE ENTORNO NECESARIAS EN .env:
#   SUPABASE_URL    = https://xxxx.supabase.co
#   SUPABASE_KEY    = tu-anon-key
#   SUPABASE_BUCKET = nombre-del-bucket
#
# ¿CÓMO ADAPTARLO A OTRO PROYECTO?
#   - Cambia IMG_DIR si quieres otra carpeta local.
#   - Si no usas Supabase, elimina supabase_client() y save_img_remote().
#   - Puedes agregar más funciones utilitarias aquí (resize, validación, etc.).
# =============================================================================

import os
import shutil                          # para copiar el stream de archivo a disco
from pathlib import Path               # manejo de rutas compatible con todos los SO
from supabase import create_client, Client  # SDK oficial de Supabase para Python
from dotenv import load_dotenv         # carga variables del .env
from fastapi import UploadFile, File, HTTPException  # tipos de FastAPI para archivos

# Carga el .env (debe estar en la raíz del proyecto)
load_dotenv()

# ─── Configuración ───────────────────────────────────────────────────────────
# Carpeta local donde se guardarán las imágenes subidas.
# Path() usa "/" como separador en cualquier OS; mkdir(parents=True) crea
# subdirectorios si no existen.
IMG_DIR = Path("files/img")

# Nombre del bucket de Supabase Storage (viene del .env)
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")


# ─── GUARDAR IMAGEN LOCAL ────────────────────────────────────────────────────
# Recibe un objeto UploadFile de FastAPI (archivo subido vía multipart/form-data).
# Valida que sea imagen, crea la carpeta si no existe y copia el archivo al disco.
# Retorna la ruta (Path) donde quedó guardado.
def save_img_local(file: UploadFile):
    # Validación de seguridad: rechaza archivos que no sean imágenes.
    # content_type viene en el header del request (ej: "image/jpeg").
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    IMG_DIR.mkdir(parents=True, exist_ok=True)   # crea files/img/ si no existe
    destination = IMG_DIR / file.filename        # ruta completa del archivo destino

    # shutil.copyfileobj copia el stream del archivo al disco de forma eficiente
    # sin cargar todo en memoria (importante para archivos grandes).
    with destination.open("wb") as stores:
        shutil.copyfileobj(file.file, stores)

    return destination   # retorna la ruta para mostrarla en el response


# ─── CLIENTE SUPABASE ────────────────────────────────────────────────────────
# Función auxiliar que crea y retorna el cliente de Supabase.
# Se separa en su propia función para poder reutilizarla o mockeara en tests.
# Lanza RuntimeError si no hay credenciales (fallo rápido y claro).
def supabase_client():
    url = os.getenv("SUPABASE_URL")   # URL del proyecto Supabase
    key = os.getenv("SUPABASE_KEY")   # anon key o service key de Supabase

    if not url or not key:
        raise RuntimeError("No credentials provided")   # evita errores crípticos más adelante
    return create_client(url, key)


# ─── GUARDAR IMAGEN EN SUPABASE STORAGE (remoto) ─────────────────────────────
# Sube el archivo al bucket configurado en SUPABASE_BUCKET.
# Retorna la URL pública del archivo subido para poder guardarla en BD o responder al cliente.
#
# FLUJO:
#   1. Valida que sea imagen
#   2. Lee todo el contenido en memoria (bytes)
#   3. Sube a Supabase Storage con el tipo de contenido correcto
#   4. Obtiene y retorna la URL pública
def save_img_remote(file: UploadFile):
    # Validación de seguridad: solo imágenes
    if not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Invalid file type")

    contents = file.file.read()   # lee el archivo completo en bytes
    path     = file.filename      # nombre del archivo en el bucket

    client = supabase_client()    # obtiene el cliente autenticado de Supabase

    # Sube el archivo al bucket; file_options especifica el MIME type correcto
    response = client.storage.from_(SUPABASE_BUCKET).upload(
        path         = path,
        file         = contents,
        file_options = {"content-type": file.content_type},
    )

    # Genera y retorna la URL pública del archivo recién subido
    public_url_bucket = client.storage.from_(SUPABASE_BUCKET).get_public_url(path)
    return public_url_bucket



