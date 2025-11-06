# 📜 Guia de Scripts Shell

Scripts para gerenciamento do servidor XML SOAP Processor em ambiente Linux.

---

## 🚀 Scripts Disponíveis

### 1. `install.sh` - Instalação e Configuração

Instala todas as dependências e prepara o ambiente.

```bash
./install.sh
```

**O que faz:**
- ✅ Verifica Python3 e pip
- ✅ Instala dependências do requirements.txt
- ✅ Configura permissões dos scripts
- ✅ Cria diretórios necessários
- ✅ Verifica disponibilidade da porta 54129

**Execute apenas UMA VEZ na primeira instalação.**

---

### 2. `start.sh` - Iniciar Servidor

Inicia o servidor Flask na porta 54129.

```bash
./start.sh
```

**O que faz:**
- 🔍 Verifica se Python e Flask estão instalados
- 🔪 Mata processos existentes na porta 54129
- 🚀 Inicia aplicação em background
- 📝 Salva PID em `app.pid`
- 📊 Cria log em `app.log`

**Saída esperada:**
```
========================================
Iniciando Aplicação XML SOAP Processor
========================================
🔍 Verificando porta 54129...
✅ Porta 54129 está livre
🚀 Iniciando aplicação...
✅ Aplicação iniciada com sucesso!
📊 PID: 12345
🌐 URL: http://localhost:54129
📝 Logs: tail -f app.log
========================================
```

---

### 3. `stop.sh` - Parar Servidor

Para o servidor em execução.

```bash
./stop.sh
```

**O que faz:**
- 📄 Lê PID do arquivo `app.pid`
- 🔪 Envia SIGTERM (15) ao processo
- 🔨 Força SIGKILL (9) se necessário
- 🧹 Limpa porta 54129
- 🗑️ Remove arquivo PID

**Saída esperada:**
```
========================================
Parando Aplicação XML SOAP Processor
========================================
🔪 Matando processo PID: 12345
✅ Aplicação parada com sucesso!
✅ Serviço parado completamente
========================================
```

---

### 4. `restart.sh` - Reiniciar Servidor

Reinicia o servidor (para + inicia).

```bash
./restart.sh
```

**O que faz:**
- 🛑 Executa `stop.sh`
- ⏳ Aguarda 2 segundos
- 🚀 Executa `start.sh`

**Use quando:**
- Fez alterações no código
- Quer recarregar configurações
- Aplicação está com problemas

---

### 5. `status.sh` - Verificar Status

Mostra status detalhado do servidor.

```bash
./status.sh
```

**O que faz:**
- 📄 Verifica arquivo PID
- 🔍 Verifica se processo está rodando
- 📊 Mostra uso de CPU e memória
- 🔌 Verifica porta 54129
- 🌐 Testa acessibilidade HTTP
- 📝 Mostra últimas linhas do log

**Saída esperada:**
```
========================================
Status da Aplicação XML SOAP Processor
========================================

📄 Arquivo PID encontrado: 12345
✅ Aplicação está RODANDO (PID: 12345)

📊 Informações do Processo:
 12345     1  2.3  0.2       00:14 python3 app.py

💾 Memória:
   RAM: 38.41 MB

🔍 Verificando porta 54129...
✅ Porta 54129 está em uso pelo processo PID: 12345

🌐 Verificando acessibilidade...
✅ Aplicação está ACESSÍVEL em http://localhost:54129

========================================
📌 Resumo:
   Status: ✅ OPERACIONAL
   URL: http://localhost:54129
========================================
```

---

### 6. `network-info.sh` - Informações de Rede

Mostra todos os IPs para acesso local e remoto.

```bash
./network-info.sh
```

**O que faz:**
- 🌐 Lista URLs de acesso localhost
- 📡 Lista IPs da rede local
- 🔥 Verifica configuração de firewall
- 📝 Mostra instruções de acesso remoto

**Saída esperada:**
```
========================================
Informações de Acesso à Rede
========================================

✅ Aplicação está rodando na porta 54129

🌐 URLs de Acesso:

───────────────────────────────────────
📍 Acesso Local (mesma máquina):
   http://localhost:54129
   http://127.0.0.1:54129

📡 Acesso via Rede Local:
   http://192.168.1.100:54129
   http://10.0.0.50:54129

───────────────────────────────────────
```

---

## 🔄 Fluxo de Trabalho Típico

### Primeira vez:

```bash
# 1. Instalar
./install.sh

# 2. Iniciar
./start.sh

# 3. Ver IPs de acesso
./network-info.sh

# 4. Acessar no navegador
# http://localhost:54129
```

### Uso diário:

```bash
# Iniciar
./start.sh

# Verificar status
./status.sh

# Parar quando terminar
./stop.sh
```

### Quando fizer alterações no código:

```bash
# Reiniciar
./restart.sh

# Verificar logs
tail -f app.log
```

### Para troubleshooting:

```bash
# 1. Ver status completo
./status.sh

# 2. Ver logs em tempo real
tail -f app.log

# 3. Ver IPs disponíveis
./network-info.sh

# 4. Reiniciar se necessário
./restart.sh
```

---

## 📂 Arquivos Criados

Após executar os scripts, estes arquivos são criados:

- `app.pid` - PID do processo em execução
- `app.log` - Logs da aplicação
- `uploads/` - Pasta para arquivos enviados via web

---

## 🔥 Configuração de Firewall

### UFW (Ubuntu/Debian):

```bash
# Permitir porta 54129
sudo ufw allow 54129/tcp

# Verificar
sudo ufw status
```

### Firewalld (CentOS/RHEL):

```bash
# Permitir porta 54129
sudo firewall-cmd --permanent --add-port=54129/tcp
sudo firewall-cmd --reload

# Verificar
sudo firewall-cmd --list-ports
```

---

## 🐛 Solução de Problemas

### Erro: "Permission denied"

```bash
chmod +x *.sh
```

### Erro: "Address already in use"

```bash
./stop.sh
# ou force com lsof
sudo lsof -ti:54129 | xargs sudo kill -9
```

### Erro: "Python/Flask not found"

```bash
./install.sh
```

### Aplicação não inicia:

```bash
# Ver erros no log
cat app.log

# Testar manualmente
python3 app.py
```

### Não consigo acessar de outro computador:

```bash
# 1. Ver IPs disponíveis
./network-info.sh

# 2. Verificar firewall
sudo ufw status

# 3. Liberar porta se necessário
sudo ufw allow 54129/tcp
```

---

## 📝 Logs

### Ver logs em tempo real:

```bash
tail -f app.log
```

### Ver logs completos:

```bash
cat app.log
```

### Limpar logs:

```bash
> app.log
```

---

## 🔐 Segurança

⚠️ **IMPORTANTE:**

- O servidor roda em modo DEBUG (development)
- Não use em produção sem configurar WSGI
- Para produção, use Gunicorn ou uWSGI
- Configure HTTPS para tráfego externo

### Exemplo com Gunicorn (produção):

```bash
# Instalar
pip install gunicorn

# Executar
gunicorn -w 4 -b 0.0.0.0:54129 app:app
```

---

## 📞 Precisa de Ajuda?

Consulte:
- [README.md](README.md) - Documentação completa
- [INICIO_RAPIDO.md](INICIO_RAPIDO.md) - Guia rápido
- Logs: `app.log`
