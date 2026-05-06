from pathlib import Path
import re

ROOT = Path.cwd()
FRONTEND = ROOT / 'frontend' / 'src' / 'main.jsx'
MODELS = ROOT / 'backend' / 'core' / 'models.py'
SERIALIZERS = ROOT / 'backend' / 'core' / 'serializers.py'
SCHEMA = ROOT / 'backend' / 'db' / 'schema.sql'
DB_DIR = ROOT / 'backend' / 'db'

for path in [FRONTEND, MODELS, SERIALIZERS]:
    if not path.exists():
        raise SystemExit(f'No encontré {path}. Ejecuta este script desde la raíz del proyecto.')

def backup(path: Path):
    b = path.with_suffix(path.suffix + '.bak_filters_service_interval')
    if not b.exists():
        b.write_text(path.read_text(), encoding='utf-8')

# ---------------- FRONTEND ----------------
backup(FRONTEND)
text = FRONTEND.read_text(encoding='utf-8')

# 1) Add payment_interval_months to services fields
old_services_fields = "'service_name',\n      'provider_name',\n      'reference_number',\n      'due_day',\n      'typical_amount',\n      'currency',"
if old_services_fields in text and "'payment_interval_months'" not in text:
    text = text.replace(old_services_fields, "'service_name',\n      'provider_name',\n      'reference_number',\n      'due_day',\n      'payment_interval_months',\n      'typical_amount',\n      'currency',")

# 2) Labels
if "payment_interval_months:" not in text:
    text = text.replace("due_day: 'Día de pago',", "due_day: 'Día de pago',\n  payment_interval_months: 'Frecuencia (meses)',")

# 3) Placeholders/defaults
if "payment_interval_months: '1'" not in text:
    text = text.replace("rate_date: '2026-04-27T00:00:00',", "rate_date: '2026-04-27T00:00:00',\n  payment_interval_months: '1',")

# 4) selectOptions for payment_interval_months
if "payment_interval_months: Array.from" not in text:
    marker = "  original_currency: [\n    { value: 'CRC', label: 'CRC' },\n    { value: 'USD', label: 'USD' },\n    { value: 'EUR', label: 'EUR' },\n  ],"
    if marker in text:
        text = text.replace(marker, marker + "\n  payment_interval_months: Array.from({ length: 24 }, (_, i) => ({\n    value: String(i + 1),\n    label: i === 0 ? 'Cada mes' : `Cada ${i + 1} meses`,\n  })),")
    else:
        # compact fallback: insert before relationConfig
        text = text.replace("}; const relationConfig", "  payment_interval_months: Array.from({ length: 24 }, (_, i) => ({ value: String(i + 1), label: i === 0 ? 'Cada mes' : `Cada ${i + 1} meses` })),\n}; const relationConfig")

# 5) emptyForm default for interval
old_empty = "fields.map((field) => [field, field === 'color' ? '#22c55e' : ''])"
if old_empty in text:
    text = text.replace(old_empty, "fields.map((field) => [field, field === 'color' ? '#22c55e' : field === 'payment_interval_months' ? '1' : ''])")

# 6) CrudPage states: add filters
old_state = "const [lookups, setLookups] = useState({});\n\n  const visibleFields = config.fields;"
if old_state in text and "const [searchText, setSearchText]" not in text:
    text = text.replace(old_state, "const [lookups, setLookups] = useState({});\n  const [searchText, setSearchText] = useState('');\n  const [dateFrom, setDateFrom] = useState('');\n  const [dateTo, setDateTo] = useState('');\n\n  const visibleFields = config.fields;\n  const dateFields = useMemo(\n    () => config.fields.filter((field) => field.includes('date') || field === 'start_date' || field === 'end_date'),\n    [config.fields]\n  );")
else:
    compact_state = "const [lookups, setLookups] = useState({}); const visibleFields = config.fields;"
    if compact_state in text and "const [searchText, setSearchText]" not in text:
        text = text.replace(compact_state, "const [lookups, setLookups] = useState({}); const [searchText, setSearchText] = useState(''); const [dateFrom, setDateFrom] = useState(''); const [dateTo, setDateTo] = useState(''); const visibleFields = config.fields; const dateFields = useMemo(() => config.fields.filter((field) => field.includes('date') || field === 'start_date' || field === 'end_date'), [config.fields]);")

# 7) Clear filters on resource change
old_effect = "setForm(emptyForm(config.fields));\n    setEditing(null);\n    setError('');\n    load();"
if old_effect in text and "setSearchText('');" not in text:
    text = text.replace(old_effect, "setForm(emptyForm(config.fields));\n    setEditing(null);\n    setError('');\n    setRows([]);\n    setLookups({});\n    setSearchText('');\n    setDateFrom('');\n    setDateTo('');\n    load();")
else:
    compact_effect = "setForm(emptyForm(config.fields)); setEditing(null); setError(''); load();"
    if compact_effect in text and "setSearchText('');" not in text:
        text = text.replace(compact_effect, "setForm(emptyForm(config.fields)); setEditing(null); setError(''); setRows([]); setLookups({}); setSearchText(''); setDateFrom(''); setDateTo(''); load();")

# 8) Clean payload: payment_interval_months number
old_payload = "if (relationConfig[key] && payload[key] !== null) payload[key] = Number(payload[key]);"
if old_payload in text and "payment_interval_months" not in text[text.find("function cleanPayload"):text.find("async function submit")]:
    text = text.replace(old_payload, "if (relationConfig[key] && payload[key] !== null) payload[key] = Number(payload[key]);\n      if (key === 'payment_interval_months' && payload[key] !== null) payload[key] = Number(payload[key]);")

# 9) Insert filteredRows before return in CrudPage, after renderField function block. Use a robust marker.
if "const filteredRows = useMemo" not in text:
    marker = "  return (\n    <>\n      <section className=\"page-heading\">"
    insert = "  const filteredRows = useMemo(() => {\n    const term = searchText.trim().toLowerCase();\n\n    return rows.filter((row) => {\n      const matchesText = !term || config.fields.some((field) => {\n        const raw = relationConfig[field] ? relationLabel(field, row[field]) : row[field];\n        return String(raw ?? '').toLowerCase().includes(term);\n      });\n\n      const matchesDate = dateFields.length === 0 || dateFields.some((field) => {\n        const value = row[field];\n        if (!value) return false;\n        const current = String(value).slice(0, 10);\n        if (dateFrom && current < dateFrom) return false;\n        if (dateTo && current > dateTo) return false;\n        return true;\n      }) || (!dateFrom && !dateTo);\n\n      return matchesText && matchesDate;\n    });\n  }, [rows, searchText, dateFrom, dateTo, dateFields, config.fields, lookups]);\n\n"
    if marker in text:
        text = text.replace(marker, insert + marker)
    else:
        compact_marker = "return ( <> <section className=\"page-heading\">"
        if compact_marker in text:
            text = text.replace(compact_marker, insert.replace('\n', ' ') + compact_marker)
        else:
            print('Advertencia: no pude insertar filteredRows automáticamente.')

# 10) Insert filter panel after error and before form panel
if "className=\"panel filter-panel\"" not in text:
    marker = "      <section className=\"panel form-panel\">"
    filters = "      <section className=\"panel filter-panel\">\n        <div className=\"filter-grid\">\n          <label>Buscar\n            <input\n              type=\"search\"\n              value={searchText}\n              placeholder=\"Buscar en esta vista...\"\n              onChange={(e) => setSearchText(e.target.value)}\n            />\n          </label>\n          {dateFields.length > 0 && (\n            <>\n              <label>Desde\n                <input type=\"date\" value={dateFrom} onChange={(e) => setDateFrom(e.target.value)} />\n              </label>\n              <label>Hasta\n                <input type=\"date\" value={dateTo} onChange={(e) => setDateTo(e.target.value)} />\n              </label>\n            </>\n          )}\n          <div className=\"filter-actions\">\n            <button type=\"button\" className=\"secondary\" onClick={() => { setSearchText(''); setDateFrom(''); setDateTo(''); }}>\n              Limpiar filtros\n            </button>\n            <span>{filteredRows.length} de {rows.length} registros</span>\n          </div>\n        </div>\n      </section>\n\n"
    if marker in text:
        text = text.replace(marker, filters + marker)
    else:
        compact_marker = "<section className=\"panel form-panel\">"
        text = text.replace(compact_marker, filters + compact_marker, 1)

# 11) Use filteredRows in table + unique key
text = text.replace("{rows.map((row) => (\n                <tr key={row[config.pk]}>", "{filteredRows.map((row, index) => (\n                <tr key={`${config.endpoint}-${row[config.pk] ?? index}`}>")
text = text.replace("{rows.map((row) => ( {config.fields.slice", "{filteredRows.map((row, index) => ( {config.fields.slice")
text = text.replace("<tr key={row[config.pk]}>", "<tr key={`${config.endpoint}-${row[config.pk] ?? index}`}>" )

# 12) Inputs: numeric keyboard for amounts and interval bounds
text = text.replace("type={inputType}\n        value={form[field] ?? ''}", "type={inputType}\n        inputMode={inputType === 'number' ? 'decimal' : undefined}\n        min={field === 'payment_interval_months' ? '1' : undefined}\n        max={field === 'payment_interval_months' ? '24' : undefined}\n        value={form[field] ?? ''}")

FRONTEND.write_text(text, encoding='utf-8')

# ---------------- MODELS ----------------
backup(MODELS)
models = MODELS.read_text(encoding='utf-8')
if 'payment_interval_months' not in models:
    # formatted pattern
    old = "    due_day = models.IntegerField()\n    typical_amount = models.DecimalField("
    if old in models:
        models = models.replace(old, "    due_day = models.IntegerField()\n    payment_interval_months = models.IntegerField(default=1)\n    typical_amount = models.DecimalField(")
    else:
        # compact one-line pattern
        models = models.replace("due_day = models.IntegerField() typical_amount =", "due_day = models.IntegerField() payment_interval_months = models.IntegerField(default=1) typical_amount =")
    MODELS.write_text(models, encoding='utf-8')

# ---------------- SERIALIZERS ----------------
backup(SERIALIZERS)
serializers = SERIALIZERS.read_text(encoding='utf-8')
if 'validate_payment_interval_months' not in serializers:
    # Add validator inside ServiceSerializer before ExchangeRateSerializer
    insert = "\n    def validate_payment_interval_months(self, value):\n        if value is None:\n            return 1\n        if value < 1 or value > 24:\n            raise serializers.ValidationError('La frecuencia debe estar entre 1 y 24 meses.')\n        return value\n"
    marker = "class ExchangeRateSerializer"
    if marker in serializers:
        serializers = serializers.replace(marker, insert + "\n" + marker)
    SERIALIZERS.write_text(serializers, encoding='utf-8')

# ---------------- SQL ----------------
DB_DIR.mkdir(parents=True, exist_ok=True)
alter = DB_DIR / 'alter_service_payment_interval.sql'
alter.write_text("""USE flujex;

ALTER TABLE SERVICE
ADD COLUMN payment_interval_months INT NOT NULL DEFAULT 1 AFTER due_day;

ALTER TABLE SERVICE
ADD CONSTRAINT chk_service_payment_interval
CHECK (payment_interval_months BETWEEN 1 AND 24);
""", encoding='utf-8')

if SCHEMA.exists():
    backup(SCHEMA)
    schema = SCHEMA.read_text(encoding='utf-8')
    if 'payment_interval_months' not in schema:
        schema = schema.replace('due_day INT NOT NULL,', 'due_day INT NOT NULL,\n    payment_interval_months INT NOT NULL DEFAULT 1,')
        schema = schema.replace('CONSTRAINT chk_service_due_day\n        CHECK (due_day BETWEEN 1 AND 31)', 'CONSTRAINT chk_service_due_day\n        CHECK (due_day BETWEEN 1 AND 31),\n\n    CONSTRAINT chk_service_payment_interval\n        CHECK (payment_interval_months BETWEEN 1 AND 24)')
        SCHEMA.write_text(schema, encoding='utf-8')

print('Parche aplicado.')
print('IMPORTANTE: si ya tienes la base creada, ejecuta:')
print('sudo mysql < backend/db/alter_service_payment_interval.sql')
