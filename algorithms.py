"""Search generators yield one expansion at a time, with no Tkinter dependency."""
from collections import deque
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import count
from time import perf_counter

ALGORITHMS = ('BFS', 'DFS', 'Dijkstra', 'A*')
DESCRIPTIONS = {
    'BFS': 'FIFO queue. Finds a shortest route.',
    'DFS': 'LIFO stack. Finds a route, but does not guarantee a shortest route.',
    'Dijkstra': 'Priority queue by distance so far. Finds a shortest route.',
    'A*': 'Priority queue by distance + Manhattan distance. Finds a shortest route.',
}


@dataclass(frozen=True)
class SearchEvent:
    current: tuple | None
    added: tuple = ()
    path: tuple = ()
    expanded: int = 0
    elapsed_ms: float = 0
    done: bool = False


def search(grid, algorithm):
    """The caller must not mutate the grid while consuming this generator."""
    if algorithm not in ALGORITHMS:
        raise ValueError('Unknown algorithm: ' + str(algorithm))
    priority_search = algorithm in ('Dijkstra', 'A*')
    parents = {grid.start: None}
    distances = {grid.start: 0}
    closed = set()
    queue = deque([grid.start])
    serial = count()
    heap = [(0, next(serial), 0, grid.start)]
    elapsed = 0.0
    expanded = 0

    def heuristic(p):
        return abs(p[0] - grid.end[0]) + abs(p[1] - grid.end[1]) if algorithm == 'A*' else 0

    while heap if priority_search else queue:
        tick = perf_counter()
        if priority_search:
            _, _, distance, cell = heappop(heap)
            if cell in closed or distance != distances[cell]:
                elapsed += perf_counter() - tick
                continue
        else:
            cell = queue.pop() if algorithm == 'DFS' else queue.popleft()
        closed.add(cell)
        expanded += 1
        if cell == grid.end:
            path = []
            cursor = cell
            while cursor is not None:
                path.append(cursor)
                cursor = parents[cursor]
            path.reverse()
            elapsed += perf_counter() - tick
            yield SearchEvent(cell, path=tuple(path), expanded=expanded,
                              elapsed_ms=elapsed * 1000, done=True)
            return
        added = []
        for neighbor in grid.neighbors(cell):
            if neighbor in closed:
                continue
            candidate = distances[cell] + 1
            if neighbor not in distances or (priority_search and candidate < distances[neighbor]):
                parents[neighbor] = cell
                distances[neighbor] = candidate
                added.append(neighbor)
                if priority_search:
                    heappush(heap, (candidate + heuristic(neighbor), next(serial), candidate, neighbor))
                else:
                    queue.append(neighbor)
        elapsed += perf_counter() - tick
        yield SearchEvent(cell, tuple(added), expanded=expanded, elapsed_ms=elapsed * 1000)
    yield SearchEvent(None, expanded=expanded, elapsed_ms=elapsed * 1000, done=True)


def solve(grid, algorithm):
    """Consume a search without animation and return its final result."""
    result = None
    for result in search(grid, algorithm):
        pass
    return result
