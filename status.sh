#!/bin/bash

# Script para verificar status da aplicação Flask

PORT=54129
PID_FILE="app.pid"
LOG_FILE="app.log"

echo "========================================"
echo "Status da Aplicação XML SOAP Processor"
echo "========================================"
echo ""

# Verifica arquivo PID
if [ -f "$PID_FILE" ]; then
    PID=$(cat $PID_FILE)
    echo "📄 Arquivo PID encontrado: $PID"

    # Verifica se processo está rodando
    if ps -p $PID > /dev/null 2>&1; then
        echo "✅ Aplicação está RODANDO (PID: $PID)"

        # Informações do processo
        echo ""
        echo "📊 Informações do Processo:"
        ps -p $PID -o pid,ppid,%cpu,%mem,etime,cmd --no-headers

        # Uso de memória
        echo ""
        echo "💾 Memória:"
        ps -p $PID -o rss --no-headers | awk '{printf "   RAM: %.2f MB\n", $1/1024}'

    else
        echo "❌ Aplicação NÃO está rodando (PID registrado: $PID - processo morto)"
        echo "⚠️  Removendo arquivo PID obsoleto..."
        rm $PID_FILE
    fi
else
    echo "⚠️  Arquivo PID não encontrado"
    echo "❌ Aplicação provavelmente NÃO está rodando"
fi

# Verifica porta
echo ""
echo "🔍 Verificando porta $PORT..."
PORT_PID=$(lsof -ti:$PORT 2>/dev/null)

if [ ! -z "$PORT_PID" ]; then
    echo "✅ Porta $PORT está em uso pelo processo PID: $PORT_PID"

    # Verifica se é o PID esperado
    if [ -f "$PID_FILE" ] && [ "$PORT_PID" != "$PID" ]; then
        echo "⚠️  AVISO: PID na porta ($PORT_PID) diferente do PID registrado ($PID)"
    fi
else
    echo "❌ Porta $PORT está LIVRE (nenhum processo usando)"
fi

# Verifica acessibilidade
echo ""
echo "🌐 Verificando acessibilidade..."
if curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "✅ Aplicação está ACESSÍVEL em http://localhost:$PORT"
else
    echo "❌ Aplicação NÃO está acessível"
fi

# Informações do log
echo ""
if [ -f "$LOG_FILE" ]; then
    LOG_SIZE=$(du -h $LOG_FILE | cut -f1)
    LOG_LINES=$(wc -l < $LOG_FILE)
    echo "📝 Arquivo de Log:"
    echo "   Arquivo: $LOG_FILE"
    echo "   Tamanho: $LOG_SIZE"
    echo "   Linhas: $LOG_LINES"
    echo ""
    echo "📋 Últimas 5 linhas do log:"
    echo "   ────────────────────────────────────"
    tail -n 5 $LOG_FILE | sed 's/^/   /'
    echo "   ────────────────────────────────────"
else
    echo "⚠️  Arquivo de log não encontrado"
fi

# Resumo
echo ""
echo "========================================"
echo "📌 Resumo:"

if [ -f "$PID_FILE" ] && ps -p $(cat $PID_FILE) > /dev/null 2>&1 && curl -s http://localhost:$PORT/ > /dev/null 2>&1; then
    echo "   Status: ✅ OPERACIONAL"
    echo "   URL: http://localhost:$PORT"
elif [ ! -z "$PORT_PID" ]; then
    echo "   Status: ⚠️  PARCIAL (processo rodando mas pode ter problemas)"
else
    echo "   Status: ❌ PARADO"
    echo "   Para iniciar: ./start.sh"
fi

echo "========================================"
