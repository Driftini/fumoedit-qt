from os import path
from PyQt5 import QtWidgets


class FilenameEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.textChanged.connect(self.check_path)

    def input_path(self):
        # To override
        return

    def check_path(self):
        # Make text red if the current path doesn't exist,
        # update the tooltip to contain the absolute path

        absolute = path.abspath(self.input_path())

        if path.exists(absolute):
            self.setStyleSheet("")
        else:
            self.setStyleSheet("color: red")

        self.setToolTip(absolute)

    def setEnabled(self, bool):
        # Clear tooltip if widget gets disabled
        if not bool:
            self.setToolTip("")

        super().setEnabled(bool)
