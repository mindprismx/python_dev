#
# Amicable numbers to 1k or argv[1]
# @spiralbend 2025-06-25
#

import sys

big = int(sys.argv[1]) if len(sys.argv) > 1 else 1000

def get_factors(n):
    factors = []
    if n > 1: factors.append(1)
    i = 2
    while i * 2 <= n:
        if n % i == 0:
            factors.append(i)
        i += 1
    return factors

sum_factors = [0] * (big + 1)
for i in range(1, big + 1):
    sum_factors[i] = sum(get_factors(i))

for i in range(1,big+1):
    si = sum_factors[i]
    if si == 1: continue
    for j in range(1,big+1):
        if i == j: break
        sj = sum_factors[j]
        if (si == j) and (sj == i):
            print (f"{j}, {sj}")
