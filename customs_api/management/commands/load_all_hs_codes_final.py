import re
from django.core.management.base import BaseCommand
from customs_api.models import HsCode

class Command(BaseCommand):
    help = 'Load ALL HS codes from info.txt file, handling all variations in data format'

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
        error_count = 0
        
        for i, line in enumerate(valid_lines):
            parts = re.split(r'\t+', line)
            
            # Handle different formats
            try:
                if len(parts) >= 6:
                    code = parts[0].strip()
                    description_uz = parts[1].strip()
                    description_ru = parts[2].strip()
                    category = parts[3].strip()
                    subcategory = parts[4].strip()
                    keywords = parts[5].strip()
                    
                    # Handle variable number of parts
                    if len(parts) >= 12:
                        # Full format (12 parts)
                        duty_rate = float(parts[6].strip()) if parts[6].strip() else 0.0
                        vat_rate = float(parts[7].strip()) if parts[7].strip() else 0.0
                        excise_rate = float(parts[8].strip()) if parts[8].strip() else 0.0
                        required_certs = parts[9].strip() if len(parts) > 9 else '[]'
                    elif len(parts) >= 9:
                        # Format with 9 parts (missing excise rate, confidence, search freq)
                        duty_rate = float(parts[6].strip()) if parts[6].strip() else 0.0
                        vat_rate = float(parts[7].strip()) if parts[7].strip() else 0.0
                        excise_rate = 0.0  # Default to 0
                        required_certs = parts[8].strip() if len(parts) > 8 else '[]'
                    else:
                        self.stdout.write(f'  ERROR: Line {i+1} has only {len(parts)} parts')
                        error_count += 1
                        continue
                    
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
                        
                else:
                    self.stdout.write(f'  ERROR: Line {i+1} has only {len(parts)} parts')
                    error_count += 1
                    
            except Exception as e:
                self.stdout.write(f'  ERROR: Line {i+1} failed: {str(e)}')
                error_count += 1
        
        self.stdout.write(f'\nBazaga {new_count} ta yangi HS kod qo\'shildi')
        self.stdout.write(f'{updated_count} ta HS kod yangilandi')
        if error_count > 0:
            self.stdout.write(f'{error_count} ta xatolik yuz berdi')
        self.stdout.write('Jarayon yakunlandi!')