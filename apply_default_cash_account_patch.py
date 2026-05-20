from pathlib import Path
import re
import shutil

ROOT = Path.cwd()
MAIN = ROOT / 'frontend' / 'src' / 'main.jsx'

if not MAIN.exists():
    raise SystemExit(
        'No encontré frontend/src/main.jsx. Ejecutá este script desde la raíz del proyecto: '
        '/home/kendal/Documentos/financial_manager_login_clean'
    )

text = MAIN.read_text(encoding='utf-8')
backup = MAIN.with_suffix('.jsx.backup_default_cash_account')
if not backup.exists():
    shutil.copy2(MAIN, backup)

# 1) Insert helper functions inside CrudPage. They choose "Efectivo" as default account.
helper = r'''
  function findDefaultCashAccount(accounts) {
    if (!accounts || accounts.length === 0) return null;

    const byName = accounts.find((account) =>
      String(account.account_name || '').trim().toLowerCase() === 'efectivo'
    );
    if (byName) return byName;

    const byContainsName = accounts.find((account) =>
      String(account.account_name || '').trim().toLowerCase().includes('efectivo')
    );
    if (byContainsName) return byContainsName;

    return accounts[0];
  }

  function applyDefaultCashAccountIfNeeded() {
    if (config.endpoint !== '/movements/' || editing) return;

    const accounts = lookups['/accounts/'] || [];
    const defaultAccount = findDefaultCashAccount(accounts);
    if (!defaultAccount) return;

    setForm((prev) => {
      if (prev.id_account) return prev;

      return {
        ...prev,
        id_account: String(defaultAccount.id_account),
        original_currency: defaultAccount.currency || prev.original_currency || 'CRC',
      };
    });
  }
'''

if 'function findDefaultCashAccount(accounts)' not in text:
    # Prefer to insert before updateFormField if previous currency patch is installed.
    marker = '  function updateFormField(field, value) {'
    pos = text.find(marker)
    if pos == -1:
        # Fallback: insert before renderCell in older main.jsx versions.
        marker = '  function renderCell(row, field) {'
        pos = text.find(marker)
    if pos == -1:
        raise SystemExit('No pude ubicar dónde insertar la lógica de cuenta Efectivo en CrudPage.')
    text = text[:pos] + helper + '\n' + text[pos:]

# 2) Add effect after lookups load or when editing ends.
effect = r'''
  useEffect(() => {
    applyDefaultCashAccountIfNeeded();
  }, [config.endpoint, editing, lookups]);
'''

if 'applyDefaultCashAccountIfNeeded();' not in text[text.find('function CrudPage'):]:
    # insert after the useEffect that handles config.endpoint change, if possible
    pattern = r"  useEffect\(\(\) => \{\n    setRows\(\[\]\);[\s\S]*?loadLookups\(\);\n  \}, \[config\.endpoint\]\);"
    m = re.search(pattern, text)
    if m:
        insert_at = m.end()
        text = text[:insert_at] + '\n' + effect + text[insert_at:]
    else:
        marker = '  function cleanPayload() {'
        pos = text.find(marker)
        if pos == -1:
            raise SystemExit('No pude insertar el useEffect para aplicar Efectivo por defecto.')
        text = text[:pos] + effect + '\n' + text[pos:]

# 3) After a successful submit, reset form with Efectivo as soon as lookups are available.
# Existing setForm(emptyForm(config.fields)) remains; the new useEffect will refill id_account automatically.

MAIN.write_text(text, encoding='utf-8')

print('Patch aplicado correctamente.')
print(f'Respaldo creado en: {backup}')
print('Cambio realizado:')
print('- En Transacciones, Cuenta afectada queda por defecto en Efectivo si existe.')
print('- El usuario puede cambiarla manualmente.')
print('- La moneda de la transacción sigue tomándose de la cuenta seleccionada.')
