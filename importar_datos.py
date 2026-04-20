#!/usr/bin/env python3
"""
importar_datos.py — Importa propiedades y clientes a Airtable en un solo paso.
Ejecuta: python3 importar_datos.py
"""
from dotenv import load_dotenv
load_dotenv()

import os
from pyairtable import Api

api = Api(os.environ["AIRTABLE_API_KEY"])
tbl_prop = api.table(os.getenv("AIRTABLE_BASE_PROPIEDADES", "appqYlISCjGnla9EN"), "Propiedades_FBR")
tbl_cli  = api.table(os.getenv("AIRTABLE_BASE_CLIENTES",    "appb4XJ04yi27i2X4"), "Clientes_FBR")

# ── PROPIEDADES ───────────────────────────────────────────────
PROPIEDADES = [
    {
        "Titulo": "Casa El Trébol - Villeda",
        "Tipo": "Casa", "Operacion": "Venta", "Precio": 50000,
        "Zona": "Urb. El Trébol III y IV, Santa Ana",
        "Recamaras": 3, "Banos": 2, "M2": 70, "Estado": "Disponible",
        "Descripcion": (
            "3 niveles. 3ra planta: cuarto máster con vista 360°. 2da planta: hab con baño. "
            "1ra planta: 2 hab, baño social, sala, comedor-cocina, patio. "
            "Techo Sincalum 2021. 120/220V. Tel: 6027-2418"
        ),
    },
    {
        "Titulo": "Casa Residencial Las Mercedes",
        "Tipo": "Casa", "Operacion": "Venta", "Precio": 230000,
        "Zona": "Residencial Las Mercedes, Santa Ana",
        "Recamaras": 5, "Banos": 4, "M2": 236, "Estado": "Disponible",
        "Descripcion": (
            "236m². 5 hab + 1 servicio. Sala, comedor formal, cocina amplia, área cine, "
            "garage 2 vehículos, patio, cisterna, agua caliente, A/C. "
            "Minutos de Metrocentro. Tel: 6027-2418"
        ),
    },
    {
        "Titulo": "Casa Cantón Primavera - Gerardo",
        "Tipo": "Casa", "Operacion": "Venta", "Precio": 80000,
        "Zona": "Cantón Primavera, Santa Ana",
        "Recamaras": 4, "Banos": 1, "M2": 469, "Estado": "Disponible",
        "Descripcion": (
            "Terreno esquinero 469m². 4 hab, 1 baño, sala, comedor-cocina, garage. "
            "Ideal remodelar. Avalúo $75k. Mínimo aceptable $60-65k. Comisión 5%. "
            "GPS: 13.973622,-89.538162"
        ),
    },
    {
        "Titulo": "Auto Hotel San Miguelito",
        "Tipo": "Local", "Operacion": "Venta", "Precio": 465000,
        "Zona": "Urb. San Miguelito, By Pass Los 44, Santa Ana",
        "Recamaras": 15, "Banos": 8, "M2": 539, "Estado": "Disponible",
        "Descripcion": (
            "15 habitaciones (6 operativas). Genera $1,600-1,800/mes. "
            "Construcción 370.62m², terreno 538.76m². 6 cocheras, bodega, patio, oficina. "
            "Se vende a puerta cerrada (aires, camas, lavadora, cámaras). Precio negociable."
        ),
    },
    {
        "Titulo": "Terreno Santa Teresa - Lote 8x20",
        "Tipo": "Terreno", "Operacion": "Venta", "Precio": 19000,
        "Zona": "Lotificación Santa Teresa, Santa Ana",
        "M2": 160, "Estado": "Disponible",
        "Descripcion": "8m x 20m. Prima mínima $5,000. Financiamiento 5 años al 15% anual. Carretera Panamericana.",
    },
    {
        "Titulo": "Terreno Santa Teresa - Esquina Etapa 3 (11x20)",
        "Tipo": "Terreno", "Operacion": "Venta", "Precio": 30000,
        "Zona": "Lotificación Santa Teresa Etapa 3, Santa Ana",
        "M2": 220, "Estado": "Disponible",
        "Descripcion": "Lote esquinero 11x20m. Prima $15k, saldo $15k a 5 años al 15%. Negociable. GPS: 13.957942,-89.583138",
    },
    {
        "Titulo": "Terreno Santa Teresa - Etapa 3 (8x21)",
        "Tipo": "Terreno", "Operacion": "Venta", "Precio": 30000,
        "Zona": "Lotificación Santa Teresa Etapa 3, Santa Ana",
        "M2": 168, "Estado": "Disponible",
        "Descripcion": "8x21m. Prima $15k, saldo $15k a 5 años al 15%. Negociable. GPS: 13.958550,-89.582306",
    },
    {
        "Titulo": "Terreno Lot. Los Amates - San Sebastián",
        "Tipo": "Terreno", "Operacion": "Venta", "Precio": 40000,
        "Zona": "Lot. Los Amates, San Sebastián Salitrillo, Santa Ana",
        "M2": 480, "Estado": "Disponible",
        "Descripcion": (
            "480m². Lote plano, puede dividirse en 3 lotes de 8x20. "
            "Avalúo $25,033. Mínimo $36k. GPS: 13.993799,-89.646660"
        ),
    },
    {
        "Titulo": "Casa San Nicolás",
        "Tipo": "Casa", "Operacion": "Venta", "Precio": 100000,
        "Zona": "San Nicolás, Santa Ana",
        "Recamaras": 2, "Banos": 3, "Estado": "Disponible",
        "Descripcion": (
            "2 hab con baño propio + baño social. Sala-cocina-comedor integrados. "
            "1.5 años construida. Hipoteca Promerica ~$70k. 120/220V, internet, cable, biodigestor. Negociable."
        ),
    },
    {
        "Titulo": "Cuarto en Alquiler - Calle Samaria",
        "Tipo": "Departamento", "Operacion": "Renta", "Precio": 0,
        "Zona": "Calle Samaria, Santa Ana",
        "Estado": "Disponible",
        "Descripcion": "Actualmente ocupado. Cuando desocupe hay demanda recurrente. Registrado para seguimiento.",
    },
]

# ── CLIENTES ─────────────────────────────────────────────────
CLIENTES_NUEVOS = [
    {"Nombre": "Griss",            "Telefono": "7578-3181",        "Interes": "Lote / Terreno esquinero",    "Presupuesto": ""},
    {"Nombre": "Y M",              "Telefono": "7210-5658",        "Interes": "Lote segunda etapa",          "Presupuesto": ""},
    {"Nombre": "Angélica",         "Telefono": "7951-1670",        "Interes": "Finca Mezquita",              "Presupuesto": ""},
    {"Nombre": "Rebeca",           "Telefono": "7403-2900",        "Interes": "Terreno esquinero",           "Presupuesto": "$80,000"},
    {"Nombre": "Lissette Marroquín","Telefono": "7201-2400",       "Interes": "Locales comerciales",         "Presupuesto": ""},
    {"Nombre": "Erick",            "Telefono": "7371-1215",        "Interes": "Casa",                        "Presupuesto": "$230,000"},
    {"Nombre": "Zoé",              "Telefono": "+32 492 85 76 39", "Interes": "Terreno",                     "Presupuesto": "$30,000",  "Origen": "Otro"},
    {"Nombre": "Miguel Rosales",   "Telefono": "7052-0772",        "Interes": "Casa",                        "Presupuesto": "$90,000"},
    {"Nombre": "Álvaro",           "Telefono": "+1 (213) 858-1254","Interes": "Santa Teresa",                "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Josué",            "Telefono": "7382-4046",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Lorena",           "Telefono": "7802-5747",        "Interes": "Santa Teresa",                "Presupuesto": ""},
    {"Nombre": "Wilbur",           "Telefono": "7855-6284",        "Interes": "Casa",                        "Presupuesto": "$90,000"},
    {"Nombre": "La chata",         "Telefono": "6934-3520",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Celina",           "Telefono": "6051-2274",        "Interes": "Varias propiedades",          "Presupuesto": ""},
    {"Nombre": "Sierva de Dios",   "Telefono": "7122-3920",        "Interes": "Locales cómodos",             "Presupuesto": ""},
    {"Nombre": "Samuel",           "Telefono": "+1(574) 368-7955", "Interes": "Terreno",                     "Presupuesto": "$9,000",   "Origen": "Otro"},
    {"Nombre": "Ely García",       "Telefono": "7849-8633",        "Interes": "Locales comerciales",         "Presupuesto": ""},
    {"Nombre": "Alma",             "Telefono": "+1(405) 882-8539", "Interes": "Santa Teresa",                "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Ive",              "Telefono": "7965-7241",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Wilberto",         "Telefono": "7757-6087",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Carlos Beltrán",   "Telefono": "7520-9970",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Hugo Aguilar",     "Telefono": "7671-6078",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "José Andrade",     "Telefono": "+1 (202) 322-5275","Interes": "Santa Teresa",                "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Estefanía",        "Telefono": "7743-6850",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Gerardo",          "Telefono": "7081-0996",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Carlos Trejo",     "Telefono": "7214-3491",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Hermès Abrego",    "Telefono": "+1(970) 888-1642", "Interes": "Casa",                        "Presupuesto": "$75,000",  "Origen": "Otro"},
    {"Nombre": "Jesús Constanza",  "Telefono": "7802-6620",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Thefa",            "Telefono": "6011-8129",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Maura de Aguilar", "Telefono": "7109-5063",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Margarita",        "Telefono": "+1 (415) 691-9534","Interes": "",                            "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Miguel Mena",      "Telefono": "7711-5667",        "Interes": "",                            "Presupuesto": ""},
    {"Nombre": "Jorge Alejandro",  "Telefono": "+1(818) 235-9303", "Interes": "",                            "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Karla Ramírez",    "Telefono": "7605-7129",        "Interes": "",                            "Presupuesto": ""},
    # Clientes ya existentes — actualizamos teléfono e interés
    {"Nombre": "Dora Corado",      "Telefono": "+1 (825) 735-1784","Interes": "Lote Santa Teresa",           "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Ernesto",          "Telefono": "7048-2622",        "Interes": "Casas económicas/limitadas",  "Presupuesto": ""},
    {"Nombre": "Carmen Morán",     "Telefono": "7551-4856",        "Interes": "Santa Teresa financiado",     "Presupuesto": ""},
    {"Nombre": "Adriana",          "Telefono": "6039-3222",        "Interes": "Casa en renta",               "Presupuesto": ""},
    {"Nombre": "Silvia",           "Telefono": "6166-7949",        "Interes": "Santa Teresa",                "Presupuesto": ""},
    {"Nombre": "José Sánchez",     "Telefono": "7550-9531",        "Interes": "Casa",                        "Notas": "Mediano plazo"},
    {"Nombre": "Erika",            "Telefono": "6073-3781",        "Interes": "Santa Teresa",                "Presupuesto": ""},
    {"Nombre": "Oscar",            "Telefono": "6823-7238",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Norma",            "Telefono": "6007-9368",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Ana Torres",       "Telefono": "7389-9044",        "Interes": "Casa",                        "Presupuesto": "$60,000"},
    {"Nombre": "Álvaro",           "Telefono": "+1 (213) 858-1254","Interes": "Santa Teresa",                "Presupuesto": "",         "Origen": "Otro"},
    {"Nombre": "Leo",              "Telefono": "7996-0547",        "Interes": "Casa",                        "Presupuesto": "$80,000"},
    {"Nombre": "Luis",             "Telefono": "7064-8556",        "Interes": "Compra casa",                 "Presupuesto": ""},
    {"Nombre": "Moisés Matel",     "Telefono": "7233-2992",        "Notas": "Da casa en parte de pago",      "Presupuesto": ""},
    {"Nombre": "Eduardo",          "Telefono": "7553-4561",        "Interes": "Santa Teresa",                "Presupuesto": ""},
    {"Nombre": "José Ramos",       "Telefono": "7028-3110",        "Interes": "Casa",                        "Presupuesto": ""},
]

# ── IMPORTAR ──────────────────────────────────────────────────
GREEN, RED, YELLOW, NC = "\033[92m", "\033[91m", "\033[93m", "\033[0m"

def ok(msg):  print(f"{GREEN}  ✓{NC} {msg}")
def err(msg): print(f"{RED}  ✗{NC} {msg}")
def inf(msg): print(f"{YELLOW}  →{NC} {msg}")


print("\n=== IMPORTANDO PROPIEDADES ===")
# Verificar cuáles ya existen
existentes_prop = {r["fields"].get("Titulo", "") for r in tbl_prop.all(fields=["Titulo"])}

for p in PROPIEDADES:
    if p["Titulo"] in existentes_prop:
        inf(f"Ya existe: {p['Titulo']}")
        continue
    try:
        campos = {k: v for k, v in p.items() if v not in (None, "", 0) or k in ("Precio",)}
        tbl_prop.create(campos)
        ok(p["Titulo"])
    except Exception as e:
        err(f"{p['Titulo']}: {e}")


print("\n=== ACTUALIZANDO / IMPORTANDO CLIENTES ===")
# Construir índice de clientes existentes por nombre
existentes_cli = {}
for r in tbl_cli.all(fields=["Nombre", "Telefono"]):
    nombre = r["fields"].get("Nombre", "").strip()
    if nombre:
        existentes_cli[nombre] = r["id"]

for c in CLIENTES_NUEVOS:
    nombre = c["Nombre"]
    campos = {"Estado": "Nuevo", "Origen": c.get("Origen", "WhatsApp")}
    if c.get("Telefono"): campos["Telefono"] = c["Telefono"]
    if c.get("Interes"):  campos["Interes"]  = c["Interes"]
    if c.get("Presupuesto") and c["Presupuesto"]: campos["Presupuesto"] = c["Presupuesto"]
    if c.get("Notas"):    campos["Notas"]    = c["Notas"]

    try:
        if nombre in existentes_cli:
            # Actualizar teléfono e interés si faltan
            tbl_cli.update(existentes_cli[nombre], {k: v for k, v in campos.items() if k not in ("Estado",)})
            inf(f"Actualizado: {nombre}")
        else:
            campos["Nombre"] = nombre
            tbl_cli.create(campos)
            ok(f"Creado: {nombre}")
    except Exception as e:
        err(f"{nombre}: {e}")

print("\n✅ Importación completa.\n")
