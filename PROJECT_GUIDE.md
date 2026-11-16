# APP project explanation

## Objective

Show how four graph-search strategies choose routes through a grid containing
obstacles and weighted terrain. The grid is an implicit graph: every walkable
cell is a vertex; adjacent walkable cells are linked by edges.

## Program flow

1. main.py creates App and starts Tkinter's mainloop.
2. App creates a Grid model and draws it using Canvas rectangles.
3. Mouse callbacks update walls, weights or endpoints in the model.
4. Run creates a search generator and starts an after() callback.
5. Each next() resumes the generator until it yields a SearchEvent.
6. App colors the expanded node and newly queued nodes, then schedules another callback.
7. Reaching the destination reconstructs the route through parent links.
8. The UI displays route moves, cost, expansions and measured computation time.

## APP concepts actually present

| Concept | Concrete use |
| --- | --- |
| Classes and objects | Grid model and App window/controller |
| Inheritance | App inherits tkinter.Tk |
| Encapsulation | Model operations live in Grid; search algorithms do not depend on GUI |
| Dataclasses | Mutable Grid and frozen SearchEvent |
| Event-driven programming | Mouse/key callbacks and the Tk event loop |
| Generators / lazy execution | search yields one expansion rather than computing a full animation upfront |
| Higher-order functions | Button commands, key bindings, lambda callbacks |
| Functional operations | map(grid.cost, path[1:]) and sum for route cost |
| Iterators | Neighbor generator and comparison algorithm iterator |
| Exception handling | Invalid files and file-system errors produce dialogs |
| Serialization / file handling | JSON layout save/load, with validation before replacing the grid |
| Modular design | Model, algorithm engine and GUI separated into files |
| Automated verification | unittest with an independent shortest-cost oracle |

The design separates model and view/controller; it is not a strict three-class
MVC framework. It uses cooperative event-loop scheduling, not parallel execution
or worker threads. Do not claim Java, JDBC, sockets, database integration, or
multithreading: these are not part of this implementation.

## Why generators?

A normal function would compute everything at once. A generator preserves its
local queue, parents and distances between calls, allowing one expansion at a
time. Pause simply stops requesting more events; Step requests one event;
Resume starts requesting events again. The generator does not touch Tkinter.

## Why after()?

Tkinter processes input and drawing on its main thread. sleep() would block it.
after() schedules the next piece of work and returns control to mainloop, letting
the app redraw and process Pause, resizing or speed changes between callbacks.
Comparison similarly consumes at most 100 expansions per callback.

## Search mechanics

- BFS: append neighbors to a deque, remove from its left. First discovery gives
  the fewest edges because all graph edges are treated equally.
- DFS: append neighbors, remove from the right. It explores depth-first and may
  reach the goal by a long detour.
- Dijkstra: prioritize accumulated cost g. Relax a neighbor if the proposed
  cost is smaller; stale heap entries are skipped.
- A*: prioritize g + h, with h = abs(row difference) + abs(column difference).
  It uses the same relaxation rule as Dijkstra.
- Parent dictionary: each successful discovery/relaxation remembers the
  preceding node; follow parents from end back to start, then reverse.
- Maze: randomized depth-first backtracking carves odd-coordinate cells and
  corridors. An explicit stack avoids Python recursion-depth failures. Endpoint
  connectors guarantee access to the carved maze even from border cells.

For V vertices and E edges, BFS/DFS take O(V+E); heap-based weighted searches
take O((V+E) log V) on this grid. Space is O(V), since grid degree is bounded.

## Three-minute demonstration

1. Launch with run.bat. Explain the grid, start and end.
2. Load examples/weighted_demo.json. Run BFS and observe cost versus moves.
3. Compare All. Explain why Dijkstra/A* can choose more moves at a lower cost.
4. Clear Path; generate a random maze. Select A*, Run, Pause, Step, Resume.
5. Save the maze, Clear All and Load it again.

## Viva questions

**Does BFS find the cheapest weighted path?** No. It minimizes moves; it does not
use weights for its search decisions.

**Is DFS optimal?** No. It is useful for reachability and backtracking, but its
first found route can be long.

**Why is Manhattan distance safe?** You must make at least that many orthogonal
moves, and every move costs at least one. It never overestimates remaining cost.

**Why a heap counter?** It supplies deterministic insertion-order tie-breaking
when multiple entries have equal priorities.

**What happens when no path exists?** The frontier empties and the generator
yields a final event with an empty path. The GUI reports failure.

**Why disallow editing while paused?** The generator's distances and parent
links describe the original layout; changing it would invalidate the search.

**What is saved?** Dimensions, endpoints, walls and weights. Animation state and
visited cells are transient and deliberately excluded.
