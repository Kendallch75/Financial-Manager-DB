# FLUJEX - Proyecto completo

Estructura recomendada:

```text
flujex_full_project/
├── backend/
└── frontend/
```

## 1. Backend Django

```bash
cd backend
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edita `.env` con tu usuario y contraseña de MySQL. Antes de migrar, crea la base de datos:

```sql
CREATE DATABASE flujex_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Luego ejecuta:

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py runserver
```

La API queda en:

```text
http://127.0.0.1:8000/api/
```

Endpoints principales:

```text
/api/users/
/api/categories/
/api/accounts/
/api/services/
/api/movements/
/api/exchange-rates/
/api/account-limits/
/api/dashboard/
```

## 2. Frontend React

En otra terminal:

```bash
cd frontend
npm install
npm run dev
```

El frontend queda en:

```text
http://localhost:5173
```

Por defecto consume:

```text
http://127.0.0.1:8000/api
```

Si necesitas cambiarlo, crea un archivo `.env` en `frontend/`:

```env
VITE_API_URL=http://127.0.0.1:8000/api
```

## 3. Nota importante

Las tablas del backend respetan la propuesta definitiva:

- USER
- CATEGORY
- ACCOUNT
- SERVICE
- EXCHANGE_RATE
- MOVEMENT
- ACCOUNT_LIMIT

