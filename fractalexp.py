# fractal_minimal.py
# Minimal fractal renderer with adjustable exponent and conjugation

import pygame
import numpy as np
from numba import njit
import math

# ─── CONFIG ──────────────────────────────────────────────────────────
WINDOW_SIZE = 2000  # display window is 2000×2000
RENDER_RES = 1000  # compute at 1000×1000 resolution
MAX_ITER = 200  # base iteration count
EXPONENT = 5  # power n in z^n + c (e.g., 2 for Mandelbrot, 3+ for Multibrot)
USE_CONJ = True  # if True, use conjugate z = conj(z) before power
# initial viewport (square) covering the full set
X_MIN, X_MAX = -2.5, 1.0
Y_MIN, Y_MAX = -1.75, 1.75


# ─── FRACTAL ENGINE ──────────────────────────────────────────────────
@njit(cache=True)
def fractal_engine(max_iter, exponent, use_conj, W, H, xmin, xmax, ymin, ymax):
    out = np.empty((H, W), np.int32)
    for i in range(H):
        y0 = ymin + i / H * (ymax - ymin)
        for j in range(W):
            x0 = xmin + j / W * (xmax - xmin)
            z = complex(0.0, 0.0)
            c = complex(x0, y0)
            it = 0
            while it < max_iter and (z.real * z.real + z.imag * z.imag) <= 4.0:
                if use_conj:
                    z = z.conjugate()
                # z^n + c
                # for integer exponent > 2, could use cmath.pow, but simple loop is fine
                zr, zi = z.real, z.imag
                # compute z**exponent via repeated multiplication
                zn = complex(1.0, 0.0)
                for _ in range(exponent):
                    zn = complex(
                        zn.real * zr - zn.imag * zi, zn.real * zi + zn.imag * zr
                    )
                z = zn + c
                it += 1
            out[i, j] = it if it < max_iter else -1
    return out


# ─── COLOR MAPPING ───────────────────────────────────────────────────
def color_map(k, max_k):
    if k < 0:
        return (0, 0, 0)
    t = math.log(k + 1) / math.log(max_k + 1)
    val = int(255 * t)
    return (val, val // 2, 255 - val)


# ─── DRAW FUNCTION ───────────────────────────────────────────────────
def draw_fractal(surface, engine, bounds, res, max_iter, exponent, use_conj):
    xmin, xmax, ymin, ymax = bounds
    escape = engine(max_iter, exponent, use_conj, res, res, xmin, xmax, ymin, ymax)
    # dynamic max for coloring
    pos = escape[escape >= 0]
    max_k = int(pos.max()) if pos.size else 1
    small = pygame.Surface((res, res))
    pix = pygame.PixelArray(small)
    for y in range(res):
        for x in range(res):
            pix[x, y] = small.map_rgb(color_map(int(escape[y, x]), max_k))
    del pix
    scaled = pygame.transform.smoothscale(small, (WINDOW_SIZE, WINDOW_SIZE))
    surface.blit(scaled, (0, 0))


# ─── MAIN LOOP ───────────────────────────────────────────────────────
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Fractal Minimal")
    clock = pygame.time.Clock()

    bounds = (X_MIN, X_MAX, Y_MIN, Y_MAX)
    engine = fractal_engine

    # initial render
    draw_fractal(screen, engine, bounds, RENDER_RES, MAX_ITER, EXPONENT, USE_CONJ)
    pygame.display.flip()

    running = True
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
        clock.tick(30)

    pygame.quit()


if __name__ == "__main__":
    main()
