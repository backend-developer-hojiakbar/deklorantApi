import re

# Read the file
with open('info.txt', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Filter valid HS code lines
valid_lines = []
for line in lines:
    line = line.strip()
    if line and re.match(r'^\d{10}', line):
        valid_lines.append(line)

print('Line 251:')
parts = re.split(r'\t+', valid_lines[250])
print(f'Parts: {len(parts)}')
for i, part in enumerate(parts):
    print(f'  {i}: {repr(part[:50])}')

print('\nLine 252:')
parts = re.split(r'\t+', valid_lines[251])
print(f'Parts: {len(parts)}')
for i, part in enumerate(parts):
    print(f'  {i}: {repr(part[:50])}')