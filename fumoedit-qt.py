from forms.MainWindow import MainWindow
from settings import *
import sys
from PyQt5.QtWidgets import QApplication

load_settings()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
