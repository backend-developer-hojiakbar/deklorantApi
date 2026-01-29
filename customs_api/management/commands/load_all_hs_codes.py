import re
from django.core.management.base import BaseCommand
from customs_api.models import HsCode

class Command(BaseCommand):
    help = 'Load all HS codes from info.txt file'

    def handle(self, *args, **options):
        self.stdout.write('HS kodlarni o\'qish boshlanmoqda...')
        
        # Read the file
        with open('info.txt', 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Filter valid HS code lines
        valid_lines = []
        for line in lines:
            line = line.strip()
            if line and re.match(r'^\d{10}', line):
                valid_lines.append(line)
        
        self.stdout.write(f'Jami {len(valid_lines)} ta HS kod topildi')
        
        new_count = 0
        updated_count = 0
        
        for line in valid_lines:
            parts = re.split(r'\t+', line)
            if len(parts) >= 10:
                code = parts[0].strip()
                description_uz = parts[1].strip()
                description_ru = parts[2].strip()
                category = parts[3].strip()
                subcategory = parts[4].strip()
                keywords = parts[5].strip()
                duty_rate = float(parts[6].strip()) if parts[6].strip() else 0.0
                vat_rate = float(parts[7].strip()) if parts[7].strip() else 0.0
                excise_rate = float(parts[8].strip()) if parts[8].strip() else 0.0
                required_certs = parts[9].strip() if len(parts) > 9 else '[]'
                
                obj, created = HsCode.objects.update_or_create(
                    code=code,
                    defaults={
                        'description_uz': description_uz,
                        'description_ru': description_ru,
                        'category': category,
                        'subcategory': subcategory,
                        'keywords': keywords,
                        'duty_rate': duty_rate,
                        'vat_rate': vat_rate,
                        'excise_rate': excise_rate,
                        'required_certificates': required_certs,
                    }
                )
                
                if created:
                    new_count += 1
                else:
                    updated_count += 1
        
        self.stdout.write(f'\nBazaga {new_count} ta yangi HS kod qo\'shildi')
        self.stdout.write(f'{updated_count} ta HS kod yangilandi')
        self.stdout.write('Jarayon yakunlandi!')