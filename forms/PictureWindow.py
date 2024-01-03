from os import path
from PyQt5 import QtWidgets, uic
from settings import *


class SettingsWindow(QtWidgets.QDialog):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndPicture.ui", self)
        self.connect_signals()

    def connect_signals(self):
        pass

    def accept(self):
        # Override to commit post changes upon pressing OK
        self.apply_settings()
        super().accept()

    # Picture variant methods
    def update_variants_table(self, reset):
        # If reset is on, the contents will be cleared and reinserted
        # Else, only the visible values will change
        if self.current_picture:
            if (reset):
                self.TwVariants.clearContents()
                self.TwVariants.setRowCount(len(self.current_picture.variants))

            for i in range(0, len(self.current_picture.variants)):
                variant = self.current_picture.variants[i]

                self.TwVariants.setItem(
                    i, 0, QtWidgets.QTableWidgetItem(variant.label))
                self.TwVariants.setItem(
                    i, 1, QtWidgets.QTableWidgetItem(variant.filename))

    def add_variant(self):
        # Add a new empty variant to the current picture
        if self.current_picture:
            self.current_picture.new_variant()
            self.update_variants_table(True)

    def save_variant(self):
        # Apply variant fields' values to the current variant
        if self.current_picture and self.current_variant:
            self.current_variant.filename = self.LeVariantFilename.text()
            self.current_variant.label = self.LeVariantLabel.text()

            print(
                f"* Saved variant {self.current_variant.get_label()} at {currenttime()}"
            )
            self.update_variants_table(False)

    def select_variant(self, variant):
        # Set all variant fields' values to the selected variant's
        # If there's already a loaded variant, save its edits beforehand
        if self.current_picture:
            if self.current_variant:
                self.save_variant()

            self.current_variant = variant

            self.PbVariantDelete.setEnabled(True)
            self.LeVariantFilename.setEnabled(True)
            self.LeVariantLabel.setEnabled(True)

            self.LeVariantFilename.setText(self.current_variant.filename)
            self.LeVariantLabel.setText(self.current_variant.label)

            self.GbPicMan3.setEnabled(True)

    def deselect_variant(self):
        # If there's already a loaded variant, save its edits beforehand
        if self.current_variant:
            self.save_variant()

        # Clear and disable all variant fields
        self.current_variant = None

        self.PbVariantDelete.setEnabled(False)
        self.LeVariantFilename.setEnabled(False)
        self.LeVariantLabel.setEnabled(False)

        self.LeVariantFilename.clear()
        self.LeVariantLabel.clear()

    def delete_variant(self):
        # Delete the selected variant from the current picture
        if self.current_picture and self.current_variant:
            self.current_picture.variants.remove(self.current_variant)
            self.update_variants_table(True)

    def validate_variant(self):
        # TODO
        return True

    def validate_picture(self):
        # TODO
        return True

    def save_picture(self):
        # Apply picture fields' values to the current picture
        if self.current_picture:
            self.current_picture.thumbnail_name = self.LeThumbFilename.text()

            offset = [None, None]

            if self.CbThumbCenterX.isChecked():
                offset[0] = "center"
            else:
                offset[0] = -self.SbThumbX.value()

            if self.CbThumbCenterY.isChecked():
                offset[1] = "center"
            else:
                offset[1] = -self.SbThumbY.value()

            self.current_picture.thumbnail_offset = offset

            print(
                f"* Saved picture {self.current_post.pictures.index(self.current_picture)} at {currenttime()}"
            )
            self.update_pictures_table(False)

    def select_picture(self, picture):
        # Set all picture fields' values to the given picture's,
        # update variants table accordingly
        # If there's already a loaded picture, save its edits beforehand
        if self.current_picture:
            self.deselect_variant()
            self.save_picture()

        self.current_picture = picture

        self.LeThumbFilename.setText(self.current_picture.thumbnail_name)

        center_x = self.current_picture.thumbnail_offset[0] == "center"
        center_y = self.current_picture.thumbnail_offset[1] == "center"

        if center_x:
            self.CbThumbCenterX.setChecked(True)
            self.SbThumbX.setValue(0)
        else:
            self.CbThumbCenterX.setChecked(False)
            self.SbThumbX.setValue(-self.current_picture.thumbnail_offset[0])

        if center_y:
            self.CbThumbCenterY.setChecked(True)
            self.SbThumbY.setValue(0)
        else:
            self.CbThumbCenterY.setChecked(False)
            self.SbThumbY.setValue(-self.current_picture.thumbnail_offset[1])

        self.update_variants_table(True)
        self.TwVariants.setEnabled(True)
        self.PbPictureDelete.setEnabled(True)
        self.PbVariantNew.setEnabled(True)
        self.GbPicMan2.setEnabled(True)
        self.update_thumbnail_preview()
