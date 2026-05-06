from pathlib import Path

ROOT = Path.cwd()
main_path = ROOT / "frontend" / "src" / "main.jsx"
styles_path = ROOT / "frontend" / "src" / "styles.css"

if not main_path.exists():
    raise SystemExit(f"No encontré {main_path}. Ejecuta este script desde la raíz del proyecto.")

text = main_path.read_text(encoding="utf-8")

# Evitar aplicar dos veces
if "color-picker-row" not in text:
    marker = "const inputType = field.includes('date') ? 'date' : field.includes('amount') || field === 'rate' || field === 'due_day' ? 'number' : 'text';"
    block = """
    if (field === 'color') {
      const colorValue = form[field] || '#22c55e';
      return (
        <div className="color-picker-row">
          <input
            className="color-picker-input"
            type="color"
            value={colorValue}
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
            aria-label="Seleccionar color"
          />
          <input
            className="color-picker-hex"
            type="text"
            value={colorValue}
            placeholder="#22c55e"
            maxLength="7"
            onChange={(e) => setForm({ ...form, [field]: e.target.value })}
          />
        </div>
      );
    }

"""
    if marker not in text:
        raise SystemExit(
            "No pude encontrar el punto exacto para insertar el color picker. "
            "Busca en frontend/src/main.jsx la línea que empieza con: const inputType = field.includes('date')"
        )
    text = text.replace(marker, block + "    " + marker, 1)
    main_path.write_text(text, encoding="utf-8")
    print("✓ frontend/src/main.jsx actualizado: color usa selector visual.")
else:
    print("• frontend/src/main.jsx ya parecía tener el color picker aplicado.")

css = """

/* Selector visual de color para categorías */
.color-picker-row {
  display: flex;
  align-items: center;
  gap: 0.65rem;
  width: 100%;
}

.color-picker-input {
  width: 3.25rem;
  min-width: 3.25rem;
  height: 2.75rem;
  padding: 0.2rem;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 0.9rem;
  background: rgba(15, 23, 42, 0.04);
  cursor: pointer;
}

.color-picker-hex {
  flex: 1;
  min-width: 0;
}

@media (max-width: 640px) {
  .color-picker-row {
    gap: 0.5rem;
  }

  .color-picker-input {
    width: 3rem;
    min-width: 3rem;
  }
}
"""

if styles_path.exists():
    styles = styles_path.read_text(encoding="utf-8")
    if "color-picker-row" not in styles:
        styles_path.write_text(styles.rstrip() + css + "\n", encoding="utf-8")
        print("✓ frontend/src/styles.css actualizado: estilos del selector de color agregados.")
    else:
        print("• frontend/src/styles.css ya tenía estilos de color picker.")
else:
    print("⚠ No encontré frontend/src/styles.css; solo se actualizó main.jsx.")

print("\nListo. Reinicia el frontend con: cd frontend && npm run dev")
