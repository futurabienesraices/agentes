#!/bin/bash
# =============================================================
# setup.sh — Instalación automática del sistema de agentes
# Ejecutar: bash setup.sh
# =============================================================
set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()  { echo -e "${GREEN}✓${NC} $1"; }
warn(){ echo -e "${YELLOW}⚠${NC}  $1"; }
err(){ echo -e "${RED}✗${NC} $1"; }

echo ""
echo "================================================"
echo "   FUTURA BIENES RAÍCES — Equipo de Agentes IA"
echo "   Setup automático"
echo "================================================"
echo ""

# ── 1. Homebrew ──────────────────────────────────────────────
if ! command -v brew &>/dev/null; then
  warn "Homebrew no encontrado. Instalando..."
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
  ok "Homebrew instalado"
fi

# ── 2. Python 3 ──────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  warn "Python 3 no encontrado. Instalando..."
  brew install python@3.11
else
  PYVER=$(python3 --version)
  ok "$PYVER instalado"
fi

# ── 3. FFmpeg ─────────────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
  warn "FFmpeg no encontrado. Instalando (puede tardar 2-3 min)..."
  brew install ffmpeg
else
  ok "FFmpeg instalado"
fi

# ── 4. Entorno virtual ────────────────────────────────────────
if [ ! -d ".venv" ]; then
  echo "→ Creando entorno virtual..."
  python3 -m venv .venv
  ok "Entorno virtual creado (.venv)"
else
  ok "Entorno virtual ya existe"
fi

# ── 5. Dependencias Python ───────────────────────────────────
echo "→ Instalando dependencias Python..."
source .venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
ok "Dependencias instaladas"

# ── 6. Variables de entorno ──────────────────────────────────
if [ ! -f ".env" ]; then
  cp .env.example .env
  warn ".env creado desde .env.example — DEBES editar las API keys"
else
  ok ".env ya existe"
fi

# ── 7. Carpetas de media ──────────────────────────────────────
mkdir -p media/input media/output proyectos
ok "Carpetas media/ y proyectos/ creadas"

# ── Resumen ───────────────────────────────────────────────────
echo ""
echo "================================================"
echo -e "${GREEN}   Setup completado.${NC}"
echo "================================================"
echo ""
echo "SIGUIENTE PASO:"
echo "  1. Edita el archivo .env con tus API keys"
echo "  2. Ejecuta: source .venv/bin/activate"
echo "  3. Ejecuta: python verificar.py"
echo "  4. Ejecuta: python main.py"
echo ""
