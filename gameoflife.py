import pygame
import numpy as np
import sys
#
W, H = 600, 400  # width, height in cells
SCALE = 4  # pixel size per cell
FPS = 60


def step(P: np.ndarray) -> np.ndarray:
    # Vectorized neighbor count with wraps (toroidal)
    N = (
        np.roll(P, 1, 0)
        + np.roll(P, -1, 0)
        + np.roll(P, 1, 1)
        + np.roll(P, -1, 1)
        + np.roll(np.roll(P, 1, 0), 1, 1)
        + np.roll(np.roll(P, 1, 0), -1, 1)
        + np.roll(np.roll(P, -1, 0), 1, 1)
        + np.roll(np.roll(P, -1, 0), -1, 1)
    )
    # Life rule: births (N==3) or survive (alive & N==2)
    return ((N == 3) | ((P == 1) & (N == 2))).astype(np.uint8)


def main(width=W, height=H, scale=SCALE, fps=FPS):
    pygame.init()
    screen = pygame.display.set_mode((width * scale, height * scale))
    pygame.display.set_caption("CGOL")
    clock = pygame.time.Clock()

    # world as uint8 0/1
    # P = np.random.randint(0, 2, size=(height, width), dtype=np.uint8)
    P = np.ones((height, width), dtype=np.uint8)
    # y, x = np.mgrid[0:H, 0:W]
    # P[:] = ((np.sin(x / 7.3) + np.sin(y / 9.7) + np.sin((x + y) / 15.1)) > 1.0).astype(
    #     np.uint8
    # )

    # stamp(P, ascii_to_array(Pulsar), H // 2, W // 2)
    # stamp(P, ascii_to_array(Gun), 5, 5)
    # stamp(P, Toad, 20, 20)

    # a 1:1 pixel surface we’ll scale up once per frame
    surf = pygame.Surface((width, height))

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        P = step(P)

        # Write directly into the surface’s pixel buffer (width, height, 3)
        arr = pygame.surfarray.pixels3d(surf)
        bw = (P.T * 255).astype(np.uint8)  # P is (h,w); surfarray is (w,h)
        arr[..., 0] = bw
        arr[..., 1] = bw
        arr[..., 2] = bw
        del arr  # important: release the view before blitting

        if scale != 1:
            frame = pygame.transform.scale(surf, (width * scale, height * scale))
        else:
            frame = surf

        screen.blit(frame, (0, 0))
        pygame.display.flip()
        clock.tick(fps)

    pygame.quit()
    sys.exit()


def stamp(P, pat, y=0, x=0):
    h, w = pat.shape
    P[y : y + h, x : x + w] = pat


def ascii_to_array(lines):
    # '.' dead, 'O' live
    w = max(len(s) for s in lines)
    A = np.zeros((len(lines), w), np.uint8)
    for y, s in enumerate(lines):
        for x, ch in enumerate(s):
            if ch == "O":
                A[y, x] = 1
    return A


R = np.array([[0, 1, 1], [1, 1, 0], [0, 1, 0]], np.uint8)

Ac = np.array(
    [[0, 1, 0, 0, 0, 0, 0], [0, 0, 0, 1, 0, 0, 0], [1, 1, 0, 0, 1, 1, 1]], np.uint8
)

Dh = np.array(
    [[0, 0, 0, 0, 0, 0, 1], [1, 1, 0, 0, 0, 0, 0], [0, 1, 0, 0, 0, 1, 1]], np.uint8
)

LWSS = np.array(
    [[0, 1, 0, 0, 1], [1, 0, 0, 0, 0], [1, 0, 0, 0, 1], [1, 1, 1, 1, 0]], np.uint8
)

Puf = np.array(
    [[0, 1, 1, 0, 0, 0], [1, 0, 0, 1, 0, 0], [0, 0, 0, 0, 1, 1], [1, 1, 0, 0, 0, 0]],
    np.uint8,
)

Toad = np.array([[0, 1, 1, 1], [1, 1, 1, 0]], np.uint8)

Pulsar = np.array(
    [
        "..OOO...OOO..",
        ".............",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        "..OOO...OOO..",
        ".............",
        "..OOO...OOO..",
        "O....O.O....O",
        "O....O.O....O",
        "O....O.O....O",
        ".............",
        "..OOO...OOO..",
    ],
    dtype=object,
)

Gun = np.array(
    [
        "........................O...........",
        "......................O.O...........",
        "............OO......OO............OO",
        "...........O...O....OO............OO",
        "OO........O.....O...OO...............",
        "OO........O...O.OO....O.O............",
        "..........O.....O.......O............",
        "...........O...O.....................",
        "............OO.......................",
    ],
    dtype=object,
)

if __name__ == "__main__":
    main()
