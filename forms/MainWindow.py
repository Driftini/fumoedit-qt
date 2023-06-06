from forms.SettingsWindow import SettingsWindow
import fumoedit
from os import path
from PyQt5 import QtGui, QtWidgets, uic
import time
from yaml.scanner import ScannerError

# TODO configuration for word wrap, font size and site root
# TODO Confirmation when saving to a folder mismatching the post's collection
# TODO Confirmation when saving with a internal name that mismatches the currently open file


def currenttime():
    return time.strftime('%H:%M:%S', time.localtime())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndMain.ui", self)
        self.connect_signals()

        self.current_post = None
        self.current_picture = None
        self.current_variant = None
        self.set_current_filepath(None)
        self.dirty_file = False

        self.new_post()

    def connect_signals(self):
        # Actions
        self.ActionNewPost.triggered.connect(self.new_post)
        self.ActionOpenPost.triggered.connect(self.open_post)
        self.ActionSavePost.triggered.connect(self.save_post)
        self.ActionSavePostAs.triggered.connect(self.save_post_as)
        self.ActionSettings.triggered.connect(self.show_settings)
        self.ActionQuit.triggered.connect(self.close)

        # Post editor widgets
        self.LePostID.textEdited.connect(self.update_internal_name)
        self.DePostDate.dateChanged.connect(self.update_internal_name)
        self.CbPostCollection.currentTextChanged.connect(
            self.set_post_collection
        )
        self.PtePostBody.textChanged.connect(self.update_post_preview)

        # Picture manager widgets (pictures)
        self.TwPictures.itemSelectionChanged.connect(
            self.picture_selection_changed
        )
        self.PbPictureNew.clicked.connect(self.add_picture)
        self.PbPictureDelete.clicked.connect(self.delete_picture)
        self.LeThumbFilename.textEdited.connect(self.thumbnail_props_changed)
        self.SbThumbX.valueChanged.connect(self.thumbnail_props_changed)
        self.SbThumbY.valueChanged.connect(self.thumbnail_props_changed)
        self.CbThumbCenterX.toggled.connect(self.thumbnail_props_changed)
        self.CbThumbCenterY.toggled.connect(self.thumbnail_props_changed)

        # Picture manager widgets (variants)
        self.TwVariants.itemSelectionChanged.connect(
            self.variant_selection_changed
        )
        self.PbVariantNew.clicked.connect(self.add_variant)
        self.PbVariantDelete.clicked.connect(self.delete_variant)

        # Dirty signaling (abhorrent)
        self.LePostID.textEdited.connect(self.dirty)
        self.DePostDate.dateChanged.connect(self.dirty)
        self.CbPostCollection.currentTextChanged.connect(self.dirty)
        self.LePostTitle.textEdited.connect(self.dirty)
        self.LePostThumbName.textEdited.connect(self.dirty)
        self.PtePostBody.textChanged.connect(self.dirty)

        self.TwPictures.itemSelectionChanged.connect(self.dirty)
        self.PbPictureNew.clicked.connect(self.dirty)
        self.PbPictureDelete.clicked.connect(self.dirty)
        self.LeThumbFilename.textEdited.connect(self.dirty)
        self.SbThumbX.valueChanged.connect(self.dirty)
        self.SbThumbY.valueChanged.connect(self.dirty)
        self.CbThumbCenterX.toggled.connect(self.dirty)
        self.CbThumbCenterY.toggled.connect(self.dirty)

        self.TwVariants.itemSelectionChanged.connect(self.dirty)
        self.PbVariantNew.clicked.connect(self.dirty)
        self.PbVariantDelete.clicked.connect(self.dirty)
        self.LeVariantFilename.textEdited.connect(self.dirty)
        self.LeVariantLabel.textEdited.connect(self.dirty)

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

    def thumbnail_props_changed(self):
        if self.current_picture:
            self.update_thumbnail_preview()

    # Miscellaneous methods
    def dirty(self):
        # Tag current post as dirty, update window title to reflect so
        if not self.dirty_file:
            self.setWindowTitle(f"*{self.windowTitle()}")

        self.dirty_file = True

    def undirty(self):
        # Remove dirty tag from the current post,
        # update window title to reflect so
        if self.dirty_file and self.windowTitle()[0] == "*":
            # ^probably useless redundancy
            self.setWindowTitle(self.windowTitle()[1:])

        self.dirty_file = False

    def discard_confirmation(self):
        # If the current file is dirty, ask for
        # confirmation before possibly discarding changes
        if self.dirty_file:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setWindowTitle("Discard changes?")
            msgbox.setText(
                "There might be unsaved changes in the current post.\nDo you want to discard them?"
            )
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)
            msgbox.addButton(QtWidgets.QMessageBox.StandardButton.Discard)
            msgbox.addButton(QtWidgets.QMessageBox.StandardButton.Cancel)

            reply = msgbox.question(
                self, "Discard changes?",
                "There might be unsaved changes in the current post.\nDo you want to discard them?",
                QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel
            )

            if reply == QtWidgets.QMessageBox.StandardButton.Discard:
                return True
            else:
                return False
        return True

    def show_settings(self):
        dialog = SettingsWindow(self)
        dialog.showNormal()

    def closeEvent(self, event):
        # Override for the window's close event, prompts the user
        # for confirmation if there are unsaved changes
        if self.discard_confirmation():
            event.accept()
        else:
            event.ignore()

    # File-related methods
    def set_current_filepath(self, filepath):
        # Update the current post's filepath and
        # the window title to reflect it
        self.current_filepath = filepath

        if self.current_filepath:
            absolute = path.abspath(self.current_filepath)
            self.setWindowTitle(f"{absolute} - FumoEdit-QT")
        else:
            self.setWindowTitle(f"Unsaved - FumoEdit-QT")

    def open_post(self):
        # Load a post from a file chosen
        # via an open file dialog
        if self.discard_confirmation():
            dialog = QtWidgets.QFileDialog(self)
            dialog.setFileMode(QtWidgets.QFileDialog.ExistingFile)
            dialog.setNameFilter("Markdown files (*.md)")

            if dialog.exec():
                filepath = dialog.selectedFiles()[0]

                try:
                    post = fumoedit.post_from_file(filepath)
                except (
                    ScannerError, KeyError,
                    AttributeError, fumoedit.PostNameError
                ) as e:
                    self.open_error(filepath, e)
                else:
                    self.load_post(post, filepath)
                    self.undirty()

    def open_error(self, filepath, exception):
        # Display an error related to post opening,
        # with its relevant message.
        msg = ""
        e_type = exception.__class__

        # kinda ugly
        if e_type == ScannerError:
            msg = f"{filepath}'s front matter's syntax is invalid."
        elif e_type == KeyError or e_type == AttributeError:
            msg = f"{filepath}'s metadata and/or properties are invalid."
        elif e_type == fumoedit.PostNameError:
            msg = f"{filepath}'s name is invalid."

        # could use rich text
        msg += f" ({e_type.__name__})\n\nDetails:\n{exception}"

        QtWidgets.QMessageBox.critical(self, "Failed to open post", msg)

    def save_post_internal(self):
        # Set post properties to the GUI's fields' values,
        # NOT to be called directly
        self.current_post.id = self.LePostID.text()

        d_day = self.DePostDate.date().day()
        d_month = self.DePostDate.date().month()
        d_year = self.DePostDate.date().year()
        self.current_post.set_date(d_year, d_month, d_day)

        # Set filepath again, just in case
        # the post's internal name has been changed
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

        self.undirty()

    def save_post(self):
        # Immediately save the current post if it already
        # has a filepath, otherwise let the user choose a
        # save directory.
        if self.validate_post():
            if not self.current_filepath:
                self.save_post_as()
            else:
                self.save_post_internal()

    def save_post_as(self):
        # Present a dialog to choose the save directory,
        # then save the current post
        if self.validate_post():
            dialog = QtWidgets.QFileDialog(self)
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
            dialog.setNameFilter("Markdown files (*.md)")

            if dialog.exec():
                self.set_current_filepath(dialog.selectedFiles()[0])
                self.save_post_internal()

    # Post methods
    def new_post(self):
        # Load a blank post in the Blog collection
        if self.discard_confirmation():
            self.load_post(fumoedit.Post())
            self.set_post_collection("Blog")
            self.undirty()
            print(f"* Created new post at {currenttime()}")

    def load_post(self, post, filepath=None):
        # Brings focus to the Post Editor and fills in every field
        # of the GUI with the given post's properties
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

        self.update_internal_name()
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
        # Set the current post's collection
        # using the latters' "pretty names"
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

    def update_post_preview(self):
        # Update the Markdown preview of the post body, while retaining
        # the old scrollbar position unless autoscroll has been enabled.
        old_scrollpos_x = self.TePostBodyPreview.horizontalScrollBar().value()
        old_scrollpos_y = self.TePostBodyPreview.verticalScrollBar().value()

        self.TePostBodyPreview.setMarkdown(self.PtePostBody.toPlainText())

        if self.CbPostPreviewAutoscroll.isChecked():
            self.TePostBodyPreview.horizontalScrollBar().setValue(old_scrollpos_x)
            self.TePostBodyPreview.verticalScrollBar().setValue(
                self.TePostBodyPreview.maximumHeight()
            )
        else:
            self.TePostBodyPreview.horizontalScrollBar().setValue(old_scrollpos_x)
            self.TePostBodyPreview.verticalScrollBar().setValue(old_scrollpos_y)

    def validate_post(self):
        # Post validation conditions:
        # Has title, has ID, has body
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

            for f in to_fill:
                msg += f"\n• {f[:-1]}"

            QtWidgets.QMessageBox.critical(
                self, "Validation failed", msg
            )

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

    def update_thumbnail_preview(self):
        # Update the picture in the thumbnail preview box,
        # while applying offsets from the relevant fields

        # Saving the pic outside of save method is painful
        self.current_picture.thumbnail_name = self.LeThumbFilename.text()
        absolute = path.abspath(self.current_picture.get_thumbnail_path())

        # I don't think I should instance a new scene every time
        scene = QtWidgets.QGraphicsScene()

        # If the file exists...
        if path.exists(absolute):
            pixmap = QtGui.QPixmap(absolute)
            scene.addPixmap(pixmap)
            self.GvThumbPreview.setScene(scene)

            self.LeThumbFilename.setStyleSheet("")

            # Prepare offsets
            offset_x = 0
            offset_y = 0

            if self.CbThumbCenterX.isChecked():
                offset_x = pixmap.width() / 2
                offset_x -= self.GvThumbPreview.width() / 2
            else:
                offset_x = self.SbThumbX.cleanText()

            if self.CbThumbCenterY.isChecked():
                offset_y = pixmap.height() / 2
                offset_y -= self.GvThumbPreview.height() / 2
            else:
                offset_y = self.SbThumbY.cleanText()

            # Apply offsets
            self.GvThumbPreview.horizontalScrollBar().setValue(int(offset_x))
            self.GvThumbPreview.verticalScrollBar().setValue(int(offset_y))
        else:
            self.GvThumbPreview.setScene(scene)
            self.LeThumbFilename.setStyleSheet("color: red")

    def add_picture(self):
        # Add a new empty picture to the current post
        self.current_post.new_picture()

        self.update_pictures_table(True)

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
        # Delete the selected picture from the current post
        if self.current_picture:
            self.current_post.pictures.remove(self.current_picture)
            self.current_picture = None  # to prevent saving when deselecting the picture

        self.update_pictures_table(True)

    def validate_picture(self):
        # TODO
        return True

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
