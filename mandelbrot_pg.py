# mandelbrot_zoom.py
# @spiralbend 27 July 2025 - Mandelbrot zoom with compute feedback, animated recenter+zoom, enhanced UI

import pygame
import numpy as np
from numba import njit
import math

# Window size (square)
WINDOW_SIZE = 2000

# Initial fractal bounds (full Mandelbrot), square viewport
X_MIN0, X_MAX0 = -2.5, 1.0
Y_MIN0, Y_MAX0 = -1.75, 1.75

# Iteration settings
MAX_ITER_HI = 200

# Render resolution for hi-res compute
RENDER_RES_HI = 1500
SUPER_RES_MULT = 1.7  # 170% super-resolution
SUPER_ITER_MULT = 1.2  # 120% max_iter on super-res

# Zoom and animation config
ZOOM_FACTOR = 10  # 10× zoom per click
ANIM_FRAMES = 15  # number of frames in the animation

# Button rectangles: Reset and SuperRes
BTN_WIDTH, BTN_HEIGHT = 200, 80
BTN_MARGIN = 20
RESET_BUTTON = pygame.Rect(
    WINDOW_SIZE - BTN_WIDTH - BTN_MARGIN, BTN_MARGIN, BTN_WIDTH, BTN_HEIGHT
)
SUPER_BUTTON = pygame.Rect(
    WINDOW_SIZE - BTN_WIDTH - BTN_MARGIN,
    BTN_MARGIN + BTN_HEIGHT + BTN_MARGIN,
    BTN_WIDTH,
    BTN_HEIGHT,
)

pygame.init()
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE))
pygame.display.set_caption("Mandelbrot Zoom Explorer")
font = pygame.font.SysFont(None, 24)
clock = pygame.time.Clock()


@njit(cache=True)
def mandelbrot(max_iter, W, H, xmin, xmax, ymin, ymax):
    output = np.zeros((H, W), dtype=np.int32)
    for i in range(H):
        y0 = ymin + i / H * (ymax - ymin)
        for j in range(W):
            x0 = xmin + j / W * (xmax - xmin)
            x = 0.0
            y = 0.0
            it = 0
            while x * x + y * y <= 4.0 and it < max_iter:
                xt = x * x - y * y + x0
                y = 2 * x * y + y0
                x = xt
                it += 1
            output[i, j] = it if it < max_iter else -1
    return output


def get_color(k, max_k):
    if k == -1:
        return (0, 0, 0)
    t = math.log(k + 1) / math.log(max_k + 1)
    val = int(255 * t)
    return (val, val // 2, 255 - val)


def draw_compute_feedback():
    txt = font.render("Computing...", True, (255, 255, 255))
    bg = pygame.Surface(txt.get_size(), pygame.SRCALPHA)
    bg.fill((0, 0, 0, 180))
    x = (WINDOW_SIZE - txt.get_width()) // 2
    y = (WINDOW_SIZE - txt.get_height()) // 2
    screen.blit(bg, (x, y))
    screen.blit(txt, (x, y))
    draw_buttons()
    pygame.display.flip()


def draw_fractal(res, bounds, iter_count):
    # show feedback
    draw_compute_feedback()
    # compute escape counts
    xmin, xmax, ymin, ymax = bounds
    escape = mandelbrot(iter_count, res, res, xmin, xmax, ymin, ymax)
    # dynamic color range
    pos = escape[escape >= 0]
    max_k = int(pos.max()) if pos.size > 0 else 1
    surf = pygame.Surface((res, res))
    for yi in range(res):
        for xi in range(res):
            surf.set_at((xi, yi), get_color(escape[yi, xi], max_k))
    scaled = pygame.transform.smoothscale(surf, (WINDOW_SIZE, WINDOW_SIZE))
    screen.blit(scaled, (0, 0))


def draw_center_and_res(bounds, res, iter_count):
    xmin, xmax, ymin, ymax = bounds
    cx = (xmin + xmax) / 2
    cy = (ymin + ymax) / 2
    txt1 = f"Center: {cx:.10f} + {cy:.10f}j"
    txt2 = f"Resolution: {res}×{res}, Iter: {iter_count}"
    surf1 = font.render(txt1, True, (255, 255, 255))
    bg1 = pygame.Surface(surf1.get_size(), pygame.SRCALPHA)
    bg1.fill((0, 0, 0, 180))
    screen.blit(bg1, (10, 10))
    screen.blit(surf1, (10, 10))
    y2 = 10 + surf1.get_height() + 5
    surf2 = font.render(txt2, True, (255, 255, 0))
    bg2 = pygame.Surface(surf2.get_size(), pygame.SRCALPHA)
    bg2.fill((0, 0, 0, 180))
    screen.blit(bg2, (10, y2))
    screen.blit(surf2, (10, y2))


def draw_buttons(highlight=None):
    # Reset button
    color = (70, 70, 70) if highlight == "reset" else (30, 30, 30)
    pygame.draw.rect(screen, color, RESET_BUTTON)
    txt = font.render("Reset", True, (200, 200, 200))
    tx = RESET_BUTTON.x + (BTN_WIDTH - txt.get_width()) // 2
    ty = RESET_BUTTON.y + (BTN_HEIGHT - txt.get_height()) // 2
    screen.blit(txt, (tx, ty))
    # SuperRes button
    color = (70, 70, 70) if highlight == "super" else (30, 30, 30)
    pygame.draw.rect(screen, color, SUPER_BUTTON)
    txt2 = font.render("SuperRes", True, (200, 200, 200))
    tx2 = SUPER_BUTTON.x + (BTN_WIDTH - txt2.get_width()) // 2
    ty2 = SUPER_BUTTON.y + (BTN_HEIGHT - txt2.get_height()) // 2
    screen.blit(txt2, (tx2, ty2))


def map_click_to_bounds(x, y, bounds):
    xmin, xmax, ymin, ymax = bounds
    cx = xmin + x / WINDOW_SIZE * (xmax - xmin)
    cy = ymin + y / WINDOW_SIZE * (ymax - ymin)
    half_w = (xmax - xmin) / (2 * ZOOM_FACTOR)
    half_h = (ymax - ymin) / (2 * ZOOM_FACTOR)
    return (cx - half_w, cx + half_w, cy - half_h, cy + half_h)


def animate_zoom(old_surf, click_x, click_y, bounds):
    # animate both recenter and zoom
    old_cx = WINDOW_SIZE / 2
    old_cy = WINDOW_SIZE / 2
    for frame in range(1, ANIM_FRAMES + 1):
        t = frame / ANIM_FRAMES
        # interpolate center
        cx_pix = old_cx + (click_x - old_cx) * t
        cy_pix = old_cy + (click_y - old_cy) * t
        # interpolate scale
        scale = 1 + (ZOOM_FACTOR - 1) * t
        region_size = max(2, int(WINDOW_SIZE / scale))
        rx = max(0, min(WINDOW_SIZE - region_size, int(cx_pix - region_size // 2)))
        ry = max(0, min(WINDOW_SIZE - region_size, int(cy_pix - region_size // 2)))
        region = old_surf.subsurface((rx, ry, region_size, region_size))
        zoom_surf = pygame.transform.smoothscale(region, (WINDOW_SIZE, WINDOW_SIZE))
        screen.blit(zoom_surf, (0, 0))
        draw_center_and_res(bounds, current_res, current_iter)
        draw_buttons()
        pygame.display.flip()
        clock.tick(30)


def main():
    global current_bounds, current_res, current_iter
    current_bounds = (X_MIN0, X_MAX0, Y_MIN0, Y_MAX0)
    current_res = RENDER_RES_HI
    current_iter = MAX_ITER_HI

    # initial draw
    draw_fractal(current_res, current_bounds, current_iter)
    draw_center_and_res(current_bounds, current_res, current_iter)
    draw_buttons()
    pygame.display.flip()

    running = True
    while running:
        for evt in pygame.event.get():
            if evt.type == pygame.QUIT:
                running = False
            elif evt.type == pygame.MOUSEBUTTONDOWN:
                x, y = evt.pos
                if RESET_BUTTON.collidepoint(evt.pos):
                    draw_buttons(highlight="reset")
                    pygame.display.flip()
                    pygame.time.delay(100)
                    current_bounds = (X_MIN0, X_MAX0, Y_MIN0, Y_MAX0)
                    current_res = RENDER_RES_HI
                    current_iter = MAX_ITER_HI
                    draw_fractal(current_res, current_bounds, current_iter)
                    draw_center_and_res(current_bounds, current_res, current_iter)
                    draw_buttons()
                    pygame.display.flip()
                elif SUPER_BUTTON.collidepoint(evt.pos):
                    draw_buttons(highlight="super")
                    pygame.display.flip()
                    pygame.time.delay(100)
                    super_res = int(RENDER_RES_HI * SUPER_RES_MULT)
                    super_iter = int(MAX_ITER_HI * SUPER_ITER_MULT)
                    draw_fractal(super_res, current_bounds, super_iter)
                    # revert to defaults
                    current_res = RENDER_RES_HI
                    current_iter = MAX_ITER_HI
                    draw_center_and_res(current_bounds, super_res, super_iter)
                    draw_buttons()
                    pygame.display.flip()
                else:
                    old_surf = screen.copy()
                    new_bounds = map_click_to_bounds(x, y, current_bounds)
                    animate_zoom(old_surf, x, y, current_bounds)
                    current_bounds = new_bounds
                    current_res = RENDER_RES_HI
                    current_iter = MAX_ITER_HI
                    draw_fractal(current_res, current_bounds, current_iter)
                    draw_center_and_res(current_bounds, current_res, current_iter)
                    draw_buttons()
                    pygame.display.flip()
        clock.tick(60)

    pygame.quit()


if __name__ == "__main__":
    main()
