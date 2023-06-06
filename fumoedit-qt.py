from forms.MainWindow import MainWindow
import sys
from PyQt5.QtWidgets import QApplication

app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
