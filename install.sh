#!/bin/bash

# Script de instalação e configuração inicial

echo "========================================"
echo "Instalação XML SOAP Processor"
echo "========================================"
echo ""

# Verifica Python
echo "🔍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 não encontrado!"
    echo "   Instale com: sudo apt-get install python3 python3-pip"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✅ Python encontrado: $PYTHON_VERSION"

# Verifica pip
echo ""
echo "🔍 Verificando pip..."
if ! command -v pip3 &> /dev/null && ! command -v pip &> /dev/null; then
    echo "❌ pip não encontrado!"
    echo "   Instale com: sudo apt-get install python3-pip"
    exit 1
fi
echo "✅ pip encontrado"

# Instala dependências
echo ""
echo "📦 Instalando dependências Python..."
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt

    if [ $? -eq 0 ]; then
        echo "✅ Dependências instaladas com sucesso!"
    else
        echo "❌ Erro ao instalar dependências"
        exit 1
    fi
else
    echo "❌ Arquivo requirements.txt não encontrado!"
    exit 1
fi

# Dá permissões de execução aos scripts
echo ""
echo "🔧 Configurando permissões dos scripts..."
chmod +x start.sh stop.sh restart.sh status.sh install.sh

if [ $? -eq 0 ]; then
    echo "✅ Permissões configuradas!"
else
    echo "⚠️  Aviso: Erro ao configurar permissões"
fi

# Cria pasta de uploads se não existir
echo ""
echo "📁 Criando diretórios necessários..."
mkdir -p uploads

if [ $? -eq 0 ]; then
    echo "✅ Diretório 'uploads' criado/verificado"
else
    echo "⚠️  Aviso: Erro ao criar diretório"
fi

# Verifica porta 54129
echo ""
echo "🔍 Verificando porta 54129..."
if lsof -ti:54129 > /dev/null 2>&1; then
    echo "⚠️  Porta 54129 está em uso!"
    echo "   Execute './stop.sh' para liberar a porta"
else
    echo "✅ Porta 54129 está livre"
fi

# Resumo
echo ""
echo "========================================"
echo "✅ Instalação Concluída!"
echo "========================================"
echo ""
echo "📝 Próximos passos:"
echo ""
echo "   1. Iniciar o servidor:"
echo "      ./start.sh"
echo ""
echo "   2. Verificar status:"
echo "      ./status.sh"
echo ""
echo "   3. Acessar no navegador:"
echo "      http://localhost:54129"
echo ""
echo "   4. Ver logs em tempo real:"
echo "      tail -f app.log"
echo ""
echo "Comandos disponíveis:"
echo "   ./start.sh    - Inicia o servidor"
echo "   ./stop.sh     - Para o servidor"
echo "   ./restart.sh  - Reinicia o servidor"
echo "   ./status.sh   - Mostra status do servidor"
echo ""
echo "========================================"
