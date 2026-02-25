#!/bin/bash
# Script para iniciar o servidor em modo de desenvolvimento

echo "Iniciando API Sistema Escolar em modo desenvolvimento..."
echo "========================================"

# Ativa ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Cria diretório de logs
mkdir -p logs

# Inicia servidor com reload automático
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --log-level info
