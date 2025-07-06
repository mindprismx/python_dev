#
# prime factorize argv[1]
# @spiralbend 2025-07-05
#


import sys


def main():
    if len(sys.argv) > 1:
        num = int(sys.argv[1])
    else:
        num = int(input("Number to factor: "))

    product = []
    primes = find_factors(num, {})
    if num in primes.keys():
        print(f"{num} is prime.")
        sys.exit()
    for prime in primes:
        ex = super(primes[prime])
        product.append(f"{prime}{ex}")
    print(f"{num} =", f" {sup['x']} ".join(product))


def find_factors(n, factors):
    for i in range(2, n + 1):
        if n % i == 0 and is_prime(i):
            factors[i] = factors.get(i, 0) + 1
            quotient = n // i
            if quotient > 1:
                find_factors(quotient, factors)
            break
    return factors


def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True


def super(n):
    if n == 1:
        return ""
    x = ""
    for digit in str(n):
        x += sup[int(digit)]
    return x


sup = {
    0: "\u2070",
    1: "\u00b9",
    2: "\u00b2",
    3: "\u00b3",
    4: "\u2074",
    5: "\u2075",
    6: "\u2076",
    7: "\u2077",
    8: "\u2078",
    9: "\u2079",
    "x": "\u00b7",
}

main()
