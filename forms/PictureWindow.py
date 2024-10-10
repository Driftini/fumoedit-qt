from os import path
from PyQt5 import QtWidgets, uic
from settings import *


class PictureWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndPicture.ui", self)
        self.connect_signals()

        self.LeThumbFilename.path_part_1 = lambda: settings["site_path"]
        self.LeThumbFilename.path_part_2 = lambda: self.picture.get_thumbnail_path()[1:]
        self.LeOriginalFilename.path_part_1 = lambda: settings["site_path"]
        self.LeOriginalFilename.path_part_2 = lambda: self.picture.get_original_path()[1:]

        # self.picture must be set before opening this dialog

    def connect_signals(self):
        self.LeThumbFilename.textEdited.connect(self.update_thumbnail_preview)
        self.SbThumbPos.valueChanged.connect(self.update_thumbnail_preview)

    def accept(self):
        # Override to commit changes upon pressing OK
        self.save_picture()
        super().accept()

    def save_variant(self):
        print(
            f"* Saved variant {self.current_variant.get_label()} at {currenttime()}"
        )

    def validate_picture(self):
        # TODO
        return True

    def load_picture(self):
        # Set all fields' values to self.picture's
        self.LeLabel.setText(self.picture.label)
        self.LeOriginalFilename.setText(self.picture.original_filename)
        self.LeThumbFilename.setText(self.picture.thumbnail_filename)
        self.SbThumbPos.setValue(int(self.picture.thumbnail_offset))

        if self.picture.thumbnail_offset == 50:
            self.CbThumbCenter.setChecked(True)
        else:
            self.CbThumbCenter.setChecked(False)

    def save_picture(self):
        # Apply picture fields' values to the current picture
        if self.validate_picture():
            self.picture.label = self.LeLabel.text()
            self.picture.original_filename = self.LeOriginalFilename.text()
            self.picture.thumbnail_filename = self.LeThumbFilename.text()

            if self.CbThumbCenter.isChecked():
                self.picture.thumbnail_offset = 50
            else:
                self.picture.thumbnail_offset = self.SbThumbPos.cleanText()

    def update_thumbnail_preview(self):
        # Saving the pic outside of save method is painful
        self.picture.thumbnail_filename = self.LeThumbFilename.text()
        path = self.picture.get_thumbnail_path()
        offset_percent = int(self.SbThumbPos.cleanText())

        self.GvThumbPreview.update_preview(path, offset_percent)
