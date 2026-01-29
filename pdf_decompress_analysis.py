import os
import zlib
import re
from pathlib import Path

def decompress_stream(compressed_data):
    """Siqilgan streamni ochish"""
    try:
        # FlateDecode (zlib) siqishini ochish
        decompressed = zlib.decompress(compressed_data)
        return decompressed
    except Exception as e:
        print(f"Decompress xato: {e}")
        return None

def extract_and_decompress_streams(pdf_path):
    """PDFdan streamlarni chiqarish va ochish"""
    print("=== PDF Streamlarini Ochish ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    # Streamlarni qidirish
    stream_positions = []
    for i in range(len(data) - 20):
        if data[i:i+6] == b'stream':
            stream_start = i + 6
            # Stream tugashini topish
            stream_end = data.find(b'endstream', stream_start)
            if stream_end != -1:
                stream_positions.append((stream_start, stream_end))
    
    print(f"Topilgan streamlar: {len(stream_positions)}")
    
    # Katta streamlarni tahlil qilish
    large_streams = [(start, end) for start, end in stream_positions if (end - start) > 1000]
    print(f"Katta streamlar (>1000 bytes): {len(large_streams)}")
    
    # Dastlabki 10 katta streamni ochish
    for i, (start, end) in enumerate(large_streams[:10]):
        stream_data = data[start:end]
        print(f"\nStream {i+1} ({len(stream_data)} bytes):")
        
        # Streamni ochish
        decompressed = decompress_stream(stream_data)
        if decompressed:
            print(f"  Ochilgan hajmi: {len(decompressed)} bytes")
            
            # Ochilgan matndan HS kodlarni qidirish
            try:
                text = decompressed.decode('utf-8', errors='ignore')
                if len(text.strip()) > 100:
                    # HS kodlarni qidirish
                    hs_patterns = [
                        r'\b\d{10}\b',
                        r'\b\d{4}\s*\d{2}\s*\d{4}\b',
                        r'HS\s*\d{10}',
                        r'TNVED\s*\d{10}',
                        r'ТН\s*\d{10}',
                        r'ТНВЭД\s*\d{10}',
                    ]
                    
                    found_codes = set()
                    for pattern in hs_patterns:
                        matches = re.findall(pattern, text, re.IGNORECASE)
                        found_codes.update(matches)
                    
                    if found_codes:
                        print(f"  Topilgan HS kodlar: {list(found_codes)[:5]}")
                        if len(found_codes) > 5:
                            print(f"  ... va yana {len(found_codes) - 5} ta")
                        return found_codes
                    else:
                        print("  HS kodlar topilmadi")
                        # Matnning dastlabki qismini ko'rsatish
                        print(f"  Matn sample: {text[:200]}...")
                else:
                    print("  Qisqa matn")
            except Exception as e:
                print(f"  Decode xato: {e}")
        else:
            print("  Ochib bo'lmadi")

def search_for_compressed_hs_data(pdf_path):
    """PDF ichidan siqilgan HS ma'lumotlarini qidirish"""
    print("\n=== Siqilgan HS Ma'lumotlarni Qidirish ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    # HS kodga o'xshash patternlarni siqilgan ma'lumotlardan qidirish
    hs_patterns = [
        rb'\d{10}',  # 10 xonali raqamlar
        rb'\d{4}\s*\d{2}\s*\d{4}',  # HS formati
        rb'HS\s*\d{10}',  # HS bilan
        rb'TNVED\s*\d{10}',  # TNVED bilan
    ]
    
    # Barcha streamlarni qidirish
    stream_positions = []
    for i in range(len(data) - 20):
        if data[i:i+6] == b'stream':
            stream_start = i + 6
            stream_end = data.find(b'endstream', stream_start)
            if stream_end != -1:
                stream_positions.append((stream_start, stream_end))
    
    print(f"Jami streamlar: {len(stream_positions)}")
    
    # Har bir streamda qidirish
    total_found = set()
    for i, (start, end) in enumerate(stream_positions):
        stream_data = data[start:end]
        
        # Streamni ochishga harakat qilish
        decompressed = decompress_stream(stream_data)
        if decompressed:
            # Ochilgan ma'lumotdan qidirish
            for pattern in hs_patterns:
                try:
                    matches = re.findall(pattern, decompressed, re.IGNORECASE)
                    if matches:
                        total_found.update(matches)
                except:
                    pass
        
        # Agar 100 ta streamdan keyin to'xtasak
        if i > 100:
            break
    
    if total_found:
        print(f"Topilgan HS kodlar: {len(total_found)}")
        for i, code in enumerate(sorted(total_found)[:20]):
            print(f"  {i+1}. {code}")
        if len(total_found) > 20:
            print(f"  ... va yana {len(total_found) - 20} ta")
        return total_found
    else:
        print("HS kodlar topilmadi")
        return set()

def analyze_pdf_content_structure(pdf_path):
    """PDF tarkibini tuzilmasini tahlil qilish"""
    print("\n=== PDF Tarkib Tuzilmasini Tahlil Qilish ===")
    
    with open(pdf_path, 'rb') as f:
        data = f.read()
    
    # Ob'ekt turlarini aniqlash
    object_types = {}
    for i in range(len(data) - 50):
        if data[i:i+6] == b'<<\n/':
            # Ob'ekt boshlanishi
            obj_end = data.find(b'\n>>', i, i + 200)
            if obj_end != -1:
                obj_header = data[i+3:obj_end].decode('ascii', errors='ignore')
                lines = obj_header.split('\n')
                for line in lines:
                    if line.startswith('/Type'):
                        obj_type = line.split()[1] if len(line.split()) > 1 else 'Unknown'
                        object_types[obj_type] = object_types.get(obj_type, 0) + 1
    
    print("Ob'ekt turlari:")
    for obj_type, count in sorted(object_types.items()):
        print(f"  {obj_type}: {count}")
    
    # Font ob'ektlarini tahlil qilish
    font_objects = []
    for i in range(len(data) - 50):
        if b'/Type /Font' in data[i:i+100]:
            # Font ob'ektini topish
            obj_start = data.rfind(b'\n', 0, i)
            if obj_start != -1:
                obj_line = data[obj_start+1:data.find(b'\n', i)].decode('ascii', errors='ignore')
                if 'obj' in obj_line:
                    font_objects.append(obj_line.strip())
    
    print(f"\nFont ob'ektlari: {len(font_objects)}")
    for i, font_obj in enumerate(font_objects[:10]):
        print(f"  {i+1}. {font_obj}")

def main():
    pdf_path = "TIF TN 2022 UZ.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Fayl topilmadi: {pdf_path}")
        return
    
    print(f"PDF fayl tahlili: {pdf_path}")
    print("=" * 50)
    
    try:
        # Streamlarni ochish
        found_codes = extract_and_decompress_streams(pdf_path)
        
        # Agar kodlar topilmasa, chuqur qidiruv
        if not found_codes:
            found_codes = search_for_compressed_hs_data(pdf_path)
        
        # Tarkib tuzilmasini tahlil qilish
        analyze_pdf_content_structure(pdf_path)
        
        if found_codes:
            print(f"\nMuvaffaqiyat! Jami {len(found_codes)} ta HS kod topildi!")
        else:
            print("\nAfsuski, HS kodlar topilmadi.")
            
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()