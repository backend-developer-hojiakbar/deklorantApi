from customs_api.models import HsCode
import json

# Load the batch file
with open('chapter_0101_batch.json', 'r') as f:
    data = json.load(f)

print('Processing chapter 0101 batch...')
new_count = 0

for item in data:
    # Process the HS code
    obj, created = HsCode.objects.update_or_create(
        code=item['code'],
        defaults={
            'description_uz': item['description_uz'],
            'description_ru': item['description_ru'],
            'category': item['category'],
            'subcategory': item['subcategory'],
            'keywords': item['keywords'],
            'duty_rate': float(item['duty_rate']),
            'vat_rate': float(item['vat_rate']),
            'excise_rate': float(item['excise_rate']),
            'required_certificates': item['required_certificates'],
        }
    )
    
    if created:
        new_count += 1
        print(f'Added: {item["code"]} - {item["description_uz"]}')
    else:
        print(f'Updated: {item["code"]} - {item["description_uz"]}')

print(f'\nAdded {new_count} new codes')
print(f'Total codes now: {HsCode.objects.count()}')