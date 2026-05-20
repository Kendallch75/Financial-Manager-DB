# Patch: Efectivo por defecto en transacciones

Este parche modifica `frontend/src/main.jsx` para que, al entrar a **Transacciones**, el campo **Cuenta afectada** seleccione automáticamente la cuenta llamada **Efectivo**.

Si no encuentra una cuenta exactamente llamada `Efectivo`, intenta encontrar una que contenga esa palabra. Si tampoco existe, usa la primera cuenta disponible.

El usuario puede cambiar la cuenta manualmente.

## Instalación

Desde la raíz del proyecto:

```bash
cd /home/kendal/Documentos/financial_manager_login_clean
unzip /home/kendal/Descargas/financial_manager_default_cash_account_patch.zip
python3 apply_default_cash_account_patch.py
```

Si el archivo está en Downloads:

```bash
unzip /home/kendal/Downloads/financial_manager_default_cash_account_patch.zip
python3 apply_default_cash_account_patch.py
```

Luego reinicia el frontend:

```bash
cd /home/kendal/Documentos/financial_manager_login_clean/frontend
npm run dev -- --host 0.0.0.0
```

## Respaldo

El script crea un respaldo en:

```text
frontend/src/main.jsx.backup_default_cash_account
```
