#!/bin/bash

# Script para mostrar informações de acesso à rede

PORT=54129

echo "========================================"
echo "Informações de Acesso à Rede"
echo "========================================"
echo ""

# Verifica se a aplicação está rodando
if ! lsof -ti:$PORT > /dev/null 2>&1; then
    echo "❌ Aplicação NÃO está rodando na porta $PORT"
    echo ""
    echo "Para iniciar: ./start.sh"
    exit 1
fi

echo "✅ Aplicação está rodando na porta $PORT"
echo ""
echo "🌐 URLs de Acesso:"
echo ""
echo "───────────────────────────────────────"

# Localhost
echo "📍 Acesso Local (mesma máquina):"
echo "   http://localhost:$PORT"
echo "   http://127.0.0.1:$PORT"
echo ""

# IPs da rede local
echo "📡 Acesso via Rede Local:"

# Tenta vários métodos para pegar IPs
if command -v ip &> /dev/null; then
    # Usa comando ip (mais moderno)
    IPS=$(ip -4 addr show | grep -oP '(?<=inet\s)\d+(\.\d+){3}' | grep -v '127.0.0.1')
elif command -v ifconfig &> /dev/null; then
    # Usa ifconfig (mais antigo)
    IPS=$(ifconfig | grep -Eo 'inet (addr:)?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*' | grep -v '127.0.0.1')
elif command -v hostname &> /dev/null; then
    # Usa hostname como fallback
    IPS=$(hostname -I 2>/dev/null | tr ' ' '\n' | grep -v '127.0.0.1')
fi

if [ -z "$IPS" ]; then
    echo "   ⚠️  Não foi possível detectar IPs automaticamente"
    echo ""
    echo "   Execute manualmente para ver seus IPs:"
    echo "   hostname -I"
    echo "   ou"
    echo "   ifconfig"
else
    for IP in $IPS; do
        echo "   http://$IP:$PORT"
    done
fi

echo ""
echo "───────────────────────────────────────"
echo ""
echo "📝 Como acessar de outros dispositivos:"
echo ""
echo "   1. Certifique-se de que os dispositivos estão"
echo "      na mesma rede (WiFi ou LAN)"
echo ""
echo "   2. Use um dos IPs de rede local acima"
echo ""
echo "   3. Exemplo: http://192.168.1.100:$PORT"
echo ""
echo "───────────────────────────────────────"
echo ""
echo "🔥 Firewall:"

# Verifica se ufw está ativo
if command -v ufw &> /dev/null; then
    UFW_STATUS=$(sudo ufw status 2>/dev/null | grep -i "status:" | awk '{print $2}')

    if [ "$UFW_STATUS" == "active" ]; then
        echo "   ⚠️  UFW Firewall está ATIVO"
        echo ""
        echo "   Para permitir acesso externo, execute:"
        echo "   sudo ufw allow $PORT/tcp"
        echo ""

        # Verifica se a porta já está liberada
        if sudo ufw status | grep -q "$PORT"; then
            echo "   ✅ Porta $PORT já está liberada no firewall"
        else
            echo "   ❌ Porta $PORT NÃO está liberada no firewall"
        fi
    else
        echo "   ✅ UFW Firewall está inativo"
    fi
elif command -v firewall-cmd &> /dev/null; then
    echo "   ℹ️  firewalld detectado"
    echo ""
    echo "   Para permitir acesso externo, execute:"
    echo "   sudo firewall-cmd --permanent --add-port=$PORT/tcp"
    echo "   sudo firewall-cmd --reload"
else
    echo "   ✅ Nenhum firewall detectado ou gerenciado"
fi

echo ""
echo "───────────────────────────────────────"
echo ""
echo "🧪 Testar conectividade:"
echo ""
echo "   De outro dispositivo na mesma rede, execute:"
echo "   curl http://[IP_DA_MÁQUINA]:$PORT"
echo ""
echo "   Ou simplesmente abra o endereço no navegador"
echo ""
echo "========================================"
