# 🚀 Início Rápido - Aplicação Web

## Como iniciar a aplicação em 3 passos:

### 1️⃣ Instalar dependências

```bash
pip install -r requirements.txt
```

### 2️⃣ Iniciar o servidor

```bash
python app.py
```

Você verá:
```
================================================================================
PROCESSADOR DE XML SOAP - PUBLICAÇÕES (WEB)
================================================================================

🌐 Servidor iniciando na porta 54129...
📂 Pasta de uploads: /home/user/xml/uploads

✨ Acesse: http://localhost:54129
✨ Ou: http://127.0.0.1:54129

================================================================================
```

### 3️⃣ Acessar no navegador

Abra seu navegador e vá para:
- **http://localhost:54129**

---

## 📝 Como usar

1. **Clique** no botão "Escolher arquivo XML"
2. **Selecione** seu arquivo XML de publicações
3. **Clique** em "Processar Arquivo"
4. **Veja** o relatório de duplicatas
5. **Baixe** o XML limpo (se houver duplicatas)

---

## ✨ Recursos

- ✅ Interface web moderna e intuitiva
- ✅ Upload simples de arquivos
- ✅ Relatório visual detalhado
- ✅ Download instantâneo do XML limpo
- ✅ Processamento local (seus dados ficam no seu computador)
- ✅ Não requer conhecimento técnico

---

## 🔧 Solução de Problemas

### Erro: "Address already in use"

A porta 54129 já está em uso. Mate o processo:

```bash
# Linux/Mac
lsof -ti:54129 | xargs kill -9

# Windows
netstat -ano | findstr :54129
taskkill /PID [PID_NUMBER] /F
```

### Erro: "No module named 'flask'"

Instale o Flask:

```bash
pip install Flask==3.0.0 Werkzeug==3.0.1
```

---

## 📞 Precisa de Ajuda?

Consulte o [README.md](README.md) completo para mais detalhes e instruções avançadas.
