from pathlib import Path
import re

PROJECT = Path.cwd()
main_path = PROJECT / "frontend" / "src" / "main.jsx"

if not main_path.exists():
    raise SystemExit(f"No encontré {main_path}. Ejecuta este script desde la raíz del proyecto.")

text = main_path.read_text(encoding="utf-8")
original = text

# 1) Add Cell to recharts import.
def add_cell_to_recharts_import(match: re.Match) -> str:
    content = match.group(1)
    if re.search(r"\bCell\b", content):
        return match.group(0)
    # Prefer placing Cell right after Bar if Bar exists.
    if re.search(r"\bBar\b", content):
        content = re.sub(r"\bBar\b", "Bar, Cell", content, count=1)
    else:
        content = "Cell, " + content
    # Avoid accidental duplicate commas/spaces.
    content = re.sub(r",\s*,", ",", content)
    return f"import {{{content}}} from 'recharts';"

text = re.sub(
    r"import\s*\{([^}]*)\}\s*from\s*['\"]recharts['\"]\s*;",
    add_cell_to_recharts_import,
    text,
    count=1,
    flags=re.DOTALL,
)

# 2) Add chartColors after const chart = [...] if not present.
if "const chartColors" not in text:
    chart_regex = re.compile(
        r"(const\s+chart\s*=\s*\[\s*"
        r"\{\s*name:\s*['\"]Ingresos['\"]\s*,\s*total:\s*Number\(stats\.income\)\s*\}\s*,\s*"
        r"\{\s*name:\s*['\"]Gastos['\"]\s*,\s*total:\s*Number\(stats\.expenses\)\s*\}\s*,\s*"
        r"\{\s*name:\s*['\"]Balance['\"]\s*,\s*total:\s*Number\(stats\.balance\)\s*\}\s*,?\s*"
        r"\]\s*;)",
        re.DOTALL,
    )
    replacement = (
        r"\1\n"
        "  const chartColors = {\n"
        "    Ingresos: '#22c55e',\n"
        "    Gastos: '#ef4444',\n"
        "    Balance: '#eab308',\n"
        "  };"
    )
    text, n = chart_regex.subn(replacement, text, count=1)
    if n == 0:
        raise SystemExit(
            "No pude ubicar el bloque `const chart = [...]` del Dashboard. "
            "Revisa si main.jsx cambió demasiado."
        )

# 3) Replace the dashboard Bar with per-cell colors.
if "chartColors[entry.name]" not in text:
    # Replace any self-closing Bar component whose dataKey is total.
    bar_regex = re.compile(r"<Bar\b([^>]*)dataKey=(['\"])total\2([^>]*)\s*/>", re.DOTALL)

    def replace_bar(match: re.Match) -> str:
        attrs = (match.group(1) + " dataKey=\"total\"" + match.group(3)).strip()
        # Remove existing fill/radius attributes to avoid conflicts.
        attrs = re.sub(r"\s*fill=(\{[^}]*\}|['\"][^'\"]*['\"])", "", attrs)
        attrs = re.sub(r"\s*radius=\{[^}]*\}", "", attrs)
        attrs = re.sub(r"\s+", " ", attrs).strip()
        return (
            f"<Bar {attrs} radius={{[10, 10, 0, 0]}}>"
            "{chart.map((entry) => ("
            "<Cell key={entry.name} fill={chartColors[entry.name] || '#64748b'} />"
            "))}"
            "</Bar>"
        )

    text, n = bar_regex.subn(replace_bar, text, count=1)
    if n == 0:
        raise SystemExit(
            "No pude ubicar un `<Bar dataKey=\"total\" />` para reemplazar. "
            "Busca manualmente el Bar del Dashboard."
        )

if text == original:
    print("No hubo cambios; probablemente ya estaba aplicado.")
else:
    main_path.write_text(text, encoding="utf-8")
    print("Parche aplicado correctamente en frontend/src/main.jsx")
    print("Colores: Ingresos verde, Gastos rojo, Balance amarillo.")
