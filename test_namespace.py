#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test script to debug XML namespace handling"""

import xml.etree.ElementTree as ET

# Parse the test_email.xml
tree = ET.parse('test_email.xml')
root = tree.getroot()

print(f"Root tag: {root.tag}")
print(f"Root attrib: {root.attrib}")
print(f"\n" + "="*70)

# Try different ways to find Publicacoes elements
print("\n1. Using findall('{Arquivo}Publicacoes'):")
pubs1 = root.findall('{Arquivo}Publicacoes')
print(f"   Found: {len(pubs1)} elements")

print("\n2. Using findall('Publicacoes'):")
pubs2 = root.findall('Publicacoes')
print(f"   Found: {len(pubs2)} elements")

print("\n3. Using iter():")
pubs3 = list(root.iter('{Arquivo}Publicacoes'))
print(f"   Found: {len(pubs3)} elements")

print("\n4. Iterating direct children:")
pubs4 = []
for child in root:
    print(f"   Child tag: {child.tag}")
    if 'Publicacoes' in child.tag:
        pubs4.append(child)
print(f"   Found: {len(pubs4)} elements with 'Publicacoes' in tag")

print("\n5. Checking if tag ends with 'Publicacoes':")
pubs5 = []
for child in root:
    if child.tag.endswith('Publicacoes'):
        pubs5.append(child)
        print(f"   ✓ Found: {child.tag}")
print(f"   Total found: {len(pubs5)} elements")

# If we found any, try extracting data from the first one
if pubs5:
    print(f"\n" + "="*70)
    print("Testing data extraction from first Publicacoes:")
    pub = pubs5[0]

    # Try to find Data element
    print(f"\n  Looking for 'Data' element:")
    data1 = pub.find('Data')
    print(f"    find('Data'): {data1}")

    data2 = pub.find('{Arquivo}Data')
    print(f"    find('{{Arquivo}}Data'): {data2}")
    if data2 is not None:
        print(f"    Text: {data2.text}")

    # Try iterating children
    print(f"\n  Direct children of Publicacoes:")
    for child in pub:
        print(f"    - {child.tag}: {child.text.strip()[:50] if child.text else 'None'}...")
