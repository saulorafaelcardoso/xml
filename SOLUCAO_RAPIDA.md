# ⚡ Solução Rápida - Erro de XML

## ❌ Seu Erro

```
Erro de formatação XML (Linha 1, Coluna 772):
Caractere problemático: 'i' (código ASCII/Unicode: 105)
Contexto: ...Di�rio de Justi�a Eletr�nico...
```

Os caracteres `�` indicam **problema de encoding**!

---

## ✅ Solução (1 comando)

```bash
python fix_encoding.py seu_arquivo.xml
```

Isso irá:
1. ✅ Detectar encoding correto automaticamente
2. ✅ Converter `Di�rio` → `Diário`
3. ✅ Converter `Justi�a` → `Justiça`
4. ✅ Converter `Eletr�nico` → `Eletrônico`
5. ✅ Salvar em UTF-8: `seu_arquivo_corrigido.xml`
6. ✅ Validar XML

---

## 📋 Passo a Passo

### 1. Corrigir Encoding

```bash
# Corrige os acentos (� → á, é, í, ó, ú, ç)
python fix_encoding.py publicacoes.xml
```

**Resultado:** `publicacoes_corrigido.xml`

### 2. Processar (escolha um)

**Via Web (mais fácil):**
```bash
./start.sh
# Acesse: http://localhost:54129
# Faça upload de: publicacoes_corrigido.xml
```

**Via Linha de Comando:**
```bash
python xml_processor.py publicacoes_corrigido.xml
```

---

## 🎯 O que Aconteceu?

Seu arquivo foi salvo com **Windows-1252** ou **Latin-1**, mas está sendo lido como **UTF-8**.

### Antes (Windows-1252):
```
Diário  = byte E1
Justiça = byte E7
```

### Lido como UTF-8 (errado):
```
byte E1 = � (caractere inválido)
byte E7 = � (caractere inválido)
```

### Depois da Correção:
```
Diário  = UTF-8 correto (C3 A1)
Justiça = UTF-8 correto (C3 A7)
```

---

## 🔧 Ferramentas Disponíveis

| Problema | Ferramenta | Comando |
|----------|------------|---------|
| Caracteres � | `fix_encoding.py` | `python fix_encoding.py arquivo.xml` |
| Entidades HTML | `xml_cleaner.py` | `python xml_cleaner.py arquivo.xml` |
| Duplicatas | Interface Web | `./start.sh` + navegador |

---

## 📚 Documentação Completa

- `GUIA_ENCODING.md` - Tudo sobre encoding
- `SOLUCAO_PROBLEMAS_XML.md` - Outros problemas XML
- `README.md` - Documentação completa
- `INICIO_RAPIDO.md` - Guia de 3 passos

---

## ⚠️ Se Ainda Houver Erros

Após corrigir encoding, se ainda houver problemas XML:

```bash
# 1. Corrigir encoding
python fix_encoding.py arquivo.xml

# 2. Limpar XML (entidades, caracteres inválidos)
python xml_cleaner.py arquivo_corrigido.xml

# 3. Processar
python xml_processor.py arquivo_limpo.xml
```

---

## 💡 Dica

Para **ver todos os encodings testados** e escolher manualmente:

```bash
python fix_encoding.py arquivo.xml
```

O script mostra:
```
1. ⚠️  utf-8          - Substituições:  25 | Score:  -100
2. ✅ windows-1252   - Substituições:   0 | Score:   150  ← MELHOR
3. ✅ latin-1        - Substituições:   0 | Score:   150
```

---

## 🎉 Resumo

```bash
# Corrige acentos
python fix_encoding.py seu_arquivo.xml

# Processa
./start.sh
# Acesse: http://localhost:54129
```

**Pronto! 🚀**

---

**Tem dúvidas?** Veja `GUIA_ENCODING.md` para detalhes completos.
