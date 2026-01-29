from customs_api.models import HsCode

# Get all numeric codes
codes = [int(hs.code) for hs in HsCode.objects.all() if hs.code.isdigit()]
codes.sort()

print(f"Total codes: {len(codes)}")
print(f"Min code: {min(codes) if codes else 'None'}")
print(f"Max code: {max(codes) if codes else 'None'}")

# Group by first 4 digits (chapter)
ranges = {}
for code in codes:
    prefix = code // 1000000
    if prefix not in ranges:
        ranges[prefix] = []
    ranges[prefix].append(code)

print("\nCodes by chapter (first 4 digits):")
for prefix in sorted(ranges.keys()):
    print(f"  {prefix:04d}: {len(ranges[prefix])} codes")

# Show gaps
print("\nMissing chapters:")
all_chapters = set(range(1, 21))  # Chapters 1-20 typically
existing_chapters = set(ranges.keys())
missing_chapters = all_chapters - existing_chapters
if missing_chapters:
    for chapter in sorted(missing_chapters):
        print(f"  Chapter {chapter:02d}: Missing")
else:
    print("  No missing chapters in range 1-20")