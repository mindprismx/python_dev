import pygame
import numpy as np
import sys

H = 200
W = 300
scale = 8
fps = 30


def main(width=64, height=48, scale=8, fps=60):
    # global P
    pygame.init()
    screen = pygame.display.set_mode((width * scale, height * scale))
    pygame.display.set_caption("CGOL")
    clock = pygame.time.Clock()

    P = np.random.randint(0, 2, size=(height, width), dtype=np.uint8)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        Q = np.zeros_like(P, dtype=np.uint8)
        Q += np.roll(P, 1, axis=0)
        Q += np.roll(P, -1, axis=0)
        Q += np.roll(P, 1, axis=1)
        Q += np.roll(P, -1, axis=1)
        Q += np.roll(P, (1, 1), axis=(0, 1))
        Q += np.roll(P, (1, -1), axis=(0, 1))
        Q += np.roll(P, (-1, 1), axis=(0, 1))
        Q += np.roll(P, (-1, -1), axis=(0, 1))

        P[Q < 2] = 0
        P[Q > 3] = 0
        P[Q == 3] = 1

        for y in range(height):
            for x in range(width):
                val = P[y, x] * 255
                color = (val, val, val)
                rect = pygame.Rect(x * scale, y * scale, scale, scale)
                screen.fill(color, rect)

        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main(W, H, scale, fps)
