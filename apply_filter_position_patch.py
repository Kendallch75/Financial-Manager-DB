from pathlib import Path

root = Path.cwd()
main_path = root / 'frontend' / 'src' / 'main.jsx'

if not main_path.exists():
    raise SystemExit('No encontré frontend/src/main.jsx. Ejecuta este script desde la raíz del proyecto.')

text = main_path.read_text(encoding='utf-8')
original = text

# Si el panel ya está debajo del form-panel, no hacer nada.
filters_marker = 'className="panel filters-panel"'
form_marker = 'className="panel form-panel"'
table_marker = 'className="panel table-panel"'

if filters_marker not in text:
    raise SystemExit('No encontré el panel de filtros (panel filters-panel) en main.jsx.')

filters_pos = text.find(filters_marker)
form_pos = text.find(form_marker)
table_pos = text.find(table_marker)

if form_pos == -1 or table_pos == -1:
    raise SystemExit('No encontré form-panel o table-panel. Revisa la estructura de CrudPage en main.jsx.')

if form_pos < filters_pos < table_pos:
    print('El panel de filtros ya está entre el formulario y la tabla. No se aplicaron cambios.')
    raise SystemExit(0)

# Encontrar el bloque completo del section filters-panel.
section_start = text.rfind('      <section', 0, filters_pos)
if section_start == -1:
    raise SystemExit('No pude encontrar el inicio del section de filtros.')

# El bloque de filtros normalmente termina antes del form-panel.
next_form_section = text.find('      <section className="panel form-panel">', section_start)
if next_form_section == -1:
    raise SystemExit('No pude encontrar dónde termina el bloque de filtros antes del formulario.')

filters_block = text[section_start:next_form_section]

# Eliminar el bloque de filtros de su posición original.
text_without_filters = text[:section_start] + text[next_form_section:]

# Insertar el bloque de filtros justo antes de table-panel, o sea debajo del formulario.
table_section = text_without_filters.find('      <section className="panel table-panel">')
if table_section == -1:
    raise SystemExit('No pude encontrar table-panel para insertar los filtros antes de la tabla.')

# Evitar espacios excesivos.
filters_block = filters_block.strip('\n') + '\n\n'
text = text_without_filters[:table_section] + filters_block + text_without_filters[table_section:]

# Renombrar texto de ayuda si existe para que sea más claro.
text = text.replace('Buscar en esta vista...', 'Filtrar registros de la tabla...')
text = text.replace('Limpiar filtros', 'Limpiar filtro')

if text == original:
    print('No hubo cambios que aplicar.')
else:
    main_path.write_text(text, encoding='utf-8')
    print('Listo: el panel de búsqueda/filtros ahora aparece debajo del formulario y encima de la tabla.')
