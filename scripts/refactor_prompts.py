#!/usr/bin/env python3
"""
Refactoriza los 11 archivos de agentes para separar BASE_ESPECIALISTA
de CONTEXTO_NEGOCIO en la variable INSTRUCCIONES.

Uso: python scripts/refactor_prompts.py
"""
import re
from pathlib import Path

AGENTS_DIR = Path(__file__).parent.parent / "src" / "agents"

FORMULA = (
    '\n\nINSTRUCCIONES = f"{BASE_ESPECIALISTA}\\n\\n'
    '=== CONTEXTO DEL NEGOCIO ===\\n{CONTEXTO_NEGOCIO}"\n'
)

# ── Split markers for specialized agents ──────────────────────────
# key = filename stem, value = text that starts the CONTEXTO_NEGOCIO block
CONTEXT_SPLITS = {
    "marketing":            "Los negocios principales que gestionas:",
    "media":                "Trabajas para dos negocios:",
    "lead_manager":         "Principios:",
    "content_creator":      "Lineamientos de marca:",
    "client_service":       "Estilo de comunicación:",
    "analista_propiedades": "=== ESTÁNDARES DE MARCA ===",
}

# Pure general agents — everything stays in BASE_ESPECIALISTA
GENERAL_AGENTS = {
    "investigador", "estratega", "desarrollador",
    "analista", "trader",
}


def extract_instrucciones_block(source: str):
    """
    Returns (before, var_name, quote_style, content, after).
    Handles both:
      INSTRUCCIONES = \"\"\"...\"\"\"\n
      INSTRUCCIONES = f\"\"\"...\"\"\"\n
    """
    pattern = re.compile(
        r'(INSTRUCCIONES\s*=\s*)(f?)(""")(.*?)(""")',
        re.DOTALL,
    )
    m = pattern.search(source)
    if not m:
        raise ValueError("No se encontró INSTRUCCIONES en el archivo.")
    start, end = m.start(), m.end()
    content = m.group(4)          # raw text inside the triple-quotes
    is_fstring = m.group(2) == "f"
    before = source[:start]
    after = source[end:]
    return before, content, is_fstring, after


def build_replacement(stem: str, content: str, is_fstring: bool) -> str:
    q = 'f"""' if is_fstring else '"""'

    if stem in GENERAL_AGENTS:
        base = content.strip()
        ctx  = ""
    else:
        split_marker = CONTEXT_SPLITS[stem]
        idx = content.find(split_marker)
        if idx == -1:
            print(f"  ⚠️  Marcador no encontrado en {stem}, todo va a BASE_ESPECIALISTA.")
            base = content.strip()
            ctx  = ""
        else:
            base = content[:idx].strip()
            ctx  = content[idx:].strip()

    lines = [
        f"BASE_ESPECIALISTA = {q}\n{base}\n\"\"\"\n",
        f"\nCONTEXTO_NEGOCIO = {q}\n{ctx}\n\"\"\"" if ctx else '\nCONTEXTO_NEGOCIO = ""',
        FORMULA,
    ]
    return "".join(lines)


def refactor_file(path: Path) -> None:
    stem = path.stem
    if stem not in GENERAL_AGENTS and stem not in CONTEXT_SPLITS:
        print(f"  ⏭  Omitiendo {path.name} (no listado)")
        return

    source = path.read_text(encoding="utf-8")

    try:
        before, content, is_fstring, after = extract_instrucciones_block(source)
    except ValueError as e:
        print(f"  ❌ {path.name}: {e}")
        return

    replacement = build_replacement(stem, content, is_fstring)
    new_source = before + replacement + after

    path.write_text(new_source, encoding="utf-8")
    print(f"  ✅ {path.name}")


def main():
    all_stems = GENERAL_AGENTS | set(CONTEXT_SPLITS.keys())
    print("Refactorizando agentes...\n")
    for stem in sorted(all_stems):
        path = AGENTS_DIR / f"{stem}.py"
        if path.exists():
            refactor_file(path)
        else:
            print(f"  ⚠️  No encontrado: {path}")
    print("\nListo.")


if __name__ == "__main__":
    main()
