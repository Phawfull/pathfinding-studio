"""Run explicitly: python -m tests.gui_smoke (requires a desktop with Tk)."""
import time
from types import SimpleNamespace
from unittest.mock import patch
import tempfile
from pathlib import Path

from gui import App


def main():
    app = App()
    errors = []
    app.report_callback_exception = lambda kind, value, tb: errors.append(value)
    app.update()
    try:
        assert len(app.rectangles) == 1000
        # Exercise mouse drawing and endpoint movement through the actual callback.
        def click(cell, state=0, erase=False):
            r, c = cell
            event = SimpleNamespace(x=app.offset_x + (c + .5) * app.cell_size,
                                    y=app.offset_y + (r + .5) * app.cell_size, state=state)
            app.paint(event, erase)

        click((3, 3))
        assert (3, 3) in app.grid_model.walls
        click((3, 3), erase=True)
        assert (3, 3) not in app.grid_model.walls
        app.tool.set('Weight')
        click((3, 4))
        assert app.grid_model.weights[3, 4] == 5
        click((0, 0), state=1)
        assert app.grid_model.start == (0, 0)
        click((0, 2), state=4)
        assert app.grid_model.end == (0, 2)
        app.step()
        assert app.state == 'paused'
        assert len(app.visited) == 1
        click((4, 4))
        assert (4, 4) not in app.grid_model.weights
        app.run()
        app.pause()
        assert app.state in ('paused', 'done')
        app.speed.set(100)
        app.run()
        deadline = time.monotonic() + 5
        while app.state == 'running' and time.monotonic() < deadline:
            app.update()
        assert app.state == 'done'
        assert app.grid_model.end in app.route
        app.compare()
        deadline = time.monotonic() + 5
        while app.state == 'comparing' and time.monotonic() < deadline:
            app.update()
        assert app.state == 'idle'
        table = next(w for w in app.compare_window.winfo_children() if w.winfo_class() == 'Treeview')
        assert len(table.get_children()) == 4
        app.cancel_compare()
        with tempfile.TemporaryDirectory() as folder:
            filename = str(Path(folder) / 'scenario.json')
            before = app.grid_model.to_dict()
            with patch('gui.filedialog.asksaveasfilename', return_value=filename):
                app.save()
            app.clear_all()
            with patch('gui.filedialog.askopenfilename', return_value=filename):
                app.load()
            assert app.grid_model.to_dict() == before
            Path(filename).write_text('{broken json', encoding='utf-8')
            with patch('gui.filedialog.askopenfilename', return_value=filename), patch('gui.messagebox.showerror') as dialog:
                app.load()
                assert dialog.called
            assert app.grid_model.to_dict() == before
        app.maze()
        app.run()
        app.clear_path()
        app.update()
        assert app.state == 'idle' and not app.visited
        app.compare()
        app.clear_all()
        app.update()
        assert app.state == 'idle' and not app.grid_model.walls
        app.geometry('1000x740')
        app.update()
        assert len(app.rectangles) == 1000
        assert not errors, errors
        print('GUI smoke passed: drawing, weights, endpoints, run/pause/step, comparison, save/load, invalid load, cancellation, resize.')
    finally:
        app.close()


if __name__ == '__main__':
    main()
