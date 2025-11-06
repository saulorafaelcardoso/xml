#!/bin/bash

# Script para reiniciar a aplicação Flask

echo "========================================"
echo "Reiniciando Aplicação XML SOAP Processor"
echo "========================================"
echo ""

# Para o serviço
echo "🛑 Parando serviço..."
./stop.sh

if [ $? -ne 0 ]; then
    echo "⚠️  Aviso: Erro ao parar serviço, continuando..."
fi

echo ""
sleep 2

# Inicia o serviço
echo "🚀 Iniciando serviço..."
./start.sh

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Reinicialização concluída com sucesso!"
else
    echo ""
    echo "❌ Erro na reinicialização"
    exit 1
fi

echo "========================================"
