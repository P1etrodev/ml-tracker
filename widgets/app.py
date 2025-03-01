import webbrowser
from datetime import datetime
from typing import Literal

import PyQt6.QtWidgets as q
from PyQt6.QtCore import QSize
from PyQt6.QtWidgets import QTableWidgetItem
from winotify import Notification

from tracker.tracker import TrackerWorker
from widgets._base import CustomBaseWindow
from widgets.settings import SettingsWidget
from widgets.url_manager import URLManagerWidget


class MainWindow(q.QMainWindow, CustomBaseWindow):
	
	def __init__(self):
		super().__init__()
		
		self.setWindowTitle("ML Tracker")
		self.setFixedSize(QSize(800, 500))
		
		self.tracker = TrackerWorker()
		self.tracker.status.connect(self.add_log)
		self.tracker.updated.connect(self.update_ui)
		self.tracker.timer.connect(self.update_timer)
		
		self.url_manager_widget = URLManagerWidget(self.tracker)
		self.url_manager_widget.updated.connect(self.update_ui)
		
		self.settings_widget = SettingsWidget(self.tracker)
		
		# ---------------------------------------------------
		
		main = q.QWidget()
		main_layout = q.QVBoxLayout()
		main.setLayout(main_layout)
		
		# ---------------------------------------------------
		
		content = q.QWidget()
		content_layout = q.QVBoxLayout()
		content.setLayout(content_layout)
		main_layout.addWidget(content)
		
		tabs = q.QTabWidget()
		content_layout.addWidget(tabs)
		
		# ---------------------------------------------------
		
		# TODO fix timer
		# self.timer = q.QLabel()
		# content_layout.addWidget(self.timer)
		
		# ---------------------------------------------------
		
		self.tracked_posts = q.QTableWidget()
		self.tracked_posts.setEditTriggers(q.QTableWidget.EditTrigger.NoEditTriggers)
		self.tracked_posts.verticalHeader().setVisible(False)
		tabs.addTab(self.tracked_posts, 'Publicaciones')
		
		# ---------------------------------------------------
		
		self.logs = q.QListWidget()
		tabs.addTab(self.logs, 'Logs')
		
		# ---------------------------------------------------
		
		self.status_label = q.QLabel()
		self.status_label.setStyleSheet('background: #212121;')
		content_layout.addWidget(self.status_label)
		
		# ---------------------------------------------------
		
		menu = q.QWidget()
		menu_layout = q.QHBoxLayout()
		menu.setLayout(menu_layout)
		main_layout.addWidget(menu)
		
		self.start_button = q.QPushButton('👍🏻 Iniciar')
		self.start_button.clicked.connect(self.start_tracker)
		menu_layout.addWidget(self.start_button)
		
		self.stop_button = q.QPushButton('🤚🏻 Detener')
		self.stop_button.clicked.connect(self.stop_tracker)
		menu_layout.addWidget(self.stop_button)
		
		self.modify_urls_button = q.QPushButton('🔗 Modificar URLs')
		self.modify_urls_button.clicked.connect(self.url_manager_widget.show)
		menu_layout.addWidget(self.modify_urls_button)
		
		self.settings_button = q.QPushButton('⚙️ Opciones')
		self.settings_button.clicked.connect(self.settings_widget.show)
		menu_layout.addWidget(self.settings_button)
		
		# ---------------------------------------------------
		
		self.setCentralWidget(main)
		
		self.update_ui()
	
	# TODO fix timer
	# def update_timer(self):
	# 	self.timer.setText(self.tracker.sleeping_time_left // 2)
	
	def update_ui(self):
		running = self.tracker.running
		stopping = self.tracker.stopping
		
		# Buttons
		self.start_button.setEnabled(not running and not stopping)
		self.stop_button.setEnabled(running and not stopping)
		self.modify_urls_button.setEnabled(not running and not stopping)
		self.settings_button.setEnabled(not running and not stopping)
		
		# Tracked posts
		posts = self.tracker.data.copy()
		
		posts['currency'] = posts['currency'].fillna('$')
		posts['current_price'] = posts.apply(
			lambda row: f'{row["currency"]} {row["current_price"]:,}', axis=1
		)
		posts['product'] = posts['product'].fillna('-')
		posts['free_ship'] = posts['free_ship'].apply(lambda x: 'Sí' if x else 'No')
		posts['available'] = posts['available'].apply(lambda x: 'Sí' if x else 'No')
		posts['with_discount'] = posts['with_discount'].apply(lambda x: 'Sí' if x else 'No')
		
		posts = posts[['product', 'current_price', 'free_ship', 'with_discount', 'available', 'url']]
		
		posts.rename(
			columns={
				'url': "",
				'current_price': "Precio",
				"product": "Producto",
				"free_ship": "Envío gratis",
				"available": "Disponible",
				"with_discount": "En descuento"
			},
			inplace=True
		)
		
		self.tracked_posts.setRowCount(posts.shape[0])
		self.tracked_posts.setColumnCount(posts.shape[1])
		self.tracked_posts.setHorizontalHeaderLabels(posts.columns)
		self.tracked_posts.horizontalHeader().setSectionResizeMode(
			0, self.tracked_posts.horizontalHeader().ResizeMode.Stretch
		)
		
		for row in range(posts.shape[0]):
			for col in range(posts.shape[1]):
				if posts.columns[col] == '':  # Verificamos si la columna es 'url'
					# Creamos un botón con el texto de la URL
					button = q.QPushButton("Ver")
					button.clicked.connect(lambda checked, url=posts.iloc[row, col]: webbrowser.open(url))
					# Establecemos el botón en la celda correspondiente
					self.tracked_posts.setCellWidget(row, col, button)
				else:
					# Para las demás celdas, agregamos los datos como texto
					item = QTableWidgetItem(str(posts.iloc[row, col]))
					self.tracked_posts.setItem(row, col, item)
	
	def start_tracker(self):
		if not self.tracker.running:
			self.tracker.start()
	
	def stop_tracker(self):
		if self.tracker.running:
			self.tracker.stop()
	
	def set_status(self, status: str, color: str = None):
		self.status_label.setText(status)
		if color:
			self.status_label.setStyleSheet(f'color: {color};')
	
	def is_level_enabled(self, level: str) -> bool:
		return self.tracker.settings.get('LOGS', level, 'bool')
	
	def add_log(
		self,
		content: str,
		level: Literal["error", "success", "info", "debug", "warning"],
		notify: bool = False
	):
		if not self.is_level_enabled(level):
			return
		
		# Diccionario con colores asociados a cada nivel de log
		colors = {
			"error": "crimson",
			"success": "lime",
			"info": "DeepSkyBlue",
			"debug": "gray",
			"warning": "gold"
		}
		
		# Crear un nuevo elemento para la lista
		log_item = q.QListWidgetItem()
		
		# Crear el widget que contendrá el log
		item_widget = q.QWidget()
		log_item_layout = q.QHBoxLayout()
		item_widget.setLayout(log_item_layout)
		
		# Formato de la hora y etiqueta
		time_str = datetime.now().strftime("%H:%M:%S")
		time_label = q.QLabel()
		time_label.setText(time_str)
		time_label.setStyleSheet('font-weight: bold;')
		log_item_layout.addWidget(time_label)
		
		# Crear la etiqueta de contenido y aplicar color
		content_label = q.QLabel()
		content_label.setText(content)
		content_label.setStyleSheet(f'color: {colors[level]}; font-weight: bold;')
		log_item_layout.addWidget(content_label, 1)
		
		# Añadir el item a la lista
		log_item.setSizeHint(item_widget.sizeHint())
		
		self.logs.addItem(log_item)
		self.logs.setItemWidget(log_item, item_widget)
		
		self.set_status(content, colors[level])
		
		if notify:
			Notification(
				'ML Tracker',
				'ML Tracker',
				content
			).show()