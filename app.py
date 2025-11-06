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


def comparar_textos_api(texto1, texto2):
    """
    Compara dois textos usando a API de duplicidades
    Retorna: dict com analise_juridica, interpretacao, sao_similares
    """
    API_URL = 'http://extracao-rtx.corejur.com.br:5000/duplicidades'
    TOKEN = 'Bearer 2390*Corejur*)23dads'

    headers = {
        'Authorization': TOKEN,
        'Content-Type': 'application/json'
    }

    payload = {
        'texto1': texto1 or '',
        'texto2': texto2 or ''
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)

        if response.status_code == 200:
            data = response.json()
            return {
                'sucesso': True,
                'analise_juridica': data.get('analise_juridica', 'N/A'),
                'interpretacao': data.get('interpretacao', 'N/A'),
                'sao_similares': data.get('sao_similares', False)
            }
        else:
            return {
                'sucesso': False,
                'erro': f'API retornou status {response.status_code}',
                'analise_juridica': 'Erro na API',
                'interpretacao': 'Erro na API',
                'sao_similares': None
            }
    except requests.exceptions.Timeout:
        return {
            'sucesso': False,
            'erro': 'Timeout na chamada da API',
            'analise_juridica': 'Timeout',
            'interpretacao': 'Timeout',
            'sao_similares': None
        }
    except Exception as e:
        return {
            'sucesso': False,
            'erro': str(e),
            'analise_juridica': f'Erro: {str(e)}',
            'interpretacao': 'Erro ao acessar API',
            'sao_similares': None
        }


class PublicacaoProcessor:
    """Classe para processar publicações SOAP XML"""

    def __init__(self, xml_path, session_id=None):
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        self.publicacoes = []
        self.duplicatas = []
        self.session_id = session_id  # Para tracking de progresso

    def carregar_xml(self):
        """Carrega o arquivo XML"""
        try:
            # Corrige encoding automaticamente antes de parsear
            print(f"📄 Processando arquivo: {os.path.basename(self.xml_path)}")
            corrigir_encoding_arquivo(self.xml_path)

            # Tenta carregar o XML
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
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

    def extrair_publicacoes(self):
        """Extrai todas as publicações do XML"""
        publicacoes = []

        # Busca por todas as publicações no XML
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
        print(f"⚡ Processamento paralelo: 5 análises simultâneas\n")

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

        # Segundo passo: Processar tarefas de API em paralelo (3 por vez)
        print(f"🚀 Iniciando processamento paralelo de {len(tarefas_api)} chamadas de API...")

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

            print(f"🔍 Grupo {idx}, ocorrência {i}: Chamando API (processo: {chave})")

            # Atualiza progresso
            if self.session_id:
                mensagem = f"📋 Processo: {chave}\n⏳ Consultando API... (Grupo {idx}/{total_grupos}, Ocorrência {i}/{total_ocorrencias})"
                atualizar_progresso(self.session_id, mensagem, comparacao_num, total_comparacoes)

            # Chama API
            comparacao = comparar_textos_api(tarefa['texto1'], tarefa['texto2'])
            comparacao['ocorrencia_comparada'] = i

            # Registra resultado
            if comparacao.get('sao_similares') == True:
                print(f"   ✅ API: Similares (duplicata confirmada)")
            elif comparacao.get('sao_similares') == False:
                print(f"   ❌ API: Diferentes (NÃO é duplicata)")
            else:
                print(f"   ⚠️ API: Erro ou resultado indefinido")

            with stats_lock:
                stats['chamadas_realizadas'] += 1

            return (tarefa, comparacao)

        # Calcula timeout dinâmico: estimativa de tempo necessário + margem
        # Com 5 workers e 60s por tarefa: (tarefas / workers) * 60s * 1.5 de margem
        timeout_total = max(3600, int((len(tarefas_api) / 5) * 60 * 1.5))  # Mínimo 1 hora
        print(f"⏱️ Timeout configurado: {timeout_total / 60:.1f} minutos")

        # Executa tarefas em paralelo com pool de 5 threads
        with ThreadPoolExecutor(max_workers=5) as executor:
            # Submete todas as tarefas
            futures = {executor.submit(processar_tarefa_api, tarefa): tarefa for tarefa in tarefas_api}

            # Coleta resultados conforme ficam prontos
            for future in as_completed(futures, timeout=timeout_total):
                try:
                    tarefa, comparacao = future.result(timeout=120)  # 120 segundos por tarefa individual
                    # Armazena resultado com índice da tarefa para manter ordem
                    tarefa_idx = tarefas_api.index(tarefa)
                    resultados[tarefa_idx] = comparacao
                except TimeoutError:
                    print(f"⏱️ Timeout ao processar tarefa")
                except Exception as e:
                    print(f"❌ Erro ao processar tarefa: {str(e)}")

        # Terceiro passo: Inserir resultados na ordem correta nos grupos
        for grupo_info in relatorio['grupos']:
            if '_tarefas' in grupo_info:
                for ocorrencia_num, tarefa_idx in grupo_info['_tarefas']:
                    if tarefa_idx in resultados:
                        grupo_info['comparacoes_api'].append(resultados[tarefa_idx])
                # Remove lista temporária
                del grupo_info['_tarefas']

        print(f"\n✅ Chamadas de API realizadas: {stats['chamadas_realizadas']}")
        print(f"⏭️ Chamadas economizadas: {stats['chamadas_puladas']}")
        print(f"💰 Economia: {(stats['chamadas_puladas'] / total_comparacoes * 100) if total_comparacoes > 0 else 0:.1f}%")
        print(f"⚡ Velocidade: 5x mais rápido com processamento paralelo\n")

        # Atualiza progresso final
        if self.session_id:
            atualizar_progresso(self.session_id, 'Análise concluída!', total_comparacoes, total_comparacoes)

        return relatorio

    def remover_duplicatas(self, output_path):
        """Remove duplicatas e gera novo XML"""
        if not self.duplicatas:
            import shutil
            shutil.copy(self.xml_path, output_path)
            return True, "Nenhuma duplicata encontrada, arquivo copiado"

        indices_remover = set()
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

        for idx in sorted(indices_remover, reverse=True):
            if idx < len(publicacoes_elements):
                result.remove(publicacoes_elements[idx])

        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)

        return True, f"XML limpo gerado: {len(indices_remover)} duplicatas removidas"


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

        # Salva resultado no progresso
        with progresso_lock:
            progresso_global[session_id]['relatorio'] = relatorio
            progresso_global[session_id]['total_duplicatas'] = len(processor.duplicatas)
            progresso_global[session_id]['concluido'] = True

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
        session['total_publicacoes'] = progresso_global[session_id].get('total_publicacoes', 0)
        session['total_duplicatas'] = progresso_global[session_id].get('total_duplicatas', 0)

    # Limpa progresso após exibir
    limpar_progresso(session_id)

    return render_template('relatorio.html',
                         relatorio=relatorio,
                         filename=filename,
                         tem_duplicatas=(relatorio is not None),
                         session_id=session_id)


@app.route('/download')
def download():
    """Gera e envia XML sem duplicatas"""
    if 'current_file' not in session:
        flash('Nenhum arquivo processado', 'error')
        return redirect(url_for('index'))

    filename = session['current_file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    processor = PublicacaoProcessor(filepath)
    processor.carregar_xml()
    processor.extrair_publicacoes()
    processor.identificar_duplicatas()

    # Gera XML limpo
    output_filename = f"limpo_{filename}"
    output_path = os.path.join(app.config['UPLOAD_FOLDER'], output_filename)

    success, message = processor.remover_duplicatas(output_path)

    if not success:
        flash(message, 'error')
        return redirect(url_for('relatorio'))

    return send_file(output_path,
                    as_attachment=True,
                    download_name=f"sem_duplicatas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml")


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
