import random
from collections import deque

from search import generate_maze, add_loops


def open_cells(maze):
    return {(x, y) for y, row in enumerate(maze) for x, v in enumerate(row) if not v}


def bfs_reachable(maze, start):
    rows, cols = len(maze), len(maze[0])
    seen = {start}
    frontier = deque([start])
    while frontier:
        x, y = frontier.popleft()
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows and not maze[ny][nx] and (nx, ny) not in seen:
                seen.add((nx, ny))
                frontier.append((nx, ny))
    return seen


def test_generate_maze_dimensions():
    maze = generate_maze(21, 15)
    assert len(maze) == 15
    assert all(len(row) == 21 for row in maze)


def test_generate_maze_border_is_solid():
    # The DFS carve only ever touches interior cells (1..cols-2, 1..rows-2),
    # so the outer ring should always stay a wall.
    maze = generate_maze(21, 15)
    assert all(maze[0][x] for x in range(21))
    assert all(maze[14][x] for x in range(21))
    assert all(maze[y][0] for y in range(15))
    assert all(maze[y][20] for y in range(15))


def test_generate_maze_is_fully_connected():
    # A perfect maze is a spanning tree - every open cell must be reachable
    # from any other.
    random.seed(0)
    maze = generate_maze(31, 31)
    cells = open_cells(maze)
    reachable = bfs_reachable(maze, next(iter(cells)))
    assert reachable == cells


def test_add_loops_never_reseals_a_wall():
    random.seed(1)
    maze = generate_maze(31, 31)
    before = open_cells(maze)
    looped = add_loops([row[:] for row in maze], 31, 31, 0.3)
    after = open_cells(looped)
    assert before <= after


def test_add_loops_actually_opens_new_walls():
    random.seed(2)
    maze = generate_maze(31, 31)
    before = open_cells(maze)
    looped = add_loops([row[:] for row in maze], 31, 31, 0.5)
    after = open_cells(looped)
    assert len(after) > len(before)


def test_add_loops_stays_fully_connected():
    # Only removing walls (never adding them) can't disconnect a maze that
    # was already fully connected.
    random.seed(3)
    maze = add_loops(generate_maze(31, 31), 31, 31, 0.3)
    cells = open_cells(maze)
    reachable = bfs_reachable(maze, next(iter(cells)))
    assert reachable == cells


def test_add_loops_zero_chance_is_a_no_op():
    random.seed(4)
    maze = generate_maze(21, 21)
    before = [row[:] for row in maze]
    add_loops(maze, 21, 21, 0.0)
    assert maze == before
