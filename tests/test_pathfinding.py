"""Headless correctness checks for the simplified maze visualizer."""
import copy
import unittest

from algorithms import ALGORITHMS, search, solve
from grid import Grid


class PathfindingTests(unittest.TestCase):
    def assert_valid_path(self, grid, result):
        self.assertTrue(result.done)
        self.assertTrue(result.path)
        self.assertEqual(result.path[0], grid.start)
        self.assertEqual(result.path[-1], grid.end)
        for a, b in zip(result.path, result.path[1:]):
            self.assertIn(b, tuple(grid.neighbors(a)))

    def test_open_grid(self):
        grid = Grid(7, 9, (0, 0), (6, 8))
        for name in ALGORITHMS:
            result = solve(grid, name)
            self.assert_valid_path(grid, result)
            if name != 'DFS':
                self.assertEqual(len(result.path) - 1, 14)

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

    def test_random_mazes(self):
        for seed in range(10):
            grid = Grid()
            grid.maze(seed)
            shortest = solve(grid, 'BFS')
            for name in ALGORITHMS:
                result = solve(grid, name)
                self.assert_valid_path(grid, result)
                if name != 'DFS':
                    self.assertEqual(len(result.path), len(shortest.path))

    def test_maze_endpoints_connected_at_edges(self):
        for rows, cols in ((5, 5), (25, 40), (6, 8), (60, 80)):
            for start, end in (((0, 0), (rows - 1, cols - 1)), ((rows // 2, 0), (0, cols // 2))):
                grid = Grid(rows, cols, start, end)
                grid.maze(seed=8)
                self.assert_valid_path(grid, solve(grid, 'BFS'))

    def test_generators_are_independent_and_do_not_mutate_grid(self):
        grid = Grid()
        grid.maze(seed=42)
        before = copy.deepcopy(grid)
        one, two = search(grid, 'BFS'), search(grid, 'A*')
        self.assertEqual(next(one).expanded, 1)
        self.assertEqual(next(two).expanded, 1)
        self.assertEqual(next(one).expanded, 2)
        self.assertEqual(grid, before)

    def test_new_maze_replaces_previous_walls(self):
        grid = Grid()
        grid.maze(seed=1)
        previous = grid.walls.copy()
        grid.maze(seed=2)
        self.assertNotEqual(previous, grid.walls)
        self.assert_valid_path(grid, solve(grid, 'BFS'))

    def test_unknown_algorithm(self):
        with self.assertRaises(ValueError):
            solve(Grid(), 'unknown')


if __name__ == '__main__':
    unittest.main()
