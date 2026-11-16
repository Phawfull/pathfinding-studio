"""Tkinter view/controller. Animation uses after(), never sleep() or threads."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from algorithms import ALGORITHMS, DESCRIPTIONS, search
from grid import Grid

COLORS = dict(empty='#f5f7fb', wall='#1c2538', weight='#c3a1dd',
              frontier='#f9d36b', visited='#a1cdea', path='#ff9b53',
              start='#27ad85', end='#e26074', line='#dde4ee')


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('Pathfinding Studio | APP Project')
        self.geometry('1250x840')
        self.minsize(960, 720)
        self.configure(bg='#eef2f7')
        self.grid_model = Grid()
        self.algorithm = tk.StringVar(value='A*')
        self.tool = tk.StringVar(value='Wall')
        self.speed = tk.DoubleVar(value=80)
        self.status = tk.StringVar(value='Ready. Draw walls or generate a maze, then press Run.')
        self.stats = tk.StringVar(value='Expanded: 0     Moves: —     Cost: —     Compute: —')
        self.description = tk.StringVar(value=DESCRIPTIONS['A*'])
        self.state = 'idle'
        self.runner = None
        self.timer = None
        self.compare_timer = None
        self.compare_window = None
        self.visited, self.frontier, self.route = set(), set(), set()
        self.rectangles = {}
        self.weight_key = False
        self.last_cell = None
        self._build()
        self.bind('<KeyPress-w>', lambda e: setattr(self, 'weight_key', True))
        self.bind('<KeyRelease-w>', lambda e: setattr(self, 'weight_key', False))
        self.bind('<FocusOut>', lambda e: setattr(self, 'weight_key', False))
        self.protocol('WM_DELETE_WINDOW', self.close)

    def _build(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('TFrame', background='#eef2f7')
        style.configure('TLabel', background='#eef2f7', font=('Segoe UI', 10))
        style.configure('TButton', font=('Segoe UI', 10), padding=(10, 7))
        style.configure('TRadiobutton', background='#eef2f7', font=('Segoe UI', 10))
        style.configure('Accent.TButton', background='#237e73', foreground='white')
        header = tk.Frame(self, bg='#162439', padx=24, pady=17)
        header.pack(fill='x')
        tk.Label(header, text='PATHFINDING STUDIO', bg='#162439', fg='white',
                 font=('Segoe UI', 20, 'bold')).pack(anchor='w')
        tk.Label(header, text='Explore the search. Understand the route.', bg='#162439',
                 fg='#a9bdd5', font=('Segoe UI', 11)).pack(anchor='w', pady=(3, 0))
        controls = ttk.Frame(self, padding=(18, 12))
        controls.pack(fill='x')
        ttk.Label(controls, text='Algorithm').pack(side='left', padx=(0, 7))
        self.selector = ttk.Combobox(controls, textvariable=self.algorithm, values=ALGORITHMS,
                                     state='readonly', width=11)
        self.selector.pack(side='left', padx=(0, 12))
        self.selector.bind('<<ComboboxSelected>>', self.change_algorithm)
        self.run_button = ttk.Button(controls, text='Run', command=self.run, style='Accent.TButton')
        self.run_button.pack(side='left', padx=3)
        self.pause_button = ttk.Button(controls, text='Pause', command=self.pause)
        self.pause_button.pack(side='left', padx=3)
        self.step_button = ttk.Button(controls, text='Step', command=self.step)
        self.step_button.pack(side='left', padx=3)
        ttk.Label(controls, text='Speed').pack(side='left', padx=(18, 6))
        ttk.Scale(controls, variable=self.speed, from_=1, to=100, length=130).pack(side='left')
        self.compare_button = ttk.Button(controls, text='Compare All', command=self.compare)
        self.compare_button.pack(side='right')
        tools = ttk.Frame(self, padding=(18, 0, 18, 8))
        tools.pack(fill='x')
        for tool in ('Wall', 'Weight', 'Erase', 'Start', 'End'):
            ttk.Radiobutton(tools, text=tool, value=tool, variable=self.tool).pack(side='left', padx=(0, 10))
        for text, command in (('Load…', self.load), ('Save…', self.save), ('Random Maze', self.maze),
                              ('Clear All', self.clear_all), ('Clear Path', self.clear_path)):
            ttk.Button(tools, text=text, command=command).pack(side='right', padx=2)
        ttk.Label(self, textvariable=self.description, padding=(20, 0, 20, 8)).pack(anchor='w')
        panel = tk.Frame(self, bg='white', padx=6, pady=6)
        panel.pack(fill='both', expand=True, padx=18)
        self.canvas = tk.Canvas(panel, bg=COLORS['empty'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.canvas.bind('<Configure>', lambda e: self.redraw())
        self.canvas.bind('<Button-1>', self.paint)
        self.canvas.bind('<B1-Motion>', self.paint)
        self.canvas.bind('<Button-3>', lambda e: self.paint(e, erase=True))
        self.canvas.bind('<B3-Motion>', lambda e: self.paint(e, erase=True))
        self.canvas.bind('<ButtonRelease-1>', lambda e: setattr(self, 'last_cell', None))
        self.canvas.bind('<ButtonRelease-3>', lambda e: setattr(self, 'last_cell', None))
        legend = ttk.Frame(self, padding=(18, 10))
        legend.pack(fill='x')
        for key in ('start', 'end', 'wall', 'weight', 'frontier', 'visited', 'path'):
            swatch = tk.Canvas(legend, width=14, height=14, highlightthickness=0, bg=COLORS[key])
            swatch.pack(side='left', padx=(0, 5))
            ttk.Label(legend, text=key.capitalize()).pack(side='left', padx=(0, 17))
        ttk.Label(self, textvariable=self.stats, font=('Segoe UI', 11, 'bold'),
                  padding=(20, 0, 20, 7)).pack(anchor='w')
        ttk.Label(self, textvariable=self.status, padding=(20, 0, 20, 5)).pack(anchor='w')
        ttk.Label(self, text='Drag: draw • Right-drag: erase • W + draw: cost 5 • Shift-click: start • Ctrl-click: end',
                  foreground='#566881', padding=(20, 0, 20, 12)).pack(anchor='w')
        self.sync_controls()

    def sync_controls(self):
        locked = self.state in ('running', 'paused', 'comparing')
        self.selector.configure(state='disabled' if locked else 'readonly')
        self.run_button.configure(state='disabled' if self.state in ('running', 'comparing') else 'normal',
                                  text='Resume' if self.state == 'paused' else 'Run')
        self.pause_button.configure(state='normal' if self.state == 'running' else 'disabled')
        self.step_button.configure(state='disabled' if self.state in ('running', 'comparing') else 'normal')
        self.compare_button.configure(state='disabled' if locked else 'normal')

    def change_algorithm(self, event=None):
        self.clear_path()
        self.description.set(DESCRIPTIONS[self.algorithm.get()])

    def color(self, cell):
        g = self.grid_model
        if cell == g.start:
            return COLORS['start']
        if cell == g.end:
            return COLORS['end']
        if cell in g.walls:
            return COLORS['wall']
        if cell in self.route:
            return COLORS['path']
        if cell in self.visited:
            return '#79accd' if cell in g.weights else COLORS['visited']
        if cell in self.frontier:
            return '#c9aa51' if cell in g.weights else COLORS['frontier']
        return COLORS['weight'] if cell in g.weights else COLORS['empty']

    def redraw(self):
        self.canvas.delete('all')
        self.rectangles.clear()
        g = self.grid_model
        self.cell_size = max(1, min(self.canvas.winfo_width() / g.cols, self.canvas.winfo_height() / g.rows))
        self.offset_x = (self.canvas.winfo_width() - self.cell_size * g.cols) / 2
        self.offset_y = (self.canvas.winfo_height() - self.cell_size * g.rows) / 2
        for r in range(g.rows):
            for c in range(g.cols):
                x, y = self.offset_x + c * self.cell_size, self.offset_y + r * self.cell_size
                self.rectangles[r, c] = self.canvas.create_rectangle(
                    x, y, x + self.cell_size, y + self.cell_size,
                    fill=self.color((r, c)), outline=COLORS['line'], width=1)
                label = 'S' if (r, c) == g.start else 'E' if (r, c) == g.end else str(g.weights.get((r, c), ''))
                if label and self.cell_size >= 13:
                    self.canvas.create_text(x + self.cell_size / 2, y + self.cell_size / 2, text=label,
                                            fill='#162439', font=('Segoe UI', max(7, int(self.cell_size * .4)), 'bold'))

    def refresh_cells(self, cells):
        for cell in cells:
            if cell in self.rectangles:
                self.canvas.itemconfigure(self.rectangles[cell], fill=self.color(cell))

    def paint(self, event, erase=False):
        if self.state in ('running', 'paused', 'comparing'):
            self.status.set('Editing is locked during search. Press Clear Path to stop and edit.')
            return
        cell = (int((event.y - self.offset_y) // self.cell_size),
                int((event.x - self.offset_x) // self.cell_size))
        if not self.grid_model.inside(cell):
            return
        if self.state == 'done':
            self.clear_path()
        tool = ('Erase' if erase else 'Start' if event.state & 0x0001 else
                'End' if event.state & 0x0004 else 'Weight' if self.weight_key else self.tool.get())
        self.grid_model.paint(cell, tool)
        self.redraw()

    def cancel_timer(self):
        if self.timer is not None:
            self.after_cancel(self.timer)
            self.timer = None

    def clear_path(self):
        self.cancel_timer()
        self.cancel_compare()
        self.runner = None
        self.state = 'idle'
        self.visited.clear()
        self.frontier.clear()
        self.route.clear()
        self.stats.set('Expanded: 0     Moves: —     Cost: —     Compute: —')
        self.status.set('Ready. Draw walls or generate a maze, then press Run.')
        self.redraw()
        self.sync_controls()

    def clear_all(self):
        self.clear_path()
        self.grid_model.clear()
        self.redraw()

    def maze(self):
        self.clear_path()
        self.grid_model.maze()
        self.redraw()
        self.status.set('Maze generated with depth-first backtracking. Both endpoints are connected.')

    def prepare(self):
        if self.state in ('idle', 'done'):
            self.clear_path()
            self.runner = search(self.grid_model, self.algorithm.get())

    def run(self):
        if self.state in ('running', 'comparing'):
            return
        self.prepare()
        self.state = 'running'
        self.status.set('Searching… Pause to inspect, or adjust the speed slider.')
        self.sync_controls()
        self.tick()

    def pause(self):
        if self.state == 'running':
            self.cancel_timer()
            self.state = 'paused'
            self.status.set('Paused. Use Step for one expansion, or Resume to continue.')
            self.sync_controls()

    def step(self):
        if self.state in ('running', 'comparing'):
            return
        self.prepare()
        self.state = 'paused'
        self.advance()
        self.sync_controls()

    def advance(self):
        try:
            event = next(self.runner)
        except StopIteration:
            self.state = 'done'
            self.sync_controls()
            return
        self.frontier.update(event.added)
        if event.current is not None:
            self.frontier.discard(event.current)
            self.visited.add(event.current)
        self.refresh_cells((*event.added, event.current))
        moves, cost = '—', '—'
        if event.done:
            self.state = 'done'
            self.route = set(event.path)
            self.refresh_cells(event.path)
            if event.path:
                moves, cost = len(event.path) - 1, event.cost
                self.status.set('Route found. Edit the grid to try another scenario, or compare all algorithms.')
            else:
                self.status.set('No route exists. Remove walls or move an endpoint and try again.')
            self.sync_controls()
        self.stats.set(f'Expanded: {event.expanded}     Moves: {moves}     Cost: {cost}     Compute: {event.elapsed_ms:.3f} ms')

    def tick(self):
        self.timer = None
        if self.state != 'running':
            return
        # At high speeds render several expansions per frame.
        for _ in range(1 + max(0, int(self.speed.get()) - 85) // 3):
            self.advance()
            if self.state != 'running':
                return
        self.timer = self.after(max(1, 101 - int(self.speed.get())), self.tick)

    def save(self):
        filename = filedialog.asksaveasfilename(parent=self, title='Save grid', defaultextension='.json',
                                              filetypes=[('Grid files', '*.json')])
        if filename:
            try:
                self.grid_model.save(filename)
                self.status.set('Grid saved. Search overlays are not included.')
            except OSError as exc:
                messagebox.showerror('Could not save', str(exc), parent=self)

    def load(self):
        filename = filedialog.askopenfilename(parent=self, title='Load grid', filetypes=[('Grid files', '*.json')])
        if filename:
            try:
                model = Grid.load(filename)
            except (OSError, ValueError, TypeError, KeyError, RecursionError) as exc:
                messagebox.showerror('Could not load', str(exc), parent=self)
                return
            self.clear_path()
            self.grid_model = model
            self.redraw()
            self.status.set('Grid loaded successfully.')

    def cancel_compare(self):
        if self.compare_timer is not None:
            self.after_cancel(self.compare_timer)
            self.compare_timer = None
        if self.compare_window is not None:
            self.compare_window.destroy()
            self.compare_window = None
        if self.state == 'comparing':
            self.state = 'idle'
            self.sync_controls()

    def compare(self):
        if self.state in ('running', 'paused', 'comparing'):
            return
        self.cancel_compare()
        self.state = 'comparing'
        self.sync_controls()
        win = self.compare_window = tk.Toplevel(self)
        win.title('Algorithm comparison | same grid')
        win.geometry('780x300')
        win.transient(self)
        ttk.Label(win, text='Same grid. Four strategies.', font=('Segoe UI', 16, 'bold'), padding=16).pack(anchor='w')
        table = ttk.Treeview(win, columns=('algorithm', 'found', 'expanded', 'moves', 'cost', 'time'),
                             show='headings', height=4)
        for key, title in zip(table['columns'], ('Algorithm', 'Found', 'Expanded', 'Moves', 'Cost', 'Compute (ms)')):
            table.heading(key, text=title)
            table.column(key, width=115, anchor='center')
        table.pack(fill='x', padx=16)
        ttk.Label(win, text='BFS / DFS ignore weights. Compute time excludes animation; timings vary per run.',
                  padding=16, wraplength=720).pack(anchor='w')
        jobs = iter(ALGORITHMS)
        active = [None, None]

        def batch():
            self.compare_timer = None
            if active[1] is None:
                try:
                    active[0] = next(jobs)
                except StopIteration:
                    self.state = 'idle'
                    self.sync_controls()
                    self.status.set('Comparison complete. The grid was not changed.')
                    return
                active[1] = search(self.grid_model, active[0])
            for _ in range(100):
                event = next(active[1])
                if event.done:
                    table.insert('', 'end', values=(active[0], 'Yes' if event.path else 'No', event.expanded,
                                 len(event.path) - 1 if event.path else '—', event.cost if event.path else '—',
                                 f'{event.elapsed_ms:.3f}'))
                    active[1] = None
                    break
            self.compare_timer = self.after(1, batch)

        win.protocol('WM_DELETE_WINDOW', self.cancel_compare)
        self.compare_timer = self.after(1, batch)

    def close(self):
        self.cancel_timer()
        self.cancel_compare()
        self.destroy()
