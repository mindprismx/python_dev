# mandelbrot plotter
# @spiralbend 16 July 2025

import numpy as np
import matplotlib.pyplot as plot

max_iter = 300
grain = 500
(xmin, xmax, ymin, ymax) = (-2, 1, -1.5, 1.5)

x = np.linspace(xmin, xmax, grain)
y = np.linspace(ymin, ymax, grain)

X, Y = np.meshgrid(x, y)  # shape (H, W)
C = X + 1j * Y  # complex plane
Z = np.zeros_like(C)
M = np.full(C.shape, True, dtype=bool)  # mask of active points
escape = np.zeros(C.shape, dtype=int)

# vectorized loop
for i in range(max_iter):
    Z[M] = Z[M] ** 2 + C[M]
    escaped = np.abs(Z) > 2
    escape[M & escaped] = i
    M[M & escaped] = False

img = escape.astype(float)
with np.errstate(divide="ignore"):
    img = np.log(img + 1)

plot.imshow(img, cmap="inferno", extent=[xmin, xmax, ymin, ymax])
plot.colorbar()
plot.title("Mandelbrot View")
plot.show()
