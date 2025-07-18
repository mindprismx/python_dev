import numpy as np
import matplotlib.pyplot as plt

max_iter = 100
grain_x = 100
grain_y = 100


def mandelbrot(xmin, xmax, ymin, ymax, grain_x, grain_y, max_iter):
    x = np.linspace(xmin, xmax, grain_x)
    y = np.linspace(ymin, ymax, grain_y)
    X, Y = np.meshgrid(x, y)
    C = X + 1j * Y
    Z = np.zeros(C.size, dtype=np.complex64)
    C = C.ravel().astype(np.complex64)
    M = np.ones(C.size, dtype=bool)
    escape = np.zeros(C.size, dtype=np.float32)

    for i in range(max_iter):
        Z[M] = Z[M] ** 2 + C[M]
        escaped = (Z.real**2 + Z.imag**2) > 4
        mask = M & escaped
        z_sub = Z[mask]
        escape[mask] = i  # - (np.log2(np.abs(z_sub))) + 4
        M[mask] = False

    escape[M] = 0
    return escape.reshape((grain_y, grain_x))


def on_zoom(event):
    global prev_limits

    # Only respond to zoom actions (button 1 = left click release)
    if event.button != 1:
        return
    xmin_new, xmax_new = ax.get_xlim()
    ymin_new, ymax_new = ax.get_ylim()
    limits = (xmin_new, xmax_new, ymin_new, ymax_new)

    if limits == prev_limits:
        return  # no actual zoom

    grain_x, grain_y, max_iter = adaptive_params(xmin_new, xmax_new, ymin_new, ymax_new)
    img = mandelbrot(xmin_new, xmax_new, ymin_new, ymax_new, grain_x, grain_y, max_iter)

    im.set_data(img)
    im.set_extent([xmin_new, xmax_new, ymin_new, ymax_new])
    fig.canvas.draw_idle()


def adaptive_params(xmin, xmax, ymin, ymax):
    span_x = xmax - xmin
    span_y = ymax - ymin

    # Base target pixel count (e.g., 2 million max)
    max_pixels = 2_000_000
    aspect = span_y / span_x
    grain_x = int(np.sqrt(max_pixels / aspect))
    grain_y = int(grain_x * aspect)

    # Minimum bounds
    grain_x = max(grain_x, 200)
    grain_y = max(grain_y, 200)
    max_iter = int(200 + 1000 / min(span_x, span_y))
    max_iter = min(max_iter, 2000)

    return grain_x, grain_y, max_iter


# Initial plot
(xmin, xmax, ymin, ymax) = (-2, 1, -1.5, 1.5)
img = mandelbrot(xmin, xmax, ymin, ymax, grain_x, grain_y, max_iter)
fig, ax = plt.subplots()
im = ax.imshow(img, cmap="inferno", extent=[xmin, xmax, ymin, ymax], origin="lower")
plt.colorbar(im, ax=ax)
plt.title("Mandelbrot View")
prev_limits = None
fig.canvas.mpl_connect("button_release_event", on_zoom)
plt.show()
