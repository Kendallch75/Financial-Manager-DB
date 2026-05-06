from pathlib import Path

path = Path('frontend/src/main.jsx')
text = path.read_text()
original = text

replacements = [
    (
        "  const load = () => {\n    api\n      .get(config.endpoint)",
        "  const load = () => {\n    setRows([]);\n    api\n      .get(config.endpoint)",
        "Agregar limpieza de filas antes de cada carga",
    ),
    (
        "  useEffect(() => {\n    setForm(emptyForm(config.fields));\n    setEditing(null);\n    setError('');\n    load();\n    loadLookups();\n  }, [config.endpoint]);",
        "  useEffect(() => {\n    setRows([]);\n    setLookups({});\n    setForm(emptyForm(config.fields));\n    setEditing(null);\n    setError('');\n    load();\n    loadLookups();\n  }, [config.endpoint]);",
        "Limpiar filas/lookups al cambiar de ventana",
    ),
    (
        "          {options.map((option) => (\n            <option key={option[relation.pk]} value={option[relation.pk]}>{relation.label(option)}</option>\n          ))}",
        "          {options.map((option, index) => (\n            <option key={`${field}-${option[relation.pk] ?? index}`} value={option[relation.pk]}>{relation.label(option)}</option>\n          ))}",
        "Hacer únicas las keys de opciones relacionadas",
    ),
    (
        "              {rows.map((row) => (\n                <tr key={row[config.pk]}>",
        "              {rows.map((row, index) => (\n                <tr key={`${config.endpoint}-${row[config.pk] ?? index}`}>",
        "Hacer únicas las keys de filas por recurso",
    ),
]

failed = []
for old, new, label in replacements:
    if old not in text:
        failed.append(label)
    else:
        text = text.replace(old, new, 1)

if failed:
    print('No pude aplicar estos cambios:')
    for item in failed:
        print('-', item)
    raise SystemExit(1)

path.write_text(text)
print('Parche aplicado correctamente en frontend/src/main.jsx')
