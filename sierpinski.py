# sierpinski triangle
# @spiralbend 21 July 2025

import random
import numpy as np
import matplotlib.pyplot as plt

rt3 = np.sqrt(3)
triangle = [(0, 1), (rt3 / 2, -0.5), (-rt3 / 2, -0.5)]
ratio = 0.5


def interpolate(x1, y1, x2, y2, r):
    return ((x1 + x2) * r, (y1 + y2) * r)


def main():
    pinsky = []
    cur_pt = random.choice(triangle)
    for i in range(100_000):
        nxt_pt = random.choice(triangle)
        new_pt = interpolate(cur_pt[0], cur_pt[1], nxt_pt[0], nxt_pt[1], ratio)
        pinsky.append(new_pt)
        cur_pt = new_pt

    x_vals, y_vals = zip(*pinsky)
    plt.figure(figsize=(10, 10), dpi=100)
    plt.scatter(x_vals, y_vals, s=0.1)
    plt.axis("off")
    plt.show()


main()
