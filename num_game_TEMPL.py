import pygame
import numpy as np
import sys

H = 200
W = 300
scale = 8
fps = 30


def main(width=64, height=48, scale=8, fps=60):

    pygame.init()
    screen = pygame.display.set_mode((width * scale, height * scale))
    pygame.display.set_caption("CGOL")
    clock = pygame.time.Clock()

    P = np.random.randint(0, 2, size=(height, width))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # pixels = np.random.randint(0, 2, size=(height, width))

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
