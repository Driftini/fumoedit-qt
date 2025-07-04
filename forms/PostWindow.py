from copy import deepcopy
from datetime import date
from forms.SettingsWindow import SettingsWindow
from forms.PictureWindow import PictureWindow
from os import path
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import Qt
from settings import *
import time
from yaml.scanner import ScannerError


def currenttime():
    return time.strftime('%H:%M:%S', time.localtime())


class PostWindow(QtWidgets.QMainWindow):
    saveSignal = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndPost.ui", self)
        self.connect_signals()

        self.check_settings()

        self.current_post = None
        self.current_picture = None
        self.set_current_filepath(None)
        self.dirty_file = False

        self.LeThumbName.input_path = lambda: self.current_post.get_prioritythumbnail_ospath()

        self.new_post()

    def connect_signals(self):
        # Actions
        self.ActionPictureNew.triggered.connect(self.add_picture)
        self.ActionPictureEdit.triggered.connect(self.open_picture)
        self.ActionPictureDelete.triggered.connect(self.delete_picture)
        self.ActionSavePost.triggered.connect(self.save_post)
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
        # If there's a mismatch between the old and current internal name,
        # ask for confirmation before continuing
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

            fumoedit.post_to_file(self.current_post)

            self.undirty()
            self.saveSignal.emit()

    def save_post(self):
        # Immediately save the current post if it already
        # has a filepath, otherwise let the user choose a
        # save directory.

        if self.validate_post():
            if not self.current_filepath:
                folderpath = self.current_post.collection.get_post_ospath()
            else:
                folderpath = path.dirname(self.current_filepath)

            # No need to normalize the folder path, post_to_file does that on its own
            self.save_post_internal(folderpath)

    # Post methods
    def new_post(self, collection="posts"):
        # Load a blank post in the given collection
        if self.discard_confirmation():
            self.load_post(fumoedit.Post(fumoedit.COLLECTIONS[collection]))

    def load_post(self, post, filepath=None):
        # Brings focus to the Body tab and fills in every field
        # of the GUI with the given post's properties
        self.TwEditors.setCurrentIndex(0)

        self.current_post = post
        self.set_current_filepath(filepath)

        self.LeID.setText(self.current_post.id)
        self.DeDate.setDate(self.current_post.date)
        self.update_internal_name()
        self.CbCollection.setCurrentText(self.current_post.collection.label)  
        self.LeTitle.setText(self.current_post.title)
        self.LeThumbName.setText(self.current_post.priority_thumbnail)
        self.PteBody.setPlainText(self.current_post.body)
        self.load_tags()

        self.update_pictures_table(False)
        self.picture_selection_changed()  # to update buttons' status

        self.undirty()

    def update_internal_name(self):
        d_day = self.DeDate.date().day()
        d_month = self.DeDate.date().month()
        d_year = self.DeDate.date().year()
        self.current_post.set_date(d_year, d_month, d_day)
        self.current_post.id = self.LeID.text()

        self.LeInternalName.setText(self.current_post.get_internal_name())

    def set_post_collection(self, label):
        # Set the current post's collection
        # using the latters' "pretty names"
        id = ""

        # Couldn't get this to work with fumoedit.COLLECTIONS[...].label/id
        # so this stays hardcoded
        match label:
            case "Blog":
                id = "posts"
            case "Artwork":
                id = "artwork"

        self.current_post.collection = fumoedit.COLLECTIONS[id]

        # Enable or disable the picture manager depending on whether or not
        # the current post is a picture post
        self.TwEditors.setTabEnabled(1, self.current_post.is_picturepost())

        # Enable or disable picture actions
        self.ActionPictureNew.setDisabled(not self.current_post.is_picturepost())
        self.ActionPictureEdit.setDisabled(not self.current_post.is_picturepost())
        self.ActionPictureDelete.setDisabled(not self.current_post.is_picturepost())

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
        to_fix = []

        if len(self.LeTitle.text()) <= 0:
            to_fix.append("Title is empty")

        if len(self.LeID.text()) <= 0:
            to_fix.append("ID is empty")

        if len(self.PteBody.toPlainText()) <= 0:
            to_fix.append("Body is empty")

        tags_trimmed = self.LeTags.text().strip()

        if len(tags_trimmed)>0:
            if tags_trimmed[0]=="," or tags_trimmed[-1]==",":
                to_fix.append("Tags must not begin or end with commas")

        if len(to_fix) == 0:
            return True  # Validation successful
        else:
            msg = "The post has failed validation:"

            for f in to_fix:
                msg += f"\n• {f}"

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

        if len(tags[0].strip())>0:
            # If there are any tags...
            for t in tags:
                i = tags.index(t)
                tags[i] = t.strip()
        else:
            tags = []

        self.current_post.tags = tags

    # Picture methods
    def update_pictures_table(self, partial):
        # If partial is off, the contents will be cleared and reinserted
        # Else, only the existing rows will change (so selection isn't lost)
        if not partial:
            self.TwPictures.clearContents()
            self.TwPictures.setRowCount(len(self.current_post.pictures))

        for p in self.current_post.pictures:
            i = self.current_post.pictures.index(p)

            self.TwPictures.setItem(
                i, 0, QtWidgets.QTableWidgetItem(p.get_label()))
            self.TwPictures.setItem(
                i, 1, QtWidgets.QTableWidgetItem(p.original_filename))

        self.update_thumbnail_preview()

    def get_selected_pictureindex(self):
        selected_rows = self.TwPictures.selectionModel().selectedRows()

        if len(selected_rows) > 0:
            return selected_rows[0].row()

    def picture_selection_changed(self):
        if self.get_selected_pictureindex() != None:
            self.PbPictureEdit.setDisabled(False)
            self.PbPictureDelete.setDisabled(False)
        else:
            self.PbPictureEdit.setDisabled(True)
            self.PbPictureDelete.setDisabled(True)

        self.update_thumbnail_preview()

    def update_thumbnail_preview(self):
        path = None
        offset_percent = 0

        selected_index = self.get_selected_pictureindex()
        if selected_index != None:
            picture = self.current_post.pictures[selected_index]

            path = picture.get_thumbnail_ospath()
            offset_percent = int(picture.thumbnail_offset)

        self.GvPicturePreview.update_preview(path, offset_percent)

    def add_picture(self):
        # Bring focus to the pictures tab, and
        # add a new picture to the current post through the Picture Editor
        self.TwEditors.setCurrentIndex(1)

        temp = deepcopy(self.current_post)

        dialog = PictureWindow(self)
        dialog.picture = temp.new_picture()
        dialog.load_picture()  # eugh
        if dialog.exec() and dialog.result():
            self.current_post = temp
            self.update_pictures_table(False)

    def open_picture(self):
        # Bring focus to the pictures tab, and
        # open the selected picture from the current post through the Picture Editor
        self.TwEditors.setCurrentIndex(1)

        selected_index = self.get_selected_pictureindex()
        if selected_index != None:
            temp = deepcopy(self.current_post.pictures[selected_index])

            dialog = PictureWindow(self)
            dialog.picture = temp
            dialog.load_picture()  # eugh
            if dialog.exec() and dialog.result():
                self.current_post.pictures[selected_index] = temp
                self.update_pictures_table(True)

    def delete_picture(self):
        # Bring focus to the pictures tab, and
        # delete the selected picture from the current post
        self.TwEditors.setCurrentIndex(1)

        selected_index = self.get_selected_pictureindex()
        if selected_index != None:
            del self.current_post.pictures[selected_index]
            self.update_pictures_table(False)
