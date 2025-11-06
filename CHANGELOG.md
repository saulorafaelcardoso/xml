# Changelog

## v1.02 - 2025-11-06

### Alterado
- **Regra de duplicidade simplificada**: Agora identifica duplicatas apenas pelo campo `numeroProcesso`
- Anteriormente verificava: numeroProcesso + dataPublicacao + anoPublicacao + codPublicacao
- Agora verifica apenas: numeroProcesso

### Adicionado
- DataTables na página de relatório para melhor visualização
- Tabela interativa com busca, ordenação e paginação
- Tradução para português (pt-BR)
- 9 colunas: Grupo, Nº Processo, Data Pub., Ano, Código, Ocorrência, Status, Diário, Órgão
- Exibição de 25 registros por página

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
