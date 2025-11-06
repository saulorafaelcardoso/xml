#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Processador de XML SOAP para Publicações
Identifica duplicatas e gera relatório e XML limpo
"""

import xml.etree.ElementTree as ET
from collections import defaultdict
from typing import List, Dict, Tuple
import sys
from datetime import datetime


class PublicacaoProcessor:
    """Classe para processar publicações SOAP XML"""

    def __init__(self, xml_path: str):
        self.xml_path = xml_path
        self.tree = None
        self.root = None
        self.namespaces = {
            'soap': 'http://schemas.xmlsoap.org/soap/envelope/',
            'ns': 'http://tempuri.org/'
        }
        self.publicacoes = []
        self.duplicatas = []

    def carregar_xml(self) -> bool:
        """Carrega o arquivo XML"""
        try:
            self.tree = ET.parse(self.xml_path)
            self.root = self.tree.getroot()
            print(f"✓ XML carregado com sucesso: {self.xml_path}")
            return True
        except Exception as e:
            print(f"✗ Erro ao carregar XML: {e}")
            return False

    def extrair_publicacoes(self) -> List[Dict]:
        """Extrai todas as publicações do XML"""
        publicacoes = []

        # Busca por todas as publicações no XML
        # Tenta com e sem namespace
        pubs = self.root.findall('.//{http://tempuri.org/}publicacao')
        if not pubs:
            pubs = self.root.findall('.//publicacao')

        for pub in pubs:
            dados = {}
            for child in pub:
                # Remove namespace se existir
                tag = child.tag.split('}')[-1] if '}' in child.tag else child.tag
                dados[tag] = child.text if child.text else ""

            dados['_element'] = pub
            publicacoes.append(dados)

        self.publicacoes = publicacoes
        print(f"✓ {len(publicacoes)} publicações encontradas")
        return publicacoes

    def identificar_duplicatas(self) -> List[Tuple[str, List[Dict]]]:
        """
        Identifica publicações duplicadas baseado apenas no numeroProcesso
        """
        grupos_duplicatas = defaultdict(list)

        for idx, pub in enumerate(self.publicacoes):
            # Chave de duplicidade: apenas numeroProcesso
            chave = pub.get('numeroProcesso', '')

            grupos_duplicatas[chave].append({
                'indice': idx,
                'dados': pub
            })

        # Filtra apenas grupos com mais de 1 entrada
        duplicatas = []
        for chave, grupo in grupos_duplicatas.items():
            if len(grupo) > 1:
                duplicatas.append((chave, grupo))

        self.duplicatas = duplicatas
        print(f"✓ {len(duplicatas)} grupos de duplicatas identificados")
        return duplicatas

    def gerar_relatorio(self, output_path: str = 'relatorio_duplicatas.txt') -> None:
        """Gera relatório detalhado das duplicatas"""
        if not self.duplicatas:
            print("✓ Nenhuma duplicata encontrada!")
            return

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("RELATÓRIO DE PUBLICAÇÕES DUPLICADAS\n")
            f.write(f"Data: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
            f.write("=" * 80 + "\n\n")

            total_duplicatas = sum(len(grupo) for _, grupo in self.duplicatas)
            f.write(f"Total de publicações analisadas: {len(self.publicacoes)}\n")
            f.write(f"Grupos de duplicatas encontrados: {len(self.duplicatas)}\n")
            f.write(f"Total de publicações duplicadas: {total_duplicatas}\n")
            f.write(f"Publicações únicas a manter: {len(self.publicacoes) - total_duplicatas + len(self.duplicatas)}\n\n")
            f.write("=" * 80 + "\n\n")

            for idx, (chave, grupo) in enumerate(self.duplicatas, 1):
                # Pega dados da primeira publicação para exibição
                primeira_pub = grupo[0]['dados']

                f.write(f"\n{'*' * 80}\n")
                f.write(f"GRUPO DE DUPLICATAS #{idx}\n")
                f.write(f"{'*' * 80}\n\n")

                f.write(f"Número do Processo: {chave}\n")  # Agora chave é apenas numeroProcesso
                f.write(f"Data de Publicação: {primeira_pub.get('dataPublicacao', 'N/A')}\n")
                f.write(f"Ano de Publicação: {primeira_pub.get('anoPublicacao', 'N/A')}\n")
                f.write(f"Código de Publicação: {primeira_pub.get('codPublicacao', 'N/A')}\n")
                f.write(f"Quantidade de duplicatas: {len(grupo)}\n\n")

                for i, item in enumerate(grupo, 1):
                    pub = item['dados']
                    f.write(f"  --- Ocorrência {i} (Índice: {item['indice']}) ---\n")
                    f.write(f"  Diário: {pub.get('descricaoDiario', 'N/A')}\n")
                    f.write(f"  Órgão: {pub.get('orgaoDescricao', 'N/A')}\n")
                    f.write(f"  Data Divulgação: {pub.get('dataDivulgacao', 'N/A')}\n")
                    f.write(f"  Data Cadastro: {pub.get('dataCadastro', 'N/A')}\n")
                    f.write(f"  Código Integração: {pub.get('codIntegracao', 'N/A')}\n")

                    # Mostra primeiros 200 caracteres do despacho
                    despacho = pub.get('despachoPublicacao', '')
                    if despacho:
                        preview = despacho[:200] + '...' if len(despacho) > 200 else despacho
                        f.write(f"  Despacho (prévia): {preview}\n")
                    f.write("\n")

            f.write("\n" + "=" * 80 + "\n")
            f.write("RECOMENDAÇÃO: Manter apenas a primeira ocorrência de cada grupo\n")
            f.write("=" * 80 + "\n")

        print(f"✓ Relatório gerado: {output_path}")

    def remover_duplicatas(self, output_path: str = 'output_sem_duplicatas.xml') -> None:
        """Remove duplicatas e gera novo XML"""
        if not self.duplicatas:
            print("✓ Nenhuma duplicata para remover")
            # Copia o arquivo original
            import shutil
            shutil.copy(self.xml_path, output_path)
            print(f"✓ Arquivo copiado para: {output_path}")
            return

        # Identifica índices a remover (mantém apenas o primeiro de cada grupo)
        indices_remover = set()
        for _, grupo in self.duplicatas:
            # Remove todos exceto o primeiro
            for item in grupo[1:]:
                indices_remover.add(item['indice'])

        print(f"✓ Removendo {len(indices_remover)} publicações duplicadas...")

        # Busca o elemento pai das publicações
        result = self.root.find('.//{http://tempuri.org/}getPublicacoesResult')
        if result is None:
            result = self.root.find('.//getPublicacoesResult')
        if result is None:
            # Tenta sem namespace
            for elem in self.root.iter():
                if 'getPublicacoesResult' in elem.tag:
                    result = elem
                    break

        if result is None:
            print("✗ Erro: Não foi possível encontrar getPublicacoesResult")
            return

        # Remove elementos duplicados
        publicacoes_elements = result.findall('{http://tempuri.org/}publicacao')
        if not publicacoes_elements:
            publicacoes_elements = result.findall('publicacao')
        for idx in sorted(indices_remover, reverse=True):
            if idx < len(publicacoes_elements):
                result.remove(publicacoes_elements[idx])

        # Salva o novo XML
        self.tree.write(output_path, encoding='utf-8', xml_declaration=True)

        print(f"✓ XML limpo gerado: {output_path}")
        print(f"  Publicações originais: {len(self.publicacoes)}")
        print(f"  Publicações removidas: {len(indices_remover)}")
        print(f"  Publicações restantes: {len(self.publicacoes) - len(indices_remover)}")


def main():
    """Função principal"""
    print("\n" + "=" * 80)
    print("PROCESSADOR DE XML SOAP - PUBLICAÇÕES")
    print("=" * 80 + "\n")

    # Verifica argumentos
    if len(sys.argv) < 2:
        print("Uso: python xml_processor.py <arquivo_xml> [--remover-duplicatas]")
        print("\nOpções:")
        print("  --remover-duplicatas    Gera XML sem duplicatas (após confirmação)")
        sys.exit(1)

    xml_path = sys.argv[1]
    remover = '--remover-duplicatas' in sys.argv

    # Processa
    processor = PublicacaoProcessor(xml_path)

    if not processor.carregar_xml():
        sys.exit(1)

    processor.extrair_publicacoes()
    processor.identificar_duplicatas()
    processor.gerar_relatorio()

    # Se houver duplicatas e o flag de remoção estiver ativo
    if processor.duplicatas and remover:
        print("\n" + "-" * 80)
        resposta = input("\nDeseja gerar o XML sem duplicatas? (s/n): ").strip().lower()
        if resposta in ['s', 'sim', 'y', 'yes']:
            processor.remover_duplicatas()
        else:
            print("✓ Operação cancelada pelo usuário")
    elif remover and not processor.duplicatas:
        print("\n✓ Não há duplicatas para remover!")

    print("\n" + "=" * 80)
    print("PROCESSAMENTO CONCLUÍDO")
    print("=" * 80 + "\n")


if __name__ == '__main__':
    main()
