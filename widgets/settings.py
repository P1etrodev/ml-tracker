import PyQt6.QtWidgets as q
from PyQt6.QtCore import Qt

from tracker import TrackerWorker
from ._base import CustomBaseWindow


class SettingsWidget(CustomBaseWindow):
	
	def __init__(self, tracker: TrackerWorker):
		super().__init__()
		
		self.tracker = tracker
		
		self.setGeometry(100, 100, 300, 200)
		self.setWindowTitle("Opciones")
		
		main_layout = q.QVBoxLayout()
		self.setLayout(main_layout)
		
		# General box
		
		general = q.QGroupBox("⚙️ General")
		main_layout.addWidget(general)
		
		general_layout = q.QVBoxLayout()
		general.setLayout(general_layout)
		
		self.track_on_startup_checkbox = q.QCheckBox('Trackear al inicio')
		self.track_on_startup_checkbox.setChecked(self.tracker.track_on_startup)
		self.track_on_startup_checkbox.stateChanged.connect(self.set_track_on_startup)
		general_layout.addWidget(self.track_on_startup_checkbox)
		
		# Interval box
		interval_box = q.QGroupBox("🕛 Intervalo")
		main_layout.addWidget(interval_box)
		
		interval_box_layout = q.QVBoxLayout()
		interval_box.setLayout(interval_box_layout)
		
		choice_1 = q.QRadioButton("15 minutos")
		choice_1.setChecked(self.tracker.interval == 900)
		choice_1.clicked.connect(lambda: self.set_interval(900))
		interval_box_layout.addWidget(choice_1)
		
		choice_2 = q.QRadioButton("30 minutos")
		choice_2.setChecked(self.tracker.interval == 1800)
		choice_2.clicked.connect(lambda: self.set_interval(1800))
		interval_box_layout.addWidget(choice_2)
		
		choice_3 = q.QRadioButton("1 hora")
		choice_3.setChecked(self.tracker.interval == 3600)
		choice_3.clicked.connect(lambda: self.set_interval(3600))
		interval_box_layout.addWidget(choice_3)
		
		choice_4 = q.QRadioButton("2 horas")
		choice_4.setChecked(self.tracker.interval == 7200)
		choice_4.clicked.connect(lambda: self.set_interval(7200))
		interval_box_layout.addWidget(choice_4)
		
		# Log levels
		log_levels = q.QGroupBox("📜 Logs")
		main_layout.addWidget(log_levels)
		
		log_levels_layout = q.QVBoxLayout()
		log_levels.setLayout(log_levels_layout)
		
		success_checkbox = q.QCheckBox('Success')
		success_checkbox.setChecked(self.tracker.settings.get('LOGS', 'success', 'bool'))
		success_checkbox.checkStateChanged.connect(
			lambda state: self.set_log_level('success', state)
		)
		log_levels_layout.addWidget(success_checkbox)
		
		warning_checkbox = q.QCheckBox('Warning')
		warning_checkbox.setChecked(self.tracker.settings.get('LOGS', 'warning', 'bool'))
		warning_checkbox.checkStateChanged.connect(
			lambda state: self.set_log_level('warning', state)
		)
		log_levels_layout.addWidget(warning_checkbox)
		
		error_checkbox = q.QCheckBox('Error')
		error_checkbox.setChecked(self.tracker.settings.get('LOGS', 'error', 'bool'))
		error_checkbox.checkStateChanged.connect(
			lambda state: self.set_log_level('error', state)
		)
		log_levels_layout.addWidget(error_checkbox)
		
		info_checkbox = q.QCheckBox('Info')
		info_checkbox.setChecked(self.tracker.settings.get('LOGS', 'info', 'bool'))
		info_checkbox.checkStateChanged.connect(
			lambda state: self.set_log_level('info', state)
		)
		log_levels_layout.addWidget(info_checkbox)
		
		debug_checkbox = q.QCheckBox('Debug')
		debug_checkbox.setChecked(self.tracker.settings.get('LOGS', 'debug', 'bool'))
		debug_checkbox.checkStateChanged.connect(
			lambda state: self.set_log_level('debug', state)
		)
		log_levels_layout.addWidget(debug_checkbox)
	
	def set_interval(self, interval: int):
		self.tracker.interval = interval
	
	def set_track_on_startup(self):
		self.tracker.track_on_startup = self.track_on_startup_checkbox.isChecked()
	
	def set_log_level(self, level: str, state: Qt.CheckState):
		self.tracker.settings.set('LOGS', level, state == Qt.CheckState.Checked)