import json
from django.core.management.base import BaseCommand
from customs_api.models import HsCode

class Command(BaseCommand):
    help = 'Process HS codes in batches of 50 for manual data entry'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch',
            type=int,
            default=1,
            help='Batch number to process (1-50, 51-100, etc.)'
        )
        parser.add_argument(
            '--file',
            type=str,
            help='JSON file containing HS codes for this batch'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List current database status'
        )

    def handle(self, *args, **options):
        if options['list']:
            self.list_database_status()
            return

        batch_num = options['batch']
        start_code = (batch_num - 1) * 50 + 1
        end_code = batch_num * 50
        
        self.stdout.write(f'\n=== HS Code Batch Processor ===')
        self.stdout.write(f'Batch: {batch_num} ({start_code}-{end_code})')
        self.stdout.write(f'Current database has {HsCode.objects.count()} codes\n')

        if options['file']:
            self.process_batch_from_file(options['file'], start_code, end_code)
        else:
            self.show_batch_info(start_code, end_code)

    def list_database_status(self):
        total_codes = HsCode.objects.count()
        self.stdout.write(f'\n=== Database Status ===')
        self.stdout.write(f'Total HS codes: {total_codes}')
        
        # Show codes by range
        codes = list(HsCode.objects.values_list('code', flat=True).order_by('code'))
        if codes:
            self.stdout.write(f'First code: {codes[0]}')
            self.stdout.write(f'Last code: {codes[-1]}')
            
            # Show batch coverage
            batch_count = (int(codes[-1]) // 1000000) + 1
            self.stdout.write(f'Approximate batches needed: {batch_count}')
            
            # Show missing ranges
            self.stdout.write(f'\nMissing ranges (approximate):')
            for i in range(1, batch_count + 1):
                start = (i - 1) * 50 + 1
                end = i * 50
                batch_codes = [code for code in codes if start <= int(code) <= end]
                if len(batch_codes) < 50:
                    self.stdout.write(f'  Batch {i} ({start}-{end}): {50 - len(batch_codes)} missing')

    def show_batch_info(self, start_code, end_code):
        self.stdout.write(f'\n=== Batch {start_code//50 + 1} Information ===')
        self.stdout.write(f'Range: {start_code:010d} - {end_code:010d}')
        
        # Check what's already in database for this range
        existing_codes = HsCode.objects.filter(
            code__gte=f'{start_code:010d}',
            code__lte=f'{end_code:010d}'
        ).order_by('code')
        
        self.stdout.write(f'Already in database: {existing_codes.count()} codes')
        if existing_codes:
            self.stdout.write('Existing codes:')
            for code in existing_codes[:10]:  # Show first 10
                self.stdout.write(f'  {code.code}: {code.description_uz[:30]}...')
            if existing_codes.count() > 10:
                self.stdout.write(f'  ... and {existing_codes.count() - 10} more')
        
        self.stdout.write(f'\nTo add codes to this batch:')
        self.stdout.write(f'1. Create a JSON file with the format:')
        self.stdout.write(f'   [')
        self.stdout.write(f'     {{')
        self.stdout.write(f'       "code": "0101210000",')
        self.stdout.write(f'       "description_uz": "Zotli naslli otlar",')
        self.stdout.write(f'       "description_ru": "Чистокровные племенные лошади",')
        self.stdout.write(f'       "category": "Tirik hayvonlar",')
        self.stdout.write(f'       "subcategory": "Otlar",')
        self.stdout.write(f'       "keywords": "ot, tirik, naslli, zotli, kon, horse",')
        self.stdout.write(f'       "duty_rate": 0.0,')
        self.stdout.write(f'       "vat_rate": 12.0,')
        self.stdout.write(f'       "excise_rate": 0.0,')
        self.stdout.write(f'       "required_certificates": "[\\"Veterinariya sertifikati\\"]"')
        self.stdout.write(f'     }}')
        self.stdout.write(f'   ]')
        self.stdout.write(f'2. Run: python manage.py batch_hs_code_processor --batch {start_code//50 + 1} --file your_file.json')

    def process_batch_from_file(self, file_path, start_code, end_code):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if not isinstance(data, list):
                self.stdout.write(self.style.ERROR('JSON file must contain an array of HS code objects'))
                return

            self.stdout.write(f'Processing {len(data)} HS codes from {file_path}')
            
            new_count = 0
            updated_count = 0
            error_count = 0

            for item in data:
                try:
                    # Validate required fields
                    required_fields = ['code', 'description_uz', 'description_ru', 'category', 'subcategory']
                    for field in required_fields:
                        if field not in item:
                            raise ValueError(f'Missing required field: {field}')

                    # Validate code format
                    code = item['code']
                    if not code.isdigit() or len(code) != 10:
                        raise ValueError(f'Invalid code format: {code}')

                    # Check if code is in the correct batch range
                    code_int = int(code)
                    if not (start_code <= code_int <= end_code):
                        self.stdout.write(self.style.WARNING(f'Code {code} is outside batch range {start_code}-{end_code}, skipping'))
                        continue

                    # Process the HS code
                    obj, created = HsCode.objects.update_or_create(
                        code=code,
                        defaults={
                            'description_uz': item['description_uz'],
                            'description_ru': item['description_ru'],
                            'category': item.get('category', ''),
                            'subcategory': item.get('subcategory', ''),
                            'keywords': item.get('keywords', ''),
                            'duty_rate': float(item.get('duty_rate', 0.0)),
                            'vat_rate': float(item.get('vat_rate', 12.0)),
                            'excise_rate': float(item.get('excise_rate', 0.0)),
                            'required_certificates': item.get('required_certificates', '[]'),
                        }
                    )

                    if created:
                        new_count += 1
                        self.stdout.write(f'Added: {code} - {item["description_uz"][:30]}...')
                    else:
                        updated_count += 1
                        self.stdout.write(f'Updated: {code} - {item["description_uz"][:30]}...')

                except Exception as e:
                    error_count += 1
                    self.stdout.write(self.style.ERROR(f'Error processing item: {str(e)}'))

            self.stdout.write(f'\n=== Batch Processing Complete ===')
            self.stdout.write(f'New codes added: {new_count}')
            self.stdout.write(f'Codes updated: {updated_count}')
            self.stdout.write(f'Errors: {error_count}')
            self.stdout.write(f'Total database codes: {HsCode.objects.count()}')

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f'File not found: {file_path}'))
        except json.JSONDecodeError:
            self.stdout.write(self.style.ERROR(f'Invalid JSON format in file: {file_path}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error processing file: {str(e)}'))