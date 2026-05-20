from pathlib import Path
import re
import shutil
from datetime import datetime

ROOT = Path.cwd()
MAIN = ROOT / 'frontend' / 'src' / 'main.jsx'

if not MAIN.exists():
    raise SystemExit(
        'No encontré frontend/src/main.jsx. Ejecutá este script desde la raíz del proyecto: '\
        '/home/kendal/Documentos/financial_manager_login_clean'
    )

text = MAIN.read_text(encoding='utf-8')
backup = MAIN.with_suffix('.jsx.backup_currency_defaults')
if not backup.exists():
    shutil.copy2(MAIN, backup)

# 1) Make labels clearer.
text = text.replace("currency: 'Moneda',", "currency: 'Moneda principal',")
text = text.replace("original_currency: 'Moneda original',", "original_currency: 'Moneda de la transacción',")

# 2) Ensure date placeholder is not a fixed old date.
text = re.sub(r"movement_date:\s*'[^']*'", "movement_date: 'Fecha de hoy'", text)

# 3) Ensure currency selects exist with the 3 standard currencies.
# If the project already has them, this keeps/normalizes them.
currency_block = """currency: [
    { value: 'CRC', label: 'CRC' },
    { value: 'USD', label: 'USD' },
    { value: 'EUR', label: 'EUR' },
  ],"""
original_currency_block = """original_currency: [
    { value: 'CRC', label: 'CRC' },
    { value: 'USD', label: 'USD' },
    { value: 'EUR', label: 'EUR' },
  ],"""

text = re.sub(r"currency:\s*\[[\s\S]*?\n\s*\],(?=\n\s*original_currency:)", currency_block, text)
text = re.sub(r"original_currency:\s*\[[\s\S]*?\n\s*\],(?=\n\s*payment_interval_months:|\n\s*\}\s*;)" , original_currency_block, text)

# If selectOptions lacks currency/original_currency, insert them after account_type block.
if "currency: [\n    { value: 'CRC'" not in text:
    marker = "  account_type: ["
    idx = text.find(marker)
    if idx != -1:
        # find end of account_type array block conservatively before currency insertion
        end_match = re.search(r"  account_type:\s*\[[\s\S]*?\n\s*\],", text[idx:])
        if end_match:
            insert_at = idx + end_match.end()
            text = text[:insert_at] + "\n  " + currency_block + "\n  " + original_currency_block + text[insert_at:]

# 4) Replace emptyForm so movements default to today and currencies default to CRC.
new_empty_form = r"""
function todayISO() {
  return new Date().toISOString().slice(0, 10);
}

function emptyForm(fields) {
  return Object.fromEntries(
    fields.map((field) => {
      if (field === 'movement_date') return [field, todayISO()];
      if (field === 'currency' || field === 'original_currency') return [field, 'CRC'];
      if (field === 'color') return [field, '#22c55e'];
      if (field === 'payment_interval_months') return [field, '1'];
      return [field, ''];
    })
  );
}
""".strip()

text, n = re.subn(r"function emptyForm\(fields\) \{[\s\S]*?\n\}", new_empty_form, text, count=1)
if n == 0:
    raise SystemExit('No pude encontrar function emptyForm(fields). No se aplicaron cambios.')

# 5) Add a controlled form updater inside CrudPage.
updater = r"""
  function updateFormField(field, value) {
    setForm((prev) => {
      const next = { ...prev, [field]: value };

      if (config.endpoint === '/movements/' && field === 'id_account') {
        const accounts = lookups['/accounts/'] || [];
        const selectedAccount = accounts.find(
          (account) => String(account.id_account) === String(value)
        );

        if (selectedAccount?.currency) {
          next.original_currency = selectedAccount.currency;
        }
      }

      return next;
    });
  }
"""

if 'function updateFormField(field, value)' not in text:
    marker = "  function renderCell(row, field) {"
    pos = text.find(marker)
    if pos == -1:
        raise SystemExit('No pude encontrar function renderCell dentro de CrudPage.')
    text = text[:pos] + updater + "\n" + text[pos:]

# 6) Use updateFormField in renderField inputs/selects/color.
text = text.replace("onChange={(e) => setForm({ ...form, [field]: e.target.value })}", "onChange={(e) => updateFormField(field, e.target.value)}")

# 7) Make currency fields look numeric/text safe and keep the date default behavior on cancel/submit via emptyForm.
MAIN.write_text(text, encoding='utf-8')

print('Patch aplicado correctamente.')
print(f'Respaldo creado en: {backup}')
print('Cambios:')
print('- Cuentas: moneda principal con opciones CRC/USD/EUR.')
print('- Transacciones: fecha por defecto = hoy.')
print('- Transacciones: moneda de la transacción se autocompleta según la cuenta origen, pero se puede cambiar.')
