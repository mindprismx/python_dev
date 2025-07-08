#!/usr/bin/env python3

import sys
import time

top = int(sys.argv[1]) if len(sys.argv) > 1 else 500_000_000
sieve = [True] * (top + 1)
sieve[0:2] = [False, False]
count = 0
for num in range(2, top + 1):
    if sieve[num]:
        print(num, end=", ", flush=True)
        count += 1
        for multiple in range(num * num, top + 1, num):
            sieve[multiple] = False
    num += 1
print(f"\n\nFound {count} primes less than {top}.")
print(f"Total time: {time.process_time()} seconds.")
