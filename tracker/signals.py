from PyQt6.QtCore import QObject, pyqtSignal
from pandas import Series


class Signals(QObject):
	status: pyqtSignal = pyqtSignal(str, str)
	log: pyqtSignal = pyqtSignal(str, str, bool)
	updated: pyqtSignal = pyqtSignal()
	thread_finished: pyqtSignal = pyqtSignal(int, Series)