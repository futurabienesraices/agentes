# Inicio Rápido — Equipo de Agentes IA

> Todo lo que necesitas para levantar el sistema en tu iMac.

---

## ✅ Lo que ya está listo (no tienes que hacer nada)

- Código completo de los 9 agentes en GitHub
- Herramientas de Airtable, Notion, Drive, Meta, Trading, Video/Media
- Workflows para Make.com y n8n
- Scripts de instalación y verificación

---

## 📋 Lo que TÚ debes hacer (en orden)

### PASO 1 — Clonar el repositorio

Abre Terminal en tu iMac y ejecuta:

```bash
cd ~/Documents
git clone https://github.com/futurabienesraices/agentes.git
cd agentes
git checkout claude/setup-business-environment-Ipc5k
```

---

### PASO 2 — Instalación automática

```bash
bash setup.sh
```

Este script instala automáticamente:
- Homebrew (si no lo tienes)
- Python 3 (si no lo tienes)
- FFmpeg para edición de video
- Todas las dependencias de Python
- Crea las carpetas `media/` y `proyectos/`
- Copia `.env.example` → `.env`

---

### PASO 3 — Configurar tus API keys

Abre el archivo `.env` en cualquier editor de texto y llena tus claves.

**Mínimo para arrancar (solo 3 líneas):**

```env
ANTHROPIC_API_KEY=sk-ant-...     ← console.anthropic.com
AIRTABLE_API_KEY=pat...           ← airtable.com/create/tokens
AIRTABLE_BASE_ID=app...           ← URL de tu base en Airtable
```

**Cómo encontrar cada key:**

| Key | Dónde obtenerla |
|-----|----------------|
| `ANTHROPIC_API_KEY` | [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys) |
| `AIRTABLE_API_KEY` | [airtable.com/create/tokens](https://airtable.com/create/tokens) — scopes: `data.records:read`, `data.records:write`, `schema.bases:read` |
| `AIRTABLE_BASE_ID` | Abre tu base en Airtable → copia el `appXXXX` de la URL |
| `TAVILY_API_KEY` | [app.tavily.com](https://app.tavily.com) — gratis, para búsqueda web |
| `ALPACA_API_KEY` | [alpaca.markets](https://alpaca.markets) — gratis, paper trading |
| `META_ACCESS_TOKEN` | [developers.facebook.com](https://developers.facebook.com) |

---

### PASO 4 — Verificar que todo funciona

```bash
source .venv/bin/activate
python verificar.py
```

Vas a ver exactamente qué está configurado y qué falta.

---

### PASO 5 — ¡Usar el sistema!

```bash
# Activar entorno (solo una vez por sesión de Terminal)
source .venv/bin/activate

# Modo interactivo (recomendado para empezar)
python main.py

# O directo con una tarea
python main.py "muéstrame mis clientes nuevos en Airtable"
python main.py "analiza NVDA y dime si comprar"
python main.py "tengo una idea de negocio, quiero un servicio de..."
```

---

## 📂 Dónde poner tus archivos

| Tipo | Carpeta |
|------|---------|
| Videos de propiedades | `media/input/` |
| Videos para reels/podcast | `media/input/` |
| Credenciales de Google | raíz del proyecto (junto a `main.py`) |
| Proyectos web generados | `proyectos/` (se crea automático) |

---

## 🤖 Referencia rápida de agentes

```bash
# Agentes generales
python main.py --agente investigador "investiga apps de renta en España"
python main.py --agente estratega "tengo idea de negocio: app de..."
python main.py --agente desarrollador "crea landing page para mi servicio X"
python main.py --agente marketing "estrategia para lanzar mi nuevo negocio"
python main.py --agente analista "dame el reporte de mis negocios este mes"
python main.py --agente trader "analiza BTC y ETH, ¿cuál tiene mejor señal?"
python main.py --agente media "analiza el video propiedad.mp4 y crea un reel"

# Agentes de inmobiliaria
python main.py --agente inmobiliaria_leads "clientes nuevos esta semana"
python main.py --agente inmobiliaria_contenido "post para casa 3 rec en Polanco"
python main.py --agente inmobiliaria_clientes "cliente busca depto 2 rec en Narvarte"

# Automático (el sistema decide quién responde)
python main.py "cualquier pregunta aquí"
```

---

## 🔧 Solución de problemas frecuentes

**`command not found: python`**
→ Usa `python3` en lugar de `python`

**`ModuleNotFoundError`**
→ Asegúrate de activar el entorno: `source .venv/bin/activate`

**`Error: ANTHROPIC_API_KEY`**
→ El archivo `.env` no tiene la key o tiene el valor de ejemplo

**FFmpeg no funciona con el Agente Media**
→ Ejecuta: `brew install ffmpeg`

**El agente de Airtable da error de tabla**
→ Verifica que los nombres exactos sean `Clientes_FBR`, `Propiedades_FBR`, `Marketing_FBR`
