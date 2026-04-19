"""Configuración central del sistema de agentes."""
import os
from dotenv import load_dotenv

load_dotenv()

# ── Claude ───────────────────────────────────────────────────────
ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
MODELO_PRINCIPAL = "claude-sonnet-4-6"
MODELO_RAPIDO = "claude-haiku-4-5-20251001"

# ── Airtable ─────────────────────────────────────────────────────
AIRTABLE_API_KEY = os.getenv("AIRTABLE_API_KEY", "")
AIRTABLE_BASE_ID = os.getenv("AIRTABLE_BASE_ID", "")
AIRTABLE_LEADS_TABLE = os.getenv("AIRTABLE_LEADS_TABLE", "Leads")
AIRTABLE_PROPIEDADES_TABLE = os.getenv("AIRTABLE_PROPIEDADES_TABLE", "Propiedades")
AIRTABLE_CLIENTES_TABLE = os.getenv("AIRTABLE_CLIENTES_TABLE", "Clientes")

# ── Notion ───────────────────────────────────────────────────────
NOTION_API_KEY = os.getenv("NOTION_API_KEY", "")
NOTION_PROPIEDADES_DB_ID = os.getenv("NOTION_PROPIEDADES_DB_ID", "")
NOTION_TAREAS_DB_ID = os.getenv("NOTION_TAREAS_DB_ID", "")

# ── Google Drive ─────────────────────────────────────────────────
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "credentials.json")
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID", "")

# ── Meta (Facebook / Instagram) ──────────────────────────────────
META_ACCESS_TOKEN = os.getenv("META_ACCESS_TOKEN", "")
META_PAGE_ID = os.getenv("META_PAGE_ID", "")
META_IG_ACCOUNT_ID = os.getenv("META_IG_ACCOUNT_ID", "")

# ── Negocio ──────────────────────────────────────────────────────
EMPRESA_NOMBRE = os.getenv("EMPRESA_NOMBRE", "Futura Bienes Raíces")
EMPRESA_CIUDAD = os.getenv("EMPRESA_CIUDAD", "México")
