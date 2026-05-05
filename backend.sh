#!/bin/bash

PROJECT_DIR="/home/kendal/Documentos/financial_manager/backend"

echo "🟢 Iniciando Backend..."

cd "$PROJECT_DIR" || exit

# Crear venv si no existe
if [ ! -d "venv" ]; then
  echo "⚙️ Creando entorno virtual..."
  python3 -m venv venv
fi

# Activar venv
source venv/bin/activate

# Instalar dependencias si faltan
./venv/bin/python -m pip install --upgrade pip
./venv/bin/python -m pip install django djangorestframework django-cors-headers mysqlclient python-dotenv

# Migraciones
./venv/bin/python manage.py makemigrations
./venv/bin/python manage.py migrate

# Levantar servidor
echo "🚀 Backend corriendo en http://127.0.0.1:8000"
./venv/bin/python manage.py runserver

