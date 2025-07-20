import numpy as np, time

grain = 100
max_iter = 10
Z0 = np.random.rand(grain, grain) + 1j * np.random.rand(grain, grain)


def compute(C, Z0, max_iter):
    Z = Z0.copy()
    M = np.full(Z.shape, True, dtype=bool)
    escape = np.zeros(Z.shape, dtype=int)
    for i in range(max_iter):
        if not M.any():
            break
        Z[M] = Z[M] ** 2 + C
        escaped = (Z.real**2 + Z.imag**2) > 4
        escape[M & escaped] = i
        M[M & escaped] = False
    return np.log(escape + 1)


start = time.perf_counter()
compute(-0.8 + 0.156j, Z0, max_iter)
end = time.perf_counter()
print(f"Elapsed: {(end - start)*1000:.2f} ms")
