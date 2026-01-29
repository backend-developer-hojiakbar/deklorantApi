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

# Check for problematic lines
for i, line in enumerate(valid_lines):
    parts = re.split(r'\t+', line)
    
    # Check if we have enough parts
    if len(parts) < 10:
        print(f'Line {i+1}: Only {len(parts)} parts')
        print('  Sample:', repr(parts[:5]))
        continue
    
    # Check if excise rate is a number
    try:
        float(parts[8].strip())
    except ValueError:
        print(f'Line {i+1}: Excise rate is not a number: {repr(parts[8])}')
        print('  Full parts:', [repr(p) for p in parts[:10]])
        break