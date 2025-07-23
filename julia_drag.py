# julia set interactive plotter
# @spiralbend 19 July 2025

import numpy as np
import matplotlib.pyplot as plt
from numba import njit

hi = {"grain": 600, "max_iter": 200}
lo = {"grain": 30, "max_iter": 10}
state = {"config": hi, "dragging": False}

c = {"xmin": -2, "xmax": 2, "ymin": -2, "ymax": 2, "grain": 100, "max_iter": 10}
C = 0  # initial complex value


def update_image(x, y):
    new_C = complex(x, y)
    Z0 = make_plane(
        c["xmin"], c["xmax"], c["ymin"], c["ymax"], state["config"]["grain"]
    )
    raw = compute(new_C, state["config"]["max_iter"], Z0)

    with np.errstate(divide="ignore"):
        img = np.log(raw + 1)
        img[raw == -1] = np.nan
        img[raw <= 2] = np.nan  # remove fast escapers

    vmin = np.nanmin(img)
    vmax = np.nanmax(img)
    norm = plt.Normalize(vmin=vmin, vmax=vmax)
    im.set_norm(norm)

    im.set_data(img)
    label.set_text(f"C = {new_C.real:.3f} + {new_C.imag:.3f}j")
    im.set_extent([c["xmin"], c["xmax"], c["ymin"], c["ymax"]])
    fig.canvas.draw_idle()


def on_press(event):
    if event.inaxes != ax:
        return
    state["dragging"] = True
    state["config"] = lo


def on_motion(event):
    if not state["dragging"] or event.inaxes != ax:
        return
    update_image(event.xdata, event.ydata)


def on_release(event):
    if not state["dragging"]:
        return
    state["dragging"] = False
    state["config"] = hi
    update_image(event.xdata, event.ydata)


def make_plane(xi, xa, yi, ya, gr):
    x = np.linspace(xi, xa, gr)
    y = np.linspace(yi, ya, gr)
    X, Y = np.meshgrid(x, y)
    return X + 1j * Y


@njit
def compute(C, max_iter, Z0):
    h, w = Z0.shape
    escape = np.full((h, w), -1, dtype=np.int32)  # default: did not escape

    for i in range(h):
        for j in range(w):
            z = Z0[i, j]
            for k in range(max_iter):
                if (z.real * z.real + z.imag * z.imag) > 4.0:
                    escape[i, j] = k
                    break
                z = z * z + C
    return escape


def render(C, ax, Z0, max_iter):
    img = compute(C, max_iter, Z0)
    cmap = plt.get_cmap("inferno").copy()
    cmap.set_bad("black")

    im = ax.imshow(
        img,
        cmap=cmap,
        norm=plt.Normalize(vmin=0, vmax=np.log(max_iter)),
        extent=[c["xmin"], c["xmax"], c["ymin"], c["ymax"]],
    )

    label = ax.text(
        0.02,
        0.98,
        f"C = {C.real:.3f} + {C.imag:.3f}j",
        color="white",
        fontsize=10,
        ha="left",
        va="top",
        transform=ax.transAxes,
    )
    return im, label


def main():
    global fig, ax, im, label, Z0
    Z0 = make_plane(c["xmin"], c["xmax"], c["ymin"], c["ymax"], c["grain"])
    fig, ax = plt.subplots()

    im, label = render(C, ax, Z0, c["max_iter"])
    ax.set_position([0, 0, 1, 1])
    ax.axis("off")
    ax.set_aspect("auto")

    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.patch.set_visible(False)
    manager = plt.get_current_fig_manager()
    manager.window.setGeometry(100, 100, 1000, 1000)

    def onclick(event):
        if event.inaxes != ax:
            return
        x, y = event.xdata, event.ydata
        new_C = complex(x, y)
        raw = compute(new_C, state["config"]["max_iter"], Z0)

        with np.errstate(divide="ignore"):
            img = np.log(raw + 1)
            img[raw == -1] = np.nan
            vmin = np.nanmin(img)
            vmax = np.nanmax(img)
            norm = plt.Normalize(vmin=vmin, vmax=vmax)
            im.set_norm(norm)

        img[raw <= 2] = np.nan
        im.set_data(img)
        label.set_text(f"C = {new_C.real:.3f} + {new_C.imag:.3f}j")
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", on_press)
    fig.canvas.mpl_connect("motion_notify_event", on_motion)
    fig.canvas.mpl_connect("button_release_event", on_release)

    plt.show()


if __name__ == "__main__":
    main()
