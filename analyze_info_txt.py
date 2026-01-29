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

print(f'Total lines: {len(lines)}')
print(f'Valid HS code lines: {len(valid_lines)}')

# Show first 3 and last 3
print('\nFirst 3 valid lines:')
for i in range(min(3, len(valid_lines))):
    print(f'{i+1}: {valid_lines[i][:100]}...')

print('\nLast 3 valid lines:')
for i in range(max(0, len(valid_lines)-3), len(valid_lines)):
    print(f'{i+1}: {valid_lines[i][:100]}...')

# Show sample of the structure
if valid_lines:
    print('\nSample structure (first line):')
    parts = re.split(r'\t+', valid_lines[0])
    print(f'Parts: {len(parts)}')
    for i, part in enumerate(parts[:10]):
        print(f'  {i}: {part}')