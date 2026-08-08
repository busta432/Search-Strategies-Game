#!/usr/bin/env python3
"""Renders a static side-by-side preview PNG (Greedy vs A*) for the README.

Runs headless (SDL dummy video driver) so it works without a display -
useful for regenerating docs/preview.png after visual changes.
"""

import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import random
import pygame

from search import generate_maze, add_loops, BestFirst, AStar

SEED = int(os.environ.get("PREVIEW_SEED", 6))
random.seed(SEED)

COLS, ROWS, BLOCK, GAP = 41, 41, 10, 40
PANEL_W, PANEL_H = COLS * BLOCK, ROWS * BLOCK
TITLE_H = 34

pygame.init()
surface = pygame.Surface((PANEL_W * 2 + GAP, PANEL_H + TITLE_H))
surface.fill("purple")

maze = add_loops(generate_maze(COLS, ROWS), COLS, ROWS, 0.15)
open_cells = [(x, y) for y, row in enumerate(maze) for x, v in enumerate(row) if not v]
start, goal = random.sample(open_cells, 2)


def draw_maze(surf, offset_x, offset_y):
    for y, row in enumerate(maze):
        for x, is_wall in enumerate(row):
            if is_wall:
                rect = pygame.Rect(offset_x + x * BLOCK, offset_y + y * BLOCK, BLOCK, BLOCK)
                pygame.draw.rect(surf, "brown", rect)
                pygame.draw.rect(surf, "black", rect, 1)


def draw_path(surf, offset_x, offset_y, path, color):
    def center(cell):
        cx, cy = cell
        return (offset_x + cx * BLOCK + BLOCK // 2, offset_y + cy * BLOCK + BLOCK // 2)

    points = [center(start)] + [center(c) for c in path]
    pygame.draw.lines(surf, color, False, points, 3)


font = pygame.font.SysFont(None, 24)
panels = [
    ("Greedy", BestFirst(), (255, 215, 0), 0), # yellow
    ("A*", AStar(), (40, 110, 255), PANEL_W + GAP), # blue
]

for label_name, strategy, color, offset_x in panels:
    offset_y = TITLE_H
    path, explored, _ = strategy.search(maze, start, goal)
    draw_maze(surface, offset_x, offset_y)

    path_color = tuple(255 - c for c in color) # same inverted-colour scheme as the game
    draw_path(surface, offset_x, offset_y, path, path_color)

    goal_rect = pygame.Rect(offset_x + goal[0] * BLOCK, offset_y + goal[1] * BLOCK, BLOCK, BLOCK)
    pygame.draw.rect(surface, "red", goal_rect)
    start_rect = pygame.Rect(offset_x + start[0] * BLOCK, offset_y + start[1] * BLOCK, BLOCK, BLOCK)
    pygame.draw.rect(surface, color, start_rect)

    label = font.render(f"{label_name}  -  explored {len(explored)}, path {len(path)}", True, "white")
    surface.blit(label, (offset_x, 6))

out_path = os.path.join(os.path.dirname(__file__), "docs", "preview.png")
pygame.image.save(surface, out_path)
print(f"wrote {out_path}")
