# Parche: moneda principal y valores por defecto en transacciones

Este parche modifica `frontend/src/main.jsx`.

## Qué cambia

1. En **Cuentas**, el campo `currency` queda como **Moneda principal** y se usa como selección entre:
   - `CRC`
   - `USD`
   - `EUR`

2. En **Transacciones**, la fecha `movement_date` aparece por defecto con la fecha de hoy.

3. En **Transacciones**, al escoger la **Cuenta afectada**, la moneda de la transacción `original_currency` se rellena automáticamente con la moneda principal de esa cuenta.
   - El usuario todavía puede cambiarla manualmente.

## Instalación

Copia este ZIP dentro de la raíz del proyecto y descomprímelo, o descomprímelo donde quieras y ejecuta el script desde la raíz del proyecto.

Ruta esperada del proyecto:

```bash
/home/kendal/Documentos/financial_manager_login_clean
```

Ejecuta:

```bash
cd /home/kendal/Documentos/financial_manager_login_clean
python3 apply_currency_defaults_patch.py
```

Luego reinicia el frontend:

```bash
cd /home/kendal/Documentos/financial_manager_login_clean/frontend
npm run dev -- --host 0.0.0.0
```

Y abre:

```text
http://192.168.40.95:5173
```

## Respaldo

El script crea un respaldo automático:

```text
frontend/src/main.jsx.backup_currency_defaults
```

Si algo sale mal, puedes restaurarlo con:

```bash
cd /home/kendal/Documentos/financial_manager_login_clean
cp frontend/src/main.jsx.backup_currency_defaults frontend/src/main.jsx
```

## Nota

Este parche no hace migraciones de base de datos. La columna de moneda ya existe; el cambio principal es de interfaz y comportamiento del formulario.
