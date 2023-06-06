import fumoedit
from os import path
from PyQt5 import QtGui, QtWidgets, uic
from settings import *


class FilenameEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.textChanged.connect(self.check_path)

    def path_component_1(self):
        # To override
        return " "

    def path_component_2(self):
        # To override
        return " "

    def check_path(self):
        # Make text red if the current path doesn't exist,
        # update the tooltip to contain the absolute path
        print(self.path_component_1())
        print(self.path_component_2())

        actual_path = path.join(
            self.path_component_1(), self.path_component_2()
        )
        absolute = path.abspath(actual_path)

        if path.exists(actual_path):
            self.setStyleSheet("")
        else:
            self.setStyleSheet("color: red")

        self.setToolTip(absolute)

    def setEnabled(self, bool):
        # Clear tooltip if widget gets disabled
        if not bool:
            self.setToolTip("")

        super.setEnabled(bool)
