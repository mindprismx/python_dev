top = 10000
is_prime = [True] * (top + 1)
is_prime[0] = is_prime[1] = False

for base in range(2, int(top**0.5) + 1):
    if is_prime[base]:
        for multiple in range(base*base, top + 1, base):
            is_prime[multiple] = False

primes = [i for i, prime in enumerate(is_prime) if prime]
print(primes)
print(len(primes))