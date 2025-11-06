# 🔧 Solução de Problemas - XML Mal Formatado

## ❌ Erro: "not well-formed (invalid token)"

Se você recebeu este erro ao processar seu XML, significa que há caracteres ou formatação inválida no arquivo.

---

## 🚀 Solução Rápida

Use a ferramenta **XML Cleaner** para limpar automaticamente o arquivo:

```bash
python xml_cleaner.py seu_arquivo.xml
```

Isso irá:
- ✅ Remover caracteres de controle inválidos
- ✅ Corrigir entidades HTML comuns (&nbsp;, &copy;, etc)
- ✅ Detectar & não escapados
- ✅ Remover BOM (Byte Order Mark)
- ✅ Validar o XML resultante
- ✅ Criar arquivo limpo: `seu_arquivo_limpo.xml`

---

## 🔍 Entendendo o Erro

O erro mostra:
```
not well-formed (invalid token): line 1, column 772
```

Isso significa:
- **Linha 1**: Primeira linha do arquivo
- **Coluna 772**: 772º caractere da linha
- **invalid token**: Há um caractere ou sequência inválida nessa posição

---

## 🐛 Causas Comuns

### 1. **Caracteres Especiais Não Escapados**

❌ **Errado:**
```xml
<texto>Empresa A & B</texto>
```

✅ **Correto:**
```xml
<texto>Empresa A &amp; B</texto>
```

**Regras de escape:**
- `&` → `&amp;`
- `<` → `&lt;`
- `>` → `&gt;`
- `"` → `&quot;`
- `'` → `&apos;`

### 2. **Entidades HTML Não Reconhecidas**

❌ **Errado:**
```xml
<texto>Copyright &copy; 2025</texto>
```

✅ **Correto:**
```xml
<texto>Copyright © 2025</texto>
<!-- ou -->
<texto>Copyright &#169; 2025</texto>
```

### 3. **Caracteres de Controle Inválidos**

Caracteres com código ASCII < 32 (exceto tab, newline, carriage return) são inválidos em XML.

### 4. **Problema de Encoding**

O arquivo deve estar em UTF-8. Se estiver em outro encoding (ISO-8859-1, Windows-1252, etc), pode causar problemas.

---

## 🛠️ Ferramentas de Diagnóstico

### 1. **XML Cleaner (Recomendado)**

```bash
# Limpa e valida
python xml_cleaner.py arquivo.xml

# Especifica arquivo de saída
python xml_cleaner.py arquivo.xml arquivo_limpo.xml
```

**Saída esperada:**
```
🔍 Lendo arquivo: arquivo.xml
📏 Tamanho original: 150000 caracteres
🧹 Removendo caracteres de controle inválidos...
🔧 Corrigindo entidades HTML...
💾 Salvando arquivo limpo: arquivo_limpo.xml

============================================================
📊 RELATÓRIO DE LIMPEZA
============================================================

✅ 3 problema(s) corrigido(s):
   1. Removidos 5 caracteres de controle inválidos
   2. Substituídas 10 ocorrências de &nbsp;
   3. Removido BOM (Byte Order Mark)

📉 Redução: 15 caracteres removidos
📁 Arquivo salvo em: arquivo_limpo.xml
============================================================
```

### 2. **Melhor Diagnóstico de Erro**

A aplicação web agora mostra:
- ✅ Linha e coluna exatas do erro
- ✅ Caractere problemático
- ✅ Código ASCII/Unicode do caractere
- ✅ Contexto (50 caracteres antes/depois)
- ✅ Possíveis causas
- ✅ Sugestões de correção

---

## 📝 Verificação Manual

### 1. Verificar Encoding

```bash
# Linux/Mac
file -bi arquivo.xml

# Deve mostrar: charset=utf-8
```

Se não for UTF-8, converta:

```bash
# Usando iconv
iconv -f ISO-8859-1 -t UTF-8 arquivo.xml > arquivo_utf8.xml
```

### 2. Procurar & Não Escapados

```bash
# Procura & que não são parte de entidades
grep -n '[^&]&[^a-z#]' arquivo.xml
```

### 3. Verificar Caracteres de Controle

```bash
# Mostra caracteres não imprimíveis
cat -A arquivo.xml | head -20
```

---

## 🔧 Correção Manual

### Opção 1: Editor de Texto

1. Abra o arquivo em um editor que mostra caracteres invisíveis:
   - VSCode (View > Render Whitespace)
   - Notepad++  (View > Show Symbol > Show All Characters)
   - Vim (`:set list`)

2. Vá para a linha e coluna indicadas no erro

3. Identifique e corrija o problema

### Opção 2: Expressões Regulares

```python
import re

# Lê o arquivo
with open('arquivo.xml', 'r', encoding='utf-8', errors='replace') as f:
    conteudo = f.read()

# Remove caracteres de controle
conteudo = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F]', '', conteudo)

# Substitui entidades HTML comuns
conteudo = conteudo.replace('&nbsp;', ' ')
conteudo = conteudo.replace('&copy;', '©')

# Salva
with open('arquivo_limpo.xml', 'w', encoding='utf-8') as f:
    f.write(conteudo)
```

### Opção 3: Usar o XML Cleaner

Já explicado acima! 😉

---

## 🌐 Validadores Online

Se ainda tiver problemas, use validadores online:

1. **XML Validator** - https://www.xmlvalidation.com/
2. **Code Beautify** - https://codebeautify.org/xmlvalidator
3. **FreeFormatter** - https://www.freeformatter.com/xml-validator-xsd.html

Cole seu XML e veja todos os erros listados.

---

## 📊 Exemplo Prático

### XML com Problema:

```xml
<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <nome>Empresa A & B</nome>              <!-- & não escapado -->
    <descricao>Copyright &copy; 2025</descricao>  <!-- entidade HTML -->
    <texto>Teste[CHAR:0x01]Fim</texto>      <!-- caractere de controle -->
  </item>
</root>
```

### Após Limpeza:

```xml
<?xml version="1.0" encoding="utf-8"?>
<root>
  <item>
    <nome>Empresa A &amp; B</nome>
    <descricao>Copyright © 2025</descricao>
    <texto>TesteFim</texto>
  </item>
</root>
```

---

## ⚙️ Configuração da Aplicação

A aplicação web foi atualizada para:

1. ✅ **Diagnóstico Detalhado**
   - Mostra linha, coluna e caractere problemático
   - Exibe contexto do erro
   - Lista possíveis causas

2. ✅ **Mensagens Claras**
   - Erros formatados e legíveis
   - Sugestões de correção
   - Links para esta documentação

3. ✅ **Tratamento de Encoding**
   - Tenta UTF-8 primeiro
   - Fallback para outros encodings
   - Substitui caracteres inválidos se necessário

---

## 🚨 Problemas Persistentes?

Se mesmo após usar o XML Cleaner o problema persiste:

### 1. Verifique o Arquivo Original

```bash
# Tamanho
ls -lh arquivo.xml

# Primeiras linhas
head -20 arquivo.xml

# Últimas linhas
tail -20 arquivo.xml

# Procura por caracteres estranhos
hexdump -C arquivo.xml | head -50
```

### 2. Teste com Arquivo Pequeno

Crie um XML mínimo para testar:

```xml
<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Body>
    <getPublicacoesResponse xmlns="http://tempuri.org/">
      <getPublicacoesResult>
        <publicacao>
          <numeroProcesso>TESTE</numeroProcesso>
        </publicacao>
      </getPublicacoesResult>
    </getPublicacoesResponse>
  </soap:Body>
</soap:Envelope>
```

Se funcionar, o problema está no arquivo grande.

### 3. Divida o Arquivo

Se o arquivo for muito grande, divida em partes menores e processe separadamente.

---

## 📞 Precisa de Ajuda?

1. Use o **XML Cleaner**: `python xml_cleaner.py arquivo.xml`
2. Veja os **logs detalhados** na aplicação web
3. Consulte esta documentação
4. Use **validadores online** para identificar todos os erros

---

## ✅ Checklist de Verificação

Antes de processar o XML:

- [ ] Arquivo está em UTF-8?
- [ ] Sem BOM (Byte Order Mark)?
- [ ] Caracteres especiais escapados (&amp;, &lt;, &gt;)?
- [ ] Sem entidades HTML (&nbsp;, &copy;, etc)?
- [ ] Sem caracteres de controle (ASCII < 32)?
- [ ] Estrutura XML válida (tags abertas/fechadas)?
- [ ] Namespaces declarados corretamente?

Use o **XML Cleaner** para garantir todos os itens! ✨

---

**🎉 Seu XML estará pronto para processar!**
