import sys
from pathlib import Path

from PyQt6.QtCore import QObject, QThreadPool
from pandas import DataFrame, Series, read_excel
from settings_manager import SettingsManager

from tracker.scrapper import ProductRunnable
from tracker.signals import Signals


class TrackerWorker(QObject):
	
	data: DataFrame
	
	settings = SettingsManager(
		defaults={
			"GENERAL": {
				"interval": 1800,
				"track_on_startup": False,
				"max_paralell_tracking": 4
			}
		}
	)
	
	def __init__(self):
		super().__init__()
		
		self.signals = Signals()
		self.signals.thread_finished.connect(self.handle_thread_result)
		
		self.threadpool = QThreadPool()
		self.threadpool.setMaxThreadCount(self.max_paralell_tracking)
		
		base_path = Path(getattr(sys, '_MEIPASS', "."))
		self.excel_path = base_path.joinpath('./products.xlsx')
		self.load_data()
	
	@property
	def interval(self) -> int:
		return self.settings.get('GENERAL', 'interval', 'int')
	
	@interval.setter
	def interval(self, value: int):
		self.settings.set('GENERAL', 'interval', value)
	
	@property
	def max_paralell_tracking(self) -> int:
		return self.settings.get('GENERAL', 'max_paralell_tracking', 'int')
	
	@max_paralell_tracking.setter
	def max_paralell_tracking(self, value: int):
		self.settings.set('GENERAL', 'max_paralell_tracking', value)
	
	@property
	def track_on_startup(self) -> bool:
		return self.settings.get('GENERAL', 'track_on_startup', 'bool')
	
	@track_on_startup.setter
	def track_on_startup(self, value: bool):
		self.settings.set('GENERAL', 'track_on_startup', value)
	
	def load_data(self):
		if not self.excel_path.exists():
			self.data = DataFrame(
				columns=['url', 'previous_price', 'current_price', 'free_ship', 'available', 'currency',
				         'product', 'with_discount']
			)
			self.save_data()
		else:
			self.data = read_excel(self.excel_path)
			self.data['free_ship'] = self.data['free_ship'].infer_objects(copy=False)
			self.data.drop_duplicates(subset=['url'], inplace=True)
	
	def start(self):
		if self.data.empty:
			self.signals.log.emit('No hay productos configurados para trackear.', "info", True)
			return
		
		self.signals.log.emit(f'Trackeando {len(self.data)} productos...', 'info', False)
		
		self.signals.status.emit('Activo.', 'success')
		
		for index, row in self.data.iterrows():
			runnable = ProductRunnable(
				index,
				row,
				self.signals
			)
			self.threadpool.start(runnable)
		
		self.signals.status.emit('En espera.', 'warning')
		self.signals.updated.emit()
	
	def handle_thread_result(self, index: int, row: Series):
		self.data.loc[index] = row
		self.signals.updated.emit()
		self.save_data()
	
	def save_data(self):
		self.data.to_excel(self.excel_path, index=False)
	
	def stop(self):
		self.signals.status.emit('Deteniendo...', 'info')
		self.threadpool.clear()
		self.signals.status.emit('Inactivo.', 'error')