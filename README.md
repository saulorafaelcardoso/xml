# Processador de XML SOAP - Publicações

Sistema para processar arquivos XML SOAP de publicações, identificar duplicatas e gerar relatórios e arquivos limpos.

**Disponível em duas versões:**
- 🌐 **Aplicação Web** (recomendado) - Interface gráfica acessível pelo navegador
- 💻 **Linha de Comando** - Script Python para uso via terminal

## 📋 Funcionalidades

1. **Leitura de XML SOAP**: Processa arquivos XML no formato SOAP com publicações
2. **Identificação de Duplicatas**: Detecta publicações duplicadas baseado em:
   - Número do Processo
   - Data de Publicação
   - Ano de Publicação
   - Código de Publicação
3. **Relatório Detalhado**: Gera relatório com todas as duplicatas encontradas
4. **Remoção de Duplicatas**: Cria novo XML sem as duplicatas (mantendo apenas a primeira ocorrência)

## 🚀 Como Usar

### 🌐 Aplicação Web (Recomendado)

#### 1. Instalar dependências

```bash
pip install -r requirements.txt
```

#### 2. Iniciar o servidor

```bash
python app.py
```

#### 3. Acessar no navegador

Abra seu navegador e acesse:
- `http://localhost:54129`
- ou `http://127.0.0.1:54129`

#### 4. Usar a interface

1. **Upload**: Clique e selecione seu arquivo XML
2. **Análise**: O sistema processa automaticamente e mostra o relatório
3. **Download**: Clique em "Baixar XML Sem Duplicatas" para obter o arquivo limpo

---

### 💻 Linha de Comando

#### 1. Requisitos

- Python 3.6 ou superior
- Nenhuma biblioteca externa necessária (usa apenas bibliotecas padrão do Python)

#### 2. Uso Básico

**Gerar apenas o relatório de duplicatas:**

```bash
python xml_processor.py arquivo.xml
```

Isso irá:
- Carregar o arquivo XML
- Identificar duplicatas
- Gerar o arquivo `relatorio_duplicatas.txt`

**Gerar relatório e XML sem duplicatas:**

```bash
python xml_processor.py arquivo.xml --remover-duplicatas
```

Isso irá:
- Carregar o arquivo XML
- Identificar duplicatas
- Gerar o arquivo `relatorio_duplicatas.txt`
- Solicitar confirmação do usuário
- Gerar o arquivo `output_sem_duplicatas.xml` (após confirmação)

#### 3. Exemplo com Arquivo de Teste

```bash
# Apenas relatório
python xml_processor.py exemplo_input.xml

# Relatório + remoção de duplicatas
python xml_processor.py exemplo_input.xml --remover-duplicatas
```

## 📁 Arquivos Gerados

### relatorio_duplicatas.txt

Relatório detalhado contendo:
- Total de publicações analisadas
- Quantidade de grupos de duplicatas
- Detalhes de cada grupo de duplicatas
- Informações de cada ocorrência duplicada

Exemplo:
```
================================================================================
RELATÓRIO DE PUBLICAÇÕES DUPLICADAS
Data: 05/11/2025 19:30:15
================================================================================

Total de publicações analisadas: 6
Grupos de duplicatas encontrados: 2
Total de publicações duplicadas: 5
Publicações únicas a manter: 3

================================================================================

********************************************************************************
GRUPO DE DUPLICATAS #1
********************************************************************************

Número do Processo: 5006751-41.2025.8.24.0019
Data de Publicação: 30/09/2025
Ano de Publicação: 2025
Código de Publicação: 8579156502
Quantidade de duplicatas: 3

  --- Ocorrência 1 (Índice: 0) ---
  Diário: TJSCDJEN
  Órgão: DJEN - Diário de Justiça Eletrônico Nacional - TJSC
  ...
```

### output_sem_duplicatas.xml

Arquivo XML no mesmo formato do original, mas contendo apenas uma ocorrência de cada publicação (mantém sempre a primeira).

## 🔍 Critérios de Duplicação

Uma publicação é considerada duplicata quando possui **todos** os seguintes campos idênticos:

1. `numeroProcesso` - Número do processo
2. `dataPublicacao` - Data de publicação
3. `anoPublicacao` - Ano de publicação
4. `codPublicacao` - Código de publicação

## 📊 Exemplo de Saída

```
================================================================================
PROCESSADOR DE XML SOAP - PUBLICAÇÕES
================================================================================

✓ XML carregado com sucesso: exemplo_input.xml
✓ 6 publicações encontradas
✓ 2 grupos de duplicatas identificados
✓ Relatório gerado: relatorio_duplicatas.txt

--------------------------------------------------------------------------------

Deseja gerar o XML sem duplicatas? (s/n): s

✓ Removendo 3 publicações duplicadas...
✓ XML limpo gerado: output_sem_duplicatas.xml
  Publicações originais: 6
  Publicações removidas: 3
  Publicações restantes: 3

================================================================================
PROCESSAMENTO CONCLUÍDO
================================================================================
```

## 🛠️ Estrutura do Projeto

```
xml/
├── app.py                     # Aplicação web Flask (porta 54129)
├── xml_processor.py           # Script linha de comando
├── requirements.txt           # Dependências Python
├── exemplo_input.xml          # Arquivo XML de exemplo (com duplicatas)
├── README.md                  # Esta documentação
├── templates/                 # Templates HTML
│   ├── base.html             # Template base
│   ├── index.html            # Página inicial
│   └── relatorio.html        # Página de relatório
├── static/                    # Arquivos estáticos
│   └── css/
│       └── style.css         # Estilos CSS
├── uploads/                   # Pasta para uploads (criada automaticamente)
├── relatorio_duplicatas.txt   # Relatório gerado (CLI)
└── output_sem_duplicatas.xml  # XML limpo gerado (CLI)
```

## 🔧 Personalização

Para alterar os critérios de duplicação, edite o método `identificar_duplicatas()` no arquivo `xml_processor.py`:

```python
def identificar_duplicatas(self) -> List[Tuple[str, List[Dict]]]:
    # Modifique a chave conforme necessário
    chave = (
        pub.get('numeroProcesso', ''),
        pub.get('dataPublicacao', ''),
        # Adicione ou remova campos aqui
    )
```

## 📝 Notas

- O sistema sempre mantém a **primeira ocorrência** de cada duplicata
- O relatório mostra todas as ocorrências para análise
- O XML gerado mantém a estrutura e formatação original
- Nenhuma publicação única é removida

## 🐛 Resolução de Problemas

### Erro: "Não foi possível encontrar getPublicacoesResult"

Verifique se o XML possui a estrutura correta do SOAP Envelope com o elemento `getPublicacoesResult`.

### Erro ao carregar XML

- Verifique se o arquivo existe no caminho especificado
- Confirme que o arquivo está em formato XML válido
- Verifique a codificação do arquivo (deve ser UTF-8)

## 📄 Licença

Este projeto é de código aberto e está disponível para uso livre.

## 👥 Contribuições

Contribuições são bem-vindas! Sinta-se à vontade para:
- Reportar bugs
- Sugerir melhorias
- Enviar pull requests

## 📧 Suporte

Para questões e suporte, abra uma issue no repositório.
