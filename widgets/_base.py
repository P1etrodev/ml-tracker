from PyQt6.QtWidgets import QWidget


class CustomBaseWindow(QWidget):
	"""
	Base class to create a frameless, draggable window.
	Can be used as a parent class for both QWidget and QMainWindow.
	"""
	
	def __init__(self):
		super().__init__()