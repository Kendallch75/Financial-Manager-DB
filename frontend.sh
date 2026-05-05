#!/bin/bash

PROJECT_DIR="/home/kendal/Documentos/financial_manager/frontend"

echo "🔵 Iniciando Frontend..."

cd "$PROJECT_DIR" || exit

# Instalar dependencias si no existen
if [ ! -d "node_modules" ]; then
  echo "📦 Instalando dependencias..."
  npm install
fi

# Ejecutar
echo "🚀 Frontend en http://localhost:5173"
npm run dev

