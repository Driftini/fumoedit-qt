from copy import deepcopy
from datetime import date
from forms.SettingsWindow import SettingsWindow
from forms.PictureWindow import PictureWindow
import fumoedit
from os import path
from PyQt5 import QtGui, QtWidgets, uic
from PyQt5.QtCore import Qt
from settings import *
import time
from yaml.scanner import ScannerError


def currenttime():
    return time.strftime('%H:%M:%S', time.localtime())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndMain.ui", self)
        self.connect_signals()

        self.check_settings()

        self.current_post = None
        self.current_picture = None
        self.set_current_filepath(None)
        self.dirty_file = False

        self.new_post()

        self.TwEditors.setCurrentIndex(1)

    def connect_signals(self):
        # Actions
        self.ActionNewPost.triggered.connect(self.new_post)
        self.ActionOpenPost.triggered.connect(self.open_post)
        self.ActionSavePost.triggered.connect(self.save_post)
        self.ActionSavePostAs.triggered.connect(self.save_post_as)
        self.ActionSettings.triggered.connect(self.show_settings)
        self.ActionQuit.triggered.connect(self.close)

        # Post editor widgets
        self.LeID.textEdited.connect(self.update_internal_name)
        self.DeDate.dateChanged.connect(self.update_internal_name)
        self.CbCollection.currentTextChanged.connect(
            self.set_post_collection
        )
        # textEdited is sent before textChanged, which
        # is what FilenameEdit uses for checks
        self.LeThumbName.textEdited.connect(self.post_thumbnail_changed)
        self.PteBody.textChanged.connect(self.update_post_preview)
        self.TeBodyPreview.wheelEvent = self.post_preview_wheeloverride

        # Picture manager widgets (pictures)
        self.TwPictures.itemSelectionChanged.connect(
            self.picture_selection_changed
        )
        self.PbPictureAdd.clicked.connect(self.add_picture)
        self.PbPictureEdit.clicked.connect(self.open_picture)
        self.PbPictureDelete.clicked.connect(self.delete_picture)

        # Dirty signaling (abhorrent)
        self.LeID.textEdited.connect(self.dirty)
        self.DeDate.dateChanged.connect(self.dirty)
        self.CbCollection.currentTextChanged.connect(self.dirty)
        self.LeTitle.textEdited.connect(self.dirty)
        self.LeThumbName.textEdited.connect(self.dirty)
        self.LeTags.textEdited.connect(self.dirty)
        self.PteBody.textChanged.connect(self.dirty)

        self.PbPictureAdd.clicked.connect(self.dirty)
        self.PbPictureEdit.clicked.connect(self.dirty)
        self.PbPictureDelete.clicked.connect(self.dirty)

    # Dirty file signaling
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

    # Close confirmations
    def discard_confirmation(self):
        # If the current file is dirty, ask for
        # confirmation before continuing
        if self.dirty_file:
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)

            reply = msgbox.question(
                self, "Discard changes?",
                "There might be unsaved changes in the current post.\nDo you want to discard them?",
                QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel
            )

            return reply == QtWidgets.QMessageBox.StandardButton.Discard
        # Continue automatically if the file isn't dirty
        return True

    def overwrite_confirmation(self, filepath):
        # If the given filepath exists, ask for
        # confirmation before continuing
        if path.exists(filepath):
            msgbox = QtWidgets.QMessageBox()
            msgbox.setIcon(QtWidgets.QMessageBox.Warning)

            reply = msgbox.question(
                self, "Overwrite file?",
                "The selected path already exists.\nDo you want to overwrite it?",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                QtWidgets.QMessageBox.Cancel
            )

            return reply == QtWidgets.QMessageBox.StandardButton.Yes
        # Continue automatically if the filepath doesn't exist
        return True

    def internal_name_mismatch_confirmation(self):
        # If there's a mismatch between the current post's collection
        # and the folder it's being saved into, ask for
        # confirmation before continuing
        if self.current_filepath:
            i_n = self.current_post.get_internal_name()
            last_i_n = path.basename(self.current_filepath)[:-3]

            if i_n != last_i_n:
                msgbox = QtWidgets.QMessageBox()
                msgbox.setIcon(QtWidgets.QMessageBox.Warning)


                reply = msgbox.question(
                    self, "Internal name mismatch",
                    f"This post's internal name has been changed from \"{last_i_n}\" to \"{i_n}\".\nSave with the new internal name?",
                    QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
                    QtWidgets.QMessageBox.Cancel
                )

                return reply == QtWidgets.QMessageBox.StandardButton.Yes
        # Continue automatically if there's no internal name mismatch
        # or if the post is being saved for the first time
        return True

    # Settings-related methods
    def show_settings(self):
        dialog = SettingsWindow(self)
        if dialog.exec():
            self.check_settings()

    def check_settings(self):
        # Read settings and configure widgets according to them
        if settings["wrap_body"]:
            self.PteBody.setLineWrapMode(
                QtWidgets.QPlainTextEdit.LineWrapMode.WidgetWidth
            )
        else:
            self.PteBody.setLineWrapMode(
                QtWidgets.QPlainTextEdit.LineWrapMode.NoWrap
            )
        body_font = self.PteBody.font()
        body_font.setPointSize(settings["fontsize_body"])
        self.PteBody.setFont(body_font)

        if settings["wrap_preview"]:
            self.TeBodyPreview.setLineWrapMode(
                QtWidgets.QTextEdit.LineWrapMode.WidgetWidth
            )
        else:
            self.TeBodyPreview.setLineWrapMode(
                QtWidgets.QTextEdit.LineWrapMode.NoWrap
            )
        preview_font = self.TeBodyPreview.font()
        preview_font.setPointSize(settings["fontsize_preview"])
        self.TeBodyPreview.setFont(preview_font)

    def get_thumb_path_wrapper(self):
        selection_index = self.get_selected_pictureindex()

        if selection_index >= 0:
            return self.current_post.pictures[selection_index].get_thumbnail_path()[1:]
        else:
            return ""

    # Collection name conversions
    def collection_to_display_name(self, collection_name):
        match collection_name:
            case "posts":
                return "Blog"
            case "walls":
                return "Wallpapers"
            case _:
                return collection_name.capitalize()

    def display_to_collection_name(self, display_name):
        match display_name:
            case "Blog":
                return "posts"
            case "Wallpapers":
                return "walls"
            case _:
                return display_name.lower()

    # Misc. event overrides
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
        msg += f" ({e_type.__name__})"

        QtWidgets.QMessageBox.critical(self, "Failed to open post", msg)

    def save_post_internal(self, folderpath):
        # Set post properties to the GUI's fields' values,
        # NOT to be called directly

        if self.current_filepath:
            # If the current post has been saved before,
            # perform internal name check...
            check_successful = self.internal_name_mismatch_confirmation()
        else:
            # ...otherwise, don't perform any checks and save right away
            check_successful = True

        if check_successful:
            self.current_post.id = self.LeID.text()

            d_day = self.DeDate.date().day()
            d_month = self.DeDate.date().month()
            d_year = self.DeDate.date().year()
            self.current_post.set_date(d_year, d_month, d_day)

            # Set filepath again, just in case
            # the post's internal name has been changed
            fp = f"{folderpath}/{self.current_post.get_filename()}"
            self.set_current_filepath(fp)

            self.current_post.title = self.LeTitle.text()
            self.current_post.priority_thumbnail = self.LeThumbName.text()
            self.current_post.body = self.PteBody.toPlainText()

            self.save_tags()

            fumoedit.post_to_file(
                self.current_post,
                path.dirname(self.current_filepath)
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
                folderpath = path.dirname(self.current_filepath)
                self.save_post_internal(folderpath)

    def save_post_as(self):
        # Present a dialog to choose the save directory,
        # then save the current post
        if self.validate_post():
            dialog = QtWidgets.QFileDialog(self)
            dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)

            if dialog.exec():
                # Proper filepath will be set by save_post_internal,
                # "placeholder" is appended so save_post_internal doesn't
                # shave off the directory name from the filepath
                # (which would actually point to a folder)
                folderpath = dialog.selectedFiles()[0]
                filepath = f"{folderpath}/{self.current_post.get_filename()}"
                if self.overwrite_confirmation(filepath):
                    self.save_post_internal(folderpath)

    # Post methods
    def new_post(self):
        # Load a blank post in the Blog collection
        if self.discard_confirmation():
            self.load_post(fumoedit.Post())
            self.set_post_collection("Blog")
            self.undirty()
            print(f"* Created new post at {currenttime()}")

    def load_post(self, post, filepath=None):
        # Brings focus to the Body tab and fills in every field
        # of the GUI with the given post's properties
        self.TwEditors.setCurrentIndex(0)

        self.current_post = post
        self.set_current_filepath(filepath)

        self.LeID.setText(self.current_post.id)
        self.DeDate.setDate(self.current_post.date)
        self.LeTitle.setText(self.current_post.title)
        self.LeThumbName.setText(self.current_post.priority_thumbnail)
        self.load_tags()
        self.PteBody.setPlainText(self.current_post.body)

        self.update_internal_name()
        self.update_pictures_table(True)
        self.picture_selection_changed()  # to update buttons' status

        self.CbCollection.setCurrentText(
            self.collection_to_display_name(self.current_post.get_collection())
        )

    def update_internal_name(self):
        d_day = self.DeDate.date().day()
        d_month = self.DeDate.date().month()
        d_year = self.DeDate.date().year()
        self.current_post.set_date(d_year, d_month, d_day)
        self.current_post.id = self.LeID.text()

        self.LeInternalName.setText(self.current_post.get_internal_name())

    def set_post_collection(self, collection):
        # Set the current post's collection
        # using the latters' "pretty names"
        self.current_post.set_collection(
            self.display_to_collection_name(collection)
        )

        # Enable or disable the picture manager depending on whether or not
        # the current post is a picture post
        self.TwEditors.setTabEnabled(1, self.current_post.is_picturepost())

    def update_post_preview(self):
        # Update the Markdown preview of the post body, while retaining
        # the old scrollbar position unless autoscroll has been enabled.
        old_scrollpos_x = self.TeBodyPreview.horizontalScrollBar().value()
        old_scrollpos_y = self.TeBodyPreview.verticalScrollBar().value()

        self.TeBodyPreview.setMarkdown(self.PteBody.toPlainText())

        if self.CbBodyPreviewAutoscroll.isChecked():
            self.TeBodyPreview.horizontalScrollBar().setValue(old_scrollpos_x)
            self.TeBodyPreview.verticalScrollBar().setValue(
                self.TeBodyPreview.maximumHeight()
            )
        else:
            self.TeBodyPreview.horizontalScrollBar().setValue(old_scrollpos_x)
            self.TeBodyPreview.verticalScrollBar().setValue(old_scrollpos_y)

    def post_preview_wheeloverride(self, event):
        # Prevent manually zooming the post body preview,
        # font size can be set in the settings
        if (
            event.modifiers() & Qt.KeyboardModifier.ControlModifier
        ) != Qt.KeyboardModifier.ControlModifier:
            QtWidgets.QTextEdit.wheelEvent(self.TeBodyPreview, event)

    def post_thumbnail_changed(self):
        self.current_post.priority_thumbnail = self.LeThumbName.text()

    def validate_post(self):
        # Post validation conditions:
        # Has title, has ID, has body, tags don't start/end with comma (TODO)
        to_fill = []

        if len(self.LeTitle.text()) <= 0:
            to_fill.append(self.LblTitle.text())

        if len(self.LeID.text()) <= 0:
            to_fill.append(self.LblID.text())

        if len(self.PteBody.toPlainText()) <= 0:
            to_fill.append(self.LblBody.text())

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

    # Tag methods
    def load_tags(self):
        # Fill out the tags field with the post's tags, comma-separated
        content = ""

        for t in self.current_post.tags:
            if self.current_post.tags.index(t) != 0:
                content += ", "
            content += t

        self.LeTags.setText(content)

    def save_tags(self):
        # Divide the content of the tags field into individual tags
        # and save them to the current post
        tags = self.LeTags.text().split(",")

        for t in tags:
            i = tags.index(t)
            tags[i] = t.strip()

        self.current_post.tags = tags

    # Picture methods
    def update_pictures_table(self, reset):
        # If reset is on, the contents will be cleared and reinserted
        # Else, only the visible values will change (so selection isn't lost)
        if (reset):
            self.TwPictures.clearContents()
            self.TwPictures.setRowCount(len(self.current_post.pictures))

        for i in range(0, len(self.current_post.pictures)):
            picture = self.current_post.pictures[i]

            self.TwPictures.setItem(
                i, 0, QtWidgets.QTableWidgetItem(picture.get_label()))
            self.TwPictures.setItem(
                i, 1, QtWidgets.QTableWidgetItem(picture.original_filename))

        self.update_thumbnail_preview()

    def get_selected_pictureindex(self):
        selected_rows = self.TwPictures.selectionModel().selectedRows()

        if len(selected_rows) > 0:
            return selected_rows[0].row()
        else:
            return -1

    def picture_selection_changed(self):
        if self.get_selected_pictureindex() >= 0:
            self.PbPictureEdit.setDisabled(False)
            self.PbPictureDelete.setDisabled(False)
        else:
            self.PbPictureEdit.setDisabled(True)
            self.PbPictureDelete.setDisabled(True)

        self.update_thumbnail_preview()

    def update_thumbnail_preview(self):
        path = ""
        offset_percent = 0

        selected_index = self.get_selected_pictureindex()
        if selected_index >= 0:
            picture = self.current_post.pictures[selected_index]

            path = picture.get_thumbnail_path()
            offset_percent = int(picture.thumbnail_offset)

        self.GvPicturePreview.update_preview(path, offset_percent)

    def add_picture(self):
        # Add a new picture to the current post through the Picture Editor
        temp = deepcopy(self.current_post)

        dialog = PictureWindow(self)
        dialog.picture = temp.new_picture()
        dialog.load_picture()  # eugh
        if dialog.exec() and dialog.result():
            self.current_post = temp
            self.update_pictures_table(True)

    def open_picture(self):
        # Open the selected picture from the current post through the Picture Editor
        selected_index = self.get_selected_pictureindex()
        temp = deepcopy(self.current_post.pictures[selected_index])

        dialog = PictureWindow(self)
        dialog.picture = temp
        dialog.load_picture()  # eugh
        if dialog.exec() and dialog.result():
            self.current_post.pictures[selected_index] = temp
            self.update_pictures_table(False)

    def delete_picture(self):
        # Delete the selected picture from the current post
        selected_index = self.get_selected_pictureindex()

        del self.current_post.pictures[selected_index]
        self.update_pictures_table(True)
