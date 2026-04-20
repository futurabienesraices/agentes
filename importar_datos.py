#!/usr/bin/env python3
"""
importar_datos.py — Importa propiedades y clientes a Airtable en un solo paso.
Ejecuta: python3 importar_datos.py

Columnas reales detectadas:
  Propiedades_FBR: Nombre de la propiedad, Tipo, Estado, Habitaciones, Baños, Ubicación, Notas
  Clientes_FBR:    Nombre, Teléfono, Estado del cliente, Propiedades interesadas, Notas
"""
from dotenv import load_dotenv
load_dotenv()

import os
from pyairtable import Api

api = Api(os.environ["AIRTABLE_API_KEY"])
tbl_prop = api.table(os.getenv("AIRTABLE_BASE_PROPIEDADES", "appqYlISCjGnla9EN"), "Propiedades_FBR")
tbl_cli  = api.table(os.getenv("AIRTABLE_BASE_CLIENTES",    "appb4XJ04yi27i2X4"), "Clientes_FBR")

GREEN, RED, YELLOW, NC = "\033[92m", "\033[91m", "\033[93m", "\033[0m"
def ok(m):  print(f"{GREEN}  ✓{NC} {m}")
def err(m): print(f"{RED}  ✗{NC} {m}")
def inf(m): print(f"{YELLOW}  →{NC} {m}")

# ── PROPIEDADES ───────────────────────────────────────────────
# Columnas: Nombre de la propiedad, Tipo, Estado, Habitaciones, Baños, Ubicación, Notas
# Precio / M2 / Operación van en Notas (no tienen columna propia)

PROPIEDADES = [
    {
        "Nombre de la propiedad": "Casa El Trébol - Villeda",
        "Tipo": "Casa", "Estado": "Disponible",
        "Habitaciones": 3, "Baños": 2,
        "Ubicación": "Urb. El Trébol III y IV, Santa Ana",
        "Notas": "Venta $100,000 | 70m² lote | 3 niveles. 3ra planta: cuarto máster vista 360°. 2da: hab con baño. 1ra: 2 hab, baño social, sala, comedor-cocina, patio. Techo Sincalum 2021. 120/220V. Tel: 6027-2418",
    },
    {
        "Nombre de la propiedad": "Casa Residencial Las Mercedes",
        "Tipo": "Casa", "Estado": "Disponible",
        "Habitaciones": 5, "Baños": 4,
        "Ubicación": "Residencial Las Mercedes, Santa Ana",
        "Notas": "Venta $230,000 | 236m² | 5 hab + 1 servicio, sala, comedor formal, cocina amplia, área cine, garage 2 vehículos, patio, cisterna, agua caliente, A/C. Minutos de Metrocentro. Tel: 6027-2418",
    },
    {
        "Nombre de la propiedad": "Casa Cantón Primavera - Gerardo",
        "Tipo": "Casa", "Estado": "Disponible",
        "Habitaciones": 4, "Baños": 1,
        "Ubicación": "Cantón Primavera, Santa Ana",
        "Notas": "Venta $80,000 (mínimo $60-65k) | 469m² esquinero | Avalúo $75k. Ideal remodelar. Comisión 5%. GPS: 13.973622,-89.538162",
    },
    {
        "Nombre de la propiedad": "Auto Hotel San Miguelito",
        "Tipo": "Local", "Estado": "Disponible",
        "Habitaciones": 15, "Baños": 8,
        "Ubicación": "By Pass Los 44 (a la par VIDRI), Santa Ana",
        "Notas": "Venta $465,000 negociable | 538.76m² terreno, 370.62m² construcción | 6 hab operativas generan $1,600-1,800/mes. 6 cocheras. Se vende a puerta cerrada.",
    },
    {
        "Nombre de la propiedad": "Terreno Santa Teresa - Lote 8x20",
        "Tipo": "Terreno", "Estado": "Disponible",
        "Ubicación": "Lotificación Santa Teresa, Santa Ana",
        "Notas": "Venta $19,000 | 160m² (8x20). Prima mínima $5,000. Financiamiento 5 años al 15% anual. Acceso Carretera Panamericana.",
    },
    {
        "Nombre de la propiedad": "Terreno Santa Teresa - Esquina Etapa 3 (11x20)",
        "Tipo": "Terreno", "Estado": "Disponible",
        "Ubicación": "Lotificación Santa Teresa Etapa 3, Santa Ana",
        "Notas": "Venta $30,000 negociable | 220m² esquinero (11x20). Prima $15k, saldo $15k a 5 años 15%. GPS: 13.957942,-89.583138",
    },
    {
        "Nombre de la propiedad": "Terreno Santa Teresa - Etapa 3 (8x21)",
        "Tipo": "Terreno", "Estado": "Disponible",
        "Ubicación": "Lotificación Santa Teresa Etapa 3, Santa Ana",
        "Notas": "Venta $30,000 negociable | 168m² (8x21). Prima $15k, saldo $15k a 5 años 15%. GPS: 13.958550,-89.582306",
    },
    {
        "Nombre de la propiedad": "Terreno Lot. Los Amates - San Sebastián",
        "Tipo": "Terreno", "Estado": "Disponible",
        "Ubicación": "Lot. Los Amates, San Sebastián Salitrillo, Santa Ana",
        "Notas": "Venta $40,000 (mínimo $36k) | 480m² lote plano. Divisible en 3 lotes de 8x20. Avalúo $25,033. GPS: 13.993799,-89.646660",
    },
    {
        "Nombre de la propiedad": "Casa San Nicolás",
        "Tipo": "Casa", "Estado": "Disponible",
        "Habitaciones": 2, "Baños": 3,
        "Ubicación": "San Nicolás, Santa Ana",
        "Notas": "Venta $100,000 negociable | 2 hab con baño propio + baño social. Sala-cocina-comedor integrados. 1.5 años construida. Hipoteca Promerica ~$70k. Biodigestor.",
    },
    {
        "Nombre de la propiedad": "Cuarto en Alquiler - Calle Samaria",
        "Tipo": "Departamento", "Estado": "Disponible",
        "Ubicación": "Calle Samaria, Santa Ana",
        "Notas": "Renta | Actualmente ocupado. Alta demanda recurrente al desocupar. Registrado para seguimiento.",
    },
]

# ── CLIENTES ─────────────────────────────────────────────────
# Columnas: Nombre, Teléfono, Estado del cliente, Propiedades interesadas, Notas
# Presupuesto y Origen van en Notas

CLIENTES = [
    {"Nombre": "Griss",             "Teléfono": "7578-3181",        "Propiedades interesadas": "Lote / Terreno esquinero"},
    {"Nombre": "Y M",               "Teléfono": "7210-5658",        "Propiedades interesadas": "Lote segunda etapa"},
    {"Nombre": "Angélica",          "Teléfono": "7951-1670",        "Propiedades interesadas": "Finca Mezquita"},
    {"Nombre": "Rebeca",            "Teléfono": "7403-2900",        "Propiedades interesadas": "Terreno esquinero",        "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Lissette Marroquín","Teléfono": "7201-2400",        "Propiedades interesadas": "Locales comerciales"},
    {"Nombre": "Erick",             "Teléfono": "7371-1215",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $230,000"},
    {"Nombre": "Zoé",               "Teléfono": "+32 492 85 76 39", "Propiedades interesadas": "Terreno",                  "Notas": "Presupuesto: $30,000. Origen: Exterior"},
    {"Nombre": "Miguel Rosales",    "Teléfono": "7052-0772",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $90,000"},
    {"Nombre": "Álvaro",            "Teléfono": "+1 (213) 858-1254","Propiedades interesadas": "Santa Teresa",             "Notas": "Desde EE.UU."},
    {"Nombre": "Josué",             "Teléfono": "7382-4046",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Lorena",            "Teléfono": "7802-5747",        "Propiedades interesadas": "Santa Teresa"},
    {"Nombre": "Wilbur",            "Teléfono": "7855-6284",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $90,000"},
    {"Nombre": "La chata",          "Teléfono": "6934-3520",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Celina",            "Teléfono": "6051-2274",        "Propiedades interesadas": "Varias propiedades"},
    {"Nombre": "Sierva de Dios",    "Teléfono": "7122-3920",        "Propiedades interesadas": "Locales cómodos"},
    {"Nombre": "Samuel",            "Teléfono": "+1(574) 368-7955", "Propiedades interesadas": "Terreno",                  "Notas": "Presupuesto: $9,000. Desde EE.UU."},
    {"Nombre": "Ely García",        "Teléfono": "7849-8633",        "Propiedades interesadas": "Locales comerciales"},
    {"Nombre": "Alma",              "Teléfono": "+1(405) 882-8539", "Propiedades interesadas": "Santa Teresa",             "Notas": "Desde EE.UU."},
    {"Nombre": "Ive",               "Teléfono": "7965-7241"},
    {"Nombre": "Wilberto",          "Teléfono": "7757-6087",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Carlos Beltrán",    "Teléfono": "7520-9970"},
    {"Nombre": "Hugo Aguilar",      "Teléfono": "7671-6078",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "José Andrade",      "Teléfono": "+1 (202) 322-5275","Propiedades interesadas": "Santa Teresa",             "Notas": "Desde EE.UU."},
    {"Nombre": "Estefanía",         "Teléfono": "7743-6850"},
    {"Nombre": "Gerardo",           "Teléfono": "7081-0996",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Carlos Trejo",      "Teléfono": "7214-3491"},
    {"Nombre": "Hermès Abrego",     "Teléfono": "+1(970) 888-1642", "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $75,000. Desde EE.UU."},
    {"Nombre": "Jesús Constanza",   "Teléfono": "7802-6620"},
    {"Nombre": "Thefa",             "Teléfono": "6011-8129"},
    {"Nombre": "Maura de Aguilar",  "Teléfono": "7109-5063"},
    {"Nombre": "Margarita",         "Teléfono": "+1 (415) 691-9534","Notas": "Desde EE.UU."},
    {"Nombre": "Miguel Mena",       "Teléfono": "7711-5667"},
    {"Nombre": "Jorge Alejandro",   "Teléfono": "+1(818) 235-9303", "Notas": "Desde EE.UU."},
    {"Nombre": "Karla Ramírez",     "Teléfono": "7605-7129"},
    # Clientes ya en Airtable — actualizar con teléfono e interés
    {"Nombre": "Dora Corado",       "Teléfono": "+1 (825) 735-1784","Propiedades interesadas": "Lote Santa Teresa",        "Notas": "Desde Canadá"},
    {"Nombre": "Ernesto",           "Teléfono": "7048-2622",        "Propiedades interesadas": "Casas económicas"},
    {"Nombre": "Carmen Morán",      "Teléfono": "7551-4856",        "Propiedades interesadas": "Santa Teresa financiado"},
    {"Nombre": "Adriana",           "Teléfono": "6039-3222",        "Propiedades interesadas": "Casa en renta"},
    {"Nombre": "Silvia",            "Teléfono": "6166-7949",        "Propiedades interesadas": "Santa Teresa"},
    {"Nombre": "José Sánchez",      "Teléfono": "7550-9531",        "Propiedades interesadas": "Casa",                     "Notas": "Mediano plazo"},
    {"Nombre": "Erika",             "Teléfono": "6073-3781",        "Propiedades interesadas": "Santa Teresa"},
    {"Nombre": "Oscar",             "Teléfono": "6823-7238",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Norma",             "Teléfono": "6007-9368",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Ana Torres",        "Teléfono": "7389-9044",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $60,000 disponible"},
    {"Nombre": "Leo",               "Teléfono": "7996-0547",        "Propiedades interesadas": "Casa",                     "Notas": "Presupuesto: $80,000"},
    {"Nombre": "Luis",              "Teléfono": "7064-8556",        "Propiedades interesadas": "Casa"},
    {"Nombre": "Moisés Matel",      "Teléfono": "7233-2992",        "Notas": "Da casa en parte de pago"},
    {"Nombre": "Eduardo",           "Teléfono": "7553-4561",        "Propiedades interesadas": "Santa Teresa / Lotes"},
    {"Nombre": "José Ramos",        "Teléfono": "7028-3110",        "Propiedades interesadas": "Casa"},
]

# ── IMPORTAR PROPIEDADES ──────────────────────────────────────
print("\n=== IMPORTANDO PROPIEDADES ===")
existentes_prop = {
    r["fields"].get("Nombre de la propiedad", "")
    for r in tbl_prop.all()
}

for p in PROPIEDADES:
    nombre = p["Nombre de la propiedad"]
    if nombre in existentes_prop:
        inf(f"Ya existe: {nombre}")
        continue
    try:
        tbl_prop.create(p)
        ok(nombre)
    except Exception as e:
        err(f"{nombre}: {e}")

# ── IMPORTAR/ACTUALIZAR CLIENTES ──────────────────────────────
print("\n=== ACTUALIZANDO / IMPORTANDO CLIENTES ===")
existentes_cli = {}
for r in tbl_cli.all():
    nombre = r["fields"].get("Nombre", "").strip()
    if nombre:
        existentes_cli[nombre] = r["id"]

for c in CLIENTES:
    nombre = c["Nombre"]
    campos = {"Estado del cliente": "Nuevo"}
    if c.get("Teléfono"):                campos["Teléfono"] = c["Teléfono"]
    if c.get("Propiedades interesadas"): campos["Propiedades interesadas"] = c["Propiedades interesadas"]
    if c.get("Notas"):                   campos["Notas"] = c["Notas"]
    try:
        if nombre in existentes_cli:
            tbl_cli.update(existentes_cli[nombre], {k: v for k, v in campos.items() if k != "Estado del cliente"})
            inf(f"Actualizado: {nombre}")
        else:
            campos["Nombre"] = nombre
            tbl_cli.create(campos)
            ok(f"Creado: {nombre}")
    except Exception as e:
        err(f"{nombre}: {e}")

print("\n✅ Importación completa.\n")
