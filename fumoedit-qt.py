from forms.MainWindow import MainWindow
from forms.PostWindow import PostWindow
from settings import *
import sys
from PyQt5.QtWidgets import QApplication

load_settings()

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
