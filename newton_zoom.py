# newton_zoomer.py
# @spiralbend 28 July 2025 - Newton fractal zoomer with denom guard

import pygame
import numpy as np
from numba import njit
import math

# ─── CONFIG ──────────────────────────────────────────────────────────
WINDOW_SIZE = 2000  # Window is WINDOW_SIZE×WINDOW_SIZE
RENDER_RES = 800  # Compute resolution
MAX_ITER = 50  # Iterations per pixel
DEGREE = 3  # Polynomial degree for z^n - 1
ZOOM_FACTOR = 2  # Zoom factor per click
EPSILON = 1e-6  # Convergence tolerance

# Initial viewport (square) covering roots around unit circle
X_MIN, X_MAX = -1.5, 1.5
Y_MIN, Y_MAX = -1.5, 1.5

# Precompute roots of unity (roots of z^DEGREE = 1)
ROOTS = np.array(
    [
        complex(math.cos(2 * math.pi * k / DEGREE), math.sin(2 * math.pi * k / DEGREE))
        for k in range(DEGREE)
    ],
    dtype=np.complex128,
)
ROOTS_RE = np.array([z.real for z in ROOTS], dtype=np.float64)
ROOTS_IM = np.array([z.imag for z in ROOTS], dtype=np.float64)


@njit(cache=True)
def newton_engine(
    max_iter, W, H, xmin, xmax, ymin, ymax, roots_re, roots_im, degree, eps
):
    out = np.empty((H, W), np.int32)
    for i in range(H):
        y0 = ymin + i / H * (ymax - ymin)
        for j in range(W):
            x0 = xmin + j / W * (xmax - xmin)
            z = complex(x0, y0)
            it = 0
            # Newton iteration
            while it < max_iter:
                # compute z^degree and z^(degree-1)
                zr, zi = z.real, z.imag
                zpow = complex(1.0, 0.0)
                zpow_m1 = complex(1.0, 0.0)
                for k in range(degree):
                    if k == degree - 1:
                        zpow_m1 = zpow
                    zpow = complex(
                        zpow.real * zr - zpow.imag * zi, zpow.real * zi + zpow.imag * zr
                    )
                # Newton step: z = z - (z^n - 1)/(n*z^(n-1))
                f = complex(zpow.real - 1.0, zpow.imag)
                fp = complex(degree * zpow_m1.real, degree * zpow_m1.imag)
                # divide f/fp with guard
                br, bi = fp.real, fp.imag
                denom = br * br + bi * bi
                if denom == 0.0:
                    break
                inv_d = 1.0 / denom
                z = complex(
                    z.real - (f.real * br + f.imag * bi) * inv_d,
                    z.imag - (f.imag * br - f.real * bi) * inv_d,
                )
                # convergence check
                mind = 1e18
                for k in range(degree):
                    dr = z.real - roots_re[k]
                    di = z.imag - roots_im[k]
                    d2 = dr * dr + di * di
                    if d2 < mind:
                        mind = d2
                if mind < eps * eps:
                    break
                it += 1
            # identify nearest root index
            min_idx = 0
            mind = 1e18
            for k in range(degree):
                dr = z.real - roots_re[k]
                di = z.imag - roots_im[k]
                d2 = dr * dr + di * di
                if d2 < mind:
                    mind = d2
                    min_idx = k
            # encode: root * max_iter + iteration
            out[i, j] = min_idx * max_iter + it
    return out


# Color mapping: hue per root, shaded by speed
def color_map(val, max_iter, degree):
    root = val // max_iter
    it = val % max_iter
    # base hue
    angle = 2 * math.pi * root / degree
    r0 = int(127 * (1 + math.cos(angle)))
    g0 = int(127 * (1 + math.cos(angle + 2 * math.pi / 3)))
    b0 = int(127 * (1 + math.cos(angle + 4 * math.pi / 3)))
    # shade by iteration
    t = 1 - it / max_iter
    return (int(r0 * t), int(g0 * t), int(b0 * t))


# Draw fractal
def draw_fractal(surface, bounds):
    xmin, xmax, ymin, ymax = bounds
    escape = newton_engine(
        MAX_ITER,
        RENDER_RES,
        RENDER_RES,
        xmin,
        xmax,
        ymin,
        ymax,
        ROOTS_RE,
        ROOTS_IM,
        DEGREE,
        EPSILON,
    )
    arr = pygame.PixelArray(surface)
    for y in range(RENDER_RES):
        for x in range(RENDER_RES):
            arr[x, y] = surface.map_rgb(color_map(int(escape[y, x]), MAX_ITER, DEGREE))
    del arr


# MAIN: click-to-zoom
def main():
    pygame.init()
    screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
    pygame.display.set_caption("Newton Fractal Explorer")
    clock = pygame.time.Clock()

    bounds = [X_MIN, X_MAX, Y_MIN, Y_MAX]
    surface = pygame.Surface((RENDER_RES, RENDER_RES))
    draw_fractal(surface, bounds)
    screen.blit(pygame.transform.scale(surface, (WINDOW_SIZE, WINDOW_SIZE)), (0, 0))
    pygame.display.flip()

    running = True
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
            elif evt.type == pygame.MOUSEBUTTONDOWN:
                mx, my = evt.pos
                cx = bounds[0] + mx / WINDOW_SIZE * (bounds[1] - bounds[0])
                cy = bounds[2] + my / WINDOW_SIZE * (bounds[3] - bounds[2])
                span_x = (bounds[1] - bounds[0]) / (2 * ZOOM_FACTOR)
                span_y = (bounds[3] - bounds[2]) / (2 * ZOOM_FACTOR)
                bounds = [cx - span_x, cx + span_x, cy - span_y, cy + span_y]
                draw_fractal(surface, bounds)
                screen.blit(
                    pygame.transform.scale(surface, (WINDOW_SIZE, WINDOW_SIZE)), (0, 0)
                )
                pygame.display.flip()
        clock.tick(30)
    pygame.quit()


if __name__ == "__main__":
    main()
