import webbrowser
from datetime import datetime, timedelta
from typing import Literal

import PyQt6.QtWidgets as q
from PyQt6.QtCore import QSize, QTimer
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QSystemTrayIcon, QTableWidgetItem

from tracker.tracker import TrackerWorker
from widgets._base import CustomBaseWindow
from widgets.settings import SettingsWidget
from widgets.tray_icon import TrayIcon
from widgets.url_manager import URLManagerWidget


class MainWindow(q.QMainWindow, CustomBaseWindow):
	
	def __init__(self):
		super().__init__()
		
		self.setWindowTitle("ML Tracker")
		self.setFixedSize(QSize(800, 500))
		
		# ---------------------------------------------------
		
		self.tray_icon = TrayIcon(self)
		self.tray_icon.show_clicked.connect(self.show_window)
		
		# ---------------------------------------------------
		
		self.tracker = TrackerWorker()
		self.tracker.signals.status.connect(self.set_status)
		self.tracker.signals.log.connect(self.add_log)
		self.tracker.signals.updated.connect(self.update_ui)
		
		# ---------------------------------------------------
		
		self.url_manager_widget = URLManagerWidget(self.tracker)
		self.url_manager_widget.updated.connect(self.update_ui)
		
		self.settings_widget = SettingsWidget(self.tracker)
		
		# ---------------------------------------------------
		
		self.tracking_timer = QTimer()
		self.tracking_timer.timeout.connect(self.tracker.start)
		
		self.clock = QTimer()
		self.clock.timeout.connect(self.update_timer_display)
		self.clock.start(1000)
		
		# ---------------------------------------------------
		
		main = q.QWidget()
		main_layout = q.QVBoxLayout()
		main.setLayout(main_layout)
		
		# ---------------------------------------------------
		
		content = q.QWidget()
		content_layout = q.QVBoxLayout()
		content.setLayout(content_layout)
		main_layout.addWidget(content)
		
		# ---------------------------------------------------
		
		tabs = q.QTabWidget()
		content_layout.addWidget(tabs)
		
		# ---------------------------------------------------
		
		self.tracked_posts = q.QTableWidget()
		self.tracked_posts.setEditTriggers(q.QTableWidget.EditTrigger.NoEditTriggers)
		self.tracked_posts.verticalHeader().setVisible(False)
		tabs.addTab(self.tracked_posts, 'Publicaciones')
		
		# ---------------------------------------------------
		
		self.logs = q.QListWidget()
		tabs.addTab(self.logs, 'Logs')
		
		# ---------------------------------------------------
		
		status_bar = q.QWidget()
		status_bar_layout = q.QHBoxLayout()
		status_bar.setLayout(status_bar_layout)
		content_layout.addWidget(status_bar)
		
		self.timer_display = q.QLabel()
		self.timer_display.setStyleSheet('font-weight: bold;')
		status_bar_layout.addWidget(self.timer_display)
		
		self.status_label = q.QLabel()
		status_bar_layout.addWidget(self.status_label, 1)
		
		if not self.tracker.track_on_startup:
			self.set_status('Inactivo.', 'error')
		
		# ---------------------------------------------------
		
		menu = q.QWidget()
		menu_layout = q.QHBoxLayout()
		menu.setLayout(menu_layout)
		main_layout.addWidget(menu)
		
		self.start_button = q.QPushButton('👍🏻 Iniciar')
		self.start_button.clicked.connect(self.start_timer)
		menu_layout.addWidget(self.start_button)
		
		self.stop_button = q.QPushButton('🤚🏻 Detener')
		self.stop_button.clicked.connect(self.stop_timer)
		menu_layout.addWidget(self.stop_button)
		
		self.modify_urls_button = q.QPushButton('🔗 Modificar URLs')
		self.modify_urls_button.clicked.connect(self.url_manager_widget.show)
		menu_layout.addWidget(self.modify_urls_button)
		
		self.settings_button = q.QPushButton('⚙️ Opciones')
		self.settings_button.clicked.connect(self.settings_widget.show)
		menu_layout.addWidget(self.settings_button)
		
		# ---------------------------------------------------
		
		self.setCentralWidget(main)
		
		if self.tracker.track_on_startup:
			self.start_timer()
		
		self.update_ui()
	
	def update_ui(self):
		running = self.is_running
		
		# Buttons
		self.start_button.setEnabled(not running)
		self.stop_button.setEnabled(running)
		self.modify_urls_button.setEnabled(not running)
		self.settings_button.setEnabled(not running)
		
		# Tracked posts
		posts = self.tracker.data.copy()
		
		posts['currency'] = posts['currency'].fillna('$')
		posts['current_price'] = posts.apply(
			lambda x: f'{"⬆️" if x["previous_price"] <= x["current_price"] else "⬇️"}'
			          f' {x["currency"]} {x["current_price"]:,}', axis=1
		)
		posts['product'] = posts['product'].fillna('-')
		posts['free_ship'] = posts['free_ship'].apply(lambda x: 'Sí' if x else 'No')
		posts['available'] = posts['available'].apply(lambda x: 'Sí' if x else 'No')
		posts['with_discount'] = posts['with_discount'].apply(lambda x: 'Sí' if x else 'No')
		
		posts = posts[[
			'product',
			'current_price',
			'free_ship',
			'with_discount',
			'available',
			'url'
		]]
		
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
				column_name = posts.columns[col]
				if column_name == '':  # Verificamos si la columna es 'url'
					# Creamos un botón con el texto de la URL
					button = q.QPushButton("Ver")
					button.clicked.connect(lambda checked, url=posts.iloc[row, col]: webbrowser.open(url))
					# Establecemos el botón en la celda correspondiente
					self.tracked_posts.setCellWidget(row, col, button)
				elif column_name != 'previous_price':
					# Para las demás celdas, agregamos los datos como texto
					value = str(posts.iloc[row, col])
					item = QTableWidgetItem(value)
					
					previous_price = self.tracker.data.loc[row, 'previous_price']
					
					if value == 'Sí' or (
						column_name == 'Precio' and
						previous_price > 0 and
						previous_price > self.tracker.data.loc[row, 'current_price']
					):
						item.setForeground(QColor('lime'))
					
					elif value == 'No' or (
						column_name == 'Precio' and
						0 < previous_price < self.tracker.data.loc[row, 'current_price']
					):
						item.setForeground(QColor('crimson'))
					
					self.tracked_posts.setItem(row, col, item)
	
	def start_timer(self):
		self.tracker.start()
		if self.tracker.threadpool.activeThreadCount() > 0:
			self.tracking_timer.start(self.tracker.interval * 1000)
		self.update_ui()
	
	def stop_timer(self):
		self.tracking_timer.stop()
		self.tracker.stop()
		self.update_ui()
	
	@property
	def is_running(self):
		return self.tracking_timer.isActive()
	
	def update_timer_display(self):
		# Obtiene el tiempo restante del temporizador (en milisegundos)
		remaining = self.tracking_timer.remainingTime()
		
		# Si el tiempo restante es negativo (el temporizador ya terminó), ponlo en 0
		if remaining < 0:
			remaining = 0
		
		# Convierte el tiempo restante en milisegundos a un objeto timedelta
		time_left = timedelta(milliseconds=remaining)
		
		# Extraemos horas, minutos y segundos
		hours, remainder = divmod(time_left.seconds, 3600)
		minutes, seconds = divmod(remainder, 60)
		
		# Formateamos el tiempo como HH:MM:SS
		formatted_time = f"{hours:02}:{minutes:02}:{seconds:02}"
		
		# Muestra el tiempo formateado en el display
		self.timer_display.setText(formatted_time)
	
	def _get_level_color(self, level: str):
		colors = {
			"error": "crimson",
			"success": "lime",
			"info": "DeepSkyBlue",
			"debug": "gray",
			"warning": "gold"
		}
		return colors[level]
	
	def set_status(self, status: str, level: str = None):
		self.status_label.setText(status)
		if level:
			color = self._get_level_color(level)
			self.status_label.setStyleSheet(f'color: {color};')
	
	def add_log(
		self,
		content: str,
		level: Literal["error", "success", "info", "debug", "warning"],
		notify: bool = False
	):
		color = self._get_level_color(level)
		
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
		content_label.setStyleSheet(f'color: {color}; font-weight: bold;')
		log_item_layout.addWidget(content_label, 1)
		
		# Añadir el item a la lista
		log_item.setSizeHint(item_widget.sizeHint())
		
		self.logs.addItem(log_item)
		self.logs.setItemWidget(log_item, item_widget)
		
		if notify:
			self.notify(content)
	
	def notify(self, content: str):
		self.tray_icon.showMessage(
			"ML Tracker",
			content,
			QSystemTrayIcon.MessageIcon.Information,
			1000
		)
	
	def closeEvent(self, event):
		"""Interceptar el cierre de la ventana y minimizar a la bandeja en su lugar."""
		event.ignore()
		self.tray_icon.show()
		self.hide()
		self.notify('La aplicación está funcionando de fondo.')
	
	def show_window(self):
		"""Restaurar la ventana cuando se hace clic en el icono de la bandeja."""
		self.showNormal()
		self.activateWindow()
		self.tray_icon.hide()