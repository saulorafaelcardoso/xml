# Changelog

## v1.11 - 2025-11-06

### Otimizado - IMPORTANTE
- **Processamento paralelo de chamadas de API**: Agora executa 3 análises simultâneas
- Velocidade até **3x mais rápida** no processamento de duplicatas
- Mantém integridade e ordem dos dados no XML

### Implementação Técnica
- ThreadPoolExecutor com `max_workers=3` para processar chamadas de API em paralelo
- Thread-safety garantida com locks para contadores e progresso
- Sistema de mapeamento de tarefas → resultados para preservar ordem exata
- Progresso em tempo real continua funcionando durante processamento paralelo

### Como Funciona
1. **Preparação**: Coleta todas as tarefas de API que precisam ser executadas
2. **Execução Paralela**: Processa 3 chamadas de API simultaneamente
3. **Consolidação**: Insere resultados na ordem correta (não bagunça o XML)

### Benefícios
- ⚡ **3x mais rápido**: 3 análises por vez ao invés de 1
- 🔒 **Seguro**: Thread-safe com locks apropriados
- 📊 **Organizado**: Mantém ordem exata dos dados
- 💻 **Eficiente**: Melhor uso dos recursos do servidor

### Logs Aprimorados
```
📊 Total de comparações necessárias: 565
💰 Chamadas de API previstas: 565
⚡ Processamento paralelo: 3 análises simultâneas

🚀 Iniciando processamento paralelo de 565 chamadas de API...
🔍 Grupo 2, ocorrência 3: Chamando API (processo: 0800123-45.2024.8.24.0000)
🔍 Grupo 5, ocorrência 2: Chamando API (processo: 0800456-78.2024.8.24.0000)
🔍 Grupo 7, ocorrência 4: Chamando API (processo: 0800789-01.2024.8.24.0000)

✅ Chamadas de API realizadas: 200
⏭️ Chamadas economizadas: 365
💰 Economia: 64.6%
⚡ Velocidade: 3x mais rápido com processamento paralelo
```

## v1.10 - 2025-11-06

### Adicionado
- **Painel de informações na barra de progresso**
- Mostra em tempo real:
  - 📄 Total de Publicações encontradas no XML
  - 🔄 Total de Grupos Duplicados
- Números formatados com separador de milhares (pt-BR)
- Design em grid com 2 colunas destacadas

### Melhorado
- Mensagens mais informativas durante o processamento:
  - "✅ 1.452 publicações encontradas!"
  - "📊 Publicações: 1.452 | Grupos duplicados: 334"
- Valores aparecem assim que são calculados (não precisa esperar o fim)
- Interface mais profissional e informativa

### Visual
- Painel roxo/azul com bordas destacadas
- Números grandes e em negrito
- Atualização em tempo real via polling

## v1.09 - 2025-11-06

### Melhorado
- **Número do processo agora aparece na barra de progresso**
- Mensagens mais detalhadas durante processamento:
  - Mostra o número completo do processo sendo analisado
  - Exibe grupo atual e total de grupos
  - Exibe ocorrência atual e total de ocorrências do grupo
  - Diferencia quando está comparando vs consultando API

### Formato das mensagens
```
📋 Processo: 0800123-45.2024.8.24.0000
🔍 Grupo 2/5 - Comparando ocorrência 3/4
```
ou
```
📋 Processo: 0800123-45.2024.8.24.0000
⏳ Consultando API... (Grupo 2/5, Ocorrência 3/4)
```

### Técnico
- CSS ajustado para exibir múltiplas linhas (white-space: pre-line)
- JavaScript usa textContent para preservar quebras de linha
- Altura da mensagem aumentada para 60px (comportar 2 linhas)

## v1.08 - 2025-11-06

### Corrigido - IMPORTANTE
- **Barra de progresso agora aparece durante o upload/processamento** (antes só aparecia depois)
- Fluxo correto: Upload → Barra de progresso → Relatório

### Alterado
- Processamento agora roda em thread separada (background)
- Upload redireciona imediatamente para página de processamento
- Nova rota `/processando` com barra de progresso em tela cheia
- Rota `/relatorio` agora pega dados já processados (não reprocessa)

### Adicionado
- Template `processando.html` - página dedicada para mostrar progresso
- Spinner animado durante processamento
- Auto-redirecionamento para relatório ao concluir
- Tratamento de erros com mensagem e redirecionamento

### Melhorias UX
- Feedback visual IMEDIATO ao clicar em "Processar Arquivo"
- Usuário vê barra de progresso desde o início
- Não precisa esperar "em branco" durante processamento
- Experiência mais fluida e profissional

## v1.07 - 2025-11-06

### Adicionado
- **Barra de progresso em tempo real** durante análise de duplicatas
- Overlay visual que mostra:
  - Mensagem do processamento atual
  - Barra de progresso animada com porcentagem
  - Contador de comparações (atual / total)
- Atualização automática a cada 500ms via polling
- Desaparece automaticamente ao concluir

### Implementação
- Sistema thread-safe de tracking de progresso
- Endpoint `/progresso` que retorna JSON com estado atual
- JavaScript com polling automático no frontend
- CSS estilizado com gradiente roxo/azul
- Integração completa com `PublicacaoProcessor`

### Melhorias UX
- Feedback visual durante chamadas lentas de API
- Usuário vê exatamente qual grupo/ocorrência está sendo processado
- Animação suave da barra de progresso
- Não bloqueia interface após conclusão

## v1.06 - 2025-11-06

### Corrigido - IMPORTANTE
- **Campo de comparação alterado**: API agora compara `processoPublicacao` (antes era `despachoPublicacao`)
- **Critério de duplicidade**: Publicação só é considerada duplicata se API retornar `sao_similares: true`

### Alterado
- Campo exibido no template: "Processo" ao invés de "Despacho"
- Mensagens de log mais claras sobre o resultado da API:
  - ✅ "API: Similares (duplicata confirmada)" quando `sao_similares: true`
  - ❌ "API: Diferentes (NÃO é duplicata)" quando `sao_similares: false`
  - ⚠️ "API: Erro ou resultado indefinido" quando houver erro

### Adicionado
- **Novas colunas na tabela DataTables**:
  - **"Duplicada"**: Mostra se a API considerou duplicata (✓ Sim / ✗ Não / ⚠ Indefinido / Referência)
  - **"Análise Jurídica"**: Exibe resumo (100 caracteres) da análise retornada pela API
- Badges coloridos para identificar resultado:
  - Verde (✓ Sim): Publicações similares segundo a API
  - Vermelho (✗ Não): Publicações diferentes segundo a API
  - Amarelo (⚠ Indefinido): Erro ou resultado indefinido
  - Azul (Referência): Primeira ocorrência do grupo (usada como base de comparação)

### Importante
- A API agora é a fonte da verdade para determinar se duas publicações são duplicatas
- Apenas quando `sao_similares: true` a publicação é tratada como duplicata

## v1.05 - 2025-11-06

### Otimizado
- **Economia de chamadas à API de duplicidades**: Sistema agora só chama API quando realmente necessário
- 3 níveis de otimização antes de chamar API:
  1. Verifica se ambos os textos têm conteúdo (pula se vazio)
  2. Compara textos localmente primeiro (pula se idênticos)
  3. Valida se numeroProcesso é realmente igual (pula se diferente)

### Adicionado
- Logs detalhados de consumo de API:
  - Total de comparações previstas
  - Chamadas realizadas vs economizadas
  - Percentual de economia
- Validação extra de numeroProcesso em cada ocorrência
- Comparação local para textos idênticos (sem consumir API)

### Exemplo de logs
```
📊 Total de grupos de duplicatas: 5
📊 Total de comparações necessárias: 12
💰 Chamadas de API previstas: 12

⏭️ Grupo 1, ocorrência 2: Textos idênticos, pulando API
🔍 Grupo 2, ocorrência 2: Chamando API (processo: 0800123-45.2024.8.24.0000)

✅ Chamadas de API realizadas: 4
⏭️ Chamadas economizadas: 8
💰 Economia: 66.7%
```

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
