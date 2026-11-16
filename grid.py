"""UI-independent grid model, maze generation and validated JSON storage."""
import json
import random
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Grid:
    rows: int = 25
    cols: int = 40
    start: tuple = (12, 5)
    end: tuple = (12, 34)
    walls: set = field(default_factory=set)
    weights: dict = field(default_factory=dict)

    def inside(self, cell):
        r, c = cell
        return 0 <= r < self.rows and 0 <= c < self.cols

    def neighbors(self, cell):
        r, c = cell
        for p in ((r - 1, c), (r, c + 1), (r + 1, c), (r, c - 1)):
            if self.inside(p) and p not in self.walls:
                yield p

    def cost(self, cell):
        return self.weights.get(cell, 1)

    def paint(self, cell, tool):
        if not self.inside(cell):
            return
        if tool in ('Start', 'End'):
            other = self.end if tool == 'Start' else self.start
            if cell == other:
                return
            setattr(self, tool.lower(), cell)
        elif cell in (self.start, self.end):
            return
        self.walls.discard(cell)
        self.weights.pop(cell, None)
        if tool == 'Wall':
            self.walls.add(cell)
        elif tool == 'Weight':
            self.weights[cell] = 5

    def clear(self):
        self.walls.clear()
        self.weights.clear()

    def maze(self, seed=None):
        """Depth-first backtracking, using an explicit stack to avoid recursion limits."""
        rng = random.Random(seed)
        self.weights.clear()
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

    def to_dict(self):
        return dict(version=1, rows=self.rows, cols=self.cols, start=list(self.start),
                    end=list(self.end), walls=sorted(self.walls),
                    weights=[[r, c, w] for (r, c), w in sorted(self.weights.items())])

    def save(self, filename):
        Path(filename).write_text(json.dumps(self.to_dict(), indent=2), encoding='utf-8')

    @classmethod
    def load(cls, filename):
        path = Path(filename)
        if path.stat().st_size > 2_000_000:
            raise ValueError('Grid file is too large (maximum 2 MB).')
        return cls.from_dict(json.loads(path.read_text(encoding='utf-8')))

    @classmethod
    def from_dict(cls, data):
        if not isinstance(data, dict) or data.get('version') != 1:
            raise ValueError('Expected a version 1 grid object.')
        rows, cols = data.get('rows'), data.get('cols')
        if type(rows) is not int or type(cols) is not int or not (5 <= rows <= 60 and 5 <= cols <= 80):
            raise ValueError('Grid dimensions must be integers: 5–60 rows, 5–80 columns.')

        def position(value):
            if (not isinstance(value, (list, tuple)) or len(value) != 2
                    or any(type(x) is not int for x in value)
                    or not (0 <= value[0] < rows and 0 <= value[1] < cols)):
                raise ValueError('Invalid or out-of-bounds cell position.')
            return tuple(value)

        start, end = position(data.get('start')), position(data.get('end'))
        if start == end:
            raise ValueError('Start and end must be different.')
        if not isinstance(data.get('walls', []), list) or not isinstance(data.get('weights', []), list):
            raise ValueError('Walls and weights must be lists.')
        walls = {position(p) for p in data.get('walls', [])}
        weights = {}
        for entry in data.get('weights', []):
            if not isinstance(entry, (list, tuple)) or len(entry) != 3:
                raise ValueError('Each weight must contain row, column, cost.')
            cell, cost = position(entry[:2]), entry[2]
            if type(cost) is not int or not 1 <= cost <= 99:
                raise ValueError('Cell costs must be integers from 1 to 99.')
            weights[cell] = cost
        if start in walls or end in walls or walls.intersection(weights):
            raise ValueError('Walls cannot overlap endpoints or weighted cells.')
        return cls(rows, cols, start, end, walls, weights)
