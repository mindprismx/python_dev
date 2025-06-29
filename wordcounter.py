#
# word counter for argv[1]
# @spiralbend 2025-06-27
#

import sys

total_words = 0
counts = {}
file = (sys.argv[1]) if len(sys.argv) > 1 else ''

with open(file) as f:
    for line in f:
        for word in line.split():
            clean = ''.join(c.lower() for c in word if c.isalpha())
            if not clean:
                continue
            counts[clean] = counts.get(clean, 0) + 1
            total_words += 1


sorted_keys = sorted(counts, key=lambda k: counts[k], reverse=True)

print (f"{total_words} words found ({len(counts)} unique).\n")

for k in sorted_keys:
    print(f"{k}: {counts[k]}")

