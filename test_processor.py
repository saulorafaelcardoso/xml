#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test the PublicacaoProcessor with email format"""

import sys
sys.path.insert(0, '/home/user/xml')

from app import PublicacaoProcessor

# Test with the email format XML
processor = PublicacaoProcessor('test_email.xml')

print("="*70)
print("TESTING EMAIL FORMAT PROCESSING")
print("="*70)

# Load file
success, message = processor.carregar_xml()
print(f"\nLoad result: {success} - {message}")
print(f"Formato detectado: {processor.formato_entrada}")

# Extract publicacoes
if success:
    publicacoes = processor.extrair_publicacoes()
    print(f"\n{'='*70}")
    print(f"RESULTADO DA EXTRAÇÃO:")
    print(f"{'='*70}")
    print(f"Total de publicações: {len(publicacoes)}")

    for idx, pub in enumerate(publicacoes):
        print(f"\nPublicação {idx+1}:")
        print(f"  Processo: {pub.get('numeroProcesso', 'N/A')}")
        print(f"  Data: {pub.get('dataPublicacao', 'N/A')}")
        print(f"  Diário: {pub.get('descricaoDiario', 'N/A')}")
        print(f"  Identificação: {pub.get('identificacao', 'N/A')[:50]}...")
        print(f"  Publicação: {pub.get('processoPublicacao', 'N/A')[:50]}...")
