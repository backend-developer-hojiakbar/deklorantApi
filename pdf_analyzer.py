"""
PDF fayldan ma'lumotlarni o'qish uchun alternativ yechim
Agar PyMuPDF, PyPDF2 va boshqalar ishlamasa, bu yerda alternativ usullar keltirilgan
"""

import subprocess
import sys
import os
import re


def analyze_pdf_with_external_tools(pdf_path):
    """
    PDF faylni tahlil qilish uchun tashqi vositalardan foydalanish
    """
    print(f"PDF fayl tahlili boshlanmoqda: {pdf_path}")
    
    # PDF faylning xususiyatlarini ko'rish
    try:
        result = subprocess.run(['pdfinfo', pdf_path], capture_output=True, text=True, check=True)
        print("PDF Info:")
        print(result.stdout)
    except FileNotFoundError:
        print("pdfinfo buyrug'i topilmadi. PDF fayl turi tekshirilmadi.")
    except subprocess.CalledProcessError:
        print("pdfinfo buyrug'i ishlamadi.")
    
    # PDF fayldan matnni olish (pdftotext)
    try:
        output_file = "temp_pdf_text.txt"
        subprocess.run(['pdftotext', '-layout', pdf_path, output_file], check=True)
        
        with open(output_file, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        print(f"PDF fayldan {len(text_content)} ta belgi o'qildi")
        
        # Matndan HS kodlarni topish
        hs_codes = extract_hs_codes_from_text(text_content)
        print(f"PDF fayldan {len(hs_codes)} ta HS kod topildi")
        
        # Temp faylni o'chirish
        os.remove(output_file)
        
        return hs_codes
        
    except FileNotFoundError:
        print("pdftotext buyrug'i topilmadi. Alternativ usulga o'tilmoqda.")
    except subprocess.CalledProcessError:
        print("pdftotext ishlamadi.")


def extract_hs_codes_from_text(text):
    """
    Matndan HS kodlarni ajratib olish
    """
    # 10 xonali yoki 8 xonali raqamlar
    pattern = r'\b(\d{10}|\d{8})\b'
    matches = re.findall(pattern, text)
    
    # Faqat noyob kodlarni qaytaramiz
    unique_codes = list(set(matches))
    
    # Har bir kod uchun kontekstni ham olish
    hs_codes_with_context = []
    for code in unique_codes:
        # Kod atrofidagi matnni olish
        start_idx = max(0, text.find(code) - 200)
        end_idx = min(len(text), text.find(code) + 300)
        context = text[start_idx:end_idx].strip()
        
        # Tavsifni ajratish (koddan keyin keladigan matn)
        parts = context.split(code)
        if len(parts) > 1:
            description = parts[1].strip()
            # Faqat birinchi 500 belgini olish
            description = description[:500]
            
            # Agar tavsif yetarlicha uzun bo'lsa, saqlash
            if len(description) > 10 and not is_header_like(description):
                hs_codes_with_context.append({
                    'code': code,
                    'description': clean_description(description),
                    'context': context
                })
    
    return hs_codes_with_context


def clean_description(desc):
    """
    Tavsifni tozalash
    """
    # Ortqali belgilarni olib tashlash
    desc = re.sub(r'[^\w\s\u0400-\u04FF\u0500-\u052F\u2DE0-\u2DFF\uA640-\uA69F\.\,\-]', ' ', desc)
    # Ortiqcha bo'sh joylarni tozalash
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc


def is_header_like(text):
    """
    Agar matn sarlavha kabi bo'lsa True qaytaradi
    """
    header_keywords = [
        'TARIF', 'NOMENKLATURA', 'KOD', 'TAVSIF', 'TASVIR', 
        'CHAPTER', 'SECTION', 'BOB', 'BOLIK', 'PART', 'TABLE',
        'PAGE', 'SANASI', 'DATE', '№', 'N', 'SANA', 'TIF', 'TN'
    ]
    
    text_upper = text.upper()
    for keyword in header_keywords:
        if keyword in text_upper:
            return True
    
    # Agar faqat katta harflarda yozilgan bo'lsa
    if text == text.upper() and len(text) < 100:
        return True
    
    return False


def analyze_pdf_bytes(pdf_path):
    """
    PDF faylni baytlar bo'yicha tahlil qilish
    """
    print(f"PDF fayl baytlar bo'yicha tahlil qilinmoqda: {pdf_path}")
    
    with open(pdf_path, 'rb') as f:
        content = f.read()
    
    # PDF signaturani tekshirish
    if content.startswith(b'%PDF-'):
        print("PDF fayl to'g'ri formatda boshlanayapti")
    else:
        print("PDF fayl noto'g'ri formatda boshlanayapti")
    
    # PDF ichidagi potentsial matnni qidirish
    try:
        # UTF-8 sifatida o'qishga harakat qilish
        text_content = content.decode('utf-8', errors='ignore')
        print(f"UTF-8 sifatida o'qilgan belgilar: {len(text_content)}")
        
        # Matndan HS kodlarni topish
        hs_codes = extract_hs_codes_from_text(text_content)
        print(f"Baytlardan o'qilgan matndan {len(hs_codes)} ta HS kod topildi")
        
        return hs_codes
    except UnicodeDecodeError:
        print("UTF-8 sifatida o'qishda xato yuz berdi")
        return []


def main():
    pdf_path = "TIF TN 2022 UZ.pdf"
    
    print("PDF fayl tahlili boshlanmoqda...")
    
    # Birinchi usul: Tashqi vositalar
    hs_codes = analyze_pdf_with_external_tools(pdf_path)
    
    if hs_codes is None:
        # Ikkinchi usul: Baytlar bo'yicha tahlil
        print("\nTashqi vositalar ishlamadi, baytlar bo'yicha tahlil qilinmoqda...")
        hs_codes = analyze_pdf_bytes(pdf_path)
    
    if hs_codes:
        print(f"\nJami {len(hs_codes)} ta HS kod topildi:")
        for i, item in enumerate(hs_codes[:10]):  # Faqatgina dastlabki 10 tasini chiqarish
            print(f"{i+1}. {item['code']}: {item['description'][:100]}...")
        
        # Barcha topilgan kodlarni faylga saqlash
        with open("extracted_hs_codes_from_pdf.txt", "w", encoding="utf-8") as f:
            f.write("PDF fayldan olingan HS kodlar:\n")
            f.write("="*50 + "\n\n")
            for i, item in enumerate(hs_codes, 1):
                f.write(f"{i}. HS Kod: {item['code']}\n")
                f.write(f"   Tavsif: {item['description']}\n")
                f.write("-" * 30 + "\n")
        
        print(f"\nBarcha topilgan HS kodlar 'extracted_hs_codes_from_pdf.txt' fayliga saqlandi")
    else:
        print("\nHech qanday HS kod topilmadi. PDF fayl ehtimol himoyalangan yoki noto'g'ri formatda.")


if __name__ == "__main__":
    main()