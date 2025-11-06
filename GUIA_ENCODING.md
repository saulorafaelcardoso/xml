# 🔤 Guia de Encoding - Caracteres Corrompidos (�)

## ❌ Problema: Caracteres � no XML

Se você vê caracteres `�` no erro como:

```
...DJEN - Di�rio de Justi�a Eletr�nico Nacional...
```

Isso significa **problema de encoding**! Os caracteres acentuados estão corrompidos.

---

## 🚀 Solução Rápida

Use o **Fix Encoding** para corrigir automaticamente:

```bash
python fix_encoding.py seu_arquivo.xml
```

### O que ele faz:

✅ **Testa 9 encodings diferentes**:
- UTF-8, UTF-8 com BOM
- Windows-1252 (CP1252)
- Latin-1 (ISO-8859-1)
- Latin-9 (ISO-8859-15)
- DOS encodings (CP850, CP437)

✅ **Escolhe o melhor automaticamente**:
- Conta caracteres corrompidos (�)
- Conta caracteres acentuados (á, é, í, ó, ú, ç)
- Calcula score e escolhe o vencedor

✅ **Converte para UTF-8**:
- Salva arquivo corrigido
- Valida XML
- Mostra preview

---

## 📋 Exemplo de Uso

### Seu arquivo (corrompido):

```xml
<orgaoDescricao>DJEN - Di�rio de Justi�a Eletr�nico Nacional</orgaoDescricao>
```

### Execute:

```bash
python fix_encoding.py publicacoes.xml
```

### Saída:

```
======================================================================
🔧 CORRETOR DE ENCODING XML
======================================================================

📂 Arquivo: publicacoes.xml

🔍 Testando 9 encodings...

1. ⚠️  utf-8                 - Substituições:  25 | Acentuados:  150 | Score:  -100
2. ⚠️  utf-8-sig             - Substituições:  25 | Acentuados:  150 | Score:  -100
3. ✅ windows-1252          - Substituições:   0 | Acentuados:  150 | Score:   150
4. ✅ cp1252                - Substituições:   0 | Acentuados:  150 | Score:   150
5. ✅ latin-1               - Substituições:   0 | Acentuados:  150 | Score:   150
...

======================================================================

🏆 MELHOR ENCODING: windows-1252
   • Caracteres corrompidos (�): 0
   • Caracteres acentuados: 150
   • Score: 150

💾 Salvando arquivo corrigido...
✅ Arquivo salvo: publicacoes_corrigido.xml

======================================================================
📄 PREVIEW DO CONTEÚDO (primeiras 500 caracteres):
----------------------------------------------------------------------
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
...
----------------------------------------------------------------------

🔍 BUSCANDO EXEMPLOS DE TEXTO COM ACENTUAÇÃO:
----------------------------------------------------------------------
Linha 45: ...DJEN - Diário de Justiça Eletrônico Nacional - TJSC...
Linha 112: ...Recuperação Judicial Nº 5006751-41.2025.8.24.0019/SC...
Linha 223: ...Decisão que deferiu o processamento da Recuperação...
----------------------------------------------------------------------

🔍 Validando XML...
✅ XML está bem formado!
📊 Publicações encontradas: 25

======================================================================
✅ CORREÇÃO CONCLUÍDA!
======================================================================

🎉 Próximos passos:
   1. Revise o arquivo: publicacoes_corrigido.xml
   2. Se houver erros XML, use: python xml_cleaner.py publicacoes_corrigido.xml
   3. Processe: python xml_processor.py publicacoes_corrigido.xml
      ou acesse: http://localhost:54129
```

### Arquivo corrigido:

```xml
<orgaoDescricao>DJEN - Diário de Justiça Eletrônico Nacional</orgaoDescricao>
```

✅ **Perfeito!** Agora os acentos estão corretos.

---

## 🔍 Como Funciona

### 1. Detecção Automática

O script testa cada encoding e:

```python
# Para cada encoding:
1. Lê o arquivo
2. Conta caracteres � (substituições)
3. Conta acentos brasileiros (á, é, í, ó, ú, ç, etc)
4. Calcula score = acentuados - (substituições × 10)
5. Escolhe o melhor score
```

### 2. Encodings Testados

| Encoding | Descrição | Comum em |
|----------|-----------|----------|
| `utf-8` | Unicode padrão | Linux, Web, Moderno |
| `windows-1252` | Windows padrão | Windows Brasil |
| `latin-1` | ISO-8859-1 | Sistemas antigos |
| `cp850` | DOS Latin-1 | DOS, Terminal |

### 3. Critérios de Escolha

- ✅ **Zero substituições (�)** = melhor
- ✅ **Mais acentos** = melhor
- ✅ **UTF-8** = preferido em empate

---

## 📊 Entendendo o Problema

### Por que acontece?

O XML foi criado/salvo com um encoding (ex: Windows-1252) mas você está tentando ler como UTF-8.

**Exemplo:**

| Caractere | UTF-8 | Windows-1252 |
|-----------|-------|--------------|
| á | `C3 A1` | `E1` |
| ç | `C3 A7` | `E7` |
| ô | `C3 B4` | `F4` |

Quando você lê bytes `E1` (Windows-1252 = á) como UTF-8, ele não reconhece e mostra `�`.

### Como identificar?

Procure por:
- ✅ Caracteres `�` no texto
- ✅ Acentos que deveriam existir mas não aparecem
- ✅ Palavras como "Dirio", "Justia", "Eletrnico"
- ✅ Erro: `not well-formed (invalid token)`

---

## 🛠️ Fluxo Completo de Correção

### Seu arquivo tem problemas? Siga este fluxo:

```
1. Arquivo XML com � (problema de encoding)
   ↓
2. python fix_encoding.py arquivo.xml
   ↓
3. Arquivo corrigido gerado: arquivo_corrigido.xml
   ↓
4. Ainda tem erros XML?
   SIM → python xml_cleaner.py arquivo_corrigido.xml
   NÃO → Vá para passo 5
   ↓
5. Processar:
   - Via web: http://localhost:54129
   - Via CLI: python xml_processor.py arquivo_corrigido.xml
```

---

## 🔧 Ferramentas Disponíveis

| Ferramenta | Uso | Resolve |
|------------|-----|---------|
| `fix_encoding.py` | Corrige encoding | Caracteres � corrompidos |
| `xml_cleaner.py` | Limpa XML | Caracteres inválidos, entidades |
| `xml_processor.py` | Processa XML | Duplicatas |
| `app.py` (web) | Interface web | Tudo acima |

---

## ⚠️ Casos Especiais

### 1. Ainda vejo � após correção

Se após usar o `fix_encoding.py` ainda há `�`:

```
⚠️  AVISO: Ainda há 5 caracteres corrompidos!
   O arquivo pode ter sido corrompido na origem.
```

**Solução:**
- Tente obter o arquivo original novamente
- O arquivo pode ter sido corrompido antes de chegar até você
- Alguns caracteres podem estar permanentemente perdidos

### 2. Múltiplos encodings no mesmo arquivo

Alguns arquivos misturam encodings (raro mas acontece):

```bash
# O fix_encoding escolhe o melhor "no geral"
# Pode não ser perfeito para todas as partes
```

### 3. Encoding declarado diferente do real

O XML pode declarar:
```xml
<?xml version="1.0" encoding="utf-8"?>
```

Mas estar salvo em Windows-1252! O `fix_encoding.py` detecta o encoding **real**.

---

## 📝 Verificação Manual

### Linux/Mac:

```bash
# Ver encoding atual
file -bi arquivo.xml

# Converter manualmente
iconv -f WINDOWS-1252 -t UTF-8 arquivo.xml > arquivo_utf8.xml

# Ver caracteres especiais
hexdump -C arquivo.xml | grep -E 'e1|e7|f4'
```

### Windows:

Use Notepad++:
1. Abra o arquivo
2. Menu: Encoding → Character Set
3. Teste: Western European → Windows-1252
4. Se ficar correto, salve como UTF-8

---

## 🎯 Resumo Rápido

### Viu caracteres `�`?

```bash
# PASSO 1: Corrigir encoding
python fix_encoding.py arquivo.xml

# PASSO 2: Limpar se necessário
python xml_cleaner.py arquivo_corrigido.xml

# PASSO 3: Processar
# Via web: ./start.sh
# Via CLI: python xml_processor.py arquivo_limpo.xml
```

### Não tem certeza?

```bash
# Use a ferramenta automática
python fix_encoding.py arquivo.xml

# Ela detecta e corrige tudo sozinha! 🎉
```

---

## 💡 Dicas

1. ✅ **Sempre peça arquivos em UTF-8** quando possível
2. ✅ **Use fix_encoding.py primeiro** para problemas de �
3. ✅ **Use xml_cleaner.py depois** para outros problemas XML
4. ✅ **Mantenha backups** dos arquivos originais
5. ✅ **Valide** sempre após correção

---

## 📞 Precisa de Ajuda?

**Comandos disponíveis:**

```bash
# Ajuda
python fix_encoding.py
python xml_cleaner.py

# Documentação
cat SOLUCAO_PROBLEMAS_XML.md  # Problemas gerais
cat GUIA_ENCODING.md           # Este guia
```

---

**🎉 Seus caracteres acentuados serão corrigidos!**
