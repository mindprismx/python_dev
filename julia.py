# julia set plotter
# @spiralbend 19 July 2025

import numpy as np
import matplotlib.pyplot as plt

print(plt.get_backend())

max_iter = 100
grain = 100
(xmin, xmax, ymin, ymax) = (-3, 3, -3, 3)

x = np.linspace(xmin, xmax, grain)
y = np.linspace(ymin, ymax, grain)

C = -0.8 + 0.156j
X, Y = np.meshgrid(x, y)  # shape (H, W)
Z = X + 1j * Y  # complex plane
M = np.full(Z.shape, True, dtype=bool)  # mask of active points
escape = np.zeros(Z.shape, dtype=int)

# vectorized loop
for i in range(max_iter):
    Z[M] = Z[M] ** 2 + C
    escaped = np.abs(Z) > 2
    escape[M & escaped] = i
    M[M & escaped] = False

img = escape.astype(float)
with np.errstate(divide="ignore"):
    img = np.log(img + 1)

plt.imshow(img, cmap="inferno", extent=[xmin, xmax, ymin, ymax])
plt.title("Julia Set")
manager = plt.get_current_fig_manager()
manager.window.setGeometry(100, 100, 1000, 1000)  # x, y, width, height
plt.show()
