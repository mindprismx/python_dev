# julia set frame generator along path in complex plane
# @spiralbend 19 July 2025


from numba import njit
import matplotlib.pyplot as plt
import numpy as np
import os

# Configuration
res = "hi"
cross = False

TBEG, TEND = -4, -0.5
WIDTH = {"lo": 200, "hi": 2000}
HEIGHT = {"lo": 200, "hi": 2000}
MAX_ITER = {"lo": 50, "hi": 300}
N_FRAMES = {"lo": 50, "hi": 4230}
OUTPUT_DIR = "frames"

# Bounds of the complex plane
XMIN, XMAX = -2.5, 2.5
YMIN, YMAX = -2.5, 2.5

t_space = np.linspace(TBEG, TEND, N_FRAMES[res])

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


# Path in complex plane: circle around Mandelbrot cardioid try 0.7885
def cardioid_orbit(n, r=1):
    return [r * np.exp(1j * t) for t in np.linspace(0, 2 * np.pi, n)]


def inward_spiral(n, r_start=1.2, r_end=0.55):
    return [
        r * np.exp(2j * np.pi * t)
        for r, t in zip(np.linspace(r_start, r_end, n), np.linspace(0, 2, n))
    ]


def real_line(n):
    return [x + 0j for x in np.linspace(TBEG, TEND, n)]


def linear_path(c0, c1, n):
    return [c1 + (c0 - c1) * t for t in t_space]


def lissajous(n, a=1.2, b=0.7, fx=3, fy=2, phase=0):
    return [a * np.sin(fx * t + phase) + 1j * b * np.sin(fy * t) for t in t_space]


def complex_to_pixel(C, xmin, xmax, ymin, ymax, width, height):
    x_idx = int((C.real - xmin) / (xmax - xmin) * (width - 1))
    y_idx = height - 1 - int((C.imag - ymin) / (ymax - ymin) * (height - 1))
    return y_idx, x_idx


# Precompute grid
Z0 = make_plane(XMIN, XMAX, YMIN, YMAX, WIDTH[res], HEIGHT[res])

# Colormap
cmap = plt.get_cmap("inferno").copy()
cmap.set_bad("black")

# Generate frames
# for i, C in enumerate(cardioid_orbit(N_FRAMES[res])):
# for i, C in enumerate(inward_spiral(N_FRAMES[res])):
for i, C in enumerate(real_line(N_FRAMES[res])):
    # for i, C in enumerate(linear_path(-1.5 + 1.5j, 1.5 - 1.5j, N_FRAMES[res])):
    # for i, C in enumerate(lissajous(N_FRAMES[res])):

    raw = compute(C, MAX_ITER[res], Z0)

    with np.errstate(divide="ignore", invalid="ignore"):
        img = np.log(raw + 1).astype(np.float32)

    img[raw == -1] = np.nan
    img[raw <= 2] = np.nan
    y, x = complex_to_pixel(C, XMIN, XMAX, YMIN, YMAX, WIDTH[res], HEIGHT[res])

    if cross:
        for dy, dx in [(-1, 0), (0, -1), (0, 0), (0, 1), (1, 0)]:
            yi = y + dy
            xi = x + dx
            if 0 <= yi < HEIGHT[res] and 0 <= xi < WIDTH[res]:
                img[yi, xi] = np.log(MAX_ITER[res])

    if res == "hi":
        plt.imsave(
            f"{OUTPUT_DIR}/frame_{i:05d}.png",
            img,
            cmap=cmap,
            vmin=0,
            vmax=np.log(MAX_ITER[res]),
        )

    if res == "lo":
        fig, ax = plt.subplots(figsize=(5, 5), dpi=100)
        ax.imshow(img, cmap=cmap, vmin=0, vmax=np.log(MAX_ITER[res]))
        ax.axis("off")

        # Display t value and frame # as label
        t = t_space[i]
        ax.text(
            10,
            20,
            f"frame = {i}\nt = {t:.7f}",
            color="white",
            fontsize=12,
            ha="left",
            va="top",
        )

        fig.tight_layout(pad=0)
        fig.savefig(
            f"{OUTPUT_DIR}/frame_{i:05d}.png", bbox_inches="tight", pad_inches=0
        )
        plt.close(fig)

    print(f"\rSaved frame {i + 1}/{N_FRAMES[res]}", end="")

print()
