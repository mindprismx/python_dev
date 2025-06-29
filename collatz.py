#
# Collatz cycles to 100k or argv[1]
# @spiralbend 2025-06-25
#

import sys
import time

start = time.time()
upto = int(sys.argv[1]) if len(sys.argv) > 1 else 100_000
counter = {}
memo = {}

def main():

    for seed in range(1, upto + 1):
        counter[seed] = co_length(seed)

    max_seed = max(counter, key=counter.get)
    nice = make_cycle(max_seed)

    print(f"The prize for under {upto} belongs to {max_seed} with "
          f"{counter[max_seed]} steps:\n{nice}")

    print(f"Elapsed time: {time.time() - start:.4f} seconds")


def co_length(n):
    if n == 1:
        return 1
    elif n in memo:
        return memo[n]
    elif n % 2 == 0:
        next_n = n // 2
    else:
        next_n = 3 * n + 1
    memo[n] = 1 + co_length(next_n)
    return memo[n]


def make_cycle(n):
    nodes = [n]
    while n != 1:
        if n % 2 == 0:
            n //= 2
        else:
            n = n * 3 + 1
        nodes.append(n)
    return " → ".join(str(x) for x in nodes)

main()