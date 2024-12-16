from os import path
from PyQt5 import QtWidgets, uic
from settings import *


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndSettings.ui", self)
        self.connect_signals()

        self.LeSitePath.input_path = self.LeSitePath.text

        self.CbWrapBody.setChecked(settings["wrap_body"])
        self.CbWrapPreview.setChecked(settings["wrap_preview"])

        self.SbBodyFontSize.setValue(settings["fontsize_body"])
        self.SbPreviewFontSize.setValue(settings["fontsize_preview"])

        self.LeSitePath.setText(settings["site_path"])

    def connect_signals(self):
        self.PbBrowseSitePath.clicked.connect(self.browse_site_path)

    def accept(self):
        # Override to apply settings upon pressing OK
        self.apply_settings()
        super().accept()

    def apply_settings(self):
        settings["wrap_body"] = self.CbWrapBody.isChecked()
        settings["wrap_preview"] = self.CbWrapPreview.isChecked()
        settings["fontsize_body"] = int(self.SbBodyFontSize.cleanText())
        settings["fontsize_preview"] = int(self.SbPreviewFontSize.cleanText())

        input_path = self.LeSitePath.text()
        absolute = path.abspath(input_path)
        if path.exists(input_path):
            set_site_path(input_path)
        else:
            QtWidgets.QMessageBox.warning(
                self, "Invalid repository path",
                f"{absolute} does not exist.\nThis setting will not be applied."
            )

        save_settings()

    def browse_site_path(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec():
            self.LeSitePath.setText(dialog.selectedFiles()[0])
