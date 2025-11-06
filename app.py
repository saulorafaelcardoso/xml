#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Aplicação Web para Processamento de XML SOAP - Publicações
Identifica duplicatas e permite download do XML limpo
"""

from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
import os
import xml.etree.ElementTree as ET
from collections import defaultdict
from datetime import datetime
from werkzeug.utils import secure_filename
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max
app.config['ALLOWED_EXTENSIONS'] = {'xml'}

# Cria pastas necessárias
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


def allowed_file(filename):
    """Verifica se o arquivo tem extensão permitida"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


class PublicacaoProcessor:
    """Classe para processar publicações SOAP XML"""

    def __init__(self, xml_path):
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        self.publicacoes = []
        self.duplicatas = []

    def carregar_xml(self):
        """Carrega o arquivo XML"""
        try:
            # Tenta carregar normalmente
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
        """Identifica publicações duplicadas"""
        grupos_duplicatas = defaultdict(list)

        for idx, pub in enumerate(self.publicacoes):
            chave = (
                pub.get('numeroProcesso', ''),
                pub.get('dataPublicacao', ''),
                pub.get('anoPublicacao', ''),
                pub.get('codPublicacao', '')
            )

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
        """Gera dados do relatório para exibição HTML"""
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

        for idx, (chave, grupo) in enumerate(self.duplicatas, 1):
            grupo_info = {
                'numero': idx,
                'numero_processo': chave[0],
                'data_publicacao': chave[1],
                'ano_publicacao': chave[2],
                'cod_publicacao': chave[3],
                'quantidade': len(grupo),
                'ocorrencias': []
            }

            for i, item in enumerate(grupo, 1):
                pub = item['dados']
                ocorrencia = {
                    'numero': i,
                    'indice': item['indice'],
                    'diario': pub.get('descricaoDiario', 'N/A'),
                    'orgao': pub.get('orgaoDescricao', 'N/A'),
                    'data_divulgacao': pub.get('dataDivulgacao', 'N/A'),
                    'data_cadastro': pub.get('dataCadastro', 'N/A'),
                    'cod_integracao': pub.get('codIntegracao', 'N/A'),
                    'despacho': pub.get('despachoPublicacao', '')[:200] + '...'
                                if len(pub.get('despachoPublicacao', '')) > 200
                                else pub.get('despachoPublicacao', '')
                }
                grupo_info['ocorrencias'].append(ocorrencia)

            relatorio['grupos'].append(grupo_info)

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

        # Processa o XML
        processor = PublicacaoProcessor(filepath)
        success, message = processor.carregar_xml()

        if not success:
            flash(message, 'error')
            return redirect(url_for('index'))

        processor.extrair_publicacoes()
        processor.identificar_duplicatas()

        # Salva informações na sessão
        session['current_file'] = filename
        session['total_publicacoes'] = len(processor.publicacoes)
        session['total_duplicatas'] = len(processor.duplicatas)

        return redirect(url_for('relatorio'))

    flash('Tipo de arquivo não permitido. Use apenas arquivos .xml', 'error')
    return redirect(url_for('index'))


@app.route('/relatorio')
def relatorio():
    """Exibe relatório de duplicatas"""
    if 'current_file' not in session:
        flash('Nenhum arquivo processado. Faça upload de um arquivo XML primeiro.', 'warning')
        return redirect(url_for('index'))

    filename = session['current_file']
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    processor = PublicacaoProcessor(filepath)
    processor.carregar_xml()
    processor.extrair_publicacoes()
    processor.identificar_duplicatas()

    relatorio = processor.gerar_relatorio_html()

    return render_template('relatorio.html',
                         relatorio=relatorio,
                         filename=filename,
                         tem_duplicatas=(relatorio is not None))


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
