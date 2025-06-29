#!/usr/local/bin/python3.12

# sieve of eratosthenes
# spiralbend 2025-06-23

import sys
arguments = sys.argv[1:]

top = int(arguments[0]) if len(arguments) > 0 else 5000

nums = list(range(2, top + 1))

for base in nums[:]:
	for i in range(base*2,top+1,base):
		if i in nums:
			nums.remove(i)

print(nums)
print(len(nums))
