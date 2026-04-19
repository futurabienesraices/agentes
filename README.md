# Flujos de trabajo Multi-IA — Make.com & n8n

Colección de workflows que conectan diferentes inteligencias artificiales (Claude, GPT-4, Gemini) para que colaboren entre sí. Disponibles para **Make.com** y **n8n** — elige la plataforma que prefieras, los flujos son equivalentes.

## Workflows disponibles

| Workflow | Descripción |
|----------|-------------|
| `1-pipeline-ia` | **Pipeline secuencial** — Claude planifica, GPT-4 ejecuta, Claude revisa |
| `2-router-ia` | **Router por tipo de tarea** — Dirige cada tarea a la IA más adecuada |
| `3-consenso-ia` | **Consenso multi-IA** — Claude + GPT-4 + Gemini responden y Claude sintetiza |

Cada workflow tiene su versión en `blueprints/` (Make.com) y en `n8n/` (n8n).

---

## Requisitos previos

1. Cuenta en [Make.com](https://www.make.com) **o** instancia de [n8n](https://n8n.io) (self-hosted o cloud)
2. Claves de API:
   - **Anthropic** (Claude): [console.anthropic.com](https://console.anthropic.com)
   - **OpenAI** (GPT-4): [platform.openai.com](https://platform.openai.com)
   - **Google AI** (Gemini): [aistudio.google.com](https://aistudio.google.com) *(solo Blueprint 3)*

---

## Cómo importar

### Make.com
1. Ve a **Scenarios** → **Create a new scenario**
2. Tres puntos (···) → **Import Blueprint**
3. Sube el archivo de `blueprints/`
4. Configura las conexiones HTTP y webhooks que Make te pedirá

### n8n
1. Ve a **Workflows** → **Import from file**
2. Sube el archivo de `n8n/`
3. En **Settings → Variables** agrega `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` y `GEMINI_API_KEY`
4. Activa el workflow

---

## Configuración de API Keys

En cada módulo HTTP del blueprint encontrarás placeholders como `YOUR_ANTHROPIC_API_KEY`. Sustitúyelos directamente en el campo **Headers** del módulo o usa variables de entorno de Make:

1. En Make, ve a **Connections** o usa el módulo de **Variables** del escenario
2. Guarda tus claves como **Data Stores** o en los headers directamente

Puedes copiar `.env.example` como guía de las variables necesarias.

---

## Blueprint 1 — Pipeline Secuencial

```
[Webhook] → [Claude: Planifica] → [GPT-4: Ejecuta] → [Claude: Revisa] → [Respuesta]
```

**Flujo:**
1. El webhook recibe `{ "prompt": "...", "context": "..." }`
2. **Claude** analiza el prompt y genera un plan estructurado
3. **GPT-4** ejecuta el plan y produce el contenido
4. **Claude** revisa y refina el resultado de GPT-4
5. El webhook responde con el resultado final y el trazado del pipeline

**Casos de uso:** Generación de artículos, reportes, análisis de documentos.

**Ejemplo de petición:**
```json
{
  "prompt": "Escribe un análisis de mercado sobre el sector fintech en Latinoamérica",
  "context": "Enfoque en tendencias 2024-2025, máximo 500 palabras"
}
```

---

## Blueprint 2 — Router por Tipo de Tarea

```
[Webhook] → [Router] → código    → [GPT-4]  → [Respuesta]
                     → creativo  → [Claude] → [Respuesta]
                     → análisis  → [Claude] → [Respuesta]
                     → default   → [GPT-4]  → [Respuesta]
```

**Flujo:**
1. El webhook recibe `{ "prompt": "...", "type": "code|creative|analysis" }`
2. El **Router** dirige la tarea según el campo `type`:
   - `code` → **GPT-4** (mejor para programación)
   - `creative` → **Claude** (mejor para contenido creativo)
   - `analysis` → **Claude** (mejor para razonamiento profundo)
   - *default* → **GPT-4**
3. La IA seleccionada responde directamente

**Casos de uso:** Automatización de tareas mixtas, workflows de agencia.

**Ejemplo de petición:**
```json
{
  "prompt": "Crea una función en Python que ordene una lista de diccionarios por múltiples campos",
  "type": "code"
}
```

---

## Blueprint 3 — Consenso Multi-IA

```
[Webhook] → [Claude] ─┐
           → [GPT-4]  ├→ [Claude: Sintetiza] → [Respuesta]
           → [Gemini] ─┘
```

**Flujo:**
1. El webhook recibe `{ "question": "..." }`
2. **Claude**, **GPT-4** y **Gemini** responden a la misma pregunta de forma independiente
3. **Claude** sintetiza las tres respuestas en una respuesta unificada y equilibrada
4. El webhook devuelve la síntesis + las 3 respuestas individuales

**Casos de uso:** Investigación, toma de decisiones, fact-checking, preguntas complejas.

**Ejemplo de petición:**
```json
{
  "question": "¿Cuáles son los principales riesgos del uso de IA generativa en empresas en 2025?"
}
```

---

## Estructura del repositorio

```
agentes/
├── README.md
├── .env.example
├── blueprints/          ← Workflows para Make.com
│   ├── 1-pipeline-ia.json
│   ├── 2-router-ia.json
│   └── 3-consenso-ia.json
└── n8n/                 ← Workflows equivalentes para n8n
    ├── 1-pipeline-ia.json
    ├── 2-router-ia.json
    └── 3-consenso-ia.json
```

---

## Personalización

- **Modelos**: Cambia `claude-opus-4-6`, `gpt-4o` o `gemini-2.0-flash` por cualquier modelo disponible en cada API
- **System prompts**: Edita el campo `system` en cada módulo HTTP para adaptar el comportamiento
- **Trigger**: Reemplaza el webhook por otro trigger de Make (Google Sheets, Slack, email, etc.)
- **Respuesta**: Ajusta el módulo de respuesta para enviar resultados a Slack, email, base de datos, etc.
