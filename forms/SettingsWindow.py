import fumoedit
from os import path
from PyQt5 import QtGui, QtWidgets, uic
from settings import *
import time
from yaml.scanner import ScannerError


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndSettings.ui", self)
        self.connect_signals()

        self.CbWrapBody.setChecked(settings["wrap_body"])
        self.CbWrapPreview.setChecked(settings["wrap_preview"])

        self.SbBodyFontSize.setValue(settings["fontsize_body"])
        self.SbPreviewFontSize.setValue(settings["fontsize_preview"])

        self.LeSitePath.setText(settings["site_path"])

        

    def connect_signals(self):
        pass

    def accept(self):
        # Override to apply settings upon pressing OK
        self.apply_settings()
        super().accept()

    def apply_settings(self):
        settings["wrap_body"] = self.CbWrapBody.isChecked()
        settings["wrap_preview"] = self.CbWrapBody.isChecked()
        settings["fontsize_body"] = int(self.SbBodyFontSize.cleanText())
        settings["fontsize_preview"] = int(self.SbPreviewFontSize.cleanText())
        
        input_path = self.LeSitePath.text()
        if path.exists(input_path):
            set_site_path(input_path)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Invalid repository path",
                f"{input_path} does not exist.\nThis setting will not be applied."
            )

        save_settings()
        
        