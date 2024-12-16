from os import path
from PyQt5 import QtCore, QtWidgets, uic
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

        self.tag_priority = settings["tag_priority"].copy()
        self.update_tagpriority_list(False)

    def connect_signals(self):
        self.PbBrowseSitePath.clicked.connect(self.browse_site_path)

        self.PbTagAdd.clicked.connect(self.tagpriority_add)
        self.PbTagDelete.clicked.connect(self.tagpriority_delete)
        self.PbTagUp.clicked.connect(self.tagpriority_up)
        self.PbTagDown.clicked.connect(self.tagpriority_down)

        self.TwTagPriority.itemSelectionChanged.connect(
            self.tag_selection_changed
        )

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
                f"{absolute} does not exist.\nThis change will not be applied."
            )

        self.commit_tags_to_local_list()
        set_tag_priority(self.tag_priority)

        save_settings()

    def browse_site_path(self):
        dialog = QtWidgets.QFileDialog(self)
        dialog.setFileMode(QtWidgets.QFileDialog.DirectoryOnly)
        if dialog.exec():
            self.LeSitePath.setText(dialog.selectedFiles()[0])

    # Tag priority management

    def get_selected_tagindex(self):
        selected_rows = self.TwTagPriority.selectedIndexes()

        if len(selected_rows) > 0:
            return selected_rows[0].row()

    def tag_selection_changed(self):
        sel = self.get_selected_tagindex()
        first_item = sel == 0
        last_item = sel == len(self.tag_priority) - 1

        self.PbTagDelete.setDisabled(sel == None)
        self.PbTagUp.setDisabled(sel == None or first_item)
        self.PbTagDown.setDisabled(sel == None or last_item)

    def commit_tags_to_local_list(self):
        # Should be called before any operation on self.tag_priority
        # so that inline edits in TwTagPriority actually get saved

        for current_row in range(0, self.TwTagPriority.rowCount()):
            tag_item = self.TwTagPriority.item(current_row, 0)
            self.tag_priority[current_row] = tag_item.text()

    def update_tagpriority_list(self, partial):
        # If partial is off, the contents will be cleared and reinserted
        # Else, only the existing rows will change (so selection isn't lost)
        if not partial:
            self.TwTagPriority.clearContents()
            self.TwTagPriority.setRowCount(len(self.tag_priority))

        for current_row in range(0, len(self.tag_priority)):
            tag_item = QtWidgets.QTableWidgetItem(self.tag_priority[current_row])

            self.TwTagPriority.setItem(current_row, 0, tag_item)

    def tagpriority_add(self):
        self.commit_tags_to_local_list()
        
        sel = self.get_selected_tagindex()
        
        if sel != None:
            sel += 1  # insert below the selected row 
            self.tag_priority.insert(sel, f"Tag {sel}")
        else:
            self.tag_priority.append(f"Tag {len(self.tag_priority)}")

        self.update_tagpriority_list(False)

        to_select = self.TwTagPriority.item(sel, 0)
        self.TwTagPriority.setCurrentItem(to_select, QtCore.QItemSelectionModel.SelectCurrent)

    def tagpriority_delete(self):
        sel = self.get_selected_tagindex()

        if sel != None:
            self.commit_tags_to_local_list()

            tag = self.tag_priority[sel]
            self.tag_priority.remove(tag)

            self.update_tagpriority_list(False)

            to_select = self.TwTagPriority.item(sel-1, 0)
            self.TwTagPriority.setCurrentItem(to_select, QtCore.QItemSelectionModel.SelectCurrent)

    def tagpriority_down(self):
        sel = self.get_selected_tagindex()

        if sel != None:
            self.commit_tags_to_local_list()

            tag = self.tag_priority[sel]
            self.tag_priority.remove(tag)
            self.tag_priority.insert(sel + 1, tag)

            to_select = self.TwTagPriority.item(sel + 1, 0)
            self.TwTagPriority.setCurrentItem(to_select, QtCore.QItemSelectionModel.SelectCurrent)

            self.update_tagpriority_list(True)

    def tagpriority_up(self):
        sel = self.get_selected_tagindex()

        if sel != None:
            self.commit_tags_to_local_list()

            tag = self.tag_priority[sel]
            self.tag_priority.remove(tag)
            self.tag_priority.insert(sel - 1, tag)

            to_select = self.TwTagPriority.item(sel - 1, 0)
            self.TwTagPriority.setCurrentItem(to_select, QtCore.QItemSelectionModel.SelectCurrent)

            self.update_tagpriority_list(True)