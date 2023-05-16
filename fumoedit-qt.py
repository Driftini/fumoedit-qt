import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
import fumoedit


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("WndMain.ui", self)
        self.connect_signals()

        self.current_post = fumoedit.Post()

    def connect_signals(self):
        self.action_Save.triggered.connect(self.export_post)

    def export_post(self):
        self.current_post.id = self.LePostID.text()
        self.current_post.title = self.LePostTitle.text()
        self.current_post.thumbnail = self.LePostThumbName.text()
        self.current_post.date_day = 0
        self.current_post.date_month = 0
        self.current_post.date_year = 0
        self.current_post.body = self.PtePostBody.toPlainText()

        print(self.current_post.get_filename())
        print(self.current_post.generate())


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
