import sys
from pathlib import Path

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QWidget


class CustomBaseWindow(QWidget):
	"""
	Base class to create a frameless, draggable window.
	Can be used as a parent class for both QWidget and QMainWindow.
	"""
	
	def __init__(self):
		super().__init__()
		
		base_path = Path(getattr(sys, '_MEIPASS', '.'))
		icon_path = base_path.joinpath("icon.ico")
		
		self.setWindowIcon(QIcon(str(icon_path)))