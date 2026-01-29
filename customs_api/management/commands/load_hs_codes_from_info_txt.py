'''
info.txt faylidan HS kodlarni o'qish va bazaga kiritish uchun Django management command
Bu command info.txt faylidan ma'lumotlarni o'qib, 
Django model orqali bazaga saqlaydi
'''

import csv
import io
from django.core.management.base import BaseCommand
from customs_api.models import HsCode


class Command(BaseCommand):
    help = 'info.txt faylidan HS kodlarni o\'qish va bazaga kiritish'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file-path',
            type=str,
            default='info.txt',
            help='Input file path (default: info.txt)'
        )

    def handle(self, *args, **options):
        file_path = options['file_path']
        self.stdout.write(f'HS kodlarni o\'qish boshlanmoqda...')
        
        # HS kodlarni o'qish
        hs_codes = self.parse_info_txt(file_path)
        
        self.stdout.write(f'Jami {len(hs_codes)} ta HS kod topildi')
        
        # Bazaga kiritish
        created_count = 0
        updated_count = 0
        
        for hs_info in hs_codes:
            # Bazada bor yoki yo'qligini tekshiramiz
            hs_code_obj, created = HsCode.objects.get_or_create(
                code=hs_info['code'],
                defaults={
                    'description_uz': hs_info['description_uz'],
                    'description_ru': hs_info['description_ru'],
                    'duty_rate': hs_info['duty_rate'],
                    'vat_rate': hs_info['vat_rate'],
                    'excise_rate': hs_info['excise_rate'],
                    'required_certs': hs_info['required_certs'],
                    'version_status': 'ACTIVE',
                    'sources': ['info.txt']
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Yangi HS kod kiritildi: {hs_info["code"]} - {hs_info["description_uz"][:50]}...')
            else:
                # Agar allaqachon mavjud bo'lsa, yangilaymiz
                hs_code_obj.description_uz = hs_info['description_uz']
                hs_code_obj.description_ru = hs_info['description_ru']
                hs_code_obj.duty_rate = hs_info['duty_rate']
                hs_code_obj.vat_rate = hs_info['vat_rate']
                hs_code_obj.excise_rate = hs_info['excise_rate']
                hs_code_obj.required_certs = hs_info['required_certs']
                hs_code_obj.version_status = 'ACTIVE'
                hs_code_obj.sources = ['info.txt']
                hs_code_obj.save()
                updated_count += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'\nBazaga {created_count} ta yangi HS kod qo\'shildi\n{updated_count} ta HS kod yangilandi\nJarayon yakunlandi!')
        )

    def parse_info_txt(self, file_path):
        """
        info.txt faylidan HS kodlarni o'qish
        """
        hs_codes = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Sarlavhalarni aniqlash
        headers = None
        for i, line in enumerate(lines):
            line = line.strip()
            if line.startswith('HS Code'):
                headers = line.split('\t')
                break
        
        if not headers:
            self.stdout.write('Sarlavha topilmadi')
            return hs_codes
        
        # Ma'lumotlarni o'qish
        for line in lines[i+1:]:  # Sarlavhadan keyingi qatorlardan boshlab
            line = line.strip()
            if not line:
                continue
                
            # Agar qator sarlavha bo'lsa, o'tkazib yuboramiz
            if line.startswith('HS Code'):
                continue
                
            # Tab belgisi bo'yicha bo'lish
            parts = line.split('\t')
            
            # Agar qator to'liq bo'lmasa, o'tkazib yuboramiz
            if len(parts) < len(headers):
                # Qatorni uzunroq qilish uchun bo'sh joylar qo'shamiz
                parts.extend([''] * (len(headers) - len(parts)))
            
            # Faqat 10 xonali yoki 8 xonali HS kodlarini qabul qilamiz
            hs_code = parts[0].strip() if len(parts) > 0 else ''
            
            # HS koding faqat raqamlardan iboratligini tekshiramiz
            if not hs_code.isdigit() or (len(hs_code) != 10 and len(hs_code) != 8):
                continue
                
            # Ma'lumotlarni yig'amiz
            try:
                product_name_uz = parts[1].strip() if len(parts) > 1 else ''
                product_name_ru = parts[2].strip() if len(parts) > 2 else ''
                category = parts[3].strip() if len(parts) > 3 else ''
                subcategory = parts[4].strip() if len(parts) > 4 else ''
                keywords = parts[5].strip() if len(parts) > 5 else ''
                
                # Stavkalarni o'qish
                duty_rate_str = parts[6].strip() if len(parts) > 6 else '0.00'
                vat_rate_str = parts[7].strip() if len(parts) > 7 else '0.00'
                excise_rate_str = parts[8].strip() if len(parts) > 8 else '0.00'
                
                # Stavkalarni son ko'rinishiga o'tkazish
                try:
                    duty_rate = float(duty_rate_str) if duty_rate_str else 0.00
                except ValueError:
                    duty_rate = 0.00
                    
                try:
                    vat_rate = float(vat_rate_str) if vat_rate_str else 0.00
                except ValueError:
                    vat_rate = 0.00
                    
                try:
                    excise_rate = float(excise_rate_str) if excise_rate_str else 0.00
                except ValueError:
                    excise_rate = 0.00
                
                # Talab qilinadigan sertifikatlar
                certs_str = parts[9].strip() if len(parts) > 9 else '[]'
                try:
                    # Sertifikatlar ro'yxatini olish
                    required_certs = eval(certs_str) if certs_str.startswith('[') else [certs_str]
                except:
                    required_certs = []
                
                # Ma'lumotlarni saqlash
                hs_info = {
                    'code': hs_code,
                    'description_uz': product_name_uz,
                    'description_ru': product_name_ru,
                    'category': category,
                    'subcategory': subcategory,
                    'keywords': keywords,
                    'duty_rate': duty_rate,
                    'vat_rate': vat_rate,
                    'excise_rate': excise_rate,
                    'required_certs': required_certs,
                }
                
                hs_codes.append(hs_info)
                
            except IndexError:
                # Agar qator yetarlicha ma'lumotga ega bo'lmasa
                continue
        
        return hs_codes
