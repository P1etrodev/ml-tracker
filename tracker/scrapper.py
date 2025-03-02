from PyQt6.QtCore import QRunnable
from pandas import Series
from selenium.webdriver import Chrome
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.expected_conditions import presence_of_element_located
from selenium.webdriver.support.wait import WebDriverWait

from tracker.signals import Signals


class ProductRunnable(QRunnable):
	
	def __init__(
		self,
		index: int,
		row: Series,
		signals: Signals,
	):
		super().__init__()
		self.index = index
		self.row = row
		self.signals = signals
	
	def run(self):
		options = Options()
		options.add_argument("--headless")  # Configurar en modo headless si es necesario
		options.add_argument("--disable-gpu")  # Desactivar la GPU si es necesario
		driver = Chrome(options=options)
		
		try:
			driver.get(self.row['url'])
			
			WebDriverWait(driver, 10).until(
				presence_of_element_located(
					(By.ID, 'price')
				)
			)
			
			if 'Error!' in driver.title:
				self.signals.log.emit(
					'MercadoLibre está en mantenimiento o fuera de servicio.', 'error', True
				)
				return
			
			self.row['product'] = driver.title
			
			try:
				driver.find_element(By.ID, 'item_status_short_description_message')
				self.row['available'] = False
				self.signals.thread_finished.emit(self.row)
				return
			except:
				pass
			
			shipping_container = None
			
			try:
				shipping_container = driver.find_element(By.ID, 'buybox-form')
			except:
				try:
					shipping_container = driver.find_element(By.ID, 'shipping_summary')
				except:
					pass
			
			if shipping_container is not None:
				elements = shipping_container.find_elements(By.CLASS_NAME, 'ui-pdp-color--GREEN')
				self.row['free_ship'] = any(
					text in el.text for el in elements for text in {'Llega gratis', 'Envío gratis'}
				)
			
			price_container = driver.find_element(By.ID, 'price')
			
			try:
				self.row['currency'] = price_container.find_element(
					By.CLASS_NAME, 'andes-money-amount__currency-symbol'
				).text
			except Exception as e:
				print(e)
			
			try:
				price_element = price_container.find_element(By.CLASS_NAME,
				                                             'andes-money-amount__fraction')
				self.row['previous_price'] = self.row['current_price']
				self.row['current_price'] = float(price_element.text.replace('.', '').replace(',',
				                                                                              '.'))
			except Exception as e:
				print(e)
				self.signals.log.emit(f'Error al obtener precio.', 'error', False)
				self.row['available'] = False
			
			try:
				price_container.find_element(By.CLASS_NAME, 'andes-money-amount__discount')
				self.row['with_discount'] = True
			except:
				pass
		
		except Exception as e:
			print(e)
			self.signals.log.emit(f'General error: {e}', 'error', False)
		
		self.signals.thread_finished.emit(self.index, self.row)
		driver.quit()