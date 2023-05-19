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

    def validate_post(self):
        to_fill = []

        if len(self.LePostTitle.text()) <= 0:
            to_fill.append(self.LblPostTitle.text())

        if len(self.LePostID.text()) <= 0:
            to_fill.append(self.LblPostID.text())

        if len(self.PtePostBody.toPlainText()) <= 0:
            to_fill.append(self.LblPostBody.text())

        if len(to_fill) == 0:
            return True  # Validation successful
        else:
            msg = "The following fields haven't been filled out:"

            # TODO figure out how to use rich text
            for f in to_fill:
                msg += f"\n• {f[:-1]}"

            msgbox = QtWidgets.QMessageBox()
            msgbox.setWindowTitle("Export failed")
            msgbox.setText(msg)
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.exec()

            return False  # Validation failed

    def validate_pictures(self):
        return True

    def export_post(self):
        if self.validate_post():
            self.current_post.id = self.LePostID.text()

            d_day = self.DePostDate.date().day()
            d_month = self.DePostDate.date().month()
            d_year = self.DePostDate.date().year()
            self.current_post.set_date(d_year, d_month, d_day)

            self.current_post.title = self.LePostTitle.text()
            self.current_post.thumbnail = self.LePostThumbName.text()
            self.current_post.body = self.PtePostBody.toPlainText()

            print(self.current_post.get_filename())
            print(self.current_post.generate())


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
