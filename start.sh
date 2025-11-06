#!/bin/bash

# Script para iniciar a aplicação Flask na porta 54129

PORT=54129
APP_FILE="app.py"
LOG_FILE="app.log"
PID_FILE="app.pid"

echo "========================================"
echo "Iniciando Aplicação XML SOAP Processor"
echo "========================================"

# Verifica se o arquivo da aplicação existe
if [ ! -f "$APP_FILE" ]; then
    echo "❌ Erro: Arquivo $APP_FILE não encontrado!"
    exit 1
fi

# Verifica se Python está instalado
if ! command -v python3 &> /dev/null; then
    echo "❌ Erro: Python3 não está instalado!"
    exit 1
fi

# Verifica se Flask está instalado
if ! python3 -c "import flask" &> /dev/null; then
    echo "⚠️  Flask não encontrado. Instalando dependências..."
    pip install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ Erro ao instalar dependências!"
        exit 1
    fi
fi

# Mata qualquer processo usando a porta 54129
echo "🔍 Verificando porta $PORT..."
PID=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PID" ]; then
    echo "⚠️  Porta $PORT em uso pelo processo PID: $PID"
    echo "🔪 Matando processo..."
    kill -9 $PID
    sleep 2

    # Verifica novamente
    PID=$(lsof -ti:$PORT 2>/dev/null)
    if [ ! -z "$PID" ]; then
        echo "❌ Erro: Não foi possível liberar a porta $PORT"
        exit 1
    fi
    echo "✅ Porta $PORT liberada!"
else
    echo "✅ Porta $PORT está livre"
fi

# Remove PID file antigo se existir
if [ -f "$PID_FILE" ]; then
    rm "$PID_FILE"
fi

# Inicia a aplicação em background
echo "🚀 Iniciando aplicação..."
nohup python3 $APP_FILE > $LOG_FILE 2>&1 &
APP_PID=$!

# Salva o PID
echo $APP_PID > $PID_FILE

# Aguarda alguns segundos para verificar se iniciou corretamente
sleep 3

# Verifica se o processo está rodando
if ps -p $APP_PID > /dev/null; then
    echo "✅ Aplicação iniciada com sucesso!"
    echo "📊 PID: $APP_PID"
    echo "🌐 URL: http://localhost:$PORT"
    echo "📝 Logs: tail -f $LOG_FILE"
    echo ""
    echo "Para parar o serviço, execute: ./stop.sh"
else
    echo "❌ Erro: Aplicação falhou ao iniciar"
    echo "📝 Verifique o arquivo de log: $LOG_FILE"
    rm $PID_FILE 2>/dev/null
    exit 1
fi

echo "========================================"
