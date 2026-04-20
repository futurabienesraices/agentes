"""Herramientas para interactuar con Airtable — Futura Bienes Raíces."""
from __future__ import annotations
from typing import Any
from src.config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_CLIENTES, AIRTABLE_BASE_MARKETING, AIRTABLE_BASE_PROPIEDADES,
    AIRTABLE_PROPIEDADES_TABLE, AIRTABLE_MARKETING_TABLE, AIRTABLE_CLIENTES_TABLE,
)

# Columnas reales en Airtable (detectadas el 2025-04-20)
# Propiedades_FBR: Nombre de la propiedad, Tipo, Estado, Habitaciones, Baños, Ubicación, Notas
# Clientes_FBR:    Nombre, Teléfono, Estado del cliente, Propiedades interesadas, Notas

_TABLA_BASE = {
    AIRTABLE_CLIENTES_TABLE:    AIRTABLE_BASE_CLIENTES,
    AIRTABLE_MARKETING_TABLE:   AIRTABLE_BASE_MARKETING,
    AIRTABLE_PROPIEDADES_TABLE: AIRTABLE_BASE_PROPIEDADES,
}


def _get_table(nombre_tabla: str):
    from pyairtable import Api
    base_id = _TABLA_BASE.get(nombre_tabla, AIRTABLE_BASE_CLIENTES)
    return Api(AIRTABLE_API_KEY).table(base_id, nombre_tabla)


TOOLS_AIRTABLE: list[dict] = [
    {
        "name": "airtable_listar_clientes",
        "description": "Lista los clientes/prospectos del CRM en Airtable. Filtra por estado si se indica.",
        "input_schema": {
            "type": "object",
            "properties": {
                "estado": {"type": "string", "description": "Nuevo, Contactado, Calificado, Cerrado"},
                "limite": {"type": "integer", "default": 20},
            },
            "required": [],
        },
    },
    {
        "name": "airtable_crear_cliente",
        "description": "Registra un nuevo cliente o prospecto en Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre":      {"type": "string"},
                "telefono":    {"type": "string"},
                "interes":     {"type": "string", "description": "Qué tipo de propiedad busca"},
                "presupuesto": {"type": "string"},
                "origen":      {"type": "string", "description": "WhatsApp, Instagram, Referido, etc."},
                "notas":       {"type": "string"},
            },
            "required": ["nombre"],
        },
    },
    {
        "name": "airtable_actualizar_cliente",
        "description": "Actualiza datos o estado de un cliente existente en Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id":        {"type": "string", "description": "ID del registro (rec...)"},
                "estado":           {"type": "string", "description": "Nuevo, Contactado, Calificado, Cerrado"},
                "notas":            {"type": "string"},
                "siguiente_accion": {"type": "string"},
            },
            "required": ["record_id"],
        },
    },
    {
        "name": "airtable_listar_propiedades",
        "description": "Lista propiedades del inventario en Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "tipo":   {"type": "string", "description": "Casa, Terreno, Local, Departamento, etc."},
                "estado": {"type": "string", "description": "Disponible, Vendida, Rentada"},
                "limite": {"type": "integer", "default": 10},
            },
            "required": [],
        },
    },
    {
        "name": "airtable_crear_propiedad",
        "description": "Registra una nueva propiedad en el inventario de Airtable.",
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre":      {"type": "string", "description": "Nombre o título de la propiedad"},
                "tipo":        {"type": "string", "description": "Casa, Terreno, Local, Departamento, Oficina, Bodega"},
                "operacion":   {"type": "string", "description": "Venta o Renta"},
                "precio":      {"type": "number"},
                "ubicacion":   {"type": "string"},
                "habitaciones":{"type": "integer"},
                "banos":       {"type": "number"},
                "m2":          {"type": "number"},
                "notas":       {"type": "string"},
            },
            "required": ["nombre", "tipo"],
        },
    },
    {
        "name": "airtable_listar_marketing",
        "description": "Lista registros de la tabla Marketing_FBR.",
        "input_schema": {
            "type": "object",
            "properties": {"limite": {"type": "integer", "default": 10}},
            "required": [],
        },
    },
    {
        "name": "airtable_registrar_accion_marketing",
        "description": "Registra una acción o campaña de marketing en la tabla Marketing_FBR.",
        "input_schema": {
            "type": "object",
            "properties": {
                "titulo": {"type": "string"},
                "canal":  {"type": "string", "enum": ["Instagram", "Facebook", "WhatsApp", "Portal", "Email", "Otro"]},
                "tipo":   {"type": "string", "enum": ["Post", "Story", "Anuncio", "Email", "Llamada", "Evento"]},
                "propiedad_relacionada": {"type": "string"},
                "notas":  {"type": "string"},
            },
            "required": ["titulo", "canal"],
        },
    },
    {
        "name": "airtable_reporte_clientes",
        "description": "Resumen estadístico de clientes: total por estado y conversión.",
        "input_schema": {"type": "object", "properties": {}, "required": []},
    },
]


# ── Funciones ejecutoras ──────────────────────────────────────────

def ejecutar_herramienta(nombre: str, parametros: dict) -> str:
    handlers = {
        "airtable_listar_clientes":        _listar_clientes,
        "airtable_crear_cliente":          _crear_cliente,
        "airtable_actualizar_cliente":     _actualizar_cliente,
        "airtable_listar_propiedades":     _listar_propiedades,
        "airtable_crear_propiedad":        _crear_propiedad,
        "airtable_listar_marketing":       _listar_marketing,
        "airtable_registrar_accion_marketing": _registrar_accion_marketing,
        "airtable_reporte_clientes":       _reporte_clientes,
    }
    if nombre not in handlers:
        return f"Herramienta desconocida: {nombre}"
    try:
        return handlers[nombre](**parametros)
    except Exception as exc:
        return f"Error en {nombre}: {exc}"


def _listar_clientes(estado: str | None = None, limite: int = 20) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    formula = f"{{'Estado del cliente'}}='{estado}'" if estado else None
    registros = tabla.all(formula=formula, max_records=limite)
    if not registros:
        return "No se encontraron clientes."
    lineas = [f"Clientes ({len(registros)}):"]
    for r in registros:
        f = r["fields"]
        lineas.append(
            f"• [{r['id']}] {f.get('Nombre', '—')} | "
            f"Tel: {f.get('Teléfono', '—')} | "
            f"Estado: {f.get('Estado del cliente', '—')} | "
            f"Busca: {f.get('Propiedades interesadas', '—')}"
        )
    return "\n".join(lineas)


def _crear_cliente(
    nombre: str,
    telefono: str = "",
    interes: str = "",
    presupuesto: str = "",
    origen: str = "",
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    campos: dict[str, Any] = {"Nombre": nombre, "Estado del cliente": "Nuevo"}
    if telefono:    campos["Teléfono"] = telefono
    if interes:     campos["Propiedades interesadas"] = interes
    # Presupuesto y origen van en Notas (no tienen columna propia)
    nota_extra = ""
    if presupuesto: nota_extra += f"Presupuesto: {presupuesto}. "
    if origen:      nota_extra += f"Origen: {origen}. "
    if notas:       nota_extra += notas
    if nota_extra:  campos["Notas"] = nota_extra.strip()
    r = tabla.create(campos)
    return f"Cliente registrado. ID: {r['id']} | {nombre}"


def _actualizar_cliente(
    record_id: str,
    estado: str | None = None,
    notas: str | None = None,
    siguiente_accion: str | None = None,
) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    campos: dict[str, Any] = {}
    if estado:           campos["Estado del cliente"] = estado
    if notas:            campos["Notas"] = notas
    if siguiente_accion: campos["Notas"] = (campos.get("Notas", "") + f" | Próximo: {siguiente_accion}").strip(" |")
    if not campos:
        return "No se proporcionaron campos para actualizar."
    tabla.update(record_id, campos)
    return f"Cliente {record_id} actualizado."


def _listar_propiedades(
    tipo: str | None = None,
    estado: str | None = None,
    limite: int = 10,
) -> str:
    tabla = _get_table(AIRTABLE_PROPIEDADES_TABLE)
    partes: list[str] = []
    if tipo:   partes.append(f"{{Tipo}}='{tipo}'")
    if estado: partes.append(f"{{Estado}}='{estado}'")
    formula = f"AND({', '.join(partes)})" if partes else None
    registros = tabla.all(formula=formula, max_records=limite)
    if not registros:
        return "No se encontraron propiedades."
    lineas = [f"Propiedades ({len(registros)}):"]
    for r in registros:
        f = r["fields"]
        lineas.append(
            f"• [{r['id']}] {f.get('Nombre de la propiedad', '—')} | "
            f"{f.get('Tipo', '—')} | Estado: {f.get('Estado', '—')} | "
            f"Hab: {f.get('Habitaciones', '—')} | Baños: {f.get('Baños', '—')} | "
            f"Zona: {f.get('Ubicación', '—')}"
        )
    return "\n".join(lineas)


def _crear_propiedad(
    nombre: str,
    tipo: str,
    operacion: str = "Venta",
    precio: float = 0,
    ubicacion: str = "",
    habitaciones: int = 0,
    banos: float = 0,
    m2: float = 0,
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_PROPIEDADES_TABLE)
    campos: dict[str, Any] = {
        "Nombre de la propiedad": nombre,
        "Tipo": tipo,
        "Estado": "Disponible",
    }
    if ubicacion:    campos["Ubicación"] = ubicacion
    if habitaciones: campos["Habitaciones"] = habitaciones
    if banos:        campos["Baños"] = banos
    # Precio, M2 y operación van en Notas
    extra = f"{operacion}. "
    if precio: extra += f"Precio: ${precio:,.0f}. "
    if m2:     extra += f"M2: {m2}. "
    if notas:  extra += notas
    if extra:  campos["Notas"] = extra.strip()
    r = tabla.create(campos)
    return f"Propiedad '{nombre}' registrada. ID: {r['id']}"


def _listar_marketing(limite: int = 10) -> str:
    tabla = _get_table(AIRTABLE_MARKETING_TABLE)
    try:
        registros = tabla.all(max_records=limite)
    except Exception as e:
        return f"Error al leer Marketing_FBR: {e}"
    if not registros:
        return "No hay registros de marketing."
    lineas = [f"Marketing ({len(registros)}):"]
    for r in registros:
        f = r["fields"]
        lineas.append(f"• {list(f.values())[:3]}")
    return "\n".join(lineas)


def _registrar_accion_marketing(
    titulo: str,
    canal: str,
    tipo: str = "Post",
    propiedad_relacionada: str = "",
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_MARKETING_TABLE)
    # Intentar con campos genéricos — si falla, crear con lo disponible
    try:
        campos: dict[str, Any] = {"Notas": f"{titulo} | {canal} | {tipo}"}
        if propiedad_relacionada: campos["Notas"] += f" | {propiedad_relacionada}"
        if notas: campos["Notas"] += f" | {notas}"
        r = tabla.create(campos)
        return f"Acción '{titulo}' registrada. ID: {r['id']}"
    except Exception as e:
        return f"Error registrando marketing: {e}"


def _reporte_clientes() -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    todos = tabla.all()
    if not todos:
        return "No hay clientes en el sistema."
    estados: dict[str, int] = {}
    for r in todos:
        est = r["fields"].get("Estado del cliente", "Sin clasificar")
        estados[est] = estados.get(est, 0) + 1
    total = len(todos)
    cerrados = estados.get("Cerrado", 0)
    lineas = [
        f"Total clientes: {total}",
        f"Tasa de conversión: {cerrados/total*100:.1f}%",
        "\nPor estado:",
    ]
    for k, v in sorted(estados.items(), key=lambda x: -x[1]):
        lineas.append(f"  {k}: {v}")
    return "\n".join(lineas)
