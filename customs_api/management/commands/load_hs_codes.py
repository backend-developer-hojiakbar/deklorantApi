from django.core.management.base import BaseCommand
from customs_api.models import HsCode
from decimal import Decimal, InvalidOperation
import json
import os


class Command(BaseCommand):
    help = 'Load HS codes from info.txt file'

    def handle(self, *args, **options):
        # Path to info.txt file
        file_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'info.txt')
        
        if not os.path.exists(file_path):
            self.stdout.write(self.style.ERROR(f'info.txt file not found at {file_path}'))
            return
        
        loaded_count = 0
        skipped_count = 0
        
        with open(file_path, 'r', encoding='utf-8') as file:
            for line_num, line in enumerate(file, 1):
                line = line.strip()
                if not line or line.startswith('HS Code') or line.startswith('TIF TN') or line.startswith('#'):
                    continue
                
                try:
                    # Parse tab-separated values
                    parts = line.split('\t')
                    if len(parts) < 10:  # Minimum 10 columns required
                        continue
                    
                    hs_code = parts[0]
                    name_uz = parts[1]
                    name_ru = parts[2]
                    category = parts[3] if len(parts) > 3 else ''
                    subcategory = parts[4] if len(parts) > 4 else ''
                    keywords = parts[5] if len(parts) > 5 else ''
                    duty_rate = parts[6] if len(parts) > 6 else '0.00'
                    vat_rate = parts[7] if len(parts) > 7 else '12.00'
                    excise_rate = parts[8] if len(parts) > 8 else '0.00'
                    required_certs = parts[9] if len(parts) > 9 else '[]'
                    confidence = parts[10] if len(parts) > 10 else '0.95'
                    
                    # Skip if HS code already exists
                    if HsCode.objects.filter(code=hs_code).exists():
                        skipped_count += 1
                        continue
                    
                    # Parse required certificates
                    try:
                        certs = json.loads(required_certs) if required_certs.startswith('[') else [required_certs]
                    except:
                        certs = ['Veterinariya sertifikati'] if 'Veterinariya' in required_certs else ['Gigiyenik sertifikat']
                    
                    # Create hierarchy from category and subcategory
                    hierarchy = []
                    if category:
                        hierarchy.append(category)
                    if subcategory:
                        hierarchy.append(subcategory)
                    if not hierarchy:
                        hierarchy = [hs_code[:2], hs_code[:4], hs_code[:6]]
                    
                    # Convert rates to Decimal with better error handling
                    try:
                        if isinstance(duty_rate, str):
                            if duty_rate in ['Narxga bog\'liq', 'Maxsus stavka']:
                                duty_rate = Decimal('0.00')
                            else:
                                duty_rate = Decimal(str(duty_rate).replace(',', '.'))
                    except (ValueError, TypeError, InvalidOperation):
                        duty_rate = Decimal('0.00')
                    
                    try:
                        if isinstance(vat_rate, str):
                            vat_rate = Decimal(str(vat_rate).replace(',', '.'))
                    except (ValueError, TypeError, InvalidOperation):
                        vat_rate = Decimal('12.00')
                    
                    try:
                        if isinstance(excise_rate, str):
                            excise_rate = Decimal(str(excise_rate).replace(',', '.'))
                    except (ValueError, TypeError, InvalidOperation):
                        excise_rate = Decimal('0.00')
                    
                    # Create HS Code record
                    hs_code_obj = HsCode.objects.create(
                        code=hs_code,
                        description_uz=name_uz,
                        description_ru=name_ru,
                        hierarchy=hierarchy,
                        duty_rate=duty_rate,
                        vat_rate=vat_rate,
                        excise_rate=excise_rate,
                        required_certs=certs,
                        history=f'Loaded from info.txt line {line_num}'
                    )
                    
                    loaded_count += 1
                    
                    if loaded_count % 100 == 0:
                        self.stdout.write(f'Loaded {loaded_count} records...')
                        
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Error parsing line {line_num}: {str(e)}'))
                    continue
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully loaded {loaded_count} HS codes. Skipped {skipped_count} existing records.'
            )
        )
