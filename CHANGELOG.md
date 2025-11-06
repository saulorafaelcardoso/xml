# Changelog

## v1.01 - 2025-11-06

### Corrigido
- Problema de encoding em XML (caracteres � corrompidos)
- Adicionado `fix_encoding.py` para corrigir automaticamente
- Detecta 9 tipos de encoding diferentes
- Converte para UTF-8
- Melhora diagnóstico de erros em `app.py`

### Adicionado
- `fix_encoding.py` - Corretor automático de encoding
- Detecção automática de encoding correto
- Validação XML após correção

### Uso
```bash
python fix_encoding.py arquivo.xml
```

## v1.00 - 2025-11-06

### Inicial
- Processador XML SOAP para publicações
- Interface web na porta 54129
- Remoção de duplicatas
- Scripts shell de gerenciamento
- Linha de comando e interface web
