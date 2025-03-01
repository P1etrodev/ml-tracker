import re

from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtWidgets import (
	QLineEdit,
	QListWidget,
	QMessageBox,
	QPushButton,
	QVBoxLayout,
)
from pandas import DataFrame, concat

from tracker import TrackerWorker
from widgets._base import CustomBaseWindow


class URLManagerWidget(CustomBaseWindow):
	
	updated: pyqtSignal = pyqtSignal()
	
	def __init__(self, tracker: TrackerWorker):
		
		super().__init__()
		
		self.tracker = tracker
		
		self.setWindowTitle("Modificar URLs")
		self.setFixedSize(QSize(500, 300))
		
		self.layout = QVBoxLayout()
		
		self.listbox = QListWidget(self)
		self.layout.addWidget(self.listbox)
		
		for url in self.tracker.data['url']:
			self.listbox.addItem(url)
		
		self.entry = QLineEdit(self)
		self.layout.addWidget(self.entry)
		
		self.btn_add = QPushButton("Agregar URL", self)
		self.btn_add.clicked.connect(self.add_url)
		self.layout.addWidget(self.btn_add)
		
		self.btn_remove = QPushButton("Eliminar", self)
		self.btn_remove.clicked.connect(self.remove_url)
		self.layout.addWidget(self.btn_remove)
		
		self.setLayout(self.layout)
		
		self.setWindowModality(Qt.WindowModality.ApplicationModal)
	
	def is_url_valid(self, url: str):
		pattern = re.compile('https://([a-z]+\\.)?mercadolibre(\\.[a-z]+)+(/.+)?')
		
		match = pattern.match(url) is not None
		
		if url and not match:
			self.entry.setStyleSheet('background: red;')
		else:
			self.entry.setStyleSheet('background: gray;')
		
		return match
	
	def add_url(self) -> None:
		"""Add a new URL to the DataFrame and listbox."""
		url = self.entry.text().strip()
		if url and self.is_url_valid(url):
			# Add URL to DataFrame
			new_data = {
				"url": url,
				"available": True,
				"currency": None,
				"previous_price": 0.0,
				"current_price": 0.0,
				"product": None,
				"free_ship": False,
				"with_discount": False
			}
			self.tracker.data = concat(
				[self.tracker.data, DataFrame([new_data])], ignore_index=True
			)
			# Save updated DataFrame to CSV
			self.tracker.save_data()
			self.listbox.addItem(url)
			self.entry.clear()
			self.updated.emit()
	
	def remove_url(self) -> None:
		"""Remove selected URL from DataFrame and listbox."""
		selected_item = self.listbox.currentItem()
		if selected_item:
			url = selected_item.text()
			self.listbox.takeItem(self.listbox.row(selected_item))
			
			# Remove URL from DataFrame
			self.tracker.data = self.tracker.data[self.tracker.data["url"] != url]
			# Save updated DataFrame to CSV
			self.tracker.save_data()
			self.updated.emit()
		else:
			QMessageBox.warning(self, "Warning", "Please select a URL to remove.")