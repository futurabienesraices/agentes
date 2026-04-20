#!/usr/bin/env python3
"""
verificar.py — Verifica que todas las integraciones estén configuradas.
Ejecuta: python verificar.py
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

GREEN  = "\033[92m"
YELLOW = "\033[93m"
RED    = "\033[91m"
BOLD   = "\033[1m"
NC     = "\033[0m"

ok   = lambda msg: print(f"{GREEN}  ✓{NC} {msg}")
warn = lambda msg: print(f"{YELLOW}  ⚠{NC}  {msg}")
fail = lambda msg: print(f"{RED}  ✗{NC} {msg}")

resultados = {"ok": 0, "warn": 0, "fail": 0}

def check(nombre, fn):
    try:
        fn()
        ok(nombre)
        resultados["ok"] += 1
    except Exception as e:
        fail(f"{nombre}: {e}")
        resultados["fail"] += 1

def check_var(nombre, var, opcional=False):
    val = os.getenv(var, "")
    if val and not val.endswith("...") and len(val) > 5:
        ok(f"{nombre} configurado")
        resultados["ok"] += 1
        return True
    elif opcional:
        warn(f"{nombre} no configurado (opcional)")
        resultados["warn"] += 1
        return False
    else:
        fail(f"{nombre} falta — variable: {var}")
        resultados["fail"] += 1
        return False

print(f"\n{BOLD}================================================{NC}")
print(f"{BOLD}   Verificando integraciones del sistema...{NC}")
print(f"{BOLD}================================================{NC}\n")

# ── OBLIGATORIO ───────────────────────────────────────────────
print(f"{BOLD}[ OBLIGATORIO ]{NC}")
anthropic_ok = check_var("Anthropic API Key", "ANTHROPIC_API_KEY")

if anthropic_ok:
    def test_claude():
        import anthropic
        c = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        r = c.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=10,
            messages=[{"role": "user", "content": "di hola"}]
        )
        assert r.content
    check("Conexión con Claude API", test_claude)

print()

# ── AIRTABLE ─────────────────────────────────────────────────
print(f"{BOLD}[ AIRTABLE ]{NC}")
at_key = check_var("Airtable API Key", "AIRTABLE_API_KEY")
at_base = check_var("Airtable Base ID", "AIRTABLE_BASE_ID")

if at_key and at_base:
    def test_airtable():
        from pyairtable import Api
        api = Api(os.environ["AIRTABLE_API_KEY"])
        base = api.base(os.environ["AIRTABLE_BASE_ID"])
        tablas = [t.name for t in base.tables()]
        esperadas = [
            os.getenv("AIRTABLE_CLIENTES_TABLE", "Clientes_FBR"),
            os.getenv("AIRTABLE_PROPIEDADES_TABLE", "Propiedades_FBR"),
            os.getenv("AIRTABLE_MARKETING_TABLE", "Marketing_FBR"),
        ]
        encontradas = [t for t in esperadas if t in tablas]
        faltantes = [t for t in esperadas if t not in tablas]
        if faltantes:
            raise Exception(f"Tablas no encontradas: {faltantes}. Disponibles: {tablas}")
    check("Conexión Airtable + tablas FBR", test_airtable)

print()

# ── NOTION ────────────────────────────────────────────────────
print(f"{BOLD}[ NOTION ]{NC}")
notion_key = check_var("Notion API Key", "NOTION_API_KEY", opcional=True)
if notion_key:
    check_var("Notion DB Propiedades", "NOTION_PROPIEDADES_DB_ID", opcional=True)
    check_var("Notion DB Tareas", "NOTION_TAREAS_DB_ID", opcional=True)
    def test_notion():
        from notion_client import Client
        c = Client(auth=os.environ["NOTION_API_KEY"])
        c.users.me()
    check("Conexión con Notion", test_notion)

print()

# ── META ─────────────────────────────────────────────────────
print(f"{BOLD}[ META — Facebook / Instagram ]{NC}")
meta_token = check_var("Meta Access Token", "META_ACCESS_TOKEN", opcional=True)
if meta_token:
    check_var("Facebook Page ID", "META_PAGE_ID", opcional=True)
    check_var("Instagram Account ID", "META_IG_ACCOUNT_ID", opcional=True)

print()

# ── GOOGLE DRIVE ─────────────────────────────────────────────
print(f"{BOLD}[ GOOGLE DRIVE ]{NC}")
google_file = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
if os.path.exists(google_file):
    ok(f"credentials.json encontrado")
    resultados["ok"] += 1
    check_var("Drive Folder ID", "GOOGLE_DRIVE_FOLDER_ID", opcional=True)
else:
    warn("credentials.json no encontrado (opcional — para Drive)")
    resultados["warn"] += 1

print()

# ── TRADING ──────────────────────────────────────────────────
print(f"{BOLD}[ TRADING ]{NC}")
alpaca_key = check_var("Alpaca API Key", "ALPACA_API_KEY", opcional=True)
if alpaca_key:
    modo = "PAPER" if os.getenv("ALPACA_PAPER", "true").lower() == "true" else "⚠️  REAL (dinero real)"
    warn(f"Modo Alpaca: {modo}")
    resultados["warn"] += 1

def test_yfinance():
    import yfinance as yf
    t = yf.Ticker("AAPL")
    h = t.history(period="1d")
    assert not h.empty
check("yfinance (datos de mercado gratis)", test_yfinance)

print()

# ── BÚSQUEDA WEB ─────────────────────────────────────────────
print(f"{BOLD}[ BÚSQUEDA WEB ]{NC}")
tavily = check_var("Tavily API Key", "TAVILY_API_KEY", opcional=True)
if not tavily:
    check_var("Brave Search API Key", "BRAVE_API_KEY", opcional=True)

print()

# ── HERRAMIENTAS DEL SISTEMA ──────────────────────────────────
print(f"{BOLD}[ HERRAMIENTAS DEL SISTEMA ]{NC}")
import shutil
if shutil.which("ffmpeg"):
    ok("FFmpeg instalado (edición de video)")
    resultados["ok"] += 1
else:
    warn("FFmpeg no instalado — necesario para el Agente Media\n     Instala con: brew install ffmpeg")
    resultados["warn"] += 1

try:
    import whisper
    ok("Whisper instalado (transcripción de audio)")
    resultados["ok"] += 1
except ImportError:
    warn("Whisper no instalado (opcional)\n     Instala con: pip install openai-whisper")
    resultados["warn"] += 1

try:
    from fpdf import FPDF
    ok("fpdf2 instalado (creación de ebooks)")
    resultados["ok"] += 1
except ImportError:
    warn("fpdf2 no instalado (opcional)\n     Instala con: pip install fpdf2")
    resultados["warn"] += 1

# ── RESUMEN ───────────────────────────────────────────────────
print(f"\n{BOLD}================================================{NC}")
total = sum(resultados.values())
print(f"  {GREEN}✓ OK:{NC}      {resultados['ok']}")
print(f"  {YELLOW}⚠  Opcionales:{NC} {resultados['warn']}")
print(f"  {RED}✗ Faltan:{NC}   {resultados['fail']}")
print(f"{BOLD}================================================{NC}")

if resultados["fail"] == 0:
    print(f"\n{GREEN}{BOLD}  Sistema listo. Ejecuta: python main.py{NC}\n")
elif resultados["fail"] == 1 and not os.getenv("ANTHROPIC_API_KEY"):
    print(f"\n{RED}  Solo falta la ANTHROPIC_API_KEY en el .env{NC}\n")
else:
    print(f"\n{YELLOW}  Agrega las keys faltantes en el archivo .env{NC}\n")
