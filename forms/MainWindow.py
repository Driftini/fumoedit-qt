from datetime import date
from forms.PostWindow import PostWindow
from forms.SettingsWindow import SettingsWindow
from os import path, listdir, remove
from PyQt5 import QtCore, QtWidgets, uic
from PyQt5.QtCore import Qt
from settings import *
from widgets.ThumbnailPreview import ThumbnailPreview


class MainWindow(QtWidgets.QMainWindow):
    saveSignal = QtCore.pyqtSignal()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndMain.ui", self)
        self.editor = PostWindow(self)
        self.connect_signals()

        # Set better column widths for the tables
        table_headers = [
            self.TwBlogPosts.horizontalHeader(),
            self.TwArtPosts.horizontalHeader(),
            self.TwSelection.horizontalHeader()
        ]

        for h in table_headers:
            h.resizeSection(0, 120)

        self.selection = []

        self.reload_collections(False)

    def post_saved(self):
        self.reload_collections(True)
        self.update_selection_table(True)

    def connect_signals(self):
        self.ActionNew.triggered.connect(self.new_post)
        self.ActionEdit.triggered.connect(self.edit_post)
        self.ActionDelete.triggered.connect(self.delete_post)
        self.ActionSelectionClear.triggered.connect(self.clear_selection)
        self.ActionSettings.triggered.connect(self.show_settings)
        self.ActionQuit.triggered.connect(self.close)

        self.PbAdd.clicked.connect(self.new_post)
        self.PbEdit.clicked.connect(self.edit_post)
        self.PbDelete.clicked.connect(self.delete_post)
        self.PbRefresh.clicked.connect(self.reload_collections)

        self.TwCollections.currentChanged.connect(self.tab_changed)
        self.TwBlogPosts.itemSelectionChanged.connect(self.blog_clicked)
        self.TwArtPosts.itemSelectionChanged.connect(self.art_clicked)
        self.TwBlogPosts.itemDoubleClicked.connect(self.blog_clicked) # Ugly but necessary to allow to de/select
        self.TwArtPosts.itemDoubleClicked.connect(self.art_clicked)   # a row in the tables that is already the current one

        self.PbSelectionClear.clicked.connect(self.clear_selection)
        self.LeTags.textEdited.connect(self.taginput_edited)
        self.PbTagsAdd.clicked.connect(self.add_tags)
        self.PbTagsRemove.clicked.connect(self.remove_tags)

        self.editor.saveSignal.connect(self.post_saved)

    def show_settings(self):
        dialog = SettingsWindow(self)
        dialog.exec()
        #     self.check_settings()

    # Events
    def tab_changed(self):
        # Deselect rows in the post lists
        self.TwBlogPosts.setCurrentCell(-1, -1)
        self.TwArtPosts.setCurrentCell(-1, -1)

        self.clear_selection()        

    def blog_clicked(self):
        sel = len(self.TwBlogPosts.selectedIndexes())>0

        if sel:
            # Get selected post in the TableWidget
            row = self.TwBlogPosts.selectedIndexes()[0].row()
            post = self.TwBlogPosts.item(row, 0).referenced_post

            # Update info panel
            date_str = post.date.strftime('%d %B %Y')

            self.LblBlogInfoTitle.setText(post.title)
            self.LblBlogInfoDate.setText(date_str)
            self.LblBlogInfoTags.setText(post.get_tags())

            if post.has_thumbnail():
                self.GvPicturePreview.update_preview(post.get_thumbnail_ospath())
            else:
                self.GvPicturePreview.update_preview()

            # Toggles blog post selection when shift-clicking
            if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.toggle_selection(post)

        # Dis/enable edit/delete buttons
        self.PbEdit.setDisabled(not sel)
        self.PbDelete.setDisabled(not sel)
        self.ActionEdit.setDisabled(not sel)
        self.ActionDelete.setDisabled(not sel)

    def art_clicked(self):
        sel = len(self.TwArtPosts.selectedIndexes())>0

        if sel:
            # Get selected post in the TableWidget
            row = self.TwArtPosts.selectedIndexes()[0].row()
            post = self.TwArtPosts.item(row, 0).referenced_post

            # Update info panel
            date_str = post.date.strftime('%d %B %Y')

            self.LblArtInfoTitle.setText(post.title)
            self.LblArtInfoDate.setText(date_str)
            self.LblArtInfoTags.setText(post.get_tags())

            if post.has_thumbnail():
                path, offset = post.get_thumbnail_ospath_withoffset()
                self.GvArtSelectionPreview.update_preview(path, offset)
            else:
                self.GvArtSelectionPreview.update_preview()

            # Toggles art post selection when shift-clicking
            if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
                self.toggle_selection(post)

        # Dis/enable edit/delete actions/buttons
        self.PbEdit.setDisabled(not sel)
        self.PbDelete.setDisabled(not sel)
        self.ActionEdit.setDisabled(not sel)
        self.ActionDelete.setDisabled(not sel)

    def taginput_edited(self):
        no_sel = len(self.selection)<1
        no_taginput = len(self.LeTags.text())<1

        self.PbTagsAdd.setDisabled(no_sel or no_taginput)
        self.PbTagsRemove.setDisabled(no_sel or no_taginput)

    # Collection loading
    def reload_collections(self, partial=False):
        # If partial is off, the contents will be cleared and reinserted
        # Else, only the existing rows will change (so selection isn't lost)
        if not partial:
            self.clear_selection()
            self.GvPicturePreview.update_preview()
            self.GvArtSelectionPreview.update_preview()

        for c in fumoedit.COLLECTIONS:
            post_dir = fumoedit.COLLECTIONS[c].get_post_ospath()

            if path.exists(post_dir):
                posts = []
                current_row = 0

                for filename in sorted(listdir(post_dir), reverse=True):
                    filepath = path.normpath(f"{post_dir}/{filename}")

                    if filename[-3:] == ".md":
                        try:
                            posts.append(fumoedit.post_from_file(filepath))
                        except Exception as e:
                            print(e)

                match c:
                    case "posts":
                        self.TwBlogPosts.clearContents()
                        if not partial:
                            self.TwBlogPosts.setRowCount(0)

                        for p in posts:
                            if not partial:
                                self.TwBlogPosts.insertRow(current_row)

                            self.append_blogpost(p, current_row)

                            current_row += 1
                    case "artwork":
                        # Clear the SCRAPPED art grid
                        # From https://stackoverflow.com/a/13103617
                        # for i in reversed(range(self.TwArtPosts.count())):
                        #     self.TwArtPosts.itemAt(i).widget().setParent(None)

                        self.TwArtPosts.clearContents()
                        if not partial:
                            self.TwArtPosts.setRowCount(0)

                        for p in posts:
                            if not partial:
                                self.TwArtPosts.insertRow(current_row)
                                
                            self.append_artpost(p, current_row)

                            current_row += 1
            else:
                msg = f"The {fumoedit.COLLECTIONS[c].label} collection's post folder couldn't be found.\n({post_dir})"

                QtWidgets.QMessageBox.critical(self, "Failed to load collection", msg)

    def append_blogpost(self, post, row):
        date_str = post.date.strftime(r'%d %B %Y')
        date_item = QtWidgets.QTableWidgetItem(date_str)
        date_item.referenced_post = post

        title_item = QtWidgets.QTableWidgetItem(post.title)

        tags_item = QtWidgets.QTableWidgetItem(post.get_tags())

        self.TwBlogPosts.setItem(row, 0, date_item)
        self.TwBlogPosts.setItem(row, 1, title_item)
        self.TwBlogPosts.setItem(row, 2, tags_item)

    # SCRAPPED ART GRID
    # def append_artpost(self, post):
        # post_count = self.listWidget.count()

        # w = ThumbnailPreview(self.centralwidget)
        # w.referenced_post = post

        # self.TwArtPosts.addWidget(w, post_count // 5, post_count % 5)

        # w.setFixedWidth(104)
        # w.setFixedHeight(78)
        # w.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        # w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        # w.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # thumb_path = post.pictures[0].get_thumbnail_path()

        # w.update_preview(thumb_path, post.pictures[0].thumbnail_offset)

    def append_artpost(self, post, row):
        date_str = post.date.strftime(r'%d %B %Y')
        date_item = QtWidgets.QTableWidgetItem(date_str)
        date_item.referenced_post = post

        title_item = QtWidgets.QTableWidgetItem(post.title)

        tags_item = QtWidgets.QTableWidgetItem(post.get_tags())

        self.TwArtPosts.setItem(row, 0, date_item)
        self.TwArtPosts.setItem(row, 1, title_item)
        self.TwArtPosts.setItem(row, 2, tags_item)

    # Post management
    def get_selected_post(self):
        # Figure out the active collection and get selected post in the TableWidget
        post = ""

        match self.TwCollections.currentIndex():
            case 0:  # Blog
                if len(self.TwBlogPosts.selectedIndexes())<1:
                    return

                row = self.TwBlogPosts.selectedIndexes()[0].row()
                post = self.TwBlogPosts.item(row, 0).referenced_post
            case 1:  # Artwork
                if len(self.TwArtPosts.selectedIndexes())<1:
                    return
                
                row = self.TwArtPosts.selectedIndexes()[0].row()
                post = self.TwArtPosts.item(row, 0).referenced_post

        return post

    def new_post(self):
        collection = ""

        match self.TwCollections.currentIndex():
            case 0:  # Blog
                collection = "posts"
            case 1:  # Artwork
                collection = "artwork"

        self.editor.new_post(collection)
        self.editor.show()
        self.editor.raise_()

    def edit_post(self):
        post = self.get_selected_post()

        filepath = post.get_ospath()

        self.editor.load_post(post, filepath)
        self.editor.show()
        self.editor.raise_()

    def delete_post(self):
        post = self.get_selected_post()

        msgbox = QtWidgets.QMessageBox()
        msgbox.setIcon(QtWidgets.QMessageBox.Warning)
        reply = msgbox.question(
            self,
            "Delete post?",
            f"The post \"{post.get_internal_name()}\" will be DELETED IRREVERSIBLY.\nAre you sure?",
            QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.Cancel,
            QtWidgets.QMessageBox.Cancel
        )

        if reply == QtWidgets.QMessageBox.StandardButton.Yes:
            filepath = post.get_ospath()

            try:
                remove(filepath)

                QtWidgets.QMessageBox.information(
                    self, "Post deleted", f"The post \"{post.get_internal_name()}\" has been deleted successfully."
                )
            except FileNotFoundError:
                absolute = path.abspath(filepath)
    
                QtWidgets.QMessageBox.critical(
                    self, "Post not found", f"The post deletion has failed.\n\"{absolute}\" was not found."
                )

            self.reload_collections(False)

    # Selection management
    def toggle_selection(self, post):
        if post in self.selection:
            self.selection.remove(post)
        else:
            self.selection.append(post)
        self.update_selection_table(False)

    def clear_selection(self):
        self.selection.clear()
        self.update_selection_table(False)

        self.PbSelectionClear.setDisabled(True)
        self.ActionSelectionClear.setDisabled(True)


    def update_selection_table(self, partial=False):
        # If partial is off, the contents will be cleared and reinserted
        # Else, only the existing rows will change (so selection isn't lost)
        self.TwSelection.clearContents()
        if not partial:
            self.TwSelection.setRowCount(0)

        sel = len(self.selection)>0
        no_taginput = len(self.LeTags.text())<1

        if sel:
            row_counter = 0

            for post in self.selection:
                if not partial:
                    self.TwSelection.insertRow(row_counter)

                date_str = post.date.strftime('%d %B %Y')
                date_item = QtWidgets.QTableWidgetItem(date_str)
                date_item.referenced_post = post

                title_item = QtWidgets.QTableWidgetItem(post.title)

                tags_item = QtWidgets.QTableWidgetItem(post.get_tags())

                self.TwSelection.setItem(row_counter, 0, date_item)
                self.TwSelection.setItem(row_counter, 1, title_item)
                self.TwSelection.setItem(row_counter, 2, tags_item)

                row_counter += 1

        self.PbSelectionClear.setDisabled(not sel)
        self.ActionSelectionClear.setDisabled(not sel)
        self.PbTagsAdd.setDisabled(not sel or no_taginput)
        self.PbTagsRemove.setDisabled(not sel or no_taginput)

    # Tags management
    def add_tags(self):
        new_tags = self.LeTags.text().split(",")

        for post in self.selection:
            if len(new_tags[0].strip())>0:
                for tag in new_tags:
                    if tag not in post.tags:
                        post.tags.append(tag.strip())
        
                fumoedit.post_to_file(post)

        self.reload_collections(True)
        self.update_selection_table(True)

    def remove_tags(self):
        removed_tags = self.LeTags.text().split(",")

        for post in self.selection:
            if len(removed_tags[0].strip())>0:
                for tag in removed_tags:
                    if tag in post.tags:
                        post.tags.remove(tag.strip())

                fumoedit.post_to_file(post)

        self.reload_collections(True)
        self.update_selection_table(True)
