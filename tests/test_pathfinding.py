import random
import tempfile
import unittest
from collections import deque
from pathlib import Path

from algorithms import ALGORITHMS, search, solve
from grid import Grid


class PathfindingTests(unittest.TestCase):
    def assert_valid_path(self, grid, result):
        self.assertEqual(result.path[0], grid.start)
        self.assertEqual(result.path[-1], grid.end)
        self.assertEqual(result.cost, sum(grid.cost(p) for p in result.path[1:]))
        for a, b in zip(result.path, result.path[1:]):
            self.assertIn(b, tuple(grid.neighbors(a)))

    def test_open_grid(self):
        grid = Grid(7, 9, (0, 0), (6, 8))
        for name in ALGORITHMS:
            result = solve(grid, name)
            self.assert_valid_path(grid, result)
            if name != 'DFS':
                self.assertEqual(len(result.path) - 1, 14)

    def test_weights_change_optimal_route(self):
        grid = Grid(5, 7, (2, 0), (2, 6))
        grid.weights = {(2, c): 5 for c in range(1, 6)}
        bfs = solve(grid, 'BFS')
        self.assertEqual(len(bfs.path) - 1, 6)
        self.assertEqual(bfs.cost, 26)
        for name in ('Dijkstra', 'A*'):
            result = solve(grid, name)
            self.assert_valid_path(grid, result)
            self.assertEqual(result.cost, 8)

    def test_unreachable(self):
        grid = Grid(5, 5, (0, 0), (4, 4))
        grid.walls = {(2, c) for c in range(5)}
        for name in ALGORITHMS:
            result = solve(grid, name)
            self.assertFalse(result.path)
            self.assertTrue(result.done)

    def test_adjacent_endpoints(self):
        for name in ALGORITHMS:
            result = solve(Grid(5, 5, (1, 1), (1, 2)), name)
            self.assertEqual(result.path, ((1, 1), (1, 2)))

    def test_random_weighted_grids_against_independent_relaxation(self):
        # Bellman-Ford style relaxation supplies an independent minimum-cost oracle.
        for seed in range(20):
            rng = random.Random(seed)
            grid = Grid(6, 8, (0, 0), (5, 7))
            for r in range(6):
                for c in range(8):
                    if (r, c) in (grid.start, grid.end):
                        continue
                    if rng.random() < .23:
                        grid.walls.add((r, c))
                    elif rng.random() < .4:
                        grid.weights[r, c] = rng.randint(2, 9)
            distance = {grid.start: 0}
            for _ in range(48):
                changed = False
                for cell, value in list(distance.items()):
                    for nxt in grid.neighbors(cell):
                        candidate = value + grid.cost(nxt)
                        if candidate < distance.get(nxt, float('inf')):
                            distance[nxt] = candidate
                            changed = True
                if not changed:
                    break
            for name in ('Dijkstra', 'A*'):
                result = solve(grid, name)
                self.assertEqual(bool(result.path), grid.end in distance)
                if result.path:
                    self.assert_valid_path(grid, result)
                    self.assertEqual(result.cost, distance[grid.end])

    def test_maze_endpoints_connected_at_edges(self):
        for rows, cols in ((5, 5), (25, 40), (6, 8), (60, 80)):
            for start, end in (((0, 0), (rows - 1, cols - 1)), ((rows // 2, 0), (0, cols // 2))):
                grid = Grid(rows, cols, start, end)
                grid.maze(seed=8)
                self.assert_valid_path(grid, solve(grid, 'BFS'))

    def test_save_load_round_trip(self):
        grid = Grid()
        grid.walls.add((1, 2))
        grid.weights[3, 4] = 5
        with tempfile.TemporaryDirectory() as directory:
            filename = Path(directory) / 'grid.json'
            grid.save(filename)
            self.assertEqual(Grid.load(filename).to_dict(), grid.to_dict())

    def test_invalid_files(self):
        mutations = ({'rows': True}, {'start': [-1, 2]}, {'end': [12, 5]},
                     {'weights': [[1, 1, 0]]}, {'weights': [[1, 1, 1.5]]},
                     {'walls': [[12, 5]]}, {'walls': [[1, 1]], 'weights': [[1, 1, 5]]},
                     {'version': 2}, {'cols': 5000}, {'weights': [None]})
        for mutation in mutations:
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                Grid.from_dict({**Grid().to_dict(), **mutation})

    def test_paint_preserves_endpoints(self):
        grid = Grid()
        grid.paint(grid.start, 'Wall')
        self.assertNotIn(grid.start, grid.walls)
        grid.paint((2, 2), 'Weight')
        grid.paint((2, 2), 'Start')
        self.assertEqual(grid.start, (2, 2))
        self.assertNotIn(grid.start, grid.weights)
        grid.paint(grid.end, 'Start')
        self.assertNotEqual(grid.start, grid.end)

    def test_generators_are_independent_and_do_not_mutate_grid(self):
        grid = Grid()
        before = grid.to_dict()
        one, two = search(grid, 'BFS'), search(grid, 'A*')
        self.assertEqual(next(one).expanded, 1)
        self.assertEqual(next(two).expanded, 1)
        self.assertEqual(next(one).expanded, 2)
        self.assertEqual(grid.to_dict(), before)

    def test_unknown_algorithm(self):
        with self.assertRaises(ValueError):
            solve(Grid(), 'unknown')


if __name__ == '__main__':
    unittest.main()
