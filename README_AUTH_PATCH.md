# Parche mínimo de login y cuentas independientes

Este parche mantiene la estructura visual del frontend original y agrega autenticación por sesión.

## Cambios principales

- Al abrir `http://localhost:5173`, primero aparece login/registro.
- Se conserva la cuenta demo: `demo@flujex.local` / `demo1234`.
- Ya no se muestra la gestión manual de usuarios en el menú.
- El frontend ya no envía `id_user` al crear categorías, cuentas o servicios.
- El backend toma el usuario desde `request.session`.
- Cada usuario ve solo sus cuentas, categorías, servicios, movimientos, límites y dashboard.

## Archivos reemplazados

```text
backend/config/settings.py
backend/core/serializers.py
backend/core/views.py
backend/core/urls.py
frontend/src/services/api.js
frontend/src/main.jsx
frontend/src/styles.css
```
