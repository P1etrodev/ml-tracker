import sys
from pathlib import Path
from warnings import simplefilter

import PyQt6.QtWidgets as q

from widgets.app import MainWindow

simplefilter(action='ignore', category=FutureWarning)

base_path = Path(getattr(sys, '_MEIPASS', '.'))
with base_path.joinpath('Darkeum.qss').open('r') as f:
	styles = f.read()

app = q.QApplication(sys.argv)
app.setStyleSheet(styles)

window = MainWindow()

try:
	window.show()
	app.exec()
except Exception as e:
	print(f"Application crashed: {e}")

finally:
	if hasattr(window, "tracker"):
		window.stop_timer()
	sys.exit()