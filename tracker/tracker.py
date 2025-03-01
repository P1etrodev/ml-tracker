import sys
from pathlib import Path
from time import sleep

from PyQt6.QtCore import QThread, pyqtSignal
from pandas import DataFrame, isna, read_excel
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from settings_manager import SettingsManager

options = Options()
options.add_argument('--headless=new')


class TrackerWorker(QThread):
	status: pyqtSignal = pyqtSignal(str, str, bool)
	updated: pyqtSignal = pyqtSignal()
	timer: pyqtSignal = pyqtSignal(int)
	
	running = False
	stopping = False
	driver: Chrome
	
	excel_path = Path('./products.xlsx')
	
	settings = SettingsManager(
		defaults={
			"GENERAL": {
				"interval": 1800,
				"track_on_startup": False
			},
			"LOGS": {
				"success": True,
				"info": True,
				"error": True,
				"warning": True,
				"debug": True
			}
		}
	)
	
	def __init__(self):
		super().__init__()
		
		self.sleeping_time_left = self.interval * 2
		
		if not self.excel_path.exists():
			self.data = DataFrame(
				columns=[
					'url',
					'previous_price',
					'current_price',
					'free_ship',
					'available',
					'currency',
					'product',
					'with_discount'
				]
			)
			self.save_data()
		else:
			self.data = read_excel(self.excel_path)
			self.data['free_ship'] = self.data['free_ship'].infer_objects(copy=False)
			self.data.drop_duplicates(subset=['url'], inplace=True)
			self.save_data()
		
		if self.track_on_startup:
			self.start()
	
	@property
	def interval(self) -> int:
		return self.settings.get('GENERAL', 'interval', 'int')
	
	@interval.setter
	def interval(self, value: int):
		self.settings.set('GENERAL', 'interval', value)
	
	@property
	def track_on_startup(self) -> bool:
		return self.settings.get('GENERAL', 'track_on_startup', 'bool')
	
	@track_on_startup.setter
	def track_on_startup(self, value: bool):
		self.settings.set('GENERAL', 'track_on_startup', value)
	
	def run(self):
		"""
		Main tracking loop to monitor product prices and free shipping availability.
		"""
		if self.data.empty:
			self.status.emit('No hay productos configurados para trackear.', "info", True)
			return
		
		self.status.emit('Iniciando driver...', "info", False)
		
		# Initialize WebDriver
		try:
			self.driver = Chrome(options=options)
			self.status.emit('¡Iniciado!', "info", True)
		except Exception as e:
			self.status.emit(f'Error al iniciar el WebDriver: {str(e)}', 'error', True)
			return
		
		self.running = True
		self.updated.emit()
		
		while self.running:
			num_products = self.data.shape[0]
			self.status.emit(f'Trackeando {num_products} productos...', 'info', False)
			
			# Track free shipping products
			free_mask = self.data['free_ship']
			previous_free_count = free_mask.sum()
			
			# Update product information
			self.data = self.data.apply(self.fetch_product_info, axis=1)
			new_free_count = self.data['free_ship'].sum() - previous_free_count
			
			if new_free_count > 0:
				self.status.emit(
					f'¡{new_free_count} nuevos productos con envío gratis encontrados!', "info", True
				)
			
			# Track price changes
			price_changes = self.data['current_price'] != self.data['previous_price']
			self.save_data()
			
			for _, row in self.data[price_changes].iterrows():
				price_diff = round(row['current_price'] - row['previous_price'], 2)
				change_type = "subió" if price_diff > 0 else "bajó"
				status_level = "error" if price_diff > 0 else "success"
				self.status.emit(f'El precio de {row["product"]} {change_type}.', status_level, True)
			
			self.updated.emit()
			self.status.emit('En espera...', 'info', False)
			
			# Sleep loop with controlled interruption
			self.sleeping_time_left = self.interval * 2
			while self.running and self.sleeping_time_left > 0:
				sleep(0.5)
				self.sleeping_time_left -= 0.5
		
		self.stopping = False
		self.updated.emit()
	
	def stop(self):
		self.stopping = True
		self.running = False
		self.status.emit('Deteniendo...', "info", False)
		self.updated.emit()
		if hasattr(self, "driver") and self.driver is not None:
			self.driver.quit()
			self.driver = None
		self.status.emit('Detenido.', 'info', True)
	
	def save_data(self):
		self.data.to_excel(self.excel_path, index=False)
	
	def fetch_product_info(self, row: dict) -> dict:
		"""
		Fetch product information from MercadoLibre and update row data.
		"""
		try:
			self.driver.get(row['url'])
			self.driver.implicitly_wait(1)
			
			# Check if MercadoLibre is down
			if 'Error!' in self.driver.title:
				self.status.emit('MercadoLibre está en mantenimiento o fuera de servicio.', 'error', True)
				self.stop()
			
			# Check if product is unavailable
			try:
				self.driver.find_element(By.ID, 'item_status_short_description_message')
				row['available'] = False
				return row
			except Exception:
				pass
			
			# Retrieve currency if missing
			if isna(row['currency']):
				try:
					row['currency'] = self.driver.find_element(
						By.CLASS_NAME, 'andes-money-amount__currency-symbol'
					).text
				except Exception as e:
					self.status.emit(f'Currency: {e}', 'error', False)
			
			# Retrieve product title if missing
			if isna(row['product']):
				row['product'] = self.driver.title
			
			# Check for free shipping
			try:
				buy_box = self.driver.find_element(By.ID, 'buybox-form')
				elements = buy_box.find_elements(By.CLASS_NAME, 'ui-pdp-color--GREEN')
			except Exception:
				try:
					shipping_summary = self.driver.find_element(By.ID, 'shipping_summary')
					elements = shipping_summary.find_elements(By.CLASS_NAME, 'ui-pdp-color--GREEN')
				except Exception as e:
					self.status.emit(f'Free: {e}', 'error', False)
					elements = []
			
			row['free_ship'] = any(
				text in el.text for el in elements for text in {'Llega gratis', 'Envío gratis'}
			)
			
			# Retrieve current price
			try:
				price_element = self.driver.find_element(By.CLASS_NAME, 'andes-money-amount__fraction')
				row['previous_price'] = row['current_price']
				row['current_price'] = float(price_element.text.replace('.', '').replace(',', '.'))
			except Exception as e:
				self.status.emit(f'Price: {e}', 'error', False)
				row['available'] = False
			
			# Check for discount
			try:
				price_container = self.driver.find_element(By.ID, 'price')
				price_container.find_element(By.CLASS_NAME, 'andes-money-amount__discount')
				row['with_discount'] = True
			except Exception as e:
				self.status.emit(f'Discount: {e}', 'error', False)
		
		except Exception as e:
			self.status.emit(f'General error: {e}', 'error', False)
		
		return row