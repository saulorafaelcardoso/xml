# Changelog

## v1.04 - 2025-11-06

### Adicionado
- **Correção automática de encoding**: Sistema agora detecta e corrige problemas de encoding automaticamente durante o upload
- Integração direta no `app.py` - não precisa mais usar script separado
- Detecta 9 tipos de encoding: UTF-8, UTF-8-sig, Windows-1252, CP1252, Latin-1, ISO-8859-1, ISO-8859-15, CP850, CP437
- Converte automaticamente para UTF-8 antes de processar o XML

### Corrigido
- Erro "Caractere problemático: 'i'" com Di�rio, Justi�a, Eletr�nico
- Arquivos com encoding Windows-1252 agora são detectados e convertidos automaticamente
- Eliminada necessidade de usar `fix_encoding.py` manualmente

### Como funciona
1. Ao fazer upload, sistema detecta encoding do arquivo
2. Se não for UTF-8, converte automaticamente
3. Processa o XML normalmente

## v1.03 - 2025-11-06

### Adicionado
- **Análise de Similaridade via API**: Integração com API externa para comparar textos de duplicatas
- Comparação automática do campo `despachoPublicacao` entre ocorrências do mesmo processo
- API endpoint: `http://extracao-rtx.corejur.com.br:5000/duplicidades`
- Campos retornados: `analise_juridica`, `interpretacao`, `sao_similares`
- Exibição visual da análise no relatório com badges de status
- Tratamento de erros e timeout (30s) nas chamadas da API
- Adicionada biblioteca `requests` às dependências

### Interface
- Nova seção "Análise de Similaridade (API)" em cada grupo de duplicatas
- Badges coloridos: Verde (Similares), Vermelho (Diferentes), Amarelo (Erro)
- Exibe análise jurídica e interpretação para cada comparação
- CSS estilizado para seção de análise

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
