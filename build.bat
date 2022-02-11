pyinstaller --name="MSLibMatchMgr" -c --noconfirm --onefile --add-data="MSLibMatchmakerMainWindow.ui;." MSLibRepSniffer_GUI_main.py  
copy  MSLibMatchmakerMainWindow.ui .\dist\ /Y
