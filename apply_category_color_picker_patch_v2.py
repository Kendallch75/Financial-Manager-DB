from pathlib import Path

root = Path.cwd()
main_path = root / 'frontend' / 'src' / 'main.jsx'
css_path = root / 'frontend' / 'src' / 'styles.css'

if not main_path.exists():
    raise SystemExit(f'No encontré {main_path}. Ejecuta este script desde la raíz del proyecto.')

text = main_path.read_text(encoding='utf-8')

if "field === 'color'" in text and "color-picker-row" in text:
    print('El selector de color ya parece estar aplicado en main.jsx.')
else:
    marker = "function renderField(field) { if (selectOptions[field]) {"
    insert = """function renderField(field) { if (field === 'color') { return ( <div className=\"color-picker-row\"> <input className=\"color-picker\" type=\"color\" value={form[field] || '#22c55e'} onChange={(e) => setForm({ ...form, [field]: e.target.value })} /> <input className=\"color-code-input\" type=\"text\" value={form[field] || '#22c55e'} placeholder=\"#22c55e\" onChange={(e) => setForm({ ...form, [field]: e.target.value })} /> </div> ); } if (selectOptions[field]) {"""
    if marker in text:
        text = text.replace(marker, insert, 1)
    else:
        # Más flexible por si hay saltos de línea distintos
        marker2 = "function renderField(field) {"
        if marker2 not in text:
            raise SystemExit("No pude encontrar function renderField(field) en frontend/src/main.jsx")
        insert2 = """function renderField(field) { if (field === 'color') { return ( <div className=\"color-picker-row\"> <input className=\"color-picker\" type=\"color\" value={form[field] || '#22c55e'} onChange={(e) => setForm({ ...form, [field]: e.target.value })} /> <input className=\"color-code-input\" type=\"text\" value={form[field] || '#22c55e'} placeholder=\"#22c55e\" onChange={(e) => setForm({ ...form, [field]: e.target.value })} /> </div> ); }"""
        text = text.replace(marker2, insert2, 1)
    main_path.write_text(text, encoding='utf-8')
    print('Actualicé frontend/src/main.jsx para usar selector visual en field=color.')

if css_path.exists():
    css = css_path.read_text(encoding='utf-8')
else:
    css = ''

css_block = """

/* Selector visual de color para categorías */
.color-picker-row {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  width: 100%;
}

.color-picker {
  width: 3.2rem;
  min-width: 3.2rem;
  height: 2.75rem;
  padding: 0.2rem;
  border: 1px solid rgba(148, 163, 184, 0.35);
  border-radius: 0.9rem;
  background: rgba(15, 23, 42, 0.85);
  cursor: pointer;
}

.color-code-input {
  flex: 1;
  min-width: 0;
}
"""

if 'color-picker-row' not in css:
    css_path.write_text(css.rstrip() + css_block, encoding='utf-8')
    print('Agregué estilos del selector de color en frontend/src/styles.css.')
else:
    print('Los estilos del selector de color ya estaban en styles.css.')

print('Listo. Reinicia el frontend con: cd frontend && npm run dev')
