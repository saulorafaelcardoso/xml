#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web para Processamento de XML SOAP - Publicações
Identifica duplicatas e permite download do XML limpo
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session, Response, stream_with_context
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from werkzeug.utils import secure_filename
import secrets
import requests
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['ALLOWED_EXTENSIONS'] = {'xml'}

# Cria pastas necessárias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Dicionário global para armazenar progresso (thread-safe com lock)
progresso_global = {}
progresso_lock = threading.Lock()


def atualizar_progresso(session_id, mensagem, atual, total):
    """Atualiza o progresso de uma sessão"""
    with progresso_lock:
        # Mantém dados existentes e atualiza apenas o progresso
        if session_id not in progresso_global:
            progresso_global[session_id] = {}

        progresso_global[session_id].update({
            'mensagem': mensagem,
            'atual': atual,
            'total': total,
            'porcentagem': int((atual / total * 100)) if total > 0 else 0,
            'timestamp': time.time()
        })


def obter_progresso(session_id):
    """Obtém o progresso de uma sessão"""
    with progresso_lock:
        return progresso_global.get(session_id, None)


def limpar_progresso(session_id):
    """Remove o progresso de uma sessão"""
    with progresso_lock:
        if session_id in progresso_global:
            del progresso_global[session_id]


def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def detectar_encoding(filepath):
    """
    Detecta o encoding correto do arquivo XML
    Testa vários encodings e retorna o melhor
    """
    encodings = [
        'utf-8',
        'utf-8-sig',
        'windows-1252',
        'cp1252',
        'latin-1',
        'iso-8859-1',
        'iso-8859-15',
        'cp850',
        'cp437'
    ]

    melhor_encoding = None
    melhor_score = -999999

    for encoding in encodings:
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                conteudo = f.read()

            # Conta caracteres corrompidos
            corrupted = conteudo.count('�')

            # Conta caracteres acentuados válidos
            acentuados = sum([
                conteudo.count('á'), conteudo.count('à'), conteudo.count('ã'),
                conteudo.count('é'), conteudo.count('ê'),
                conteudo.count('í'), conteudo.count('ó'), conteudo.count('ô'),
                conteudo.count('õ'), conteudo.count('ú'), conteudo.count('ç')
            ])

            # Score: mais acentos = melhor, caracteres corrompidos = péssimo
            score = acentuados - (corrupted * 10)

            print(f"  Encoding {encoding:15s}: {acentuados:3d} acentos, {corrupted:3d} corrompidos, score: {score}")

            if score > melhor_score:
                melhor_score = score
                melhor_encoding = encoding

            # Se não tem corrupção e tem acentos, encontramos!
            if corrupted == 0 and acentuados > 0:
                print(f"✓ Encoding correto detectado: {encoding}")
                return encoding

        except (UnicodeDecodeError, UnicodeError):
            continue
        except Exception:
            continue

    print(f"✓ Melhor encoding detectado: {melhor_encoding}")
    return melhor_encoding or 'utf-8'


def corrigir_encoding_arquivo(filepath):
    """
    Corrige o encoding do arquivo XML automaticamente
    Retorna o caminho do arquivo corrigido
    """
    print(f"🔍 Detectando encoding de {os.path.basename(filepath)}...")

    encoding_correto = detectar_encoding(filepath)

    # Se já é UTF-8, não precisa corrigir
    if encoding_correto == 'utf-8':
        print("✓ Arquivo já está em UTF-8")
        return filepath

    # Lê com encoding correto e salva em UTF-8
    print(f"🔧 Convertendo de {encoding_correto} para UTF-8...")

    try:
        with open(filepath, 'r', encoding=encoding_correto) as f:
            conteudo = f.read()

        # Salva como UTF-8
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(conteudo)

        print(f"✓ Arquivo convertido com sucesso para UTF-8")
        return filepath

    except Exception as e:
        print(f"✗ Erro ao converter: {str(e)}")
        return filepath


def comparar_textos_api(texto1, texto2, max_tentativas=2):
    """
    Compara dois textos usando a API de duplicidades com retry automático
    Retorna: dict com analise_juridica, interpretacao, sao_similares
    """
    import time
    import random

    API_URL = 'http://extracao-rtx.corejur.com.br:4000/duplicidades_llm'
    TOKEN = 'Bearer 2390*Corejur*)23dads'

    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json'
    }

    payload = {
        'texto1': texto1 or '',
        'texto2': texto2 or ''
    }

    ultima_excecao = None

    # Tenta até max_tentativas vezes com backoff exponencial
    for tentativa in range(1, max_tentativas + 1):
        try:
            if tentativa > 1:
                # Backoff exponencial: 2s, 4s, 8s...
                tempo_espera = 2 ** (tentativa - 1)
                print(f"   ⏳ Aguardando {tempo_espera}s antes de tentar novamente...")
                time.sleep(tempo_espera)
                print(f"   🔄 Tentativa {tentativa}/{max_tentativas}...")

            # Pequeno delay aleatório para evitar sobrecarga simultânea
            time.sleep(random.uniform(0.1, 0.5))

            # Log ANTES da chamada com comando CURL completo
            import json
            inicio_chamada = time.time()

            # Monta comando curl para teste
            payload_json = json.dumps(payload, ensure_ascii=False)
            curl_command = f"""curl -X POST '{API_URL}' \\
  -H 'Authorization: {TOKEN}' \\
  -H 'Content-Type: application/json' \\
  --max-time 50 \\
  -d '{payload_json}'"""

            print(f"\n   📡 CHAMANDO API /duplicidades_llm (timeout: 50s)...")
            print(f"\n   🧪 TESTE MANUAL (copie e cole no terminal):")
            print(f"   {'─'*70}")
            print(f"   {curl_command.replace(chr(10), chr(10) + '   ')}")
            print(f"   {'─'*70}\n")

            response = requests.post(API_URL, headers=headers, json=payload, timeout=50)

            # Log DEPOIS da chamada
            tempo_resposta = time.time() - inicio_chamada
            print(f"   ✅ API RESPONDEU em {tempo_resposta:.1f}s")

            if response.status_code == 200:
                data = response.json()

                # Log da resposta completa da API para debug
                print(f"\n   📥 RESPOSTA DA API:")
                print(f"   ├─ sao_similares: {data.get('sao_similares')}")
                print(f"   ├─ interpretacao: {data.get('interpretacao', 'N/A')}")
                print(f"   ├─ analise_juridica (primeiros 100 chars): {str(data.get('analise_juridica', 'N/A'))[:100]}...")
                print(f"   └─ Outros campos: {[k for k in data.keys() if k not in ['sao_similares', 'interpretacao', 'analise_juridica']]}\n")

                return {
                    'sucesso': True,
                    'analise_juridica': data.get('analise_juridica', 'N/A'),
                    'interpretacao': data.get('interpretacao', 'N/A'),
                    'sao_similares': data.get('sao_similares', False)
                }
            else:
                print(f"   ⚠️ API retornou status {response.status_code}")
                return {
                    'sucesso': False,
                    'erro': f'API retornou status {response.status_code}',
                    'analise_juridica': 'Erro na API',
                    'interpretacao': f'Erro HTTP {response.status_code}',
                    'sao_similares': None
                }
        except requests.exceptions.Timeout as e:
            ultima_excecao = e
            tempo_decorrido = time.time() - inicio_chamada
            print(f"\n   {'─'*70}")
            print(f"   ⚠️  TIMEOUT NA API! (tentativa {tentativa}/{max_tentativas})")
            print(f"   {'─'*70}")
            print(f"   ⏱️  Tempo decorrido: {tempo_decorrido:.1f}s (limite: 50s)")
            print(f"   📡 Endpoint: /duplicidades_llm")
            if tentativa < max_tentativas:
                print(f"   🔄 Tentando novamente...")
                print(f"   {'─'*70}\n")
                continue
            else:
                print(f"   ❌ TIMEOUT DEFINITIVO - Todas as tentativas falharam")
                print(f"   💡 API não respondeu em {max_tentativas} tentativas de 50s")
                print(f"   {'─'*70}\n")
                return {
                    'sucesso': False,
                    'erro': f'Timeout após {max_tentativas} tentativas (50s cada)',
                    'analise_juridica': 'Timeout',
                    'interpretacao': f'API não respondeu após {max_tentativas} tentativas',
                    'sao_similares': None
                }
        except requests.exceptions.ConnectionError as e:
            ultima_excecao = e
            print(f"   ❌ Erro de conexão na tentativa {tentativa}: API recusou conexão")
            if tentativa < max_tentativas:
                tempo_espera = 3 * tentativa  # Espera mais em caso de connection refused
                print(f"   ⏳ Aguardando {tempo_espera}s (API pode estar sobrecarregada)...")
                time.sleep(tempo_espera)
                continue
            else:
                return {
                    'sucesso': False,
                    'erro': 'API recusou conexão (sobrecarga ou rate limiting)',
                    'analise_juridica': 'Erro de Conexão',
                    'interpretacao': 'API recusou conexão - servidor sobrecarregado',
                    'sao_similares': None
                }
        except Exception as e:
            ultima_excecao = e
            print(f"   ❌ Erro na tentativa {tentativa}: {str(e)}")
            if tentativa < max_tentativas:
                time.sleep(2)
                continue
            else:
                return {
                    'sucesso': False,
                    'erro': str(e),
                    'analise_juridica': f'Erro: {str(e)}',
                    'interpretacao': 'Erro ao acessar API',
                    'sao_similares': None
                }

    # Se chegou aqui, todas as tentativas falharam
    return {
        'sucesso': False,
        'erro': f'Falha após {max_tentativas} tentativas: {str(ultima_excecao)}',
        'analise_juridica': 'Erro',
        'interpretacao': 'Todas as tentativas falharam',
        'sao_similares': None
    }


class PublicacaoProcessor:
    """Classe para processar publicações em XML (SOAP ou E-mail)"""

    def __init__(self, xml_path, session_id=None):
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        self.publicacoes = []
        self.duplicatas = []
        self.session_id = session_id  # Para tracking de progresso
        self.formato_entrada = None  # 'soap' ou 'email'

    def carregar_xml(self):
        """Carrega o arquivo XML e detecta o formato"""
        try:
            # Corrige encoding automaticamente antes de parsear
            print(f"📄 Processando arquivo: {os.path.basename(self.xml_path)}")
            corrigir_encoding_arquivo(self.xml_path)

            # Tenta carregar o XML
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()

            # Detecta formato
            self.formato_entrada = self._detectar_formato()
            print(f"🔍 Formato detectado: {self.formato_entrada.upper()}")

            return True, "XML carregado com sucesso"
        except ET.ParseError as e:
            # Erro de parsing - tenta diagnosticar
            erro_msg = str(e)

            # Tenta identificar o problema
            try:
                with open(self.xml_path, 'r', encoding='utf-8', errors='replace') as f:
                    conteudo = f.read()

                # Verifica tamanho
                if len(conteudo) == 0:
                    return False, "Arquivo XML está vazio"

                # Extrai linha e coluna do erro
                import re
                match = re.search(r'line (\d+), column (\d+)', erro_msg)
                if match:
                    linha = int(match.group(1))
                    coluna = int(match.group(2))

                    # Pega contexto do erro
                    linhas = conteudo.split('\n')
                    if linha <= len(linhas):
                        linha_erro = linhas[linha - 1]
                        if coluna <= len(linha_erro):
                            inicio = max(0, coluna - 50)
                            fim = min(len(linha_erro), coluna + 50)
                            contexto = linha_erro[inicio:fim]
                            char_problema = linha_erro[coluna - 1] if coluna > 0 else '?'

                            char_code = ord(char_problema) if char_problema != '?' else 0

                            return False, (
                                f"Erro de formatação XML (Linha {linha}, Coluna {coluna}):\n\n"
                                f"Caractere problemático: '{char_problema}' (código ASCII/Unicode: {char_code})\n\n"
                                f"Contexto:\n...{contexto}...\n\n"
                                f"Possíveis causas:\n"
                                f"• Caracteres especiais não escapados (&, <, >, ', \")\n"
                                f"• Caracteres de controle inválidos (ASCII < 32)\n"
                                f"• Entidades HTML não reconhecidas (&nbsp;, &copy;, etc)\n"
                                f"• Problema de encoding (arquivo não está em UTF-8)\n\n"
                                f"Sugestões:\n"
                                f"1. Verifique o encoding do arquivo (deve ser UTF-8)\n"
                                f"2. Substitua & por &amp;, < por &lt;, > por &gt;\n"
                                f"3. Remova caracteres de controle inválidos\n"
                                f"4. Use um validador XML online para identificar todos os erros"
                            )

                return False, f"Erro ao processar XML: {erro_msg}"

            except Exception as diag_e:
                return False, f"Erro ao carregar XML: {erro_msg}"

        except Exception as e:
            return False, f"Erro inesperado ao carregar XML: {str(e)}"

    def _detectar_formato(self):
        """
        Detecta se o XML é formato SOAP ou E-mail
        SOAP: tem getPublicacoesResult e namespace http://tempuri.org/
        E-mail: tem <Arquivo><Publicacoes> simples
        """
        # Tenta encontrar elementos característicos de SOAP
        soap_element = self.root.find('.//{http://tempuri.org/}getPublicacoesResult')
        if soap_element is not None:
            return 'soap'

        # Verifica se é formato E-mail (Arquivo > Publicacoes)
        if self.root.tag == 'Arquivo' or 'Arquivo' in self.root.tag:
            # Tenta com namespace primeiro (xmlns="Arquivo")
            publicacoes = self.root.findall('{Arquivo}Publicacoes')
            if not publicacoes:
                # Tenta sem namespace
                publicacoes = self.root.findall('Publicacoes')
            if publicacoes:
                print(f"   ✓ Detectado formato E-mail ({len(publicacoes)} elementos Publicacoes)")
                return 'email'

        # Padrão: assume SOAP
        return 'soap'

    def extrair_publicacoes(self):
        """Extrai todas as publicações do XML (SOAP ou E-mail)"""
        if self.formato_entrada == 'email':
            return self._extrair_publicacoes_email()
        else:
            return self._extrair_publicacoes_soap()

    def _extrair_publicacoes_soap(self):
        """Extrai publicações do formato SOAP"""
        publicacoes = []

        # Busca por todas as publicações no XML SOAP
        pubs = self.root.findall('.//{http://tempuri.org/}publicacao')
        if not pubs:
            pubs = self.root.findall('.//publicacao')

        for pub in pubs:
            dados = {}
            for child in pub:
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                dados[tag] = child.text if child.text else ""

            dados['_element'] = pub
            publicacoes.append(dados)

        self.publicacoes = publicacoes
        return publicacoes

    def _extrair_publicacoes_email(self):
        """Extrai publicações do formato E-mail"""
        publicacoes = []

        # Busca por todos os elementos <Publicacoes>
        # Tenta com namespace primeiro
        pubs_elements = self.root.findall('{Arquivo}Publicacoes')

        # Se não encontrou, tenta sem namespace
        if not pubs_elements:
            pubs_elements = self.root.findall('Publicacoes')

        # Se ainda não encontrou, itera pelos filhos diretos
        if not pubs_elements:
            pubs_elements = []
            for elem in self.root:
                # Verifica se é exatamente 'Publicacoes', não 'Total_de_Publicacoes'
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                if tag_name == 'Publicacoes':
                    pubs_elements.append(elem)

        print(f"📧 Encontrados {len(pubs_elements)} elementos <Publicacoes>")

        for idx, pub_elem in enumerate(pubs_elements):
            dados = {}

            # Função helper para extrair texto de um elemento com namespace
            def extrair_texto(parent, nome_campo):
                # Tenta com namespace primeiro
                elem = parent.find(f'{{Arquivo}}{nome_campo}')
                if elem is None:
                    # Tenta sem namespace
                    elem = parent.find(nome_campo)
                if elem is not None and elem.text:
                    return elem.text.strip()
                return ''

            # Extrai campos simples
            dados['data'] = extrair_texto(pub_elem, 'Data')
            dados['processo'] = extrair_texto(pub_elem, 'Processo')
            dados['diario'] = extrair_texto(pub_elem, 'Diario')
            dados['identificacao'] = extrair_texto(pub_elem, 'Identificacao')
            dados['publicacao'] = extrair_texto(pub_elem, 'Publicacao')

            # Mapeia para nomes usados no SOAP
            dados['numeroProcesso'] = dados['processo']
            dados['dataPublicacao'] = dados['data']
            dados['descricaoDiario'] = dados['diario']
            dados['processoPublicacao'] = dados['publicacao']

            # Armazena elemento original
            dados['_element'] = pub_elem
            dados['_indice_original'] = idx

            # Debug: mostra o que foi extraído
            print(f"  📋 Publicação {idx+1}: Processo={dados.get('numeroProcesso', 'N/A')}, Data={dados.get('dataPublicacao', 'N/A')}")

            publicacoes.append(dados)

        self.publicacoes = publicacoes
        print(f"✅ {len(publicacoes)} publicações extraídas do formato E-mail")
        return publicacoes

    def identificar_duplicatas(self):
        """Identifica publicações duplicadas baseado apenas no numeroProcesso"""
        grupos_duplicatas = defaultdict(list)

        for idx, pub in enumerate(self.publicacoes):
            # Chave de duplicidade: apenas numeroProcesso
            chave = pub.get('numeroProcesso', '')

            grupos_duplicatas[chave].append({
                'indice': idx,
                'dados': pub
            })

        duplicatas = []
        for chave, grupo in grupos_duplicatas.items():
            if len(grupo) > 1:
                duplicatas.append((chave, grupo))

        self.duplicatas = duplicatas
        return duplicatas

    def gerar_relatorio_html(self):
        """Gera dados do relatório para exibição HTML com processamento paralelo"""
        if not self.duplicatas:
            return None

        relatorio = {
            'total_publicacoes': len(self.publicacoes),
            'grupos_duplicatas': len(self.duplicatas),
            'total_duplicadas': sum(len(grupo) for _, grupo in self.duplicatas),
            'grupos': []
        }

        relatorio['publicacoes_unicas'] = (
            relatorio['total_publicacoes'] -
            relatorio['total_duplicadas'] +
            relatorio['grupos_duplicatas']
        )

        # Calcula quantas chamadas de API serão necessárias
        total_comparacoes = sum(len(grupo) - 1 for _, grupo in self.duplicatas)
        print(f"\n📊 Total de grupos de duplicatas: {len(self.duplicatas)}")
        print(f"📊 Total de comparações necessárias: {total_comparacoes}")
        print(f"💰 Chamadas de API previstas: {total_comparacoes}")
        print(f"🚀 Processamento paralelo: 10 análises simultâneas (otimizado!)\n")

        # Atualiza progresso inicial
        if self.session_id:
            atualizar_progresso(self.session_id, 'Iniciando análise de duplicatas...', 0, total_comparacoes)

        # Contadores thread-safe
        stats_lock = threading.Lock()
        stats = {
            'chamadas_realizadas': 0,
            'chamadas_puladas': 0,
            'comparacao_atual': 0
        }

        # Primeiro passo: Preparar estruturas de dados e identificar comparações necessárias
        tarefas_api = []  # Lista de tarefas para processar em paralelo

        for idx, (chave, grupo) in enumerate(self.duplicatas, 1):
            # Validação: só processa se houver numeroProcesso válido
            if not chave or chave.strip() == '':
                print(f"⚠️ Grupo {idx}: numeroProcesso vazio, pulando...")
                continue

            # Pega dados da primeira publicação do grupo para exibição
            primeira_pub = grupo[0]['dados']
            texto_referencia = primeira_pub.get('processoPublicacao', '')

            grupo_info = {
                'numero': idx,
                'numero_processo': chave,
                'data_publicacao': primeira_pub.get('dataPublicacao', 'N/A'),
                'ano_publicacao': primeira_pub.get('anoPublicacao', 'N/A'),
                'cod_publicacao': primeira_pub.get('codPublicacao', 'N/A'),
                'quantidade': len(grupo),
                'ocorrencias': [],
                'comparacoes_api': [],
                '_tarefas': []  # Lista temporária para mapear tarefas
            }

            for i, item in enumerate(grupo, 1):
                pub = item['dados']
                texto_atual = pub.get('processoPublicacao', '')

                # Validação: verifica se numeroProcesso é realmente o mesmo
                numero_processo_atual = pub.get('numeroProcesso', '')
                if numero_processo_atual != chave:
                    print(f"⚠️ Aviso: numeroProcesso diferente no grupo {idx}, ocorrência {i}")

                ocorrencia = {
                    'numero': i,
                    'indice': item['indice'],
                    'diario': pub.get('descricaoDiario', 'N/A'),
                    'orgao': pub.get('orgaoDescricao', 'N/A'),
                    'data_divulgacao': pub.get('dataDivulgacao', 'N/A'),
                    'data_cadastro': pub.get('dataCadastro', 'N/A'),
                    'cod_integracao': pub.get('codIntegracao', 'N/A'),
                    'processo': texto_atual[:200] + '...' if len(texto_atual) > 200 else texto_atual
                }
                grupo_info['ocorrencias'].append(ocorrencia)

                # Prepara comparação se não for a primeira ocorrência
                if i > 1:
                    with stats_lock:
                        stats['comparacao_atual'] += 1
                        comparacao_num = stats['comparacao_atual']

                    # Otimização 1: Só chama API se ambos os textos têm conteúdo
                    if not texto_referencia or not texto_atual:
                        print(f"⏭️ Grupo {idx}, ocorrência {i}: processoPublicacao vazio, pulando API")
                        with stats_lock:
                            stats['chamadas_puladas'] += 1
                        continue

                    # Otimização 2: Se textos são idênticos, não precisa chamar API
                    if texto_referencia.strip() == texto_atual.strip():
                        print(f"⏭️ Grupo {idx}, ocorrência {i}: processoPublicacao idênticos, pulando API")
                        comparacao = {
                            'sucesso': True,
                            'ocorrencia_comparada': i,
                            'analise_juridica': 'Processos idênticos (comparação local)',
                            'interpretacao': 'Os processos são exatamente iguais',
                            'sao_similares': True
                        }
                        grupo_info['comparacoes_api'].append(comparacao)
                        with stats_lock:
                            stats['chamadas_puladas'] += 1
                        continue

                    # Otimização 3: Só chama API se numeroProcesso for realmente igual
                    if numero_processo_atual == chave:
                        # Adiciona tarefa para processar em paralelo
                        tarefa = {
                            'grupo_idx': idx,
                            'grupo_total': len(self.duplicatas),
                            'ocorrencia_num': i,
                            'ocorrencia_total': len(grupo),
                            'chave': chave,
                            'texto1': texto_referencia,
                            'texto2': texto_atual,
                            'comparacao_num': comparacao_num
                        }
                        tarefas_api.append(tarefa)
                        # Marca posição para inserir resultado depois
                        grupo_info['_tarefas'].append((i, len(tarefas_api) - 1))
                    else:
                        print(f"⚠️ Grupo {idx}, ocorrência {i}: numeroProcesso diferente, pulando API")
                        with stats_lock:
                            stats['chamadas_puladas'] += 1

            relatorio['grupos'].append(grupo_info)

        # Segundo passo: Processar tarefas de API em paralelo (5 por vez - OTIMIZADO!)
        print(f"\n{'='*80}")
        print(f"🚀 PREPARANDO PROCESSAMENTO PARALELO")
        print(f"{'='*80}")
        print(f"📊 Total de chamadas API necessárias: {len(tarefas_api)}")
        print(f"⚡ Workers simultâneos: 5 (otimizado para evitar sobrecarga)")
        print(f"{'='*80}")

        # Dicionário para armazenar resultados na ordem correta
        resultados = {}

        def processar_tarefa_api(tarefa):
            """Processa uma única tarefa de API"""
            idx = tarefa['grupo_idx']
            i = tarefa['ocorrencia_num']
            chave = tarefa['chave']
            total_grupos = tarefa['grupo_total']
            total_ocorrencias = tarefa['ocorrencia_total']
            comparacao_num = tarefa['comparacao_num']

            # Log de início da tarefa
            print(f"\n{'─'*80}")
            print(f"🔍 INICIANDO COMPARAÇÃO #{comparacao_num}/{total_comparacoes}")
            print(f"{'─'*80}")
            print(f"📋 Processo: {chave}")
            print(f"👥 Grupo {idx}/{total_grupos}, Ocorrência {i}/{total_ocorrencias}")
            print(f"{'─'*80}")

            # Atualiza progresso
            if self.session_id:
                mensagem = f"📋 Processo: {chave}\n⏳ Consultando API... (Grupo {idx}/{total_grupos}, Ocorrência {i}/{total_ocorrencias})"
                atualizar_progresso(self.session_id, mensagem, comparacao_num, total_comparacoes)

            # Chama API
            comparacao = comparar_textos_api(tarefa['texto1'], tarefa['texto2'])
            comparacao['ocorrencia_comparada'] = i

            with stats_lock:
                stats['chamadas_realizadas'] += 1

            return (tarefa, comparacao)

        # Calcula timeout dinâmico: estimativa de tempo necessário + margem
        # Com 5 workers e 50s por tentativa * 2 tentativas + backoff = 110s por tarefa
        # Tempo estimado: (tarefas / workers) * 110s * 1.3 de margem
        timeout_total = max(3600, int((len(tarefas_api) / 5) * 110 * 1.3))  # Mínimo 1 hora
        print(f"\n{'='*80}")
        print(f"⚙️  CONFIGURAÇÃO DO PROCESSAMENTO")
        print(f"{'='*80}")
        print(f"🚀 Workers paralelos: 5")
        print(f"⏱️  Timeout por chamada API: 50s")
        print(f"🔄 Tentativas por comparação: 2 (com backoff exponencial)")
        print(f"⏱️  Timeout total estimado: {timeout_total / 60:.1f} minutos")
        print(f"📊 Total de comparações: {len(tarefas_api)}")
        print(f"{'='*80}\n")

        # Executa tarefas em paralelo com pool de 5 threads
        cancelado = False
        import time
        tempo_inicio = time.time()

        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submete todas as tarefas
            futures = {executor.submit(processar_tarefa_api, tarefa): tarefa for tarefa in tarefas_api}
            total_tarefas = len(tarefas_api)

            print(f"\n{'='*80}")
            print(f"🚀 INICIANDO PROCESSAMENTO PARALELO")
            print(f"{'='*80}\n")

            # Coleta resultados conforme ficam prontos
            for future in as_completed(futures, timeout=timeout_total):
                # Verifica se foi cancelado
                if self.session_id:
                    progresso = obter_progresso(self.session_id)
                    if progresso and progresso.get('cancelado'):
                        print(f"\n{'='*80}")
                        print(f"⚠️  PROCESSAMENTO CANCELADO PELO USUÁRIO")
                        print(f"📊 Gerando relatório parcial com {len(resultados)} comparações...")
                        print(f"{'='*80}\n")
                        cancelado = True

                        # Gera relatório parcial IMEDIATAMENTE
                        for grupo_info in relatorio['grupos']:
                            if '_tarefas' in grupo_info:
                                for ocorrencia_num, tarefa_idx in grupo_info['_tarefas']:
                                    if tarefa_idx in resultados:
                                        grupo_info['comparacoes_api'].append(resultados[tarefa_idx])
                                del grupo_info['_tarefas']

                        # Salva relatório parcial imediatamente
                        with progresso_lock:
                            progresso_global[self.session_id]['relatorio'] = relatorio
                            progresso_global[self.session_id]['concluido'] = True

                        print(f"✅ Relatório parcial gerado! Cancelando tarefas pendentes...")

                        # ⚡ CANCELA TUDO IMEDIATAMENTE - MODO EMERGÊNCIA
                        executor.shutdown(wait=False, cancel_futures=True)
                        break

                try:
                    tarefa, comparacao = future.result(timeout=5)  # ⚡ 5 segundos - resposta rápida
                    # Armazena resultado com índice da tarefa para manter ordem
                    tarefa_idx = tarefas_api.index(tarefa)
                    resultados[tarefa_idx] = comparacao

                    # Calcula estatísticas de progresso
                    concluidas = len(resultados)
                    porcentagem = (concluidas / total_tarefas) * 100
                    tempo_decorrido = time.time() - tempo_inicio

                    # Calcula tempo estimado restante
                    if concluidas > 0:
                        tempo_por_tarefa = tempo_decorrido / concluidas
                        tarefas_restantes = total_tarefas - concluidas
                        tempo_estimado = tempo_por_tarefa * tarefas_restantes
                        taxa_processamento = concluidas / tempo_decorrido if tempo_decorrido > 0 else 0

                        # Formata tempo estimado
                        if tempo_estimado < 60:
                            tempo_fmt = f"{tempo_estimado:.0f}s"
                        else:
                            minutos = int(tempo_estimado / 60)
                            segundos = int(tempo_estimado % 60)
                            tempo_fmt = f"{minutos}m{segundos}s"

                        # Formata tempo decorrido
                        if tempo_decorrido < 60:
                            decorrido_fmt = f"{tempo_decorrido:.0f}s"
                        else:
                            minutos = int(tempo_decorrido / 60)
                            segundos = int(tempo_decorrido % 60)
                            decorrido_fmt = f"{minutos}m{segundos}s"

                        # Barra de progresso visual
                        barra_tamanho = 40
                        barra_completa = int(barra_tamanho * porcentagem / 100)
                        barra = '█' * barra_completa + '░' * (barra_tamanho - barra_completa)

                        # Resultado da comparação
                        if comparacao.get('sao_similares') == True:
                            resultado_emoji = "✅"
                            resultado_texto = "SIMILAR"
                        elif comparacao.get('sao_similares') == False:
                            resultado_emoji = "❌"
                            resultado_texto = "DIFERENTE"
                        else:
                            resultado_emoji = "⚠️"
                            resultado_texto = "INDEFINIDO"

                        # Log detalhado de progresso
                        print(f"\n┌{'─'*78}┐")
                        print(f"│ 📊 PROGRESSO: {concluidas}/{total_tarefas} ({porcentagem:.1f}%) {' '*(49-len(str(concluidas))-len(str(total_tarefas)))}│")
                        print(f"│ {barra} │")
                        print(f"│ {resultado_emoji} Resultado: {resultado_texto:<58} │")
                        print(f"│ ⏱️  Tempo decorrido: {decorrido_fmt:<52} │")
                        print(f"│ ⏳ Tempo estimado restante: {tempo_fmt:<45} │")
                        print(f"│ ⚡ Taxa: {taxa_processamento:.2f} comparações/segundo{' '*(37-len(f'{taxa_processamento:.2f}'))}│")
                        print(f"└{'─'*78}┘")

                    # Salva relatório parcial a cada 5 comparações
                    if self.session_id and len(resultados) % 5 == 0:
                        relatorio_parcial = self._montar_relatorio_parcial(relatorio, resultados)
                        with progresso_lock:
                            progresso_global[self.session_id]['relatorio'] = relatorio_parcial

                except TimeoutError:
                    concluidas = len(resultados)
                    print(f"\n{'='*80}")
                    print(f"⚠️  TIMEOUT DETECTADO!")
                    print(f"{'='*80}")
                    print(f"│ 📊 Progresso: {concluidas}/{total_tarefas} ({(concluidas/total_tarefas*100):.1f}%)")
                    print(f"│ ⏱️  A tarefa não respondeu dentro do limite de 5s")
                    print(f"│ 💡 Possível causa: API travou ou está muito lenta")
                    print(f"{'='*80}\n")
                except Exception as e:
                    concluidas = len(resultados)
                    print(f"\n{'='*80}")
                    print(f"❌ ERRO DETECTADO!")
                    print(f"{'='*80}")
                    print(f"│ 📊 Progresso: {concluidas}/{total_tarefas} ({(concluidas/total_tarefas*100):.1f}%)")
                    print(f"│ ⚠️  Tipo: {type(e).__name__}")
                    print(f"│ 💬 Mensagem: {str(e)}")
                    print(f"{'='*80}\n")

        # Terceiro passo: Inserir resultados na ordem correta nos grupos (pula se cancelado)
        if not cancelado:
            for grupo_info in relatorio['grupos']:
                if '_tarefas' in grupo_info:
                    for ocorrencia_num, tarefa_idx in grupo_info['_tarefas']:
                        if tarefa_idx in resultados:
                            grupo_info['comparacoes_api'].append(resultados[tarefa_idx])
                    # Remove lista temporária
                    del grupo_info['_tarefas']

        # Quarto passo: Marcar quais ocorrências serão removidas baseado na API
        print(f"\n{'='*80}")
        print(f"📋 MARCANDO OCORRÊNCIAS PARA REMOÇÃO")
        print(f"{'='*80}\n")

        for grupo_info in relatorio['grupos']:
            comparacoes = grupo_info.get('comparacoes_api', [])

            # Cria um dicionário de comparações por número de ocorrência
            comp_por_ocorrencia = {}
            for comp in comparacoes:
                ocorrencia_num = comp.get('ocorrencia_comparada')
                if ocorrencia_num:
                    comp_por_ocorrencia[ocorrencia_num] = comp

            # Marca cada ocorrência
            for ocorrencia in grupo_info['ocorrencias']:
                num = ocorrencia['numero']

                # Primeira ocorrência sempre mantida
                if num == 1:
                    ocorrencia['sera_removida'] = False
                    continue

                # Para outras ocorrências, verifica resultado da API
                if num in comp_por_ocorrencia:
                    comp = comp_por_ocorrencia[num]
                    sao_similares = comp.get('sao_similares')
                    interpretacao = comp.get('interpretacao', '')

                    # ✅ Remove SE: sao_similares == True OU interpretacao == "Textos idênticos"
                    if sao_similares == True or interpretacao == "Textos idênticos":
                        ocorrencia['sera_removida'] = True
                        print(f"   ✅ {grupo_info['numero_processo']}, ocorrência {num}: SERÁ REMOVIDA (sao_similares={sao_similares}, interpretacao='{interpretacao}')")
                    else:
                        ocorrencia['sera_removida'] = False
                        print(f"   ❌ {grupo_info['numero_processo']}, ocorrência {num}: SERÁ MANTIDA (sao_similares={sao_similares}, interpretacao='{interpretacao}')")
                else:
                    # Sem comparação da API, assume que não remove
                    ocorrencia['sera_removida'] = False
                    print(f"   ⚠️  {grupo_info['numero_processo']}, ocorrência {num}: SERÁ MANTIDA (sem resultado da API)")

        print(f"\n{'='*80}\n")

        # Resumo final
        tempo_total = time.time() - tempo_inicio
        if tempo_total < 60:
            tempo_total_fmt = f"{tempo_total:.1f}s"
        else:
            minutos = int(tempo_total / 60)
            segundos = int(tempo_total % 60)
            tempo_total_fmt = f"{minutos}m{segundos}s"

        taxa_final = len(resultados) / tempo_total if tempo_total > 0 else 0

        if not cancelado:
            print(f"\n{'='*80}")
            print(f"✅ PROCESSAMENTO CONCLUÍDO COM SUCESSO!")
            print(f"{'='*80}")
        else:
            print(f"\n{'='*80}")
            print(f"⚠️  PROCESSAMENTO CANCELADO - RELATÓRIO PARCIAL GERADO")
            print(f"{'='*80}")
        print(f"│")
        print(f"│ 📊 ESTATÍSTICAS FINAIS:")
        print(f"│")
        print(f"│   ✅ Chamadas realizadas: {stats['chamadas_realizadas']}")
        print(f"│   ⏭️  Chamadas economizadas: {stats['chamadas_puladas']}")
        print(f"│   💰 Economia: {(stats['chamadas_puladas'] / total_comparacoes * 100) if total_comparacoes > 0 else 0:.1f}%")
        print(f"│")
        print(f"│ ⏱️  PERFORMANCE:")
        print(f"│")
        print(f"│   ⏱️  Tempo total: {tempo_total_fmt}")
        print(f"│   ⚡ Taxa média: {taxa_final:.2f} comparações/segundo")
        print(f"│   🚀 Workers paralelos: 10 threads")
        print(f"│")
        print(f"{'='*80}\n")

        # Atualiza progresso final
        if self.session_id:
            if cancelado:
                atualizar_progresso(self.session_id,
                    f'⚠️ Processamento cancelado! {len(resultados)} de {len(tarefas_api)} comparações realizadas',
                    len(resultados), total_comparacoes)
            else:
                atualizar_progresso(self.session_id, 'Análise concluída!', total_comparacoes, total_comparacoes)

        return relatorio

    def _montar_relatorio_parcial(self, relatorio_base, resultados):
        """Monta relatório parcial com os resultados processados até o momento"""
        # Cria uma cópia do relatório base
        relatorio_parcial = {
            'total_publicacoes': relatorio_base['total_publicacoes'],
            'grupos_duplicatas': relatorio_base['grupos_duplicatas'],
            'total_duplicadas': relatorio_base['total_duplicadas'],
            'publicacoes_unicas': relatorio_base['publicacoes_unicas'],
            'grupos': []
        }

        # Copia grupos e insere resultados disponíveis
        for grupo_info in relatorio_base['grupos']:
            grupo_copia = grupo_info.copy()
            grupo_copia['ocorrencias'] = [occ.copy() for occ in grupo_info['ocorrencias']]
            grupo_copia['comparacoes_api'] = []

            if '_tarefas' in grupo_info:
                for ocorrencia_num, tarefa_idx in grupo_info['_tarefas']:
                    if tarefa_idx in resultados:
                        grupo_copia['comparacoes_api'].append(resultados[tarefa_idx])

            # Marca ocorrências para remoção no relatório parcial
            comp_por_ocorrencia = {}
            for comp in grupo_copia['comparacoes_api']:
                ocorrencia_num = comp.get('ocorrencia_comparada')
                if ocorrencia_num:
                    comp_por_ocorrencia[ocorrencia_num] = comp

            for ocorrencia in grupo_copia['ocorrencias']:
                num = ocorrencia['numero']
                if num == 1:
                    ocorrencia['sera_removida'] = False
                elif num in comp_por_ocorrencia:
                    comp = comp_por_ocorrencia[num]
                    sao_similares = comp.get('sao_similares')
                    interpretacao = comp.get('interpretacao', '')
                    ocorrencia['sera_removida'] = (sao_similares == True or interpretacao == "Textos idênticos")
                else:
                    ocorrencia['sera_removida'] = False

            relatorio_parcial['grupos'].append(grupo_copia)

        return relatorio_parcial

    def remover_duplicatas(self, output_path, relatorio=None):
        """
        Remove duplicatas e gera novo XML (SOAP ou E-mail)

        Args:
            output_path: Caminho do arquivo de saída
            relatorio: Relatório com resultados da API (opcional)
                      Se fornecido, só remove publicações confirmadas pela API
        """
        if not self.duplicatas:
            import shutil
            shutil.copy(self.xml_path, output_path)
            return True, "Nenhuma duplicata encontrada, arquivo copiado"

        # Direciona para o método apropriado conforme o formato
        if self.formato_entrada == 'email':
            return self._remover_duplicatas_email(output_path, relatorio)
        else:
            return self._remover_duplicatas_soap(output_path, relatorio)

    def _remover_duplicatas_soap(self, output_path, relatorio=None):
        """Remove duplicatas do formato SOAP"""
        indices_remover = set()

        # Se temos relatório com resultados da API, usa-o para decidir o que remover
        if relatorio and 'grupos' in relatorio:
            print(f"\n{'='*80}")
            print(f"🔍 VERIFICANDO DUPLICATAS COM RESULTADOS DA API")
            print(f"{'='*80}\n")

            for grupo_rel in relatorio['grupos']:
                numero_processo = grupo_rel.get('numero_processo', '')
                comparacoes = grupo_rel.get('comparacoes_api', [])
                ocorrencias = grupo_rel.get('ocorrencias', [])

                # Para cada comparação com a API
                for comp in comparacoes:
                    ocorrencia_num = comp.get('ocorrencia_comparada')
                    sao_similares = comp.get('sao_similares')
                    interpretacao = comp.get('interpretacao', '')

                    # ✅ SÓ REMOVE SE:
                    # 1. sao_similares == True OU
                    # 2. interpretacao == "Textos idênticos"
                    if sao_similares == True or interpretacao == "Textos idênticos":
                        # Encontra o índice real da publicação
                        if ocorrencia_num and ocorrencia_num <= len(ocorrencias):
                            indice = ocorrencias[ocorrencia_num - 1]['indice']
                            indices_remover.add(indice)
                            print(f"   ✅ Processo {numero_processo}, ocorrência {ocorrencia_num}: DUPLICATA CONFIRMADA - será removida")
                    else:
                        print(f"   ❌ Processo {numero_processo}, ocorrência {ocorrencia_num}: NÃO é duplicata - será mantida")

            print(f"\n{'='*80}")
            print(f"📊 Total de publicações a remover: {len(indices_remover)}")
            print(f"{'='*80}\n")
        else:
            # Modo antigo: remove todas as duplicatas (exceto a primeira de cada grupo)
            print(f"\n⚠️  ATENÇÃO: Removendo duplicatas SEM verificação da API")
            print(f"⚠️  Para usar verificação da API, forneça o relatório\n")
            for _, grupo in self.duplicatas:
                for item in grupo[1:]:
                    indices_remover.add(item['indice'])

        result = self.root.find('.//{http://tempuri.org/}getPublicacoesResult')
        if result is None:
            result = self.root.find('.//getPublicacoesResult')
        if result is None:
            for elem in self.root.iter():
                if 'getPublicacoesResult' in elem.tag:
                    result = elem
                    break

        if result is None:
            return False, "Erro: Não foi possível encontrar getPublicacoesResult"

        publicacoes_elements = result.findall('{http://tempuri.org/}publicacao')
        if not publicacoes_elements:
            publicacoes_elements = result.findall('publicacao')

        # Remove publicações confirmadas como duplicatas
        for idx in sorted(indices_remover, reverse=True):
            if idx < len(publicacoes_elements):
                result.remove(publicacoes_elements[idx])

        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)

        # Mensagem detalhada
        if relatorio:
            total_analisadas = sum(len(g.get('comparacoes_api', [])) for g in relatorio.get('grupos', []))
            mantidas = total_analisadas - len(indices_remover)
            mensagem = (f"✅ XML limpo gerado!\n"
                       f"📊 {len(indices_remover)} duplicatas removidas | "
                       f"{mantidas} publicações mantidas (não duplicadas)")
        else:
            mensagem = f"XML limpo gerado: {len(indices_remover)} duplicatas removidas"

        return True, mensagem

    def _remover_duplicatas_email(self, output_path, relatorio=None):
        """Remove duplicatas do formato E-mail"""
        print(f"\n{'='*80}")
        print(f"📧 _remover_duplicatas_email INICIADO")
        print(f"{'='*80}")
        print(f"   📂 Output path: {output_path}")
        print(f"   📊 Relatório fornecido: {relatorio is not None}")

        indices_remover = set()

        # Se temos relatório com resultados da API, usa-o para decidir o que remover
        if relatorio and 'grupos' in relatorio:
            print(f"   ✅ Usando relatório da API para decisão de remoção")
            print(f"\n{'='*80}")
            print(f"🔍 VERIFICANDO DUPLICATAS COM RESULTADOS DA API (Formato E-mail)")
            print(f"{'='*80}\n")

            for grupo_rel in relatorio['grupos']:
                numero_processo = grupo_rel.get('numero_processo', '')
                comparacoes = grupo_rel.get('comparacoes_api', [])
                ocorrencias = grupo_rel.get('ocorrencias', [])

                # Para cada comparação com a API
                for comp in comparacoes:
                    ocorrencia_num = comp.get('ocorrencia_comparada')
                    sao_similares = comp.get('sao_similares')
                    interpretacao = comp.get('interpretacao', '')

                    # ✅ SÓ REMOVE SE:
                    # 1. sao_similares == True OU
                    # 2. interpretacao == "Textos idênticos"
                    if sao_similares == True or interpretacao == "Textos idênticos":
                        # Encontra o índice real da publicação
                        if ocorrencia_num and ocorrencia_num <= len(ocorrencias):
                            indice = ocorrencias[ocorrencia_num - 1]['indice']
                            indices_remover.add(indice)
                            print(f"   ✅ Processo {numero_processo}, ocorrência {ocorrencia_num}: DUPLICATA CONFIRMADA - será removida")
                    else:
                        print(f"   ❌ Processo {numero_processo}, ocorrência {ocorrencia_num}: NÃO é duplicata - será mantida")

            print(f"\n{'='*80}")
            print(f"📊 Total de publicações a remover: {len(indices_remover)}")
            print(f"{'='*80}\n")
        else:
            # Modo antigo: remove todas as duplicatas (exceto a primeira de cada grupo)
            print(f"\n⚠️  ATENÇÃO: Removendo duplicatas SEM verificação da API")
            print(f"⚠️  Para usar verificação da API, forneça o relatório\n")
            for _, grupo in self.duplicatas:
                for item in grupo[1:]:
                    indices_remover.add(item['indice'])

        # Busca todos os elementos <Publicacoes> no formato E-mail
        print(f"\n🔍 Buscando elementos <Publicacoes>...")
        print(f"   Root tag: {self.root.tag}")

        # Tenta com namespace primeiro
        print(f"   1. Tentando findall('{{Arquivo}}Publicacoes')...")
        publicacoes_elements = self.root.findall('{Arquivo}Publicacoes')
        print(f"      Encontrados: {len(publicacoes_elements)}")

        # Se não encontrou, tenta sem namespace
        if not publicacoes_elements:
            print(f"   2. Tentando findall('Publicacoes')...")
            publicacoes_elements = self.root.findall('Publicacoes')
            print(f"      Encontrados: {len(publicacoes_elements)}")

        # Se ainda não encontrou, itera pelos filhos diretos
        if not publicacoes_elements:
            print(f"   3. Iterando filhos diretos do root...")
            publicacoes_elements = []
            for elem in self.root:
                tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                print(f"      - Filho: {elem.tag} (nome: {tag_name})")
                if tag_name == 'Publicacoes':
                    publicacoes_elements.append(elem)
                    print(f"        ✅ Match!")
            print(f"      Total encontrados: {len(publicacoes_elements)}")

        if not publicacoes_elements:
            print(f"   ❌ ERRO: Nenhum elemento Publicacoes encontrado!")
            return False, "Erro: Não foi possível encontrar elementos <Publicacoes>"

        print(f"   ✅ Total de {len(publicacoes_elements)} elementos <Publicacoes> encontrados")

        print(f"🗑️ Removendo {len(indices_remover)} de {len(publicacoes_elements)} publicações")

        # Remove publicações confirmadas como duplicatas (de trás para frente para não afetar índices)
        for idx in sorted(indices_remover, reverse=True):
            if idx < len(publicacoes_elements):
                self.root.remove(publicacoes_elements[idx])

        # Atualiza contador total se existir (tenta com e sem namespace)
        total_elem = self.root.find('{Arquivo}Total_de_Publicacoes/{Arquivo}Total')
        if total_elem is None:
            total_elem = self.root.find('Total_de_Publicacoes/Total')

        if total_elem is not None:
            novo_total = len(publicacoes_elements) - len(indices_remover)
            total_elem.text = str(novo_total)
            print(f"📊 Contador atualizado: {novo_total} publicações")

        # Salva o XML com encoding ISO-8859-1 (padrão do formato E-mail)
        self.tree.write(output_path, encoding='ISO-8859-1', xml_declaration=True)

        # Mensagem detalhada
        if relatorio:
            total_analisadas = sum(len(g.get('comparacoes_api', [])) for g in relatorio.get('grupos', []))
            mantidas = total_analisadas - len(indices_remover)
            mensagem = (f"✅ XML E-mail limpo gerado!\n"
                       f"📊 {len(indices_remover)} duplicatas removidas | "
                       f"{mantidas} publicações mantidas (não duplicadas)")
        else:
            mensagem = f"XML E-mail limpo gerado: {len(indices_remover)} duplicatas removidas"

        return True, mensagem

    def converter_para_email(self, soap_path, email_path):
        """
        Converte XML SOAP para formato Email simplificado

        Estrutura Email:
        <Arquivo>
          <Publicacoes>
            <Data>...</Data>
            <Processo>...</Processo>
            <Diario>...</Diario>
            <Identificacao><![CDATA[...]]></Identificacao>
            <Publicacao><![CDATA[...]]></Publicacao>
          </Publicacoes>
        </Arquivo>
        """
        print(f"\n{'='*80}")
        print(f"🔄 CONVERTENDO SOAP PARA FORMATO EMAIL")
        print(f"{'='*80}\n")

        # Carrega o XML SOAP limpo
        tree = ET.parse(soap_path)
        root = tree.getroot()

        # Encontra todas as publicações no SOAP
        result = root.find('.//{http://tempuri.org/}getPublicacoesResult')
        if result is None:
            result = root.find('.//getPublicacoesResult')
        if result is None:
            for elem in root.iter():
                if 'getPublicacoesResult' in elem.tag:
                    result = elem
                    break

        if result is None:
            return False, "Erro: Não foi possível encontrar getPublicacoesResult no SOAP"

        publicacoes_soap = result.findall('{http://tempuri.org/}publicacao')
        if not publicacoes_soap:
            publicacoes_soap = result.findall('publicacao')

        print(f"   📊 Total de publicações a converter: {len(publicacoes_soap)}\n")

        # Cria novo XML Email
        arquivo = ET.Element('Arquivo')
        arquivo.set('xmlns', 'Arquivo')

        for idx, pub_soap in enumerate(publicacoes_soap, 1):
            # Extrai dados da publicação SOAP
            def get_text(tag_name):
                elem = pub_soap.find(f'{{http://tempuri.org/}}{tag_name}')
                if elem is None:
                    elem = pub_soap.find(tag_name)
                return elem.text if elem is not None and elem.text else ''

            numero_processo = get_text('numeroProcesso')
            data_publicacao = get_text('dataPublicacao')
            descricao_diario = get_text('descricaoDiario')
            data_divulgacao = get_text('dataDivulgacao')
            orgao_descricao = get_text('orgaoDescricao')
            processo_publicacao = get_text('processoPublicacao')

            # Cria elemento <Publicacoes>
            publicacoes = ET.SubElement(arquivo, 'Publicacoes')

            # <Data>
            data_elem = ET.SubElement(publicacoes, 'Data')
            data_elem.text = data_publicacao or data_divulgacao or ''

            # <Processo>
            processo_elem = ET.SubElement(publicacoes, 'Processo')
            processo_elem.text = numero_processo

            # <Diario>
            diario_elem = ET.SubElement(publicacoes, 'Diario')
            diario_elem.text = descricao_diario

            # <Identificacao>
            identificacao_elem = ET.SubElement(publicacoes, 'Identificacao')
            identificacao_text = f"""
      Data Disponibilização: {data_divulgacao}
      Data Publicação: {data_publicacao}
      Órgão: {orgao_descricao}
        """
            identificacao_elem.text = identificacao_text.strip()

            # <Publicacao>
            publicacao_elem = ET.SubElement(publicacoes, 'Publicacao')
            publicacao_elem.text = processo_publicacao

            if idx % 10 == 0:
                print(f"   ✅ Convertidas: {idx}/{len(publicacoes_soap)}")

        # Salva o XML Email
        email_tree = ET.ElementTree(arquivo)
        ET.indent(email_tree, space="  ")
        email_tree.write(email_path, encoding='ISO-8859-1', xml_declaration=True)

        print(f"\n   ✅ Conversão concluída: {len(publicacoes_soap)} publicações")
        print(f"{'='*80}\n")

        return True, f"XML Email gerado: {len(publicacoes_soap)} publicações convertidas"


@app.route('/')
def index():
    """Página inicial"""
    return render_template('index.html')


def processar_xml_background(filepath, session_id):
    """Processa XML em background thread"""
    try:
        atualizar_progresso(session_id, 'Carregando arquivo XML...', 0, 100)

        processor = PublicacaoProcessor(filepath, session_id=session_id)
        success, message = processor.carregar_xml()

        if not success:
            atualizar_progresso(session_id, f'Erro: {message}', 0, 100)
            with progresso_lock:
                progresso_global[session_id]['erro'] = message
            return

        atualizar_progresso(session_id, 'Extraindo publicações...', 10, 100)
        processor.extrair_publicacoes()

        # Adiciona total de publicações ao progresso
        with progresso_lock:
            progresso_global[session_id]['total_publicacoes'] = len(processor.publicacoes)

        atualizar_progresso(session_id, f'✅ {len(processor.publicacoes)} publicações encontradas!\nIdentificando duplicatas...', 20, 100)
        processor.identificar_duplicatas()

        # Adiciona total de grupos de duplicatas
        with progresso_lock:
            progresso_global[session_id]['grupos_duplicatas'] = len(processor.duplicatas)

        atualizar_progresso(session_id, f'📊 Publicações: {len(processor.publicacoes)} | Grupos duplicados: {len(processor.duplicatas)}\nGerando relatório...', 30, 100)

        # O gerar_relatorio_html já atualiza o progresso internamente
        try:
            relatorio = processor.gerar_relatorio_html()
        except Exception as e:
            print(f"❌ Erro ao gerar relatório: {str(e)}")
            import traceback
            traceback.print_exc()
            raise  # Re-lança para ser capturado pelo except externo

        # Verifica se foi cancelado
        progresso = obter_progresso(session_id)
        foi_cancelado = progresso and progresso.get('cancelado', False)

        # Salva resultado no progresso
        with progresso_lock:
            progresso_global[session_id]['relatorio'] = relatorio
            progresso_global[session_id]['total_duplicatas'] = len(processor.duplicatas)
            progresso_global[session_id]['concluido'] = True  # Marca como concluído mesmo se cancelado

        if foi_cancelado:
            atualizar_progresso(session_id, '⚠️ Relatório parcial gerado!', 100, 100)
            print(f"⚠️ Processamento cancelado para sessão {session_id} - Relatório parcial gerado")
        else:
            atualizar_progresso(session_id, 'Processamento concluído!', 100, 100)
            print(f"✅ Processamento concluído com sucesso para sessão {session_id}")

    except Exception as e:
        print(f"❌ Erro no processamento background: {str(e)}")
        import traceback
        traceback.print_exc()
        atualizar_progresso(session_id, f'Erro: {str(e)}', 0, 100)
        with progresso_lock:
            progresso_global[session_id]['erro'] = str(e)
            progresso_global[session_id]['concluido'] = False


@app.route('/upload', methods=['POST'])
def upload_file():
    """Processa upload do arquivo XML"""
    if 'file' not in request.files:
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('index'))

    file = request.files['file']

    if file.filename == '':
        flash('Nenhum arquivo selecionado', 'error')
        return redirect(url_for('index'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Gera session_id para tracking
        session_id = str(time.time()) + "_" + str(os.getpid())
        session['session_id'] = session_id
        session['current_file'] = filename

        # Captura formato escolhido (padrão: soap)
        formato_escolhido = request.form.get('formato', 'soap')
        session['formato_saida'] = formato_escolhido
        print(f"\n📋 Formato de saída escolhido: {formato_escolhido.upper()}\n")

        # Inicia processamento em background
        thread = threading.Thread(target=processar_xml_background, args=(filepath, session_id))
        thread.daemon = True
        thread.start()

        # Redireciona para página de processamento
        return redirect(url_for('processando'))

    flash('Tipo de arquivo não permitido. Use apenas arquivos .xml', 'error')
    return redirect(url_for('index'))


@app.route('/processando')
def processando():
    """Página intermediária que mostra barra de progresso"""
    if 'session_id' not in session:
        flash('Nenhum processamento em andamento', 'warning')
        return redirect(url_for('index'))

    return render_template('processando.html', session_id=session['session_id'])


@app.route('/relatorio')
def relatorio():
    """Exibe relatório de duplicatas"""
    if 'current_file' not in session or 'session_id' not in session:
        flash('Nenhum arquivo processado. Faça upload de um arquivo XML primeiro.', 'warning')
        return redirect(url_for('index'))

    filename = session['current_file']
    session_id = session['session_id']

    # Pega dados do processamento em background
    progresso = obter_progresso(session_id)

    if not progresso or not progresso.get('concluido'):
        # Verifica se houve erro durante o processamento
        if progresso and progresso.get('erro'):
            flash(f'Erro no processamento: {progresso.get("erro")}', 'error')
            return redirect(url_for('index'))
        # Se não tem erro, ainda está processando
        flash('Processamento ainda não foi concluído', 'warning')
        return redirect(url_for('processando'))

    # Recupera dados salvos
    with progresso_lock:
        relatorio = progresso_global[session_id].get('relatorio')
        foi_cancelado = progresso_global[session_id].get('cancelado', False)
        session['total_publicacoes'] = progresso_global[session_id].get('total_publicacoes', 0)
        session['total_duplicatas'] = progresso_global[session_id].get('total_duplicatas', 0)

        # ✅ IMPORTANTE: Salva relatório na sessão antes de limpar
        # O relatório é necessário para download posterior
        session['relatorio'] = relatorio

    # Limpa progresso após exibir (mas relatório foi salvo na sessão)
    limpar_progresso(session_id)

    return render_template('relatorio.html',
                         relatorio=relatorio,
                         filename=filename,
                         tem_duplicatas=(relatorio is not None),
                         foi_cancelado=foi_cancelado,
                         session_id=session_id)


@app.route('/download')
def download():
    """Gera e envia XML sem duplicatas (SOAP ou formato Email)"""
    print("\n" + "="*80, flush=True)
    print("🔽 INICIANDO DOWNLOAD", flush=True)
    print("="*80, flush=True)
    print(f"DEBUG: Função download() foi chamada! Session keys: {list(session.keys())}", flush=True)

    # Verificação 1: Arquivo na sessão
    print(f"1️⃣ Verificando sessão...", flush=True)
    if 'current_file' not in session:
        print(f"   ❌ ERRO: Nenhum arquivo na sessão", flush=True)
        flash('Nenhum arquivo processado', 'error')
        return redirect(url_for('index'))
    print(f"   ✅ Arquivo na sessão: {session.get('current_file')}", flush=True)

    # Pega formato: primeiro tenta da URL, depois da sessão, senão usa soap
    formato = request.args.get('formato') or session.get('formato_saida', 'soap')
    print(f"\n2️⃣ Formato solicitado: {formato.upper()}")

    filename = session['current_file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    session_id = session.get('session_id')

    print(f"   📁 Arquivo: {filename}")
    print(f"   📂 Caminho: {filepath}")
    print(f"   🆔 Session ID: {session_id}")

    # Verificação 2: Recupera o relatório com resultados da API
    print(f"\n3️⃣ Recuperando relatório da API...")

    # Tenta buscar da sessão Flask (onde foi salvo na rota /relatorio)
    relatorio = session.get('relatorio')

    if relatorio:
        print(f"   ✅ Relatório encontrado na sessão Flask")
        if 'grupos' in relatorio:
            print(f"   📊 {len(relatorio['grupos'])} grupos de duplicatas no relatório")
    else:
        # Fallback: tenta buscar de progresso_global (se ainda existir)
        if session_id and session_id in progresso_global:
            relatorio = progresso_global[session_id].get('relatorio')
            print(f"   ✅ Relatório encontrado em progresso_global (fallback)")
        else:
            print(f"   ⚠️  Relatório não encontrado nem na sessão nem em progresso_global")

    if not relatorio:
        print(f"   ❌ ERRO: Relatório não encontrado - redirecionando para index")
        flash('⚠️ Relatório não encontrado. Processe o XML novamente.', 'warning')
        return redirect(url_for('index'))

    # Verificação 3: Carrega e processa XML
    print(f"\n4️⃣ Carregando XML...")
    processor = PublicacaoProcessor(filepath)
    success, msg = processor.carregar_xml()
    print(f"   Carregamento: {success} - {msg}")

    print(f"\n5️⃣ Extraindo publicações...")
    pubs = processor.extrair_publicacoes()
    print(f"   {len(pubs)} publicações extraídas")

    print(f"\n6️⃣ Identificando duplicatas...")
    processor.identificar_duplicatas()
    print(f"   {len(processor.duplicatas)} grupos de duplicatas identificados")

    # Detecta formato de entrada
    formato_entrada = processor.formato_entrada
    print(f"\n7️⃣ Formatos: entrada={formato_entrada.upper()}, saída={formato.upper()}")

    # CASO 1: Entrada E-mail → Saída E-mail (mantém formato)
    if formato_entrada == 'email' and formato == 'email':
        print(f"\n8️⃣ 📧 CASO 1: E-mail → E-mail")
        output_email = f"limpo_email_{filename}"
        output_email_path = os.path.join(app.config['UPLOAD_FOLDER'], output_email)
        print(f"   📁 Arquivo de saída: {output_email_path}")

        print(f"\n9️⃣ Removendo duplicatas...")
        success, message = processor.remover_duplicatas(output_email_path, relatorio=relatorio)
        print(f"   Resultado: {success} - {message}")

        if not success:
            print(f"   ❌ ERRO na remoção: {message}")
            flash(message, 'error')
            return redirect(url_for('relatorio'))

        print(f"\n🔟 ✅ Enviando arquivo para download...")
        return send_file(output_email_path,
                        as_attachment=True,
                        download_name=f"email_sem_duplicatas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")

    # CASO 2: Entrada E-mail → Saída SOAP (conversão não implementada)
    elif formato_entrada == 'email' and formato == 'soap':
        flash('⚠️ Conversão E-mail → SOAP ainda não implementada. Use formato E-mail na saída.', 'warning')
        return redirect(url_for('relatorio'))

    # CASO 3: Entrada SOAP → Saída SOAP (mantém formato)
    elif formato_entrada == 'soap' and formato == 'soap':
        output_soap = f"limpo_soap_{filename}"
        output_soap_path = os.path.join(app.config['UPLOAD_FOLDER'], output_soap)

        success, message = processor.remover_duplicatas(output_soap_path, relatorio=relatorio)

        if not success:
            flash(message, 'error')
            return redirect(url_for('relatorio'))

        return send_file(output_soap_path,
                        as_attachment=True,
                        download_name=f"soap_sem_duplicatas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")

    # CASO 4: Entrada SOAP → Saída E-mail (converte)
    elif formato_entrada == 'soap' and formato == 'email':
        # Primeiro gera SOAP limpo
        output_soap = f"limpo_soap_{filename}"
        output_soap_path = os.path.join(app.config['UPLOAD_FOLDER'], output_soap)

        success, message = processor.remover_duplicatas(output_soap_path, relatorio=relatorio)

        if not success:
            flash(message, 'error')
            return redirect(url_for('relatorio'))

        # Depois converte para E-mail
        output_email = f"limpo_email_{filename}"
        output_email_path = os.path.join(app.config['UPLOAD_FOLDER'], output_email)

        success_conv, message_conv = processor.converter_para_email(output_soap_path, output_email_path)

        if not success_conv:
            flash(message_conv, 'error')
            return redirect(url_for('relatorio'))

        return send_file(output_email_path,
                        as_attachment=True,
                        download_name=f"email_sem_duplicatas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")

    # Fallback
    else:
        flash(f'Formato não suportado: {formato_entrada} → {formato}', 'error')
        return redirect(url_for('relatorio'))


@app.route('/limpar')
def limpar():
    """Limpa sessão e arquivos temporários"""
    if 'current_file' in session:
        filename = session['current_file']
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        output_filename = f"limpo_{filename}"
        output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

        # Remove arquivos se existirem
        for path in [filepath, output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except:
                    pass

    session.clear()
    flash('Sessão limpa com sucesso!', 'success')
    return redirect(url_for('index'))


@app.route('/cancelar', methods=['POST'])
def cancelar():
    """Cancela o processamento atual e gera relatório parcial"""
    session_id = request.args.get('session_id') or session.get('session_id')

    if not session_id:
        return json.dumps({'erro': 'session_id não fornecido', 'sucesso': False}), 400

    # Marca cancelamento
    with progresso_lock:
        if session_id in progresso_global:
            progresso_global[session_id]['cancelado'] = True
            print(f"⚠️ Cancelamento solicitado para sessão {session_id}")

    return json.dumps({'sucesso': True, 'mensagem': 'Processamento será cancelado'})


@app.route('/progresso')
def progresso():
    """Retorna o progresso atual do processamento via JSON"""
    session_id = request.args.get('session_id') or session.get('session_id')

    if not session_id:
        return json.dumps({'erro': 'session_id não fornecido'}), 400

    progresso = obter_progresso(session_id)

    if progresso is None:
        return json.dumps({
            'mensagem': 'Aguardando início do processamento...',
            'atual': 0,
            'total': 0,
            'porcentagem': 0
        })

    return json.dumps(progresso)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("PROCESSADOR DE XML SOAP - PUBLICAÇÕES (WEB)")
    print("=" * 80)
    print(f"\n🌐 Servidor iniciando na porta 54129...")
    print(f"📂 Pasta de uploads: {os.path.abspath(app.config['UPLOAD_FOLDER'])}")
    print(f"\n✨ Acesse: http://localhost:54129")
    print(f"✨ Ou: http://127.0.0.1:54129")
    print("\n" + "=" * 80 + "\n")

    app.run(host='0.0.0.0', port=54129, debug=True)
