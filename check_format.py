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

print(f'Total valid lines: {len(valid_lines)}')

# Check for format issues
for i, line in enumerate(valid_lines[:20]):
    parts = re.split(r'\t+', line)
    print(f'\nLine {i+1}:')
    print(f'  Parts: {len(parts)}')
    for j, part in enumerate(parts[:12]):
        print(f'    {j}: {repr(part[:50])}')
    
    # Check if excise rate is a number
    if len(parts) >= 9:
        try:
            float(parts[8].strip())
        except ValueError:
            print(f'  ERROR: Excise rate is not a number: {repr(parts[8])}')
            break