"""
PyPDF2 yordamida PDF faylni o'qish sinovi
"""

import PyPDF2


def test_pdf_reading():
    try:
        with open('TIF TN 2022 UZ.pdf', 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            print(f"Sahifalar soni: {len(reader.pages)}")
            
            # Birinchi sahifani o'qish
            page = reader.pages[0]
            text = page.extract_text()
            print(f"Birinchi sahifaning matni (birinchi 500 belgi):")
            print(text[:500])
            
            return reader
    except Exception as e:
        print(f"Xato yuz berdi: {e}")
        return None


if __name__ == "__main__":
    test_pdf_reading()