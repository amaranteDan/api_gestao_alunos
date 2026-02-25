#!/bin/bash
# Script para iniciar o servidor em modo de produção

echo "Iniciando API Sistema Escolar em modo produção..."
echo "========================================"

# Ativa ambiente virtual se existir
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Cria diretório de logs
mkdir -p logs

# Inicia servidor com 4 workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level warning
