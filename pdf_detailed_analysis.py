import os
import sys
import PyPDF2
import pdfplumber
import fitz  # PyMuPDF
import subprocess
import json
from pathlib import Path

def analyze_pdf_file(pdf_path):
    """PDF faylni chuqur tahlil qilish"""
    print("=== PDF Fayl Chuqur Tahlili ===")
    print(f"PDF fayl: {pdf_path}")
    
    # 1. Asosiy fayl ma'lumotlari
    file_size = os.path.getsize(pdf_path)
    print(f"Fayl hajmi: {file_size:,} bytes ({file_size/1024/1024:.2f} MB)")
    
    # 2. PDF faylning binar tarkibi
    print("\n=== Binar Tarkib Tahlili ===")
    with open(pdf_path, 'rb') as f:
        header = f.read(1024)
        print(f"PDF header: {header[:10]}")
        print(f"Header as text: {header.decode('utf-8', errors='ignore')[:100]}")
        
        # Oxirgi 1024 byte
        f.seek(-1024, 2)
        footer = f.read()
        print(f"PDF footer: {footer[-10:]}")
        print(f"Footer as text: {footer.decode('utf-8', errors='ignore')[-100:]}")
    
    # 3. PyPDF2 orqali urinish
    print("\n=== PyPDF2 Tahlili ===")
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            print(f"Sahifalar soni: {len(pdf.pages)}")
            print(f"Metadata: {pdf.metadata}")
    except Exception as e:
        print(f"PyPDF2 xato: {e}")
    
    # 4. pdfplumber orqali urinish
    print("\n=== pdfplumber Tahlili ===")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            print(f"Sahifalar soni: {len(pdf.pages)}")
            if len(pdf.pages) > 0:
                first_page = pdf.pages[0]
                text = first_page.extract_text()
                print(f"Birinchi sahifa matni: {text[:200]}...")
    except Exception as e:
        print(f"pdfplumber xato: {e}")
    
    # 5. PyMuPDF (fitz) orqali urinish
    print("\n=== PyMuPDF (fitz) Tahlili ===")
    try:
        pdf = fitz.open(pdf_path)
        print(f"Sahifalar soni: {len(pdf)}")
        if len(pdf) > 0:
            page = pdf[0]
            text = page.get_text()
            print(f"Birinchi sahifa matni: {text[:200]}...")
        pdf.close()
    except Exception as e:
        print(f"PyMuPDF xato: {e}")
    
    # 6. Tashqi vositalar orqali tekshirish
    print("\n=== Tashqi Vositalar Tahlili ===")
    try:
        # pdfinfo buyrug'i
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("pdfinfo natijasi:")
            print(result.stdout)
        else:
            print("pdfinfo ishlamadi")
    except Exception as e:
        print(f"pdfinfo xato: {e}")
    
    try:
        # qpdf buyrug'i
        result = subprocess.run(['qpdf', '--check', pdf_path], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("qpdf tekshiruvi: PDF to'g'ri")
        else:
            print("qpdf tekshiruvi: Xato bor")
            print(result.stderr)
    except Exception as e:
        print(f"qpdf xato: {e}")

def extract_text_with_multiple_methods(pdf_path):
    """Turli usullar bilan matn chiqarish"""
    print("\n=== Turli Usullar Bilan Matn Chiqarish ===")
    
    # 1. PyPDF2
    print("\n1. PyPDF2 orqali:")
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            all_text = []
            for i, page in enumerate(pdf.pages[:5]):  # Faqat dastlabki 5 sahifa
                text = page.extract_text()
                if text.strip():
                    all_text.append(f"=== Sahifa {i+1} ===\n{text[:500]}...")
            if all_text:
                print("\n".join(all_text))
            else:
                print("Matn topilmadi")
    except Exception as e:
        print(f"Xato: {e}")
    
    # 2. pdfplumber
    print("\n2. pdfplumber orqali:")
    try:
        with pdfplumber.open(pdf_path) as pdf:
            all_text = []
            for i, page in enumerate(pdf.pages[:5]):
                text = page.extract_text()
                if text.strip():
                    all_text.append(f"=== Sahifa {i+1} ===\n{text[:500]}...")
            if all_text:
                print("\n".join(all_text))
            else:
                print("Matn topilmadi")
    except Exception as e:
        print(f"Xato: {e}")
    
    # 3. PyMuPDF
    print("\n3. PyMuPDF orqali:")
    try:
        pdf = fitz.open(pdf_path)
        all_text = []
        for i in range(min(5, len(pdf))):
            page = pdf[i]
            text = page.get_text()
            if text.strip():
                all_text.append(f"=== Sahifa {i+1} ===\n{text[:500]}...")
        if all_text:
            print("\n".join(all_text))
        else:
            print("Matn topilmadi")
        pdf.close()
    except Exception as e:
        print(f"Xato: {e}")

def search_for_hs_codes(pdf_path):
    """PDF ichidan HS kodlarni qidirish"""
    print("\n=== HS Kodlarni Qidirish ===")
    
    # Oddiy matn qidiruv
    patterns = [
        r'\b\d{10}\b',  # 10 xonali raqamlar
        r'\b\d{4}\s*\d{2}\s*\d{4}\b',  # Bo'sh joy bilan ajratilgan HS kodlar
        r'HS\s*\d{10}',  # HS bilan boshlanadigan kodlar
        r'TNVED\s*\d{10}',  # TNVED bilan boshlanadigan kodlar
    ]
    
    for method_name, method in [("PyPDF2", extract_with_pypdf2), 
                                ("pdfplumber", extract_with_pdfplumber),
                                ("PyMuPDF", extract_with_pymupdf)]:
        print(f"\n{method_name} orqali qidiruv:")
        try:
            text = method(pdf_path)
            if text:
                import re
                found_codes = set()
                for pattern in patterns:
                    matches = re.findall(pattern, text)
                    found_codes.update(matches)
                if found_codes:
                    print(f"Topilgan kodlar: {list(found_codes)[:10]}")
                else:
                    print("HS kodlar topilmadi")
            else:
                print("Matn chiqarib bo'lmadi")
        except Exception as e:
            print(f"Xato: {e}")

def extract_with_pypdf2(pdf_path):
    """PyPDF2 orqali matn chiqarish"""
    try:
        with open(pdf_path, 'rb') as f:
            pdf = PyPDF2.PdfReader(f)
            text = ""
            for page in pdf.pages[:10]:  # Dastlabki 10 sahifa
                text += page.extract_text() + "\n"
            return text
    except:
        return ""

def extract_with_pdfplumber(pdf_path):
    """pdfplumber orqali matn chiqarish"""
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = ""
            for page in pdf.pages[:10]:
                text += page.extract_text() + "\n"
            return text
    except:
        return ""

def extract_with_pymupdf(pdf_path):
    """PyMuPDF orqali matn chiqarish"""
    try:
        pdf = fitz.open(pdf_path)
        text = ""
        for i in range(min(10, len(pdf))):
            page = pdf[i]
            text += page.get_text() + "\n"
        pdf.close()
        return text
    except:
        return ""

if __name__ == "__main__":
    pdf_path = "TIF TN 2022 UZ.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"Fayl topilmadi: {pdf_path}")
        sys.exit(1)
    
    analyze_pdf_file(pdf_path)
    extract_text_with_multiple_methods(pdf_path)
    search_for_hs_codes(pdf_path)