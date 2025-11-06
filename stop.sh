#!/bin/bash

# Script para parar a aplicação Flask

PORT=54129
PID_FILE="app.pid"

echo "========================================"
echo "Parando Aplicação XML SOAP Processor"
echo "========================================"

# Verifica se existe arquivo PID
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)

    # Verifica se o processo está rodando
    if ps -p $PID > /dev/null 2>&1; then
        echo "🔪 Matando processo PID: $PID"
        kill -15 $PID
        sleep 2

        # Força se ainda estiver rodando
        if ps -p $PID > /dev/null 2>&1; then
            echo "⚠️  Processo ainda ativo, forçando..."
            kill -9 $PID
            sleep 1
        fi

        # Verifica se parou
        if ! ps -p $PID > /dev/null 2>&1; then
            echo "✅ Aplicação parada com sucesso!"
            rm $PID_FILE
        else
            echo "❌ Erro: Não foi possível parar o processo"
            exit 1
        fi
    else
        echo "⚠️  Processo PID $PID não está rodando"
        rm $PID_FILE
    fi
else
    echo "⚠️  Arquivo PID não encontrado"
fi

# Mata qualquer processo usando a porta como backup
PID_PORT=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PID_PORT" ]; then
    echo "⚠️  Encontrado processo adicional na porta $PORT (PID: $PID_PORT)"
    echo "🔪 Matando processo..."
    kill -9 $PID_PORT
    sleep 1

    if [ -z "$(lsof -ti:$PORT 2>/dev/null)" ]; then
        echo "✅ Porta $PORT liberada!"
    else
        echo "❌ Erro: Não foi possível liberar a porta"
        exit 1
    fi
fi

echo "✅ Serviço parado completamente"
echo "========================================"
