# julia set frame generator along path in complex plane
# @spiralbend 19 July 2025

import numpy as np
from matplotlib.pyplot import imsave, get_cmap
from numba import njit
import os

# Configuration
WIDTH = 1500
HEIGHT = 1500
MAX_ITER = 300
N_FRAMES = 4320
OUTPUT_DIR = "frames"

# Bounds of the complex plane
XMIN, XMAX = -1.5, 1.5
YMIN, YMAX = -1.5, 1.5

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


# Complex grid
def make_plane(xmin, xmax, ymin, ymax, w, h):
    x = np.linspace(xmin, xmax, w)
    y = np.linspace(ymin, ymax, h)
    X, Y = np.meshgrid(x, y)
    return X + 1j * Y


# Compute escape iteration counts
@njit
def compute(C, max_iter, Z0):
    h, w = Z0.shape
    escape = np.full((h, w), -1, dtype=np.int32)
    for i in range(h):
        for j in range(w):
            z = Z0[i, j]
            for k in range(max_iter):
                if (z.real * z.real + z.imag * z.imag) > 4.0:
                    escape[i, j] = k
                    break
                z = z * z + C
    return escape


# Path through complex plane: circle around Mandelbrot cardioid
def cardioid_orbit(n, r=0.7885):
    return [r * np.exp(2j * np.pi * t / n) for t in range(n)]


def inward_spiral(n, r_start=1.2, r_end=0.75):
    return [
        r * np.exp(2j * np.pi * t)
        for r, t in zip(np.linspace(r_start, r_end, n), np.linspace(0, 1, n))
    ]


def real_line(n):
    return [x + 0j for x in np.linspace(-2, 0.5, n)]


def linear_path(c0, c1, n):
    return [c0 + (c1 - c0) * t for t in np.linspace(0, 1, n)]


def lissajous(n, a=1.2, b=0.7, fx=3, fy=2, phase=0):
    return [
        a * np.sin(fx * t + phase) + 1j * b * np.sin(fy * t)
        for t in np.linspace(0, 2 * np.pi, n)
    ]


def complex_to_pixel(C, xmin, xmax, ymin, ymax, width, height):
    x_idx = int((C.real - xmin) / (xmax - xmin) * (width - 1))
    y_idx = int((C.imag - ymin) / (ymax - ymin) * (height - 1))
    return y_idx, x_idx  # row, column (image coordinates)


# Precompute grid
Z0 = make_plane(XMIN, XMAX, YMIN, YMAX, WIDTH, HEIGHT)

# Colormap
cmap = get_cmap("inferno").copy()
cmap.set_bad("black")

# Generate frames
# for i, C in enumerate(cardioid_orbit(N_FRAMES)):
# for i, C in enumerate(inward_spiral(N_FRAMES)):
# for i, C in enumerate(real_line(N_FRAMES)):
# for i, C in enumerate(linear_path(N_FRAMES)):
for i, C in enumerate(lissajous(N_FRAMES)):

    raw = compute(C, MAX_ITER, Z0)

    with np.errstate(divide="ignore", invalid="ignore"):
        img = np.log(raw + 1).astype(np.float32)

    y, x = complex_to_pixel(C, XMIN, XMAX, YMIN, YMAX, WIDTH, HEIGHT)

    img[raw == -1] = np.nan
    img[raw <= 2] = np.nan

    vmin = 0
    vmax = np.log(MAX_ITER)

    if 0 <= y < HEIGHT and 0 <= x < WIDTH:
        img[y, x] = np.nanmax(img)  # or vmax if not using dynamic scaling

    # cross
    for dy, dx in [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]:
        yi = y + dy
        xi = x + dx
        if 0 <= yi < HEIGHT and 0 <= xi < WIDTH:
            img[yi, xi] = np.log(MAX_ITER)

    imsave(
        f"{OUTPUT_DIR}/frame_{i:04d}.png",
        img,
        cmap=cmap,
        vmin=0,
        vmax=np.log(MAX_ITER),
    )

    print(f"\rSaved frame {i + 1}/{N_FRAMES}", end="")

print()
