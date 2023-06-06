import fumoedit
from os import path
from PyQt5 import QtGui, QtWidgets, uic
from settings import *
import time
from yaml.scanner import ScannerError


class PreferencesWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndPreferences.ui", self)
        self.connect_signals()

    def connect_signals(self):
        pass