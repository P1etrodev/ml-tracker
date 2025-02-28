import pystray as ps
from PIL import Image

from app import App

with Image.open(r"C:\Users\Pietro\Pictures\Screenshots\Screenshot 2025-02-27 012740.png") as image:
	app = App()
	
	
	def on_close(_icon: ps.Icon):
		_icon.stop()
	
	
	icon = ps.Icon(
		'ML Tracker',
		icon=image,
		menu=ps.Menu(
			ps.MenuItem(
				"Iniciar",
				app.start_loop,
				enabled=lambda item: app.running == False
			),
			ps.MenuItem(
				"Detener",
				app.stop_loop,
				enabled=lambda item: app.running == True
			),
			ps.MenuItem(
				'Opciones',
				ps.Menu(
					ps.MenuItem(
						"Iniciar al abrir",
						checked=lambda item: app.settings.get('GENERAL', 'track_on_startup', 'bool'),
						action=lambda item: app.settings.set(
							'GENERAL', 'track_on_startup',
							not app.settings.get('GENERAL', 'track_on_startup', 'bool')
						)
					),
					ps.MenuItem(
						"Guardar en Excel",
						checked=lambda item: app.settings.get('GENERAL', 'save_to_excel', 'bool'),
						action=lambda item: app.settings.set(
							'GENERAL', 'save_to_excel',
							not app.settings.get('GENERAL', 'save_to_excel', 'bool')
						)
					),
					ps.MenuItem(
						'Intervalo',
						ps.Menu(
							ps.MenuItem(
								'120 minutos',
								lambda item: app.set_interval(7200),
								checked=lambda item: app.interval == 7200,
								radio=True
							),
							ps.MenuItem(
								'60 minutos',
								lambda item: app.set_interval(3600),
								checked=lambda item: app.interval == 3600,
								radio=True
							),
							ps.MenuItem(
								'30 minutos',
								lambda item: app.set_interval(1800),
								checked=lambda item: app.interval == 1800,
								radio=True
							),
							ps.MenuItem(
								'15 minutos',
								lambda item: app.set_interval(900),
								checked=lambda item: app.interval == 900,
								radio=True
							),
						)
					)
				)
			),
			ps.MenuItem("Cerrar", on_close)
		)
	)
	
	icon.run()