"""Run explicitly: python -m tests.gui_smoke (requires a desktop with Tk)."""
import copy
import time
from tkinter import ttk

from algorithms import ALGORITHMS
from gui import App, ANIMATION_DELAY_MS
from grid import Grid


def main():
    app = App()
    errors = []
    app.report_callback_exception = lambda kind, value, tb: errors.append(value)
    app.update()
    try:
        assert len(app.rectangles) == 1000
        assert app.grid_model.walls
        assert ANIMATION_DELAY_MS == 20
        def descendants(widget):
            for child in widget.winfo_children():
                yield child
                yield from descendants(child)
        widgets = list(descendants(app))
        assert [w.cget('text') for w in widgets if isinstance(w, ttk.Button)] == ['Random Maze', 'Run']
        assert not any(isinstance(w, (ttk.Scale, ttk.Radiobutton)) for w in widgets)
        # Mouse gestures and old keyboard shortcuts must leave the model untouched.
        before = copy.deepcopy(app.grid_model)
        for sequence in ('<Button-1>', '<B1-Motion>', '<Button-3>', '<Shift-Button-1>', '<Control-Button-1>'):
            app.canvas.event_generate(sequence, x=100, y=100)
        app.update()
        assert app.grid_model == before
        # A short fixture keeps real event-loop animation checks fast.
        app.grid_model = Grid(5, 5, (1, 1), (1, 2))
        for name in ALGORITHMS:
            app.algorithm.set(name)
            app.selector.event_generate('<<ComboboxSelected>>')
            app.run_button.invoke()
            deadline = time.monotonic() + 3
            while app.runner is not None and time.monotonic() < deadline:
                app.update()
                time.sleep(.002)
            assert app.runner is None, name
            assert app.grid_model.end in app.route, name
            assert app.run_button.instate(['!disabled'])
        app.grid_model = Grid()
        app.maze()
        app.run()
        old_timer = app.timer
        assert old_timer is not None
        app.algorithm.set('BFS')
        app.selector.event_generate('<<ComboboxSelected>>')
        app.update()
        assert app.runner is None and app.timer is None and not app.visited
        assert old_timer not in app.tk.splitlist(app.tk.call('after', 'info'))
        app.run()
        app.maze()
        app.update()
        assert app.runner is None and app.timer is None and not app.route
        assert app.grid_model.walls
        app.geometry('900x650')
        app.update()
        assert len(app.rectangles) == 1000
        app.run()
        assert app.timer is not None
        assert not errors, errors
        print('GUI smoke passed: minimal controls, read-only grid, all four algorithms, cancellation, regeneration, resize and close.')
    finally:
        app.close()


if __name__ == '__main__':
    main()
