from os import path
from PyQt5 import QtWidgets, uic
from settings import *


class PictureWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndPicture.ui", self)
        self.connect_signals()

        # self.picture must be set before opening this dialog

    def connect_signals(self):
        pass

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
        # Update the picture in the thumbnail preview box,
        # while applying offsets from the relevant fields

        # I don't think I should instance a new scene every time
        scene = QtWidgets.QGraphicsScene()

        if self.current_picture:
            # Saving the pic outside of save method is painful
            self.current_picture.thumbnail_name = self.LeThumbFilename.text()

            actual_path = path.join(
                settings["site_path"],
                self.current_picture.get_thumbnail_path()[1:]
            )
            absolute = path.abspath(actual_path)

            # If the file exists...
            if path.exists(absolute):
                pixmap = QtGui.QPixmap(absolute)
                scene.addPixmap(pixmap)
                self.GvPicturePreview.setScene(scene)

                # Prepare offsets
                offset_x = 0
                offset_y = 0

                if self.CbThumbCenterX.isChecked():
                    offset_x = pixmap.width() / 2
                    offset_x -= self.GvPicturePreview.width() / 2
                else:
                    offset_x = self.SbThumbX.cleanText()

                if self.CbThumbCenterY.isChecked():
                    offset_y = pixmap.height() / 2
                    offset_y -= self.GvPicturePreview.height() / 2
                else:
                    offset_y = self.SbThumbY.cleanText()

                # Apply offsets
                self.GvPicturePreview.horizontalScrollBar().setValue(int(offset_x))
                self.GvPicturePreview.verticalScrollBar().setValue(int(offset_y))

                return

        # This is only reached if the file doesn't exist
        # or if there's no selected picture
        self.GvPicturePreview.setScene(scene)
