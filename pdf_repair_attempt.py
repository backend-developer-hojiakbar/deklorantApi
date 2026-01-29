import os
import sys
import subprocess
import tempfile
import shutil
from pathlib import Path

def attempt_pdf_repair(pdf_path):
    """PDF faylni tiklashga harakat qilish"""
    print("=== PDF Tiklashga Harakat ===")
    print(f"PDF fayl: {pdf_path}")
    
    # 1. QPDF orqali tiklash
    print("\n1. QPDF orqali tiklash:")
    try:
        repaired_path = "repaired_TIF_TN_2022_UZ.pdf"
        result = subprocess.run(['qpdf', '--repair', pdf_path, repaired_path], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("PDF muvaffaqiyatli tiklandi!")
            print(f"Tiklangan fayl: {repaired_path}")
            return repaired_path
        else:
            print("QPDF tiklash muvaffaqiyatsiz:")
            print(result.stderr)
            return None
    except Exception as e:
        print(f"QPDF xato: {e}")
        return None

def analyze_repaired_pdf(repaired_path):
    """Tiklangan PDFni tahlil qilish"""
    if not repaired_path or not os.path.exists(repaired_path):
        print("Tiklangan PDF fayl mavjud emas")
        return
    
    print(f"\n=== Tiklangan PDF Tahlili: {repaired_path} ===")
    
    # Fayl hajmini solishtirish
    original_size = os.path.getsize("TIF TN 2022 UZ.pdf")
    repaired_size = os.path.getsize(repaired_path)
    print(f"Asl fayl hajmi: {original_size:,} bytes")
    print(f"Tiklangan fayl hajmi: {repaired_size:,} bytes")
    print(f"Hajm farqi: {abs(original_size - repaired_size):,} bytes")
    
    # PyPDF2 orqali tekshirish
    print("\nPyPDF2 orqali tekshirish:")
    try:
        import PyPDF2
        with open(repaired_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            print(f"Sahifalar soni: {len(pdf.pages)}")
            print("PDF to'g'ri tiklangan!")
            return True
    except Exception as e:
        print(f"PyPDF2 xato: {e}")
        return False

def extract_text_from_repaired_pdf(repaired_path):
    """Tiklangan PDFdan matn chiqarish"""
    if not repaired_path or not os.path.exists(repaired_path):
        return
    
    print(f"\n=== Tiklangan PDFdan Matn Chiqarish ===")
    
    # PyPDF2
    print("\nPyPDF2 orqali:")
    try:
        import PyPDF2
        with open(repaired_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            all_text = []
            for i, page in enumerate(pdf.pages[:10]):
                text = page.extract_text()
                if text.strip():
                    all_text.append(f"=== Sahifa {i+1} ===\n{text[:300]}...")
            if all_text:
                print("\n".join(all_text))
                return "\n".join(all_text)
            else:
                print("Matn topilmadi")
                return ""
    except Exception as e:
        print(f"Xato: {e}")
        return ""

def search_for_hs_codes_in_text(text):
    """Matn ichidan HS kodlarni qidirish"""
    if not text:
        return
    
    print("\n=== Matn Ichidan HS Kodlarni Qidirish ===")
    
    import re
    
    # HS kodlarni qidirish uchun patternlar
    patterns = [
        r'\b(\d{4}\s*\d{2}\s*\d{4})\b',  # Bo'sh joy bilan ajratilgan
        r'\b(\d{10})\b',  # Oddiy 10 xonali raqam
        r'HS\s*[:\s]*(\d{10})',  # HS bilan boshlanadigan
        r'TNVED\s*[:\s]*(\d{10})',  # TNVED bilan boshlanadigan
    ]
    
    found_codes = set()
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        found_codes.update(matches)
    
    if found_codes:
        print(f"Topilgan HS kodlar ({len(found_codes)} ta):")
        for i, code in enumerate(sorted(found_codes)[:20]):
            print(f"  {i+1}. {code}")
        if len(found_codes) > 20:
            print(f"  ... va yana {len(found_codes) - 20} ta")
        return found_codes
    else:
        print("HS kodlar topilmadi")
        return set()

def main():
    pdf_path = "TIF TN 2022 UZ.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Fayl topilmadi: {pdf_path}")
        return
    
    # PDFni tiklashga harakat qilish
    repaired_path = attempt_pdf_repair(pdf_path)
    
    if repaired_path:
        # Tiklangan PDFni tahlil qilish
        is_valid = analyze_repaired_pdf(repaired_path)
        
        if is_valid:
            # Matn chiqarish
            text = extract_text_from_repaired_pdf(repaired_path)
            
            # HS kodlarni qidirish
            if text:
                codes = search_for_hs_codes_in_text(text)
                if codes:
                    print(f"\nMuvaffaqiyat! {len(codes)} ta HS kod topildi!")
                else:
                    print("\nHS kodlar topilmadi, lekin PDF tiklandi")
            else:
                print("\nPDF tiklandi, lekin matn chiqarib bo'lmadi")
        else:
            print("\nPDF tiklandi, lekin hali ham to'g'ri emas")
    else:
        print("\nPDFni tiklab bo'lmadi")

if __name__ == "__main__":
    main()