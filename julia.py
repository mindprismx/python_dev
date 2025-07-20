# julia set plotter
# @spiralbend 19 July 2025

import numpy as np
import matplotlib.pyplot as plt

c = {"xmin": -2, "xmax": 2, "ymin": -2, "ymax": 2, "grain": 100, "max_iter": 10}
C = 0.358 + 0.406j  # initial complex value


def make_plane(xi, xa, yi, ya, gr):
    x = np.linspace(xi, xa, gr)
    y = np.linspace(yi, ya, gr)
    X, Y = np.meshgrid(x, y)
    return X + 1j * Y


def compute(C, max_iter, Z0):
    Z = Z0.copy()
    M = np.full(Z.shape, True, dtype=bool)
    escape = np.zeros(Z.shape, dtype=int)

    for i in range(max_iter):
        if not M.any():
            break
        Z[M] = Z[M] ** 2 + C
        gone = (Z.real**2 + Z.imag**2) > 4
        escape[M & gone] = i
        M[M & gone] = False

    with np.errstate(divide="ignore"):
        return np.log(escape + 1)


def render(C, ax, Z0, max_iter):
    img = compute(C, max_iter, Z0)
    im = ax.imshow(
        img,
        cmap="inferno",
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

    ax.axis("off")
    plt.subplots_adjust(left=0, right=1, top=1, bottom=0)
    fig.patch.set_visible(False)
    ax.set_position([0, 0, 1, 1])

    manager = plt.get_current_fig_manager()
    manager.window.setGeometry(100, 100, 1000, 1000)

    def onclick(event):
        if event.inaxes != ax:
            return
        x, y = event.xdata, event.ydata
        new_C = complex(x, y)
        img = compute(new_C, c["max_iter"], Z0)
        im.set_data(img)
        label.set_text(f"C = {new_C.real:.3f} + {new_C.imag:.3f}j")
        fig.canvas.draw_idle()

    fig.canvas.mpl_connect("button_press_event", onclick)
    plt.show()


if __name__ == "__main__":
    main()
