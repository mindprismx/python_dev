# julia_pygame.py
# @spiralbend 21 July 2025 - updated for dual-resolution rendering

import pygame
import numpy as np
from numba import njit
import math

# Window size (always fixed)
WIDTH, HEIGHT = 900, 900

# Complex plane bounds
XMIN, XMAX = -2.0, 2.0
YMIN, YMAX = -2.0, 2.0

# Iteration settings
MAX_ITER_HI = 200
MAX_ITER_LO = 80

# Resolution settings
RENDER_RES_HI = 1500
RENDER_RES_LO = 120

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Julia Set Explorer")

font = pygame.font.SysFont("monospace", 16)
clock = pygame.time.Clock()

dragging = False
max_iter = MAX_ITER_HI


def map_pixel_to_complex(x, y):
    re = XMIN + (x / WIDTH) * (XMAX - XMIN)
    im = YMIN + (y / HEIGHT) * (YMAX - YMIN)
    return complex(re, im)


@njit
def julia(C, max_iter, W, H, xmin, xmax, ymin, ymax):
    output = np.full((H, W), -1, dtype=np.int32)
    for i in range(H):
        for j in range(W):
            x = xmin + (j / W) * (xmax - xmin)
            y = ymin + (i / H) * (ymax - ymin)
            z = complex(x, y)
            for k in range(max_iter):
                if z.real * z.real + z.imag * z.imag > 4.0:
                    output[i, j] = k
                    break
                z = z * z + C
    return output


def get_color(k, max_iter):
    if k == -1:
        return (0, 0, 0)
    t = math.log(k + 1) / math.log(max_iter + 1)
    val = int(255 * t)
    return (val, val // 2, 255 - val)


def draw_julia(C, render_res):
    escape = julia(C, max_iter, render_res, render_res, XMIN, XMAX, YMIN, YMAX)

    small_surface = pygame.Surface((render_res, render_res))
    for y in range(render_res):
        for x in range(render_res):
            color = get_color(escape[y, x], max_iter)
            small_surface.set_at((x, y), color)

    scaled = pygame.transform.scale(small_surface, (WIDTH, HEIGHT))
    screen.blit(scaled, (0, 0))

    label = font.render(f"C = {C.real:.3f} + {C.imag:.3f}j", True, (255, 255, 255))
    screen.blit(label, (10, 10))
    pygame.display.flip()


def main():
    global dragging, max_iter
    cur_C = complex(0, 0)
    draw_julia(cur_C, RENDER_RES_HI)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.MOUSEBUTTONDOWN:
                dragging = True
                max_iter = MAX_ITER_LO

            elif event.type == pygame.MOUSEBUTTONUP:
                dragging = False
                max_iter = MAX_ITER_HI
                x, y = event.pos
                cur_C = map_pixel_to_complex(x, y)
                draw_julia(cur_C, RENDER_RES_HI)

            elif event.type == pygame.MOUSEMOTION and dragging:
                x, y = event.pos
                cur_C = map_pixel_to_complex(x, y)
                draw_julia(cur_C, RENDER_RES_LO)

        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
