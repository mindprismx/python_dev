# sierpinski chaos game in pygame
# @spiralbend 21 July 2025

import random
import math
import os
import sys

sys.stdout = open(os.devnull, "w")
import pygame

sys.stdout = sys.__stdout__

# Setup
WIDTH, HEIGHT = 1600, 1600
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DOT_COLOR = (0, 255, 0)

pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Sierpiński Chaos Game")
clock = pygame.time.Clock()

# Equilateral triangle centered
rt3 = math.sqrt(3)
triangle = [
    (WIDTH // 2, HEIGHT // 2 - 600),  # top
    (WIDTH // 2 + int(rt3 * 300), HEIGHT // 2 + 300),  # bottom right
    (WIDTH // 2 - int(rt3 * 300), HEIGHT // 2 + 300),  # bottom left
]

cur_pt = random.choice(triangle)
ratio = 0.5

# Draw initial triangle
screen.fill(BLACK)
for pt in triangle:
    pygame.draw.circle(screen, WHITE, pt, 3)

# Main loop
running = True
while running:
    for _ in range(300):  # draw N points per frame
        target = random.choice(triangle)
        cur_pt = (
            int((cur_pt[0] + target[0]) * ratio),
            int((cur_pt[1] + target[1]) * ratio),
        )
        screen.set_at(cur_pt, DOT_COLOR)

    pygame.display.flip()
    clock.tick(60)  # Limit to 60 FPS

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

pygame.quit()
