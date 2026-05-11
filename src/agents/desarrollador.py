"""Agente Desarrollador — programador full-stack experto."""
from __future__ import annotations
import os
from src.agents.base import AgenteBase
import src.tools.search_tools as st
import src.tools.drive_tools as dr


TOOLS_ARCHIVOS: list[dict] = [
    {
        "name": "archivo_crear",
        "description": (
            "Crea un archivo de código en el sistema de archivos local. "
            "Úsalo para generar proyectos completos: HTML, CSS, JS, Python, React, etc."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "ruta": {
                    "type": "string",
                    "description": "Ruta relativa del archivo, ej: mi-proyecto/index.html",
                },
                "contenido": {"type": "string", "description": "Contenido completo del archivo"},
            },
            "required": ["ruta", "contenido"],
        },
    },
    {
        "name": "archivo_leer",
        "description": "Lee el contenido de un archivo existente para revisarlo o modificarlo.",
        "input_schema": {
            "type": "object",
            "properties": {
                "ruta": {"type": "string", "description": "Ruta del archivo a leer"},
            },
            "required": ["ruta"],
        },
    },
    {
        "name": "proyecto_listar",
        "description": "Lista los archivos de un directorio o proyecto.",
        "input_schema": {
            "type": "object",
            "properties": {
                "directorio": {
                    "type": "string",
                    "description": "Directorio a listar (usa '.' para el actual)",
                    "default": ".",
                },
            },
            "required": [],
        },
    },
]

BASE_ESPECIALISTA = """
Eres un Desarrollador Full-Stack Senior con expertise en múltiples tecnologías.

Puedes construir cualquier tipo de software:

FRONTEND:
- Sitios web con HTML, CSS, JavaScript vanilla (cuando se necesita simplicidad)
- Aplicaciones React / Next.js (cuando se necesita interactividad)
- Diseño responsivo mobile-first con Tailwind CSS o CSS puro
- Landing pages de alto impacto y conversión

BACKEND:
- Integraciones con API REST y Webhooks
- Creación de paneles de administración y dashboards internos
- Integraciones con servicios externos: Airtable, Meta, Google, WhatsApp, Stripe
- Despliegue de aplicaciones (AWS, Vercel, Railway, Render) datos: PostgreSQL, SQLite, MongoDB

AUTOMATIZACIÓN:
- Scripts de Python para automatizar tareas repetitivas
- Integraciones entre sistemas via API
- Bots de WhatsApp o Telegram
- Scrapers y extracción de datos

IA APLICADA:
- Integración de Claude/OpenAI en productos
- Chatbots inteligentes para páginas web
- Procesamiento de documentos con IA
- Sistemas de recomendación

Principios de trabajo:
- Código que funciona desde el primer intento
- Siempre código completo — nunca fragmentos incompletos
- Mobile-first para todo lo que sea web
- Variables de configuración al inicio del archivo para personalización fácil
- Comentarios solo donde el código no es obvio
- Cuando generes un proyecto, crea TODOS los archivos necesarios
- Para HTML/CSS/JS: usa CDN links (Tailwind, Alpine.js, etc.) — sin build steps
- Para Python: especifica las dependencias necesarias

Cuando el usuario pida una web o app:
1. Pregunta si no tienes claro el objetivo
2. Define la estructura de archivos antes de codificar
3. Crea todos los archivos con código completo y funcional
4. Explica cómo ejecutar/desplegar el proyecto

Responde siempre en español.
"""

CONTEXTO_NEGOCIO = """
=== NEGOCIO ACTUAL ===
Empresa: Futura Bienes Raíces + Futura Cleaning
Ciudad: Santa Ana, El Salvador
WhatsApp: 6027-2418
Web Cleaning: www.futuracleaning.serviciosfutura.com

Negocios activos:
1. Futura Bienes Raíces — venta de casas, terrenos y propiedades en obra gris
2. Futura Cleaning — limpieza especializada de colchones y juegos de sala/sillas

Operador: Ever Quiñónez
Zona principal: Santa Ana y alrededores, El Salvador
"""

INSTRUCCIONES = f"{BASE_ESPECIALISTA}\n\n=== CONTEXTO DEL NEGOCIO ===\n{CONTEXTO_NEGOCIO}"


HERRAMIENTAS = TOOLS_ARCHIVOS + st.TOOLS_SEARCH + dr.TOOLS_DRIVE


def _ejecutar_archivo(nombre: str, parametros: dict) -> str:
    if nombre == "archivo_crear":
        return _crear_archivo(**parametros)
    if nombre == "archivo_leer":
        return _leer_archivo(**parametros)
    if nombre == "proyecto_listar":
        return _listar_proyecto(**parametros)
    return f"Herramienta desconocida: {nombre}"


def _crear_archivo(ruta: str, contenido: str) -> str:
    # Resuelve ruta relativa a una carpeta de proyectos segura
    base = os.path.join(os.getcwd(), "proyectos")
    ruta_completa = os.path.normpath(os.path.join(base, ruta))
    if not ruta_completa.startswith(base):
        return "Error: ruta fuera del directorio permitido."
    os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
    with open(ruta_completa, "w", encoding="utf-8") as f:
        f.write(contenido)
    return f"Archivo creado: proyectos/{ruta} ({len(contenido)} chars)"


def _leer_archivo(ruta: str) -> str:
    base = os.path.join(os.getcwd(), "proyectos")
    ruta_completa = os.path.normpath(os.path.join(base, ruta))
    if not ruta_completa.startswith(base):
        return "Error: ruta fuera del directorio permitido."
    if not os.path.exists(ruta_completa):
        return f"Archivo no encontrado: {ruta}"
    with open(ruta_completa, "r", encoding="utf-8") as f:
        contenido = f.read()
    return contenido[:5000] + ("..." if len(contenido) > 5000 else "")


def _listar_proyecto(directorio: str = ".") -> str:
    base = os.path.join(os.getcwd(), "proyectos")
    ruta = os.path.normpath(os.path.join(base, directorio))
    if not ruta.startswith(base):
        return "Error: ruta fuera del directorio permitido."
    if not os.path.exists(ruta):
        return "El directorio no existe aún."
    archivos = []
    for raiz, dirs, files in os.walk(ruta):
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        nivel = raiz.replace(base, "").count(os.sep)
        indent = "  " * nivel
        carpeta = os.path.basename(raiz)
        if raiz != ruta:
            archivos.append(f"{indent}{carpeta}/")
        for archivo in files:
            archivos.append(f"{indent}  {archivo}")
    return "\n".join(archivos) if archivos else "Directorio vacío."


class AgenteDesarrollador(AgenteBase):
    def __init__(self):
        super().__init__(
            nombre="Agente Desarrollador",
            instrucciones=INSTRUCCIONES,
            herramientas=HERRAMIENTAS,
        )

    def ejecutar_herramienta(self, nombre: str, parametros: dict) -> str:
        if nombre.startswith("archivo_") or nombre == "proyecto_listar":
            return _ejecutar_archivo(nombre, parametros)
        if nombre.startswith("web_"):
            return st.ejecutar_herramienta(nombre, parametros)
        if nombre.startswith("drive_"):
            return dr.ejecutar_herramienta(nombre, parametros)
        return f"Herramienta no disponible: {nombre}"
