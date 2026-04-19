"""Herramientas para interactuar con Google Drive."""
from __future__ import annotations
import io
import os
from src.config import GOOGLE_CREDENTIALS_FILE, GOOGLE_DRIVE_FOLDER_ID

SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/documents",
]


def _get_service(servicio: str = "drive", version: str = "v3"):
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    token_file = "token.json"
    creds = None
    if os.path.exists(token_file):
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_file, "w") as f:
            f.write(creds.to_json())
    return build(servicio, version, credentials=creds)


# ── Definiciones de herramientas para Claude ─────────────────────

TOOLS_DRIVE: list[dict] = [
    {
        "name": "drive_listar_archivos",
        "description": (
            "Lista archivos en la carpeta de Google Drive del negocio. "
            "Ideal para encontrar contratos, fichas de propiedades, imágenes."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Texto a buscar en el nombre del archivo"},
                "tipo": {
                    "type": "string",
                    "description": "Tipo de archivo (opcional): imagen, pdf, documento, hoja",
                    "enum": ["imagen", "pdf", "documento", "hoja"],
                },
                "limite": {"type": "integer", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "drive_crear_documento",
        "description": (
            "Crea un nuevo documento de Google Docs en la carpeta del negocio. "
            "Útil para generar contratos, reportes o fichas de propiedades."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string", "description": "Nombre del documento"},
                "contenido": {"type": "string", "description": "Contenido inicial del documento"},
            },
            "required": ["titulo", "contenido"],
        },
    },
    {
        "name": "drive_subir_archivo",
        "description": "Sube un archivo de texto/reporte a Google Drive.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre_archivo": {"type": "string", "description": "Nombre con extensión (ej: reporte.txt)"},
                "contenido": {"type": "string", "description": "Contenido del archivo"},
            },
            "required": ["nombre_archivo", "contenido"],
        },
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "drive_listar_archivos": _listar_archivos,
        "drive_crear_documento": _crear_documento,
        "drive_subir_archivo": _subir_archivo,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _listar_archivos(query: str = "", tipo: str | None = None, limite: int = 10) -> str:
    service = _get_service()
    mime_map = {
        "imagen": "image/",
        "pdf": "application/pdf",
        "documento": "application/vnd.google-apps.document",
        "hoja": "application/vnd.google-apps.spreadsheet",
    }
    q_parts = [f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents", "trashed = false"]
    if query:
        q_parts.append(f"name contains '{query}'")
    if tipo and tipo in mime_map:
        if tipo == "imagen":
            q_parts.append(f"mimeType contains 'image/'")
        else:
            q_parts.append(f"mimeType = '{mime_map[tipo]}'")
    q_str = " and ".join(q_parts)
    resultado = (
        service.files()
        .list(q=q_str, pageSize=limite, fields="files(id, name, mimeType, modifiedTime)")
        .execute()
    )
    archivos = resultado.get("files", [])
    if not archivos:
        return "No se encontraron archivos con esos criterios."
    lineas = [f"Archivos en Drive ({len(archivos)}):"]
    for a in archivos:
        lineas.append(f"• {a['name']} [{a['id']}] — {a.get('modifiedTime', '')[:10]}")
    return "\n".join(lineas)


def _crear_documento(titulo: str, contenido: str) -> str:
    from googleapiclient.discovery import build

    drive_service = _get_service("drive")
    # Crear el documento vacío
    meta = {
        "name": titulo,
        "mimeType": "application/vnd.google-apps.document",
        "parents": [GOOGLE_DRIVE_FOLDER_ID],
    }
    archivo = drive_service.files().create(body=meta, fields="id").execute()
    doc_id = archivo["id"]

    # Escribir contenido
    docs_service = _get_service("docs", "v1")
    docs_service.documents().batchUpdate(
        documentId=doc_id,
        body={
            "requests": [
                {"insertText": {"location": {"index": 1}, "text": contenido}}
            ]
        },
    ).execute()
    return (
        f"Documento '{titulo}' creado en Drive.\n"
        f"Enlace: https://docs.google.com/document/d/{doc_id}/edit"
    )


def _subir_archivo(nombre_archivo: str, contenido: str) -> str:
    from googleapiclient.http import MediaIoBaseUpload

    service = _get_service("drive")
    meta = {"name": nombre_archivo, "parents": [GOOGLE_DRIVE_FOLDER_ID]}
    media = MediaIoBaseUpload(
        io.BytesIO(contenido.encode("utf-8")),
        mimetype="text/plain",
    )
    archivo = service.files().create(body=meta, media_body=media, fields="id").execute()
    return f"Archivo '{nombre_archivo}' subido a Drive. ID: {archivo['id']}"
