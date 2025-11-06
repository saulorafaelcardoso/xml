#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Utilitário para limpar e validar arquivos XML
Remove caracteres inválidos e corrige problemas comuns
"""

import sys
import re


def limpar_xml(input_path, output_path=None):
    """
    Limpa um arquivo XML removendo caracteres inválidos
    """
    if output_path is None:
        output_path = input_path.replace('.xml', '_limpo.xml')

    print(f"🔍 Lendo arquivo: {input_path}")

    try:
        # Lê o arquivo com encoding UTF-8
        with open(input_path, 'r', encoding='utf-8', errors='replace') as f:
            conteudo = f.read()
    except UnicodeDecodeError:
        # Tenta com latin-1 se UTF-8 falhar
        print("⚠️  Erro com UTF-8, tentando latin-1...")
        with open(input_path, 'r', encoding='latin-1') as f:
            conteudo = f.read()

    print(f"📏 Tamanho original: {len(conteudo)} caracteres")

    conteudo_original = conteudo
    problemas = []

    # 1. Remove caracteres de controle inválidos (exceto \n, \r, \t)
    print("🧹 Removendo caracteres de controle inválidos...")
    caracteres_invalidos = 0
    conteudo_limpo = ''
    for char in conteudo:
        char_code = ord(char)
        # Mantém: tab (9), newline (10), carriage return (13), e caracteres >= 32
        if char_code == 9 or char_code == 10 or char_code == 13 or char_code >= 32:
            conteudo_limpo += char
        else:
            caracteres_invalidos += 1

    if caracteres_invalidos > 0:
        problemas.append(f"Removidos {caracteres_invalidos} caracteres de controle inválidos")
        conteudo = conteudo_limpo

    # 2. Corrige entidades HTML comuns que não são XML
    print("🔧 Corrigindo entidades HTML...")
    entidades_html = {
        '&nbsp;': ' ',
        '&ndash;': '-',
        '&mdash;': '—',
        '&copy;': '©',
        '&reg;': '®',
        '&trade;': '™',
        '&euro;': '€',
        '&pound;': '£',
        '&sect;': '§',
        '&para;': '¶',
        '&bull;': '•',
        '&hellip;': '...',
        '&laquo;': '«',
        '&raquo;': '»',
        '&ldquo;': '"',
        '&rdquo;': '"',
        '&lsquo;': ''',
        '&rsquo;': ''',
    }

    for html_entity, replacement in entidades_html.items():
        if html_entity in conteudo:
            count = conteudo.count(html_entity)
            conteudo = conteudo.replace(html_entity, replacement)
            problemas.append(f"Substituídas {count} ocorrências de {html_entity}")

    # 3. Verifica & não escapados (mas não toca em &amp;, &lt;, &gt;, &quot;, &apos;)
    print("🔍 Verificando & não escapados...")
    # Encontra & que não são seguidos por amp;, lt;, gt;, quot;, apos;, ou #
    pattern = r'&(?!amp;|lt;|gt;|quot;|apos;|#)'
    matches = re.findall(pattern, conteudo)
    if matches:
        problemas.append(f"⚠️  Encontrados {len(matches)} & não escapados (não foram corrigidos automaticamente)")

    # 4. Remove BOM (Byte Order Mark) se presente
    if conteudo.startswith('\ufeff'):
        conteudo = conteudo[1:]
        problemas.append("Removido BOM (Byte Order Mark)")

    # Salva o arquivo limpo
    print(f"💾 Salvando arquivo limpo: {output_path}")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(conteudo)

    print(f"📏 Tamanho final: {len(conteudo)} caracteres")

    # Relatório
    print("\n" + "=" * 60)
    print("📊 RELATÓRIO DE LIMPEZA")
    print("=" * 60)

    if problemas:
        print(f"\n✅ {len(problemas)} problema(s) corrigido(s):")
        for i, problema in enumerate(problemas, 1):
            print(f"   {i}. {problema}")
    else:
        print("\n✅ Nenhum problema encontrado!")

    if len(conteudo) != len(conteudo_original):
        diff = len(conteudo_original) - len(conteudo)
        print(f"\n📉 Redução: {diff} caracteres removidos")

    print(f"\n📁 Arquivo salvo em: {output_path}")
    print("=" * 60)

    return output_path


def validar_xml(xml_path):
    """
    Valida um arquivo XML e reporta erros
    """
    import xml.etree.ElementTree as ET

    print(f"\n🔍 Validando XML: {xml_path}")
    print("=" * 60)

    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()

        print("✅ XML está bem formado!")
        print(f"📊 Tag raiz: {root.tag}")

        # Conta elementos
        total_elements = len(list(root.iter()))
        print(f"📊 Total de elementos: {total_elements}")

        # Busca publicações
        pubs = root.findall('.//{http://tempuri.org/}publicacao')
        if not pubs:
            pubs = root.findall('.//publicacao')

        if pubs:
            print(f"📊 Publicações encontradas: {len(pubs)}")

        return True

    except ET.ParseError as e:
        print(f"❌ Erro de formatação XML:")
        print(f"   {str(e)}")

        # Tenta mostrar o contexto
        try:
            with open(xml_path, 'r', encoding='utf-8', errors='replace') as f:
                conteudo = f.read()

            match = re.search(r'line (\d+), column (\d+)', str(e))
            if match:
                linha = int(match.group(1))
                coluna = int(match.group(2))

                linhas = conteudo.split('\n')
                if linha <= len(linhas):
                    linha_erro = linhas[linha - 1]
                    print(f"\n   Linha {linha}:")
                    print(f"   {linha_erro}")
                    print(f"   {' ' * (coluna - 1)}^")

                    if coluna <= len(linha_erro):
                        char = linha_erro[coluna - 1]
                        print(f"\n   Caractere problemático: '{char}' (código: {ord(char)})")

        except Exception:
            pass

        return False

    except Exception as e:
        print(f"❌ Erro ao validar: {str(e)}")
        return False


def main():
    if len(sys.argv) < 2:
        print("=" * 60)
        print("🧹 XML Cleaner - Limpeza e Validação de XML")
        print("=" * 60)
        print("\nUso:")
        print(f"  python {sys.argv[0]} arquivo.xml [arquivo_saida.xml]")
        print("\nOpções:")
        print("  arquivo.xml         - Arquivo XML para limpar")
        print("  arquivo_saida.xml   - (Opcional) Nome do arquivo de saída")
        print("\nO script irá:")
        print("  • Remover caracteres de controle inválidos")
        print("  • Corrigir entidades HTML comuns")
        print("  • Detectar & não escapados")
        print("  • Remover BOM")
        print("  • Validar o XML resultante")
        print("\n" + "=" * 60)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    print("\n" + "=" * 60)
    print("🧹 XML CLEANER")
    print("=" * 60 + "\n")

    # Limpa o arquivo
    arquivo_limpo = limpar_xml(input_file, output_file)

    # Valida o resultado
    validar_xml(arquivo_limpo)

    print("\n✅ Processo concluído!")
    print("\nPróximos passos:")
    print(f"  1. Revise o arquivo: {arquivo_limpo}")
    print(f"  2. Processe com: python app.py")
    print(f"     ou: python xml_processor.py {arquivo_limpo}")


if __name__ == '__main__':
    main()
