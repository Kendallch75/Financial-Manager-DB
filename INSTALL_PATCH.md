# Cómo aplicar estos archivos al proyecto clonado

Supongamos que tu repo original está aquí:

```bash
/home/kendal/Documentos/financial_manager_git_original
```

Y esta carpeta de parche está descomprimida en Descargas.

## 1. Copiar archivos

Desde la carpeta del parche:

```bash
cp -r backend /home/kendal/Documentos/financial_manager_git_original/
cp README.md /home/kendal/Documentos/financial_manager_git_original/README.md
```

Esto reemplaza los archivos corregidos y agrega `backend/db/`.

## 2. Eliminar migraciones viejas de core

Como los archivos del repo estaban aplastados en una sola línea, conviene regenerar migraciones:

```bash
cd /home/kendal/Documentos/financial_manager_git_original/backend
rm -f core/migrations/000*.py
touch core/migrations/__init__.py
```

## 3. Crear base con SQL

Desde la raíz del proyecto:

```bash
cd /home/kendal/Documentos/financial_manager_git_original
sudo mysql < backend/db/init_db.sql
sudo mysql < backend/db/schema.sql
sudo mysql < backend/db/indexes.sql
sudo mysql < backend/db/sample_data.sql
```

## 4. Levantar backend

```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate --fake-initial
python manage.py runserver
```

## 5. Levantar frontend

En otra terminal:

```bash
cd /home/kendal/Documentos/financial_manager_git_original/frontend
npm install
npm run dev
```

## 6. Subir cambios

```bash
cd /home/kendal/Documentos/financial_manager_git_original
git add .
git commit -m "Agregar scripts SQL y corregir backend"
git push
```
