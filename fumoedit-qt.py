import sys
import time
from pathlib import Path
from PyQt5 import QtWidgets
from PyQt5 import uic
import fumoedit


def currenttime():
    return time.strftime('%H:%M:%S', time.localtime())

# TODO dirty file indicator
# TODO update filepath when changing date and ID

class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("WndMain.ui", self)
        self.connect_signals()
        
        self.current_post = None
        self.current_picture = None
        self.current_variant = None
        self.set_current_filepath(None)

        self.new_post()

    def connect_signals(self):
        # Actions
        self.ActionNewPost.triggered.connect(self.new_post)
        self.ActionOpenPost.triggered.connect(self.open_post)
        self.ActionSavePost.triggered.connect(self.save_post)
        # self.ActionSavePostAs.triggered.connect(self.export_post)
        self.ActionQuit.triggered.connect(self.close)

        # Post editor widgets
        self.LePostID.textEdited.connect(self.update_internal_name)
        self.DePostDate.dateChanged.connect(self.update_internal_name)
        self.CbPostCollection.currentTextChanged.connect(
            self.set_post_collection
        )

        # Picture manager widgets (pictures)
        self.TwPictures.itemSelectionChanged.connect(
            self.picture_selection_changed
        )
        self.PbPictureNew.clicked.connect(self.add_picture)
        self.PbPictureDelete.clicked.connect(self.delete_picture)

        # Picture manager widgets (variants)
        self.TwVariants.itemSelectionChanged.connect(
            self.variant_selection_changed
        )
        self.PbVariantNew.clicked.connect(self.add_variant)
        self.PbVariantDelete.clicked.connect(self.delete_variant)

    def picture_selection_changed(self):
        selected_rows = self.TwPictures.selectionModel().selectedRows()

        if len(selected_rows) > 0:
            self.select_picture(
                self.current_post.pictures[selected_rows[0].row()])
        else:
            self.deselect_picture()

    def variant_selection_changed(self):
        if self.current_picture:
            selected_rows = self.TwVariants.selectionModel().selectedRows()

            if len(selected_rows) > 0:
                self.select_variant(
                    self.current_picture.variants[selected_rows[0].row()])
            else:
                self.deselect_variant()

    # File-related methods
    def set_current_filepath(self, filepath):
        self.current_filepath = filepath

        if self.current_filepath:
            self.setWindowTitle(f"{self.current_filepath} - FumoEdit-QT")
        else:
            self.setWindowTitle(f"Unsaved - FumoEdit-QT")
    def open_post(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
        dialog.setNameFilter("Markdown files (*.md)")

        if dialog.exec():
            filepath = dialog.selectedFiles()[0]

            try:
                post = fumoedit.post_from_file(filepath)
            except Exception as e:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setWindowTitle("Opening failed")
                msgbox.setText(e.__notes__[0])
                msgbox.setIcon(QtWidgets.QMessageBox.Critical)
                msgbox.exec()
            else:
                self.load_post(post, filepath)

    def save_post(self):
        #TODO confirm if collection mismatch

        if self.validate_post():
            if not self.current_filepath:
                dialog = QtWidgets.QFileDialog(self)
                dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
                dialog.setNameFilter("Markdown files (*.md)")

                if dialog.exec():
                    self.set_current_filepath(dialog.selectedFiles()[0])
                else:
                    return

            self.current_post.id = self.LePostID.text()

            d_day = self.DePostDate.date().day()
            d_month = self.DePostDate.date().month()
            d_year = self.DePostDate.date().year()
            self.current_post.set_date(d_year, d_month, d_day)

            # Set filepath again, just in case the post's internal name has been changed
            fp = f"{fumoedit.get_folderpath(self.current_filepath)}/{self.current_post.get_filename()}"
            self.set_current_filepath(fp)

            self.current_post.title = self.LePostTitle.text()
            self.current_post.thumbnail = self.LePostThumbName.text()
            self.current_post.body = self.PtePostBody.toPlainText()

            self.save_variant()
            self.save_picture()

            fumoedit.post_to_file(
                self.current_post,
                fumoedit.get_folderpath(self.current_filepath)
            )

    # Post methods
    def new_post(self):
        # TODO in statusbar
        print(f"* Created new post at {currenttime()}")
        self.load_post(fumoedit.Post())
        self.set_post_collection("Blog")

    def load_post(self, post, filepath=None):
        self.TwMain.setCurrentIndex(0)

        self.deselect_picture()
        self.deselect_variant()

        self.current_post = post
        self.set_current_filepath(filepath)

        self.LePostID.setText(self.current_post.id)
        self.DePostDate.setDate(self.current_post.date)
        self.LePostTitle.setText(self.current_post.title)
        self.LePostThumbName.setText(self.current_post.thumbnail)
        self.PtePostBody.setPlainText(self.current_post.body)

        self.update_pictures_table(True)
        self.update_variants_table(True)

        match self.current_post.get_collection():
            case "posts":
                self.CbPostCollection.setCurrentText("Blog")
            case "artwork":
                self.CbPostCollection.setCurrentText("Artwork")
            case "walls":
                self.CbPostCollection.setCurrentText("Wallpapers")

    def update_internal_name(self):
        d_day = self.DePostDate.date().day()
        d_month = self.DePostDate.date().month()
        d_year = self.DePostDate.date().year()
        self.current_post.set_date(d_year, d_month, d_day)
        self.current_post.id = self.LePostID.text()

        self.LePostInternalName.setText(self.current_post.get_internal_name())

    def set_post_collection(self, collection):
        match collection:
            case "Blog":
                self.current_post.set_collection("posts")
            case "Artwork":
                self.current_post.set_collection("artwork")
            case "Wallpapers":
                self.current_post.set_collection("walls")

        # Enable or disable the picture manager depending on whether or not
        # the current post is a picture post
        self.TwMain.setTabEnabled(1, self.current_post.is_picturepost())

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
            msgbox.setWindowTitle("Validation failed")
            msgbox.setText(msg)
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.exec()

            return False  # Validation failed

    # Picture methods
    def update_pictures_table(self, reset):
        # If reset is on, the contents will be cleared and reinserted
        # Else, only the visible values will change
        if (reset):
            self.TwPictures.clearContents()
            self.TwPictures.setRowCount(len(self.current_post.pictures))

        for i in range(0, len(self.current_post.pictures)):
            picture = self.current_post.pictures[i]

            self.TwPictures.setItem(
                i, 0, QtWidgets.QTableWidgetItem(f"{len(picture.variants)}"))
            self.TwPictures.setItem(
                i, 1, QtWidgets.QTableWidgetItem(picture.thumbnail_name))

    def add_picture(self):
        # Add a new empty picture object to the current post
        self.current_post.new_picture()

        self.update_pictures_table(True)

    def save_picture(self):
        # Apply picture fields' values to the current picture object
        if self.current_picture:
            self.current_picture.thumbnail_name = self.LeThumbFilename.text()

            # Changing the offsets individually in the picture object
            # causes them to be "shared" across every picture
            offset = [None, None]

            if self.CbThumbCenterX.isChecked():
                offset[0] = "center"
            else:
                offset[0] = self.SbThumbX.value()

            if self.CbThumbCenterY.isChecked():
                offset[1] = "center"
            else:
                offset[1] = self.SbThumbY.value()

            self.current_picture.thumbnail_offset = offset

            print(
                f"* Saved picture {self.current_post.pictures.index(self.current_picture)} at {currenttime()}"
            )
            self.update_pictures_table(False)

    def select_picture(self, picture):
        # Set all picture fields' values to the given picture object's,
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
            self.SbThumbX.setValue(self.current_picture.thumbnail_offset[0])

        if center_y:
            self.CbThumbCenterY.setChecked(True)
            self.SbThumbY.setValue(0)
        else:
            self.CbThumbCenterY.setChecked(False)
            self.SbThumbY.setValue(self.current_picture.thumbnail_offset[1])

        self.update_variants_table(True)
        self.TwVariants.setEnabled(True)
        self.PbPictureDelete.setEnabled(True)
        self.PbVariantNew.setEnabled(True)
        self.GbPicMan2.setEnabled(True)

    def deselect_picture(self):
        # If there's already a loaded picture, save its edits beforehand
        if self.current_picture:
            self.deselect_variant()
            self.save_picture()

        # Disable all picture and variant fields
        self.current_picture = None

        self.LeThumbFilename.clear()
        self.SbThumbX.setValue(0)
        self.SbThumbY.setValue(0)
        self.CbThumbCenterX.setChecked(False)
        self.CbThumbCenterY.setChecked(False)

        self.update_variants_table(True)
        self.TwVariants.setEnabled(False)
        self.PbPictureDelete.setEnabled(False)
        self.PbVariantNew.setEnabled(False)
        self.GbPicMan2.setEnabled(False)

    def delete_picture(self):
        # Delete the selected picture object from the current post
        if self.current_picture:
            self.current_post.pictures.remove(self.current_picture)
            self.current_picture = None  # to prevent saving when deselecting the picture

        self.update_pictures_table(True)

    def validate_picture(self):
        return True

    # Picture variant methods
    def update_variants_table(self, reset):
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
        # Add a new empty variant object to the current picture
        if self.current_picture:
            self.current_picture.new_variant()
            self.update_variants_table(True)

    def save_variant(self):
        # Apply variant fields' values to the current variant object
        if self.current_picture and self.current_variant:
            self.current_variant.filename = self.LeVariantFilename.text()
            self.current_variant.label = self.LeVariantLabel.text()

            print(
                f"* Saved variant {self.current_variant.get_label()} at {currenttime()}"
            )
            self.update_variants_table(False)

    def select_variant(self, variant):
        # Set all variant fields' values to the selected variant object's
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
        # Delete the selected variant object from the current picture
        if self.current_picture and self.current_variant:
            self.current_picture.variants.remove(self.current_variant)
            self.update_variants_table(True)

    def validate_variant(self):
        return True


app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
