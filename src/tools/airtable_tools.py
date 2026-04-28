"""Herramientas para interactuar con Airtable — Futura Bienes Raíces."""
from __future__ import annotations
from typing import Any
from src.config import (
    AIRTABLE_API_KEY,
    AIRTABLE_BASE_CLIENTES, AIRTABLE_BASE_MARKETING, AIRTABLE_BASE_PROPIEDADES,
    AIRTABLE_BASE_LEADS,
    AIRTABLE_PROPIEDADES_TABLE, AIRTABLE_MARKETING_TABLE, AIRTABLE_CLIENTES_TABLE,
    AIRTABLE_LEADS_TABLE,
)

# Columnas reales en Airtable (detectadas el 2025-04-20)
# Propiedades_FBR: Nombre de la propiedad, Tipo, Estado, Habitaciones, Baños, Ubicación, Notas
# Clientes_FBR:    Nombre, Teléfono, Estado del cliente, Propiedades interesadas, Notas
# Leads_FBR:       (reutiliza Clientes_FBR) Nombre, Teléfono, Estado del cliente,
#                  Propiedades interesadas, Notas  ← origen y propiedad en Notas

_TABLA_BASE = {
    AIRTABLE_CLIENTES_TABLE:    AIRTABLE_BASE_CLIENTES,
    AIRTABLE_MARKETING_TABLE:   AIRTABLE_BASE_MARKETING,
    AIRTABLE_PROPIEDADES_TABLE: AIRTABLE_BASE_PROPIEDADES,
    AIRTABLE_LEADS_TABLE:       AIRTABLE_BASE_LEADS,
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
                "estado":           {"type": "string", "description": "Nuevo, Contactado, Calificado, Agendado, Cerrado"},
                "notas":            {"type": "string"},
                "siguiente_accion": {"type": "string"},
                "fecha_visita":     {"type": "string", "description": "YYYY-MM-DD"},
                "hora_visita":      {"type": "string", "description": "HH:MM"},
                "estado_visita":    {"type": "string", "description": "Pendiente, Confirmada, Realizada, Cancelada"},
                "nivel_interes":    {"type": "string", "description": "Caliente, Tibio, Frío"},
                "origen":           {"type": "string"},
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
    {
        "name": "airtable_crear_lead",
        "description": (
            "Registra un nuevo lead (prospecto entrante) que respondió a un flyer, post o CTA. "
            "Guarda nombre, teléfono, propiedad de interés, canal de origen y mensaje original. "
            "Usar cuando un cliente escribe por WhatsApp, Instagram DM u otro canal."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "nombre":     {"type": "string", "description": "Nombre del prospecto"},
                "telefono":   {"type": "string", "description": "Teléfono o WhatsApp del prospecto"},
                "propiedad":  {"type": "string", "description": "ID o nombre de la propiedad que le interesó"},
                "canal":      {
                    "type": "string",
                    "enum": ["WhatsApp", "Instagram", "Facebook", "Referido", "Portal", "Otro"],
                    "description": "Canal por donde llegó el lead",
                },
                "intencion":  {
                    "type": "string",
                    "enum": ["Comprar", "Rentar", "Información", "Vender", "Invertir"],
                    "description": "Intención clasificada del lead",
                },
                "mensaje":    {"type": "string", "description": "Mensaje original del cliente (si se tiene)"},
                "notas":      {"type": "string", "description": "Notas adicionales del agente"},
            },
            "required": ["nombre"],
        },
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
        "airtable_crear_lead":             _crear_lead,
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
    fecha_visita: str | None = None,
    hora_visita: str | None = None,
    estado_visita: str | None = None,
    nivel_interes: str | None = None,
    origen: str | None = None,
) -> str:
    tabla = _get_table(AIRTABLE_CLIENTES_TABLE)
    campos: dict[str, Any] = {}
    if estado:           campos["Estado del cliente"] = estado
    if notas:            campos["Notas"] = notas
    if fecha_visita:     campos["Fecha Visita"] = fecha_visita
    if hora_visita:      campos["Hora Visita"] = hora_visita
    if estado_visita:    campos["Estado Visita"] = estado_visita
    if nivel_interes:    campos["Nivel de Interés"] = nivel_interes
    if origen:           campos["Origen"] = origen
    
    nota_extra = ""
    if siguiente_accion: nota_extra += f"Próximo: {siguiente_accion} | "
    # Como fallback seguro, inyectamos en notas lo que pueda fallar
    fallback = []
    if fecha_visita: fallback.append(f"Visita: {fecha_visita} {hora_visita or ''}")
    if estado_visita: fallback.append(f"Estado Visita: {estado_visita}")
    if nivel_interes: fallback.append(f"Interés: {nivel_interes}")
    if fallback: nota_extra += " | ".join(fallback)

    if nota_extra: 
        campos["Notas"] = (campos.get("Notas", "") + "\n--- Actualización ---\n" + nota_extra).strip()

    if not campos:
        return "No se proporcionaron campos para actualizar."
    try:
        tabla.update(record_id, campos)
        return f"Cliente {record_id} actualizado con éxito."
    except Exception as e:
        # Fallback si las columnas no existen (Error 422 Unprocessable Entity)
        if "422" in str(e):
            campos_seguros: dict[str, Any] = {}
            if estado: campos_seguros["Estado del cliente"] = estado
            if "Notas" in campos: campos_seguros["Notas"] = campos["Notas"]
            tabla.update(record_id, campos_seguros)
            return f"Cliente {record_id} actualizado (fallback de columnas a Notas)."
        return f"Error actualizando cliente: {e}"


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
    nuevos = 0
    calificados = 0
    agendados = 0
    
    for r in todos:
        f = r["fields"]
        est = f.get("Estado del cliente", "Sin clasificar")
        estados[est] = estados.get(est, 0) + 1
        
        # Conteo específico de métricas
        if est.lower() in ["nuevo", "nuevos"]:
            nuevos += 1
        elif est.lower() in ["calificado", "calificados"]:
            calificados += 1
        elif est.lower() in ["agendado", "agendados", "visita"]:
            agendados += 1
            
        # También chequear estado_visita en el payload
        if f.get("Estado Visita") in ["Pendiente", "Confirmada"]:
            agendados += 1

    total = len(todos)
    cerrados = estados.get("Cerrado", 0)
    lineas = [
        f"📊 MÉTRICAS DEL PIPELINE:",
        f"Total leads: {total}",
        f"• Nuevos: {nuevos}",
        f"• Calificados: {calificados}",
        f"• Visitas Agendadas: {agendados}",
        f"• Cerrados: {cerrados} (Tasa conv: {cerrados/total*100:.1f}%)",
        "\nDistribución general por estado:",
    ]
    for k, v in sorted(estados.items(), key=lambda x: -x[1]):
        lineas.append(f"  {k}: {v}")
    return "\n".join(lineas)


def _crear_lead(
    nombre: str,
    telefono: str = "",
    propiedad: str = "",
    canal: str = "",
    intencion: str = "Información",
    mensaje: str = "",
    notas: str = "",
) -> str:
    tabla = _get_table(AIRTABLE_LEADS_TABLE)
    campos: dict[str, Any] = {"Nombre": nombre, "Estado del cliente": "Nuevo"}
    if telefono: campos["Teléfono"] = telefono
    if propiedad: campos["Propiedades interesadas"] = propiedad
    
    nota_extra = f"Intención: {intencion}."
    if canal: nota_extra += f" Canal de origen: {canal}."
    if mensaje: nota_extra += f" Mensaje original: '{mensaje}'."
    if notas: nota_extra += f"\nNotas: {notas}"
    
    campos["Notas"] = nota_extra.strip()
    r = tabla.create(campos)
    return f"Lead registrado exitosamente. ID: {r['id']} | {nombre}"
