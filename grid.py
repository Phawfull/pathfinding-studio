"""Grid model and random maze generation, independent of Tkinter."""
import random
from dataclasses import dataclass, field


@dataclass
class Grid:
    rows: int = 25
    cols: int = 40
    start: tuple = (12, 5)
    end: tuple = (12, 34)
    walls: set = field(default_factory=set)

    def inside(self, cell):
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, cell):
        r, c = cell
        for p in ((r - 1, c), (r, c + 1), (r + 1, c), (r, c - 1)):
            if self.inside(p) and p not in self.walls:
                yield p

    def maze(self, seed=None):
        """Depth-first backtracking, using an explicit stack to avoid recursion limits."""
        rng = random.Random(seed)
        self.walls = {(r, c) for r in range(self.rows) for c in range(self.cols)}
        first = (1, 1)
        seen = {first}
        self.walls.remove(first)
        stack = [first]
        while stack:
            r, c = stack[-1]
            options = [(r + dr, c + dc) for dr, dc in ((-2, 0), (0, 2), (2, 0), (0, -2))
                       if 0 < r + dr < self.rows - 1 and 0 < c + dc < self.cols - 1
                       and (r + dr, c + dc) not in seen]
            if not options:
                stack.pop()
                continue
            nxt = rng.choice(options)
            seen.add(nxt)
            self.walls.discard(nxt)
            self.walls.discard(((r + nxt[0]) // 2, (c + nxt[1]) // 2))
            stack.append(nxt)
        # Connect arbitrary endpoints to the odd-coordinate maze lattice.
        for endpoint in (self.start, self.end):
            r, c = endpoint
            target_r = min(max(1, r | 1), (self.rows - 2) if self.rows % 2 else (self.rows - 3))
            target_c = min(max(1, c | 1), (self.cols - 2) if self.cols % 2 else (self.cols - 3))
            self.walls.discard((r, c))
            while r != target_r:
                r += 1 if r < target_r else -1
                self.walls.discard((r, c))
            while c != target_c:
                c += 1 if c < target_c else -1
                self.walls.discard((r, c))
