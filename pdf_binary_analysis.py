import os
import sys
import binascii
import struct
import re
from pathlib import Path

def analyze_pdf_structure(pdf_path):
    """PDF fayl tuzilmasini tahlil qilish"""
    print("=== PDF Tuzilma Tahlili ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    print(f"Fayl hajmi: {len(data)} bytes")
    
    # PDF header aniqlash
    header_end = data.find(b'\n', 0, 100)
    if header_end != -1:
        header = data[:header_end].decode('ascii', errors='ignore')
        print(f"PDF header: {header}")
    
    # xref jadvalini qidirish
    xref_positions = []
    for i in range(len(data) - 10):
        if data[i:i+4] == b'xref':
            xref_positions.append(i)
    
    print(f"xref jadvallari soni: {len(xref_positions)}")
    for pos in xref_positions[:5]:
        print(f"  xref pozitsiyasi: {pos}")
    
    # trailer aniqlash
    trailer_positions = []
    for i in range(len(data) - 20):
        if data[i:i+7] == b'trailer':
            trailer_positions.append(i)
    
    print(f"trailerlar soni: {len(trailer_positions)}")
    for pos in trailer_positions[:3]:
        trailer_end = data.find(b'>>', pos, pos + 200)
        if trailer_end != -1:
            trailer = data[pos:trailer_end + 2].decode('ascii', errors='ignore')
            print(f"  trailer {pos}: {trailer[:100]}...")
    
    # startxref aniqlash
    startxref_positions = []
    for i in range(len(data) - 20):
        if data[i:i+9] == b'startxref':
            startxref_positions.append(i)
    
    print(f"startxref pozitsiyalari: {len(startxref_positions)}")
    for pos in startxref_positions[:3]:
        # startxref qiymatini olish
        line_end = data.find(b'\n', pos, pos + 50)
        if line_end != -1:
            try:
                xref_offset = int(data[pos + 10:line_end].strip())
                print(f"  startxref {pos}: offset {xref_offset}")
            except:
                pass

def extract_text_streams(pdf_path):
    """PDFdan matn streamlarini chiqarish"""
    print("\n=== Matn Streamlarini Chiqarish ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    # FlateDecode streamlarini qidirish
    stream_positions = []
    for i in range(len(data) - 20):
        if data[i:i+6] == b'stream':
            # Stream boshlanishini topish
            stream_start = i + 6
            # Stream tugashini topish
            stream_end = data.find(b'endstream', stream_start)
            if stream_end != -1:
                stream_positions.append((stream_start, stream_end))
    
    print(f"Topilgan streamlar: {len(stream_positions)}")
    
    # Dastlabki 5 streamni tahlil qilish
    for i, (start, end) in enumerate(stream_positions[:5]):
        stream_data = data[start:end]
        print(f"\nStream {i+1} ({len(stream_data)} bytes):")
        
        # Streamdan matn qidirish
        try:
            text = stream_data.decode('utf-8', errors='ignore')
            if len(text.strip()) > 50:
                print(f"  UTF-8 matn: {text[:200]}...")
        except:
            pass
        
        # Streamdan raqamlarni qidirish
        numbers = re.findall(r'\b\d{4,}\b', stream_data.decode('ascii', errors='ignore'))
        if numbers:
            print(f"  Topilgan raqamlar: {numbers[:10]}")

def search_for_patterns(pdf_path):
    """PDF ichidan turli patternlarni qidirish"""
    print("\n=== Patternlarni Qidirish ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    # HS kodlarga o'xshash patternlarni qidirish
    patterns = [
        (r'\b\d{10}\b', '10 xonali raqamlar'),
        (r'\b\d{4}\s*\d{2}\s*\d{4}\b', 'HS kod formati'),
        (r'HS\s*\d{10}', 'HS bilan boshlanadigan'),
        (r'TNVED\s*\d{10}', 'TNVED bilan boshlanadigan'),
        (r'ТН\s*\d{10}', 'ТН bilan boshlanadigan (ruscha)'),
        (r'ТНВЭД\s*\d{10}', 'ТНВЭД bilan boshlanadigan (ruscha)'),
    ]
    
    for pattern, description in patterns:
        matches = re.findall(pattern.encode(), data, re.IGNORECASE)
        if matches:
            print(f"{description}: {len(matches)} ta topildi")
            # Dastlabki 10 ta ko'rsatish
            for i, match in enumerate(matches[:10]):
                try:
                    print(f"  {i+1}. {match.decode('utf-8', errors='ignore')}")
                except:
                    print(f"  {i+1}. {match}")
        else:
            print(f"{description}: topilmadi")

def extract_objects(pdf_path):
    """PDF ob'ektlarini chiqarish"""
    print("\n=== PDF Ob'ektlarini Chiqarish ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    # Ob'ektlarni qidirish (n 0 obj formati)
    object_pattern = rb'(\d+)\s+(\d+)\s+obj'
    objects = re.findall(object_pattern, data)
    
    print(f"Topilgan ob'ektlar: {len(objects)}")
    
    # Dastlabki 20 ob'ektni ko'rsatish
    for i, (obj_num, gen_num) in enumerate(objects[:20]):
        print(f"  {i+1}. Ob'ekt {obj_num.decode()} {gen_num.decode()} obj")
    
    # Ob'ekt tarkibini tahlil qilish
    for obj_num, gen_num in objects[:5]:
        obj_start = data.find(f'{obj_num.decode()} {gen_num.decode()} obj'.encode())
        if obj_start != -1:
            obj_end = data.find(b'endobj', obj_start)
            if obj_end != -1:
                obj_content = data[obj_start:obj_end + 6]
                print(f"\nOb'ekt {obj_num.decode()} tarkibi:")
                print(obj_content.decode('ascii', errors='ignore')[:200] + "...")

def main():
    pdf_path = "TIF TN 2022 UZ.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Fayl topilmadi: {pdf_path}")
        return
    
    print(f"PDF fayl tahlili: {pdf_path}")
    print("=" * 50)
    
    try:
        analyze_pdf_structure(pdf_path)
        extract_text_streams(pdf_path)
        search_for_patterns(pdf_path)
        extract_objects(pdf_path)
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()