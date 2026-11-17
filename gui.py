"""A read-only maze canvas with Random Maze, algorithm selection and Run."""
import tkinter as tk
from tkinter import ttk

from algorithms import ALGORITHMS, DESCRIPTIONS, search
from grid import Grid

ANIMATION_DELAY_MS = 20
COLORS = dict(empty='#f5f7fb', wall='#1c2538', frontier='#f9d36b',
              visited='#a1cdea', path='#ff9b53', start='#27ad85',
              end='#e26074', line='#dde4ee')


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Pathfinding Studio | APP Project')
        self.geometry('1150x800')
        self.minsize(850, 620)
        self.configure(bg='#eef2f7')
        self.grid_model = Grid()
        self.grid_model.maze()
        self.algorithm = tk.StringVar(value='A*')
        self.description = tk.StringVar(value=DESCRIPTIONS['A*'])
        self.status = tk.StringVar()
        self.stats = tk.StringVar()
        self.runner = None
        self.timer = None
        self.visited, self.frontier, self.route = set(), set(), set()
        self.rectangles = {}
        self._build()
        self.reset_search()
        self.protocol('WM_DELETE_WINDOW', self.close)

    def _build(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#eef2f7')
        style.configure('TLabel', background='#eef2f7', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=(10, 7))
        style.configure('Accent.TButton', background='#237e73', foreground='white')
        header = tk.Frame(self, bg='#162439', padx=24, pady=17)
        header.pack(fill='x')
        tk.Label(header, text='PATHFINDING STUDIO', bg='#162439', fg='white',
                 font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        tk.Label(header, text='Generate a maze. Choose an algorithm. Watch the search.',
                 bg='#162439', fg='#a9bdd5', font=('Segoe UI', 11)).pack(anchor='w')
        controls = ttk.Frame(self, padding=(18, 12))
        controls.pack(fill='x')
        ttk.Button(controls, text='Random Maze', command=self.maze).pack(side='left', padx=(0, 18))
        ttk.Label(controls, text='Algorithm').pack(side='left', padx=(0, 7))
        self.selector = ttk.Combobox(controls, textvariable=self.algorithm,
                                     values=ALGORITHMS, state='readonly', width=11)
        self.selector.pack(side='left', padx=(0, 12))
        self.selector.bind('<<ComboboxSelected>>', self.change_algorithm)
        self.run_button = ttk.Button(controls, text='Run', command=self.run, style='Accent.TButton')
        self.run_button.pack(side='left')
        ttk.Label(self, textvariable=self.description, padding=(20, 0, 20, 8)).pack(anchor='w')
        panel = tk.Frame(self, bg='white', padx=6, pady=6)
        panel.pack(fill='both', expand=True, padx=18)
        self.canvas = tk.Canvas(panel, bg=COLORS['empty'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda event: self.redraw())
        legend = ttk.Frame(self, padding=(18, 10))
        legend.pack(fill='x')
        for key in ('start', 'end', 'wall', 'frontier', 'visited', 'path'):
            tk.Canvas(legend, width=14, height=14, highlightthickness=0,
                      bg=COLORS[key]).pack(side='left', padx=(0, 5))
            ttk.Label(legend, text=key.capitalize()).pack(side='left', padx=(0, 17))
        ttk.Label(self, textvariable=self.stats, font=('Segoe UI', 11, 'bold'),
                  padding=(20, 0, 20, 7)).pack(anchor='w')
        ttk.Label(self, textvariable=self.status, padding=(20, 0, 20, 12)).pack(anchor='w')

    def color(self, cell):
        if cell == self.grid_model.start:
            return COLORS['start']
        if cell == self.grid_model.end:
            return COLORS['end']
        for cells, name in ((self.grid_model.walls, 'wall'), (self.route, 'path'),
                            (self.visited, 'visited'), (self.frontier, 'frontier')):
            if cell in cells:
                return COLORS[name]
        return COLORS['empty']

    def redraw(self):
        self.canvas.delete('all')
        self.rectangles.clear()
        grid = self.grid_model
        width, height = self.canvas.winfo_width(), self.canvas.winfo_height()
        size = max(1, min(width / grid.cols, height / grid.rows))
        left, top = (width - size * grid.cols) / 2, (height - size * grid.rows) / 2
        for r in range(grid.rows):
            for c in range(grid.cols):
                cell = (r, c)
                x, y = left + c * size, top + r * size
                self.rectangles[cell] = self.canvas.create_rectangle(
                    x, y, x + size, y + size, fill=self.color(cell), outline=COLORS['line'])
                label = 'S' if cell == grid.start else 'E' if cell == grid.end else ''
                if label and size >= 13:
                    self.canvas.create_text(x + size / 2, y + size / 2, text=label,
                                            font=('Segoe UI', max(7, int(size * .4)), 'bold'))

    def refresh_cells(self, cells):
        for cell in cells:
            if cell in self.rectangles:
                self.canvas.itemconfigure(self.rectangles[cell], fill=self.color(cell))

    def cancel_search(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None
        self.runner = None

    def reset_search(self):
        self.cancel_search()
        self.visited.clear()
        self.frontier.clear()
        self.route.clear()
        self.stats.set('Expanded: 0     Moves: -     Compute: -')
        self.status.set('Ready. Choose an algorithm and press Run.')
        self.run_button.configure(state='normal')
        self.redraw()

    def change_algorithm(self, event=None):
        self.reset_search()
        self.description.set(DESCRIPTIONS[self.algorithm.get()])

    def maze(self):
        self.cancel_search()
        self.grid_model.maze()
        self.reset_search()
        self.status.set('Random maze generated. Both endpoints are connected. Press Run.')

    def run(self):
        if self.runner is not None:
            return
        self.reset_search()
        self.runner = search(self.grid_model, self.algorithm.get())
        self.run_button.configure(state='disabled')
        self.status.set('Searching. Choose another algorithm or generate a new maze to restart.')
        self.tick()

    def tick(self):
        self.timer = None
        if self.runner is None:
            return
        event = next(self.runner)
        self.frontier.update(event.added)
        if event.current is not None:
            self.frontier.discard(event.current)
            self.visited.add(event.current)
        self.refresh_cells((*event.added, event.current))
        moves = '-'
        if event.done:
            self.runner = None
            self.route = set(event.path)
            self.refresh_cells(event.path)
            self.run_button.configure(state='normal')
            if event.path:
                moves = len(event.path) - 1
                self.status.set('Route found. Try another algorithm on this maze, or generate a new maze.')
            else:
                self.status.set('No route found. Generate a new maze and try again.')
        else:
            self.timer = self.after(ANIMATION_DELAY_MS, self.tick)
        self.stats.set(f'Expanded: {event.expanded}     Moves: {moves}     Compute: {event.elapsed_ms:.3f} ms')

    def close(self):
        self.cancel_search()
        self.destroy()
