import re
from django.core.management.base import BaseCommand
from customs_api.models import HsCode

class Command(BaseCommand):
    help = 'Load new HS codes from info.txt (pages 1-50) into database'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='info.txt',
            help='Path to the info.txt file (default: info.txt)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'File {file_path} not found')
            )
            return
        except UnicodeDecodeError:
            # Try with different encodings
            try:
                with open(file_path, 'r', encoding='windows-1251') as f:
                    content = f.read()
            except UnicodeDecodeError:
                with open(file_path, 'r', encoding='cp1251') as f:
                    content = f.read()

        # Split content into lines
        lines = content.split('\n')
        
        # Pattern to match HS codes (format: XXXX XX XXX X)
        hs_code_pattern = r'^(\d{4}\s\d{2}\s\d{3}\s\d)\s*$'
        
        codes_found = []
        current_description_uz = ""
        current_description_ru = ""
        line_number = 0
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            line_number += 1
            
            # Skip empty lines and header/footer content
            if not line or line.startswith(('Ў', '©', 'ТИФ', 'ТАШҚИ', 'МУНДАРИЖА', 'ТОВАРЛАРНИ')):
                i += 1
                continue
                
            # Check if this line contains an HS code
            match = re.match(hs_code_pattern, line)
            if match:
                hs_code = match.group(1).replace(' ', '')  # Remove spaces
                
                # Get the Uzbek description (next non-empty line)
                uz_desc = ""
                ru_desc = ""
                
                # Look for descriptions in the following lines
                j = i + 1
                desc_lines_uz = []
                desc_lines_ru = []
                
                # Collect Uzbek description lines
                while j < len(lines):
                    next_line = lines[j].strip()
                    if not next_line:
                        j += 1
                        continue
                    
                    # Stop if we hit another HS code
                    if re.match(hs_code_pattern, next_line):
                        break
                    
                    # Stop if we hit section/goods headers
                    if next_line.startswith(('ТИФ', 'ТАШҚИ', '01-', '02-', '03-', '04-', '05-', '06-', '07-', '08-', '09-', '10-', '11-', '12-', '13-', '14-', '15-', '16-', '17-', '18-', '19-', '20-', '21-', '22-', '23-', '24-', '25-', '26-', '27-')):
                        break
                    
                    # Add to Uzbek description
                    if next_line and not next_line[0].isdigit():
                        desc_lines_uz.append(next_line)
                    
                    j += 1
                
                # Join descriptions
                if desc_lines_uz:
                    uz_desc = ' '.join(desc_lines_uz).strip()
                
                # Create or update HS code
                if hs_code and (uz_desc or ru_desc):
                    codes_found.append({
                        'code': hs_code,
                        'description_uz': uz_desc,
                        'description_ru': ru_desc,
                        'line_number': line_number
                    })
            
            i += 1
        
        # Process the found codes
        added_count = 0
        updated_count = 0
        skipped_count = 0
        
        for item in codes_found:
            hs_code = item['code']
            desc_uz = item['description_uz'] or ""
            desc_ru = item['description_ru'] or ""
            
            # Check if code already exists
            try:
                existing = HsCode.objects.get(code=hs_code)
                # Update only if descriptions are different or empty
                updated = False
                if not existing.description_uz and desc_uz:
                    existing.description_uz = desc_uz
                    updated = True
                if not existing.description_ru and desc_ru:
                    existing.description_ru = desc_ru
                    updated = True
                
                if updated:
                    existing.save()
                    updated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated: {hs_code} - {desc_uz[:50]}...')
                    )
                else:
                    skipped_count += 1
            except HsCode.DoesNotExist:
                # Create new entry
                HsCode.objects.create(
                    code=hs_code,
                    description_uz=desc_uz,
                    description_ru=desc_ru
                )
                added_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Added: {hs_code} - {desc_uz[:50]}...')
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\nProcessing complete!\n'
                f'Total codes found: {len(codes_found)}\n'
                f'Added to database: {added_count}\n'
                f'Updated in database: {updated_count}\n'
                f'Skipped (already up to date): {skipped_count}'
            )
        )