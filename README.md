# FLUJEX - Financial Manager

Aplicación web responsiva para la gestión de finanzas personales y flujo de caja.

El proyecto está dividido en:

```text
Financial-Manager-DB/
├── backend/
│   ├── config/
│   ├── core/
│   ├── db/
│   └── manage.py
└── frontend/
```

## 1. Tecnologías

- Backend: Django + Django REST Framework
- Base de datos: MySQL
- Frontend: React + Vite
- CORS: django-cors-headers
- Variables de entorno: python-dotenv

## 2. Base de datos

El proyecto incluye scripts SQL separados en:

```text
backend/db/
├── init_db.sql
├── schema.sql
├── indexes.sql
├── queries.sql
└── sample_data.sql
```

### Archivos SQL

- `init_db.sql`: crea la base de datos `flujex` y el usuario `flujex_user`.
- `schema.sql`: crea las tablas principales.
- `indexes.sql`: crea índices para optimización.
- `queries.sql`: contiene consultas típicas del proyecto.
- `sample_data.sql`: inserta datos de prueba.

### Tablas principales

- `USER`
- `CATEGORY`
- `ACCOUNT`
- `SERVICE`
- `EXCHANGE_RATE`
- `MOVEMENT`
- `ACCOUNT_LIMIT`

## 3. Crear la base de datos con scripts SQL

Desde la raíz del proyecto:

```bash
sudo mysql < backend/db/init_db.sql
sudo mysql < backend/db/schema.sql
sudo mysql < backend/db/indexes.sql
```

Opcionalmente, insertar datos demo:

```bash
sudo mysql < backend/db/sample_data.sql
```

Usuario demo:

```text
Email: demo@flujex.local
Contraseña: demo1234
```

> Nota: la contraseña demo funciona porque el hash fue generado con Django.

## 4. Backend Django

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
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

## 5. Frontend React

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

## 6. Normalización

La base de datos está planteada hasta Tercera Forma Normal.

### Primera Forma Normal

Cada tabla tiene atributos atómicos y cada registro se identifica con una llave primaria.

Ejemplo:

- `USER.id_user`
- `CATEGORY.id_category`
- `ACCOUNT.id_account`
- `MOVEMENT.id_movement`

### Segunda Forma Normal

Las tablas usan llaves primarias simples, por lo que los atributos no clave dependen completamente de su llave primaria.

Ejemplo:

- En `MOVEMENT`, `amount`, `description` y `movement_date` dependen de `id_movement`.

### Tercera Forma Normal

Se evita guardar datos repetidos que dependan de otras entidades.

Ejemplo:

- `MOVEMENT` no guarda el nombre del usuario.
- `MOVEMENT` referencia `ACCOUNT` y `CATEGORY`.
- `CATEGORY` y `ACCOUNT` referencian `USER`.

Esto evita dependencias transitivas y mejora la integridad de los datos.

## 7. Consultas típicas

El archivo `backend/db/queries.sql` incluye consultas para:

- Obtener movimientos de un usuario.
- Resumir gastos por categoría.
- Resumir ingresos por categoría.
- Calcular balance por cuenta.
- Ver servicios próximos a vencer.
- Ver grupos de transferencia.

## 8. Notas importantes

Este proyecto mantiene Django como backend funcional, pero agrega los scripts SQL separados para documentar y demostrar el diseño de la base de datos.

La carpeta `backend/db/` funciona como evidencia del diseño relacional, creación de tablas, restricciones, llaves foráneas, índices y consultas.
