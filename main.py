import sys

import PyQt6.QtWidgets as q

from widgets.app import MainWindow

app = q.QApplication(sys.argv)

with open('Darkeum.qss', "r") as f:
	styles = f.read()
	app.setStyleSheet(styles)

window = MainWindow()

try:
	window.show()
	app.exec()

except Exception as e:
	print(f"Application crashed: {e}")

finally:
	if hasattr(window, "tracker"):
		window.tracker.stop()
	sys.exit()