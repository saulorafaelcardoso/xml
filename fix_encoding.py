#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script para corrigir problemas de encoding em XML
Especialmente útil para arquivos com caracteres � (corrompidos)
"""

import sys
import os


def tentar_encodings(filepath):
    """
    Tenta vários encodings até encontrar o correto
    """
    # Lista de encodings comuns em ordem de probabilidade
    encodings = [
        'utf-8',
        'utf-8-sig',        # UTF-8 com BOM
        'windows-1252',     # Windows padrão (CP1252)
        'cp1252',           # Mesmo que windows-1252
        'latin-1',          # ISO-8859-1
        'iso-8859-1',
        'iso-8859-15',      # Latin-9
        'cp850',            # DOS Latin-1
        'cp437',            # DOS US
    ]

    resultados = []

    print(f"🔍 Testando {len(encodings)} encodings...\n")

    for i, encoding in enumerate(encodings, 1):
        try:
            with open(filepath, 'r', encoding=encoding) as f:
                conteudo = f.read()

            # Conta caracteres de substituição
            num_substituicoes = conteudo.count('�')

            # Procura por caracteres acentuados brasileiros comuns
            acentuados = sum([
                conteudo.count('á'), conteudo.count('à'), conteudo.count('ã'),
                conteudo.count('é'), conteudo.count('ê'),
                conteudo.count('í'),
                conteudo.count('ó'), conteudo.count('ô'), conteudo.count('õ'),
                conteudo.count('ú'),
                conteudo.count('ç'),
                conteudo.count('Á'), conteudo.count('É'), conteudo.count('Í'),
                conteudo.count('Ó'), conteudo.count('Ú'), conteudo.count('Ç'),
            ])

            # Calcula score (menos substituições = melhor, mais acentuados = melhor)
            score = acentuados - (num_substituicoes * 10)

            status = "✅" if num_substituicoes == 0 else "⚠️"
            print(f"{i}. {status} {encoding:20s} - Substituições: {num_substituicoes:3d} | Acentuados: {acentuados:4d} | Score: {score:5d}")

            resultados.append({
                'encoding': encoding,
                'conteudo': conteudo,
                'substituicoes': num_substituicoes,
                'acentuados': acentuados,
                'score': score
            })

        except (UnicodeDecodeError, UnicodeError) as e:
            print(f"{i}. ❌ {encoding:20s} - Falhou")
            continue

    return resultados


def escolher_melhor_encoding(resultados):
    """
    Escolhe o melhor encoding baseado no score
    """
    if not resultados:
        return None

    # Ordena por score (maior é melhor)
    resultados_ordenados = sorted(resultados, key=lambda x: x['score'], reverse=True)

    melhor = resultados_ordenados[0]

    # Se houver empate no topo, prefere UTF-8
    empates = [r for r in resultados_ordenados if r['score'] == melhor['score']]
    for r in empates:
        if 'utf-8' in r['encoding'].lower():
            return r

    return melhor


def corrigir_arquivo(input_path, output_path=None):
    """
    Corrige o encoding do arquivo
    """
    if output_path is None:
        base, ext = os.path.splitext(input_path)
        output_path = f"{base}_corrigido{ext}"

    print("=" * 70)
    print("🔧 CORRETOR DE ENCODING XML")
    print("=" * 70)
    print(f"\n📂 Arquivo: {input_path}\n")

    # Testa todos os encodings
    resultados = tentar_encodings(input_path)

    if not resultados:
        print("\n❌ Erro: Não foi possível ler o arquivo com nenhum encoding!")
        return False

    # Escolhe o melhor
    print("\n" + "=" * 70)
    melhor = escolher_melhor_encoding(resultados)

    print(f"\n🏆 MELHOR ENCODING: {melhor['encoding']}")
    print(f"   • Caracteres corrompidos (�): {melhor['substituicoes']}")
    print(f"   • Caracteres acentuados: {melhor['acentuados']}")
    print(f"   • Score: {melhor['score']}")

    if melhor['substituicoes'] > 0:
        print(f"\n⚠️  AVISO: Ainda há {melhor['substituicoes']} caracteres corrompidos!")
        print("   O arquivo pode ter sido corrompido na origem.")
        print("   Tente obter o arquivo original novamente se possível.")

    # Salva o arquivo corrigido
    print(f"\n💾 Salvando arquivo corrigido...")
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(melhor['conteudo'])

    print(f"✅ Arquivo salvo: {output_path}")

    # Mostra preview
    print("\n" + "=" * 70)
    print("📄 PREVIEW DO CONTEÚDO (primeiras 500 caracteres):")
    print("-" * 70)
    print(melhor['conteudo'][:500])
    print("-" * 70)

    # Mostra exemplos de texto com acentuação
    print("\n🔍 BUSCANDO EXEMPLOS DE TEXTO COM ACENTUAÇÃO:")
    print("-" * 70)

    linhas = melhor['conteudo'].split('\n')
    exemplos_encontrados = 0

    for i, linha in enumerate(linhas, 1):
        # Procura linhas com palavras comuns acentuadas
        palavras_chave = ['Justiça', 'Diário', 'Eletrônico', 'Órgão', 'Publicação',
                          'Decisão', 'Ação', 'Recuperação', 'número', 'código']

        for palavra in palavras_chave:
            if palavra in linha:
                contexto = linha.strip()[:120]
                print(f"Linha {i}: ...{contexto}...")
                exemplos_encontrados += 1
                if exemplos_encontrados >= 3:
                    break

        if exemplos_encontrados >= 3:
            break

    print("-" * 70)

    # Validação XML
    print("\n🔍 Validando XML...")
    try:
        import xml.etree.ElementTree as ET
        tree = ET.parse(output_path)
        root = tree.getroot()

        print("✅ XML está bem formado!")

        # Conta publicações
        pubs = root.findall('.//{http://tempuri.org/}publicacao')
        if not pubs:
            pubs = root.findall('.//publicacao')

        if pubs:
            print(f"📊 Publicações encontradas: {len(pubs)}")

    except ET.ParseError as e:
        print(f"❌ XML ainda tem erros de formatação:")
        print(f"   {str(e)}")
        print("\n💡 Dica: Use o xml_cleaner.py para limpar o arquivo:")
        print(f"   python xml_cleaner.py {output_path}")

    print("\n" + "=" * 70)
    print("✅ CORREÇÃO CONCLUÍDA!")
    print("=" * 70)

    return output_path


def main():
    if len(sys.argv) < 2:
        print("=" * 70)
        print("🔧 CORRETOR DE ENCODING XML")
        print("=" * 70)
        print("\nUso:")
        print(f"  python {sys.argv[0]} arquivo.xml [arquivo_saida.xml]")
        print("\nO script irá:")
        print("  1. Testar múltiplos encodings")
        print("  2. Escolher o melhor automaticamente")
        print("  3. Converter para UTF-8")
        print("  4. Validar o XML resultante")
        print("\nExemplo:")
        print(f"  python {sys.argv[0]} publicacoes.xml")
        print(f"  # Cria: publicacoes_corrigido.xml")
        print("=" * 70)
        sys.exit(1)

    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(input_file):
        print(f"❌ Erro: Arquivo não encontrado: {input_file}")
        sys.exit(1)

    arquivo_corrigido = corrigir_arquivo(input_file, output_file)

    if arquivo_corrigido:
        print("\n🎉 Próximos passos:")
        print(f"   1. Revise o arquivo: {arquivo_corrigido}")
        print(f"   2. Se houver erros XML, use: python xml_cleaner.py {arquivo_corrigido}")
        print(f"   3. Processe: python xml_processor.py {arquivo_corrigido}")
        print(f"      ou acesse: http://localhost:54129")


if __name__ == '__main__':
    main()
