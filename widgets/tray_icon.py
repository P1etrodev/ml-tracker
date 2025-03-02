import sys
from pathlib import Path

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon


class TrayIcon(QSystemTrayIcon):
	
	show_clicked: pyqtSignal = pyqtSignal()
	
	def __init__(self, parent):
		base_path = Path(getattr(sys, '_MEIPASS', '.'))
		icon_path = str(base_path.joinpath('icon.ico'))
		icon = QIcon(icon_path)
		
		super().__init__(icon, parent)
		
		self.activated.connect(self.on_tray_icon_clicked)
		
		self.tray_menu = QMenu()
		self.setContextMenu(self.tray_menu)
		
		# ---------------------------------------------------
		
		show_action = QAction("Mostrar", self)
		show_action.triggered.connect(self.show_clicked.emit)
		self.tray_menu.addAction(show_action)
		
		# ---------------------------------------------------
		
		exit_action = QAction("Cerrar", self)
		exit_action.triggered.connect(QApplication.quit)
		self.tray_menu.addAction(exit_action)
	
	def on_tray_icon_clicked(self, reason):
		"""Restores the window when clicking the tray icon."""
		if reason == QSystemTrayIcon.ActivationReason.Trigger:
			self.show_clicked.emit()