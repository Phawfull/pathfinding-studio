# Pathfinding Studio

A standalone Tkinter desktop project for visualizing BFS, DFS, Dijkstra and A*.

## Run on Windows

Double-click **run.bat** in this folder, or open a terminal here and run:

```powershell
python main.py
```

Requires Python **3.10 or newer** with Tkinter. No pip installation, server or database is needed.
If Tkinter is missing, modify the Python installation and enable Tcl/Tk support.

## Features and controls

| Action | Control |
| --- | --- |
| Paint obstacles | Wall tool, left-click and drag |
| Paint costly terrain | Weight tool, or hold W while drawing; entry cost 5 |
| Remove walls/weights | Erase tool, or right-click and drag |
| Move start | Start tool, or Shift-click |
| Move destination | End tool, or Ctrl-click |
| Animate search / resume | Run / Resume |
| Freeze animation | Pause |
| Expand one node | Step |
| Stop and remove search colors | Clear Path |
| Remove walls and weights | Clear All; keeps endpoints |
| Generate connected labyrinth | Random Maze |
| Compare four searches | Compare All |
| Save / load layout | Save / Load JSON |

The algorithm selector locks during an active search. Editing also locks while
running, paused or comparing: press Clear Path to cancel first. Clear All,
Random Maze and a successful Load cancel any active search. Saving is safe during
a search because only the underlying layout is saved.

Green = start, red = end, dark = wall, purple = weighted terrain, yellow = frontier,
blue = visited, orange = final route. Weighted cells retain their numeric labels.

## Algorithms

All moves are horizontal or vertical; diagonal movement is not allowed.
Entering an ordinary cell costs 1. Weighted terrain costs 5 when painted; imported
JSON can specify positive integer costs up to 99. The starting cell costs nothing.

| Algorithm | Structure | Weight handling | Guarantee |
| --- | --- | --- | --- |
| BFS | deque / FIFO | Ignores weights while searching | Fewest moves |
| DFS | deque / LIFO | Ignores weights while searching | Reachability, not optimality |
| Dijkstra | heapq priority queue | Uses entry cost | Minimum total cost |
| A* | heapq; g + Manhattan heuristic | Uses entry cost | Minimum total cost |

BFS/DFS still report the actual cost of the route they find. Their reported cost
can therefore exceed Dijkstra/A* even when their route uses fewer moves.
Manhattan distance is admissible and consistent here because all entry costs are
at least 1. Tie-breaking and neighbor order affect the exact path explored.

Stats: Expanded counts popped/processed nodes including the destination; Moves
counts edges in the final route; Cost sums entry costs excluding the starting cell;
Compute measures generator work only, excluding UI rendering and animation delay.
Comparison uses the same grid for each algorithm and runs in small event-loop batches.
Microsecond-scale timings vary and should not be treated as a reliable benchmark.

## Files

| File | Responsibility |
| --- | --- |
| main.py | Entry point |
| gui.py | Tkinter window, controls, canvas, animation and comparison |
| grid.py | Grid model, terrain, neighbors, maze generation, validated JSON |
| algorithms.py | Search generators, immutable events, headless solver |
| tests/test_pathfinding.py | Correctness and persistence tests |
| PROJECT_GUIDE.md | APP mapping, workflow, demo and viva notes |
| run.bat | Windows launcher |
| examples/weighted_demo.json | Ready-made comparison scenario |

## Verification

```powershell
python -m unittest discover -v
```

Tests cover open and blocked grids, weighted optimality against an independent
relaxation algorithm, maze connectivity, file validation, generator independence
and save/load round trips. GUI interaction is verified separately.

## Useful demo

Load examples/weighted_demo.json, run BFS, then Compare All. BFS takes the direct,
expensive route; Dijkstra and A* take a longer route with lower cost. Generate a
maze, run A*, pause it, step twice and resume. Save the maze, clear everything and
load it again to demonstrate persistence.
