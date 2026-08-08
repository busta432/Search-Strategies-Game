import random

import pytest

from search import (
    ALGORITHMS,
    BFS,
    UniformCostSearch,
    DepthLimitedSearch,
    IterativeDeepening,
    AStar,
    generate_maze,
    add_loops,
)

ALL_STRATEGIES = [cls for _, cls in ALGORITHMS]
# Guaranteed to return a shortest path on this uniform-step-cost grid.
OPTIMAL_STRATEGIES = [BFS, UniformCostSearch, IterativeDeepening, AStar]


def make_loop_maze():
    # 5x5 hand-built maze: a ring around a single wall cell at (2, 2), so
    # there are two equally-short routes from (1,1) to (3,3).
    W, F = True, False
    return [
        [W, W, W, W, W],
        [W, F, F, F, W],
        [W, F, W, F, W],
        [W, F, F, F, W],
        [W, W, W, W, W],
    ]


def make_unreachable_maze():
    W, F = True, False
    maze = [[W] * 5 for _ in range(5)]
    maze[1][1] = F
    maze[1][2] = F
    maze[1][3] = F  # a short open corridor along y=1
    maze[3][3] = F  # goal cell, surrounded by walls on every side
    return maze


def cells_of(maze):
    return [(x, y) for y, row in enumerate(maze) for x, v in enumerate(row) if not v]


def assert_valid_path(maze, start, goal, path):
    """A returned path must be a chain of in-bounds, open, 4-adjacent cells
    that starts adjacent to `start` and ends at `goal`."""
    if start == goal:
        assert path == []
        return
    assert path, "expected a non-empty path"
    assert path[-1] == goal
    prev = start
    for cell in path:
        x, y = cell
        assert 0 <= y < len(maze) and 0 <= x < len(maze[0]), f"{cell} out of bounds"
        assert not maze[y][x], f"path steps through a wall at {cell}"
        assert abs(cell[0] - prev[0]) + abs(cell[1] - prev[1]) == 1, (
            f"non-adjacent step from {prev} to {cell}"
        )
        prev = cell


@pytest.mark.parametrize("strategy_cls", ALL_STRATEGIES, ids=lambda c: c.__name__)
def test_finds_a_valid_path_when_one_exists(strategy_cls):
    maze = make_loop_maze()
    path, explored, max_depth = strategy_cls().search(maze, (1, 1), (3, 3))
    assert_valid_path(maze, (1, 1), (3, 3), path)
    assert (1, 1) in explored
    assert max_depth >= len(path)


@pytest.mark.parametrize("strategy_cls", ALL_STRATEGIES, ids=lambda c: c.__name__)
def test_reports_no_path_when_goal_unreachable(strategy_cls):
    maze = make_unreachable_maze()
    path, explored, _ = strategy_cls().search(maze, (1, 1), (3, 3))
    assert path == []
    assert (3, 3) not in explored


@pytest.mark.parametrize("strategy_cls", ALL_STRATEGIES, ids=lambda c: c.__name__)
def test_trivial_when_start_equals_goal(strategy_cls):
    maze = make_loop_maze()
    path, explored, _ = strategy_cls().search(maze, (1, 1), (1, 1))
    assert path == []
    assert explored == [(1, 1)]


@pytest.mark.parametrize("strategy_cls", OPTIMAL_STRATEGIES, ids=lambda c: c.__name__)
def test_optimal_strategies_find_the_shortest_path(strategy_cls):
    # The true shortest route in make_loop_maze() is 4 steps.
    maze = make_loop_maze()
    path, _, _ = strategy_cls().search(maze, (1, 1), (3, 3))
    assert len(path) == 4


@pytest.mark.parametrize("seed", range(10))
def test_optimal_strategies_agree_with_bfs_on_random_mazes(seed):
    # BFS is the reference: with uniform step cost it always finds a
    # shortest path. UCS/ID/A* must match its path *length* (not necessarily
    # the exact route - multiple shortest routes can exist once loops exist)
    # on every maze.
    random.seed(seed)
    maze = add_loops(generate_maze(21, 21), 21, 21, 0.2)
    cells = [(x, y) for y, row in enumerate(maze) for x, v in enumerate(row) if not v]
    start, goal = random.sample(cells, 2)

    reference_path, _, _ = BFS().search(maze, start, goal)
    for strategy_cls in (UniformCostSearch, IterativeDeepening, AStar):
        path, _, _ = strategy_cls().search(maze, start, goal)
        assert len(path) == len(reference_path), strategy_cls.__name__


def test_depth_limited_search_respects_its_limit():
    maze = make_loop_maze()  # shortest path from (1,1) to (3,3) is 4 steps
    too_shallow, explored, _ = DepthLimitedSearch(limit=2).search(maze, (1, 1), (3, 3))
    assert too_shallow == []
    assert len(explored) < len(cells_of(maze))  # cut off before exploring everything

    deep_enough, _, _ = DepthLimitedSearch(limit=4).search(maze, (1, 1), (3, 3))
    assert len(deep_enough) == 4
