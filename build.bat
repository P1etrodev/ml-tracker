pyinstaller.exe --noconsole ^
	--icon=icon.ico ^
	--name="ML Tracker" ^
	--add-data "Darkeum.qss;." ^
	--add-data "icon.ico;." ^
	--noconfirm ^
	main.py