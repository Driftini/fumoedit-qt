import sys
import time
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5 import uic
import fumoedit

def currenttime():
    return time.strftime('%H:%M:%S', time.localtime())


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("WndMain.ui", self)
        self.connect_signals()

        self.current_post = None
        self.current_picture = None
        self.current_variant = None
        self.new_post()
        self.deselect_picture()

    def connect_signals(self):
        self.ActionNewPost.triggered.connect(self.new_post)
        self.ActionSavePost.triggered.connect(self.export_post)
        self.ActionQuit.triggered.connect(self.close)

        self.LePostID.textEdited.connect(self.update_internal_name)
        self.DePostDate.dateChanged.connect(self.update_internal_name)

        self.PbPictureNew.clicked.connect(self.add_picture)
        self.PbPictureDelete.clicked.connect(self.delete_picture)

        self.TwPictures.itemSelectionChanged.connect(self.picture_selection_changed)

    def picture_selection_changed(self):
        selected_rows = self.TwPictures.selectionModel().selectedRows()
        
        if len(selected_rows) > 0:
            self.select_picture(self.current_post.pictures[selected_rows[0].row()])
        else:
            self.deselect_picture()

    # Post methods
    def new_post(self):
        # TODO in statusbar
        print(f"* Created new post at {currenttime()}")
        self.load_post(fumoedit.Post())

    def load_post(self, post):
        self.TwMain.setCurrentIndex(0)

        self.current_post = post

        self.LePostID.setText(self.current_post.id)
        self.DePostDate.setDate(self.current_post.date)
        self.LePostTitle.setText(self.current_post.title)
        self.LePostThumbName.setText(self.current_post.thumbnail)
        self.PtePostBody.setPlainText(self.current_post.body)

    def update_internal_name(self):
        d_day = self.DePostDate.date().day()
        d_month = self.DePostDate.date().month()
        d_year = self.DePostDate.date().year()
        self.current_post.set_date(d_year, d_month, d_day)
        self.current_post.id = self.LePostID.text()

        self.LePostInternalName.setText(self.current_post.get_internal_name())

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
            msgbox.setWindowTitle("Export failed")
            msgbox.setText(msg)
            msgbox.setIcon(QtWidgets.QMessageBox.Critical)
            msgbox.exec()

            return False  # Validation failed

    def export_post(self):
        if self.validate_post():
            print(f"* Exporting post at {currenttime()}:")
            self.current_post.id = self.LePostID.text()

            d_day = self.DePostDate.date().day()
            d_month = self.DePostDate.date().month()
            d_year = self.DePostDate.date().year()
            self.current_post.set_date(d_year, d_month, d_day)

            self.current_post.title = self.LePostTitle.text()
            self.current_post.thumbnail = self.LePostThumbName.text()
            self.current_post.body = self.PtePostBody.toPlainText()

            self.save_variant()
            self.save_picture()

            print(self.current_post.get_filename())
            print(self.current_post.generate())

    # Picture methods
    def update_pictures_table(self, reset):
        # If reset is on, the contents will be cleared and reinserted
        # Else, only the visible values will change
        if (reset):
            self.TwPictures.clearContents()
            self.TwPictures.setRowCount(len(self.current_post.pictures))

        for i in range(0, len(self.current_post.pictures)):
            picture = self.current_post.pictures[i]
            
            self.TwPictures.setItem(i, 0, QtWidgets.QTableWidgetItem(f"{len(picture.variants)}"))
            self.TwPictures.setItem(i, 1, QtWidgets.QTableWidgetItem(picture.thumbnail_path))

    def add_picture(self):
        # Add a new empty picture object to the current post
        self.current_post.pictures.append(fumoedit.Picture())

        self.update_pictures_table(True)

    def save_picture(self):
        # Apply picture fields' values to the current picture object
        if self.current_picture:
            self.current_picture.thumbnail_path = self.LeThumbFilename.text()

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

            self.update_pictures_table(False)
            print(f"* Saved picture at {currenttime()}")
            # TODO save variant (if any)

    def select_picture(self, picture):
        # Set all picture fields' values to the given picture object's,
        # update variants table accordingly
        if len(self.current_post.pictures) > 0:
            # If there's already a loaded picture, save its edits beforehand
            if self.current_picture:
                self.save_picture()

            self.current_picture = picture
        
            self.LeThumbFilename.setText(self.current_picture.thumbnail_path)

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

            self.PbPictureDelete.setEnabled(True)
            self.PbVariantNew.setEnabled(True)
            self.GbPicMan2.setEnabled(True)

        self.deselect_variant()

    def deselect_picture(self):
        # Disable all picture and variant fields
        self.current_picture = None

        self.LeThumbFilename.clear()
        self.SbThumbX.setValue(0)
        self.SbThumbY.setValue(0)
        self.CbThumbCenterX.setChecked(False)
        self.CbThumbCenterY.setChecked(False)

        self.PbPictureDelete.setEnabled(False)
        self.PbVariantNew.setEnabled(False)
        self.GbPicMan2.setEnabled(False)

        self.deselect_variant()

    def delete_picture(self):
        # Delete the selected picture object from the current post
        if self.current_picture:
            self.current_post.pictures.remove(self.current_picture)
            self.current_picture = None # to prevent saving when deselecting the picture
        
        if len(self.current_post.pictures) > 0:
            # TODO Select last (or first?) row in the pics table
            pass

        self.update_pictures_table(True)

    def validate_picture(self):
        return True

    # Picture variant methods
    def update_variants_table(self):
        self.TwVariants.clearContents()

        for i in range(0, len(self.current_picture.variants)):
            variant = self.current_picture.variants[i]

            self.TwVariants.insertRow(i)
            self.TwVariants.setItem(i, 0, QtWidgets.QTableWidgetItem(f"{len(variant.variants)}"))
            self.TwVariants.setItem(i, 1, QtWidgets.QTableWidgetItem(variant.thumbnail_path))

    def add_variant(self):
        # Add a new empty variant object to the current picture
        self.current_picture.variants.append(fumoedit.PictureVariant())
    
    def save_variant(self):
        # Apply variant fields' values to the current variant object
        pass

    def select_variant(self, variant):
        # Set all variant fields' values to the selected variant object's
        self.PbVariantDelete.setEnabled(True)
        self.LeVariantFilename.setEnabled(True)
        self.LeVariantLabel.setEnabled(True)
        
        self.LeVariantFilename.setText(variant.path)
        self.LeVariantLabel.setText(variant.label)

        self.GbPicMan3.setEnabled(True)


    def deselect_variant(self):
        # Clear and disable all variant fields
        self.PbVariantDelete.setEnabled(False)
        self.LeVariantFilename.setEnabled(False)
        self.LeVariantLabel.setEnabled(False)

        self.LeVariantFilename.clear()
        self.LeVariantLabel.clear()


    def delete_variant(self):
        # Delete the selected variant object from the current picture
        if self.current_variant:
            self.current_picure.variants.remove(self.current_variant)
        
        if len(self.current_pictures.variants) > 0:
            # TODO Select last (or first?) row in the variants table
            pass

    def validate_variant(self):
        return True
    

app = QtWidgets.QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec_()
