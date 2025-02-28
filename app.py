import sys
from pathlib import Path
from threading import Thread
from time import sleep

from pandas import DataFrame, read_excel
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from winotify import Notification
from settings_manager import SettingsManager
from atexit import register

options = Options()
options.add_argument('--headless=new')


class App:
	excel_path = Path('./products.xlsx')
	driver: Chrome
	settings = SettingsManager(
		defaults={
			"GENERAL": {
				"interval": 1800,
				"save_to_excel": False,
				"track_on_startup": False,
			}
		}
	)
	
	data: DataFrame
	main_thread: Thread
	running = False
	
	def __init__(self):
		# Si no existe el archivo Excel, crea uno nuevo
		if not self.excel_path.exists():
			self.data = DataFrame(
				columns=[
					'url',
					'previous_price',
					'current_price',
					'free_ship',
					'available',
					'currency',
					'product'
				]
			)
		else:
			self.data = read_excel(self.excel_path)
			
			# Rellena los valores faltantes en la columna 'free_ship'
			self.data['free_ship'] = self.data['free_ship'].infer_objects(copy=False)
			
			# Elimina todas las filas duplicadas basadas en la columna 'url'
			self.data.drop_duplicates(subset=['url'], inplace=True)  # Mantiene solo URLs únicas
		
		# Llama al método que verifica el estado de las URLs
		if self.settings.get('GENERAL', 'track_on_startup', 'bool'):
			self.start_loop()
	
	@classmethod
	def notify(cls, title: str, msg: str):
		noti = Notification(
			'ML Tracker',
			title,
			msg
		)
		noti.show()
	
	def start_loop(self):
		self.startup_driver()
		if self.data.empty:
			self.notify(
				'Error', 'Todavía no configuraste ningún link para trackear. El programa se '
				         'cerrará.'
			)
			self.stop_loop()
			return
		self.running = True
		self.main_thread = Thread(target=self.main_loop, daemon=True)
		self.main_thread.start()
	
	def stop_loop(self):
		self.running = False
		self.main_thread = None
		Thread(target=self.close_driver).start()
	
	@classmethod
	def startup_driver(cls):
		cls.driver = Chrome(options=options)
	
	@classmethod
	def close_driver(cls):
		"""Properly closes the Selenium driver when the program exits."""
		if cls.driver:
			cls.driver.quit()
			cls.driver = None
	
	def set_interval(self, interval: int):
		self.settings.set('GENERAL', 'interval', interval)
	
	@property
	def interval(self) -> int:
		return self.settings.get('GENERAL', 'interval', 'int')
	
	def main_loop(self):
		
		# Ejecuta un ciclo infinito para revisar el estado de las URLs
		free_mask = self.data['free_ship'] == True
		
		while self.running:
			# Número de productos con envío gratis antes de la actualización
			previous_free = self.data[free_mask].shape[0]
			
			# Aplicar la función check_status a cada fila
			self.data = self.data.apply(self.fetch_product_info, axis=1)
			
			# Número de productos con envío gratis después de la actualización
			new_free = self.data[free_mask].shape[0] - previous_free
			
			# Verificar si se encontraron nuevos productos con envío gratis
			if new_free > 0:
				self.notify(
					'Actualización',
					f'¡Se encontraron {new_free} nuevos productos con envío gratis!'
				)
			
			# Verificar cambios en los precios
			price_changes = (
				self.data['current_price'] != self.data['previous_price']
			)
			
			if self.settings.get('GENERAL', 'save_to_excel', "bool"):
				self.data.to_excel(self.excel_path, index=False)
			
			if price_changes.any():
				changed_products = self.data[price_changes]
				for index, row in changed_products.iterrows():
					# Calcular la diferencia de precio
					price_difference = row["current_price"] - row["previous_price"]
					price_difference = round(price_difference, 2)  # Redondear la diferencia a 2 decimales
					
					# Determinar si el precio ha subido o bajado
					price_change_type = "subió" if price_difference > 0 else "bajó"
					
					# Notificación de cambio de precio
					self.notify(
						'Cambio de precio',
						f'El precio de {row["product"]} {price_change_type} a '
						f'{row["currency"]}{row["current_price"]} '
						f'({row["currency"]}{price_difference})'
					)
			
			# Dormir por un segundo antes de volver a revisar
			sleep(self.settings.get('GENERAL', 'interval', "int"))
	
	@classmethod
	def fetch_product_info(cls, row: dict) -> dict:
		try:
			# Cargar la página solo una vez
			cls.driver.get(row['url'])
			cls.driver.implicitly_wait(1)
			
			if 'Error!' in cls.driver.title:
				cls.notify(
					'Error',
					'MercadoLibre está en mantenimiento, o sus servidores no están funcionando.'
				)
				sys.exit()
			
			try:
				if row['currency'] is None:
					currency_element = cls.driver.find_element(
						By.CLASS_NAME, 'andes-money-amount__currency-symbol'
					)
					row['currency'] = currency_element.text
				
				if row['product'] is None:
					row['product'] = cls.driver.title
				
				# Check free shipment
				try:
					buy_box = cls.driver.find_element(By.ID, 'buybox-form')
					elements = buy_box.find_elements(By.CLASS_NAME, 'ui-pdp-color--GREEN')
					free_texts = {'Llega gratis', 'Envío gratis'}
					for el in elements:
						if any(free_text in el.text for free_text in free_texts):
							row['free_ship'] = True
				except:
					pass
				
				try:
					# Get price
					current_price_element = cls.driver.find_element(
						By.CLASS_NAME, 'ui-pdp-price__second-line'
						)
					price_element = current_price_element.find_element(
						By.CLASS_NAME, 'andes-money-amount__fraction'
					)
					row['previous_price'] = row['current_price']
					price = price_element.text.replace('.', '')
					row['current_price'] = float(price.replace(',', '.'))
				except:
					row['available'] = False
			
			except Exception as e:
				print(e)
			
			return row
		except:
			return row


register(App.close_driver)