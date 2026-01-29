"""
PDF faylni o'qish uchun skript
Bu skript TIF TN 2022 UZ.pdf faylini o'qib, 
ichidan HS kodlarni va ularning tavsiflarini ajratadi
"""

import pdfplumber
import re
from typing import List, Dict


def extract_hs_codes_from_pdf_plumber(pdf_path: str) -> List[Dict]:
    """
    pdfplumber yordamida PDF fayldan HS kodlar va ularning tavsiflarini olish
    """
    hs_codes = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"PDF fayl ochildi. Sahifalar soni: {len(pdf.pages)}")
        
        # Har bir sahifani o'qish
        for page_num, page in enumerate(pdf.pages):
            print(f"Sahifa {page_num + 1} o'qilmoqda...")
            
            # Sahifadagi matnni olish
            text = page.extract_text()
            
            if text:
                # Matndan HS kodlarni topish uchun regex
                # Oddiy format: 10 xonali raqamlar yoki 8 xonali raqamlar
                # Masalan: 8471301000, 8517120000, 84713010, 85171200
                
                # HS kodlarni topish (10 xonali yoki 8 xonali)
                pattern = r'\b(\d{10}|\d{8})\b'
                matches = re.findall(pattern, text)
                
                # Har bir topilgan kodni tavsifi bilan birga saqlash
                lines = text.split('\n')
                for line in lines:
                    for match in matches:
                        if match in line and len(line.strip()) > 10:  # Tavsif qatorini aniqlash
                            # Tavsifni tozalash
                            clean_description = clean_text(line.replace(match, '').strip())
                            
                            # Agar tavsif yetarlicha uzun bo'lsa, saqlash
                            if len(clean_description) > 5 and not is_header_line(clean_description):
                                hs_code_entry = {
                                    'code': match,
                                    'description_uz': clean_description,
                                    'description_ru': '',
                                    'hierarchy': [],
                                    'duty_rate': 0.0,
                                    'vat_rate': 0.0,
                                    'excise_rate': 0.0,
                                    'is_sanctioned': False,
                                    'required_certs': [],
                                    'history': '',
                                    'cis_hint': None,
                                    'version_status': 'ACTIVE',
                                    'sources': ['PDF extraction - pdfplumber'],
                                    'page_number': page_num + 1
                                }
                                
                                # Agar bir xil kod allaqachon qo'shilgan bo'lsa, qo'shma
                                if not any(item['code'] == match for item in hs_codes):
                                    hs_codes.append(hs_code_entry)
    
    return hs_codes


def clean_text(text: str) -> str:
    """
    Matnni tozalash: ortiqcha belgilar, raqamlar, bo'sh joylar
    """
    # Faqat harf, probel, nuqtolar, vergullar qoldirish
    cleaned = re.sub(r'[^\w\s\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F\.\,\-]', ' ', text)
    # Ortiqcha bo'sh joylarni olib tashlash
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def is_header_line(text: str) -> bool:
    """
    Agar qator sarlavha bo'lsa (masalan, jadval sarlavhasi), True qaytaradi
    """
    header_keywords = [
        'TARIF', 'NOMENKLATURA', 'KOD', 'TAVSIF', 'TASVIR', 
        'CHAPTER', 'SECTION', 'BOB', 'BOLIK', 'PART', 'TABLE',
        'PAGE', 'SANASI', 'DATE', '№', 'N', 'SANA'
    ]
    
    text_upper = text.upper()
    for keyword in header_keywords:
        if keyword in text_upper:
            return True
    
    # Agar faqat katta harflarda yozilgan bo'lsa, sarlavha bo'lishi ehtimoli bor
    if text == text.upper() and len(text) < 100:
        return True
    
    return False


def extract_with_detailed_analysis_plumber(pdf_path: str) -> List[Dict]:
    """
    pdfplumber yordamida PDF dan ma'lumotlarni batafsil tahlil qilish orqali olish
    """
    hs_codes = []
    
    with pdfplumber.open(pdf_path) as pdf:
        print(f"PDF fayl ochildi. Sahifalar soni: {len(pdf.pages)}")
        
        # Har bir sahifani o'qish
        for page_num, page in enumerate(pdf.pages):
            print(f"Sahifa {page_num + 1} batafsil tahlil qilinmoqda...")
            
            # Sahifadagi matnni olish
            text = page.extract_text()
            
            if text:
                # HS kodlarni topish
                pattern = r'\b(\d{10}|\d{8})\b'
                matches = re.findall(pattern, text)
                
                for match in matches:
                    # Kod atrofidagi kontekstni olish
                    context_start = max(0, text.find(match) - 200)
                    context_end = min(len(text), text.find(match) + 300)
                    context = text[context_start:context_end]
                    
                    # Tavsifni ajratish (koddan keyin keladigan matn)
                    parts = context.split(match)
                    if len(parts) > 1:
                        description_part = parts[1].strip()
                        clean_desc = clean_text(description_part)
                        
                        if len(clean_desc) > 5 and not is_header_line(clean_desc):
                            # Agar tavsifda raqamlar ko'p bo'lsa, bu yana kod bo'lishi mumkin
                            # Shuning uchun to'g'ri tavsifni aniqlash kerak
                            if not re.search(r'\b\d{8,}\b', clean_desc[:50]):
                                hs_code_entry = {
                                    'code': match,
                                    'description_uz': clean_desc[:500],  # Birinchi 500 belgini olish
                                    'description_ru': '',
                                    'hierarchy': [],
                                    'duty_rate': 0.0,
                                    'vat_rate': 0.0,
                                    'excise_rate': 0.0,
                                    'is_sanctioned': False,
                                    'required_certs': [],
                                    'history': '',
                                    'cis_hint': None,
                                    'version_status': 'ACTIVE',
                                    'sources': ['PDF extraction - pdfplumber', f'Page {page_num + 1}'],
                                    'page_number': page_num + 1
                                }
                                
                                if not any(item['code'] == match for item in hs_codes):
                                    hs_codes.append(hs_code_entry)
    
    return hs_codes


def save_extracted_data_to_file(extracted_data: List[Dict], output_file: str):
    """
    Olingan ma'lumotlarni faylga saqlash
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("PDF dan olingan HS kodlar:\n")
        f.write("="*50 + "\n\n")
        
        for i, item in enumerate(extracted_data, 1):
            f.write(f"{i}. HS Kod: {item['code']}\n")
            f.write(f"   Tavsif: {item['description_uz']}\n")
            f.write(f"   Sahifa: {item['page_number']}\n")
            f.write(f"   Manba: {', '.join(item['sources'])}\n")
            f.write("-" * 30 + "\n")


def save_to_db_format(extracted_data: List[Dict], output_file: str):
    """
    Ma'lumotlarni bazaga kiritish formatida saqlash
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# HS kodlarni bazaga kiritish uchun skript\n")
        f.write("from customs_api.models import HsCode\n\n")
        f.write("def create_hs_codes():\n")
        
        for item in extracted_data:
            f.write(f"    HsCode.objects.get_or_create(\n")
            f.write(f"        code='{item['code']}',\n")
            f.write(f"        defaults={{\n")
            f.write(f"            'description_uz': '''{item['description_uz']}''',\n")
            f.write(f"            'description_ru': '''{item['description_ru']}''',\n")
            f.write(f"            'hierarchy': {item['hierarchy']},\n")
            f.write(f"            'duty_rate': {item['duty_rate']},\n")
            f.write(f"            'vat_rate': {item['vat_rate']},\n")
            f.write(f"            'excise_rate': {item['excise_rate']},\n")
            f.write(f"            'is_sanctioned': {item['is_sanctioned']},\n")
            f.write(f"            'required_certs': {item['required_certs']},\n")
            f.write(f"            'history': '''{item['history']}''',\n")
            f.write(f"            'cis_hint': '{item['cis_hint']}',\n")
            f.write(f"            'version_status': '{item['version_status']}',\n")
            f.write(f"            'sources': {item['sources']},\n")
            f.write(f"        }}\n")
            f.write(f"    )\n\n")


def main():
    pdf_path = "TIF TN 2022 UZ.pdf"
    output_file = "extracted_hs_codes_from_pdf.txt"
    db_script_file = "load_hs_codes_to_db.py"
    
    print("PDF fayldan HS kodlar olinmoqda (pdfplumber yordamida)...")
    
    # Batafsil ekstraksiya
    extracted_data = extract_with_detailed_analysis_plumber(pdf_path)
    print(f"\nJami {len(extracted_data)} ta HS kod topildi")
    
    # Natijalarni faylga saqlash
    save_extracted_data_to_file(extracted_data, output_file)
    print(f"Natijalar {output_file} fayliga saqlandi")
    
    # Bazaga kiritish uchun skript yaratish
    save_to_db_format(extracted_data, db_script_file)
    print(f"Bazaga kiritish skripti {db_script_file} fayliga saqlandi")
    
    # Bir nechta namuna ko'rsatish
    print("\nBir nechta namuna:")
    for i, item in enumerate(extracted_data[:5]):
        print(f"- {item['code']}: {item['description_uz'][:100]}...")
    
    return extracted_data


if __name__ == "__main__":
    extracted_data = main()