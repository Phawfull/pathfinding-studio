# Pathfinding Studio

A simple Tkinter application that generates random mazes and visualizes BFS,
DFS, Dijkstra and A*.

## Run

Double-click **run.bat**, or run:

```powershell
python main.py
```

Requires Python 3.10+ with Tkinter. No pip packages, server or database required.

## Controls

1. Click **Random Maze** to generate a connected maze. A maze also appears at startup.
2. Choose **BFS**, **DFS**, **Dijkstra** or **A*** from the algorithm dropdown.
3. Click **Run** to watch the search at a fixed 20 ms per expansion.

Choose another algorithm to clear the search colors and run it on the same maze.
Changing the algorithm or generating a maze cancels the current animation safely.
Run is disabled while a search is active. The canvas is read-only, and the start
and end positions are fixed. There are no editing tools, Save/Load, speed slider,
Pause, Step or comparison window.

Green = start, red = end, dark = wall, yellow = frontier, blue = expanded,
orange = final route. The statistics show expanded cells, route moves and search
computation time (excluding animation and rendering).

## Algorithms

Movement is horizontal or vertical. Every move costs one.

| Algorithm | Data structure | Behavior |
| --- | --- | --- |
| BFS | FIFO deque | Finds a shortest route |
| DFS | LIFO deque | Finds a route; shortest route is not guaranteed |
| Dijkstra | Priority queue ordered by distance | Finds a shortest route |
| A* | Priority queue ordered by distance + Manhattan estimate | Finds a shortest route |

On an unweighted maze, BFS, Dijkstra and A* agree on shortest route length.
The number and order of explored cells can differ. A generated maze can also
have only one route between the endpoints, so DFS may find that same route.

## Files

| File | Purpose |
| --- | --- |
| main.py | Starts the app |
| gui.py | Window, minimal controls and fixed-rate animation |
| grid.py | Grid neighbors and randomized depth-first maze generation |
| algorithms.py | Search generators and result events |
| PROJECT_GUIDE.md | Explanation of the implementation |
| tests/test_pathfinding.py | Algorithm and maze correctness |
| tests/gui_smoke.py | Desktop UI verification |

## Verification

```powershell
python -m unittest discover -v
python -m tests.gui_smoke
```

The second command briefly opens the application to verify its real controls,
read-only canvas, animation, algorithm switching, regeneration and resizing.
