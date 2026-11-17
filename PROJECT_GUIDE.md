# APP project explanation

## Objective and workflow

Show how four graph-search algorithms explore a randomly generated maze.
The only controls are Random Maze, the algorithm dropdown and Run.

1. main.py creates App and starts Tkinter's mainloop.
2. Grid.maze() generates a connected random maze using depth-first backtracking.
3. The user selects an algorithm and presses Run.
4. search() yields one SearchEvent for each expanded cell.
5. The GUI colors discovered and expanded cells, then schedules the next update
   with after(20, ...). There is no adjustable speed.
6. At the destination, parent links reconstruct the route and it turns orange.
7. The user can choose another algorithm on the same maze or generate a new one.

The canvas is read-only. Start and destination stay fixed. Grid editing,
weights, JSON storage, speed adjustment and extra search controls are removed.

## APP concepts present

| Concept | Implementation |
| --- | --- |
| Classes and objects | Grid stores the maze; App displays it |
| Inheritance | App inherits tkinter.Tk |
| Dataclasses | Grid and the immutable SearchEvent |
| Event-driven programming | Button commands, selection event and Tk event loop |
| Generators | search yields an event and preserves its local search state |
| Callbacks and lambdas | Buttons and canvas resize handling |
| Data structures | Sets, dictionaries, deque, heapq and an explicit stack |
| Modular design | Model, search engine and GUI in separate files |
| Testing | unittest checks routes and maze connectivity |

## How each algorithm works

- BFS removes cells from the left of a deque, exploring distance layers.
- DFS removes cells from the right, exploring a branch before alternatives.
- Dijkstra removes the smallest accumulated distance from a heap.
- A* prioritizes accumulated distance plus Manhattan distance to the end.
- A parent dictionary remembers how each cell was reached. Following it from
  destination to start and reversing the result produces the route.

All steps cost one. BFS, Dijkstra and A* therefore return shortest routes.
DFS does not guarantee optimality. On a maze with only one route, all four can
return the same path while exploring cells in different orders.

## Why generators and after()?

A generator lets the interface request one expansion at a time without losing
queue, distance or parent data. Tkinter after() schedules the next expansion
without blocking the window. No worker threads are needed. Changing algorithms,
generating a new maze or closing the window cancels the scheduled callback.

## Maze generation

Randomized depth-first backtracking visits odd-coordinate cells and carves the
walls between them. A stack stores the current branch. When no unvisited neighbor
remains, the algorithm pops the stack and backtracks. The fixed endpoints are
connected to the carved corridors. A seed is accepted internally for repeatable
tests; the application generates a fresh random maze on each button press.

## Demonstration

Generate a maze, choose BFS and press Run. Explain yellow frontier cells, blue
expanded cells and the orange route. Select A* and run it on the same maze.
Compare the expanded counts and moves. Repeat with DFS and Dijkstra.
