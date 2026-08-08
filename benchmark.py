#!/usr/bin/env python3
"""Benchmark every search strategy across many random mazes.

For each trial, generates a fresh maze, picks a random reachable start/goal
pair, and runs every algorithm in search.ALGORITHMS against it, recording
nodes explored, solution path length, and wall-clock time. Writes the raw
per-trial results to a CSV and a summary chart to a PNG.

Usage:
    python3 benchmark.py
    python3 benchmark.py --trials 50 --cols 61 --rows 61 --loop-chance 0.2
"""

import argparse
import csv
import random
import statistics
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg") # headless - just write files, don't try to open a window
import matplotlib.pyplot as plt

from search import ALGORITHMS, generate_maze, add_loops


def run_trial(maze, start, goal, strategy_cls):
    strategy = strategy_cls()
    t0 = time.perf_counter()
    path, explored, max_depth = strategy.search(maze, start, goal)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return {
        "found": bool(path),
        "path_length": len(path),
        "nodes_explored": len(explored),
        "max_depth": max_depth,
        "time_ms": elapsed_ms,
    }


def collect_results(trials, cols, rows, loop_chance):
    rows_out = []
    for trial in range(trials):
        maze = generate_maze(cols, rows)
        maze = add_loops(maze, cols, rows, loop_chance)
        open_cells = [(x, y) for y, row in enumerate(maze) for x, v in enumerate(row) if not v]
        start, goal = random.sample(open_cells, 2)

        for name, strategy_cls in ALGORITHMS:
            result = run_trial(maze, start, goal, strategy_cls)
            result["trial"] = trial
            result["algorithm"] = name
            rows_out.append(result)
    return rows_out


def summarize(rows_out):
    by_algo = {}
    for row in rows_out:
        by_algo.setdefault(row["algorithm"], []).append(row)

    summary = {}
    for name, results in by_algo.items():
        found = [r for r in results if r["found"]]
        summary[name] = {
            "trials": len(results),
            "success_rate": len(found) / len(results) if results else 0.0,
            "avg_explored": statistics.mean(r["nodes_explored"] for r in results),
            "avg_path_length": statistics.mean(r["path_length"] for r in found) if found else float("nan"),
            "avg_time_ms": statistics.mean(r["time_ms"] for r in results),
        }
    return summary


def write_csv(rows_out, path):
    fieldnames = ["trial", "algorithm", "found", "path_length", "nodes_explored", "max_depth", "time_ms"]
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows_out)


def print_summary(summary, args):
    order = [name for name, _ in ALGORITHMS]
    print(f"\nBenchmark: {args.trials} mazes, {args.cols}x{args.rows}, loop_chance={args.loop_chance}")
    print("-" * 78)
    print(f"{'Algorithm':<10} {'Success':>8} {'AvgExplored':>12} {'AvgPathLen':>11} {'AvgTime(ms)':>12}")
    print("-" * 78)
    for name in order:
        s = summary[name]
        print(
            f"{name:<10} {s['success_rate'] * 100:>7.0f}% {s['avg_explored']:>12.1f} "
            f"{s['avg_path_length']:>11.1f} {s['avg_time_ms']:>12.3f}"
        )


def plot_summary(summary, path, args):
    order = [name for name, _ in ALGORITHMS]
    explored = [summary[n]["avg_explored"] for n in order]
    path_len = [summary[n]["avg_path_length"] for n in order]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.5))
    fig.suptitle(
        f"Search strategy comparison - {args.trials} random {args.cols}x{args.rows} "
        f"mazes (loop_chance={args.loop_chance})"
    )

    bars1 = ax1.bar(order, explored, color="#4C72B0")
    ax1.set_title("Avg nodes explored (lower = less search overhead)")
    ax1.set_ylabel("nodes (log scale)")
    ax1.set_yscale("log")
    ax1.tick_params(axis="x", rotation=30)
    ax1.bar_label(bars1, fmt="%.0f", fontsize=8, padding=2)

    bars2 = ax2.bar(order, path_len, color="#DD8452")
    ax2.set_title("Avg solution path length (lower = shorter route found)")
    ax2.set_ylabel("cells")
    ax2.tick_params(axis="x", rotation=30)
    ax2.bar_label(bars2, fmt="%.1f", fontsize=8, padding=2)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=30, help="number of random mazes to test (default: 30)")
    parser.add_argument("--cols", type=int, default=41, help="maze width (default: 41)")
    parser.add_argument("--rows", type=int, default=41, help="maze height (default: 41)")
    parser.add_argument("--loop-chance", type=float, default=0.15, help="fraction of extra walls knocked down (default: 0.15)")
    parser.add_argument("--seed", type=int, default=None, help="random seed, for reproducible results")
    parser.add_argument("--out-dir", default="results", help="where to write benchmark.csv / benchmark.png")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(exist_ok=True)

    rows_out = collect_results(args.trials, args.cols, args.rows, args.loop_chance)
    summary = summarize(rows_out)

    csv_path = out_dir / "benchmark.csv"
    png_path = out_dir / "benchmark.png"
    write_csv(rows_out, csv_path)
    plot_summary(summary, png_path, args)

    print_summary(summary, args)
    print(f"\nRaw results: {csv_path}")
    print(f"Chart:       {png_path}")


if __name__ == "__main__":
    main()
