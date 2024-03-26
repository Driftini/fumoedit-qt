from datetime import date
from forms.SettingsWindow import SettingsWindow
from os import path, listdir
from PyQt5 import QtWidgets, uic
from PyQt5.QtCore import Qt
import fumoedit
from settings import *
from widgets.ThumbnailPreview import ThumbnailPreview


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        uic.loadUi("forms/WndMain.ui", self)
        self.connect_signals()

        self.selection = []

        self.load_collections()

    def connect_signals(self):
        self.ActionSettings.triggered.connect(self.show_settings)
        self.TwCollections.currentChanged.connect(self.clear_selection)
        self.PbRefresh.clicked.connect(self.load_collections)
        self.TwBlogPosts.clicked.connect(self.blog_shiftclick_check)
        self.TwArtPosts.clicked.connect(self.art_shiftclick_check)

    def show_settings(self):
        dialog = SettingsWindow(self)
        dialog.exec()
        #     self.check_settings()

    # Events
    def blog_shiftclick_check(self):
        # Toggles blog post selection when shift-clicking
        if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
            # Get selected post in the TableWidget
            row = self.TwBlogPosts.selectedIndexes()[0].row()
            post = self.TwBlogPosts.item(row, 0).referenced_post

            self.toggle_selection(post)

    def art_shiftclick_check(self):
        # Toggles art post selection when shift-clicking
        if QtWidgets.QApplication.keyboardModifiers() == Qt.ShiftModifier:
            # Get selected post in the TableWidget
            row = self.TwArtPosts.selectedIndexes()[0].row()
            post = self.TwArtPosts.item(row, 0).referenced_post

            self.toggle_selection(post)

    # Collection loading
    def load_collections(self):
        for c in fumoedit.COLLECTIONS:
            post_dir = settings['site_path']+fumoedit.COLLECTIONS[c].get_post_path()

            if path.exists(post_dir):
                posts = []

                for filename in sorted(listdir(post_dir), reverse=True):
                    filepath = f"{post_dir}/{filename}"
                    posts.append(fumoedit.post_from_file(filepath))

                match c:
                    case "posts":
                        self.TwBlogPosts.clearContents()
                        self.TwBlogPosts.setRowCount(0)

                        for p in posts:
                            self.append_blogpost(p)
                    case "artwork":
                        # Clear the artwork post grid
                        # From https://stackoverflow.com/a/13103617
                        # for i in reversed(range(self.TwArtPosts.count())):
                        #     self.TwArtPosts.itemAt(i).widget().setParent(None)

                        self.TwArtPosts.clearContents()
                        self.TwArtPosts.setRowCount(0)

                        for p in posts:
                            self.append_artpost(p)
            else:
                msg = f"The {fumoedit.COLLECTIONS[c].label} collection's post folder couldn't be found.\n({post_dir})"

                QtWidgets.QMessageBox.critical(self, "Failed to open load collection", msg)

    def append_blogpost(self, post):
        new_row = self.TwBlogPosts.rowCount()

        self.TwBlogPosts.insertRow(new_row)

        date_str = post.date.strftime('%d %B %Y')
        date_item = QtWidgets.QTableWidgetItem(date_str)
        date_item.referenced_post = post

        title_item = QtWidgets.QTableWidgetItem(post.title)

        tags_item = QtWidgets.QTableWidgetItem(post.get_tags())

        self.TwBlogPosts.setItem(new_row, 0, date_item)
        self.TwBlogPosts.setItem(new_row, 1, title_item)
        self.TwBlogPosts.setItem(new_row, 2, tags_item)

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

    def append_artpost(self, post):
        new_row = self.TwArtPosts.rowCount()

        self.TwArtPosts.insertRow(new_row)

        date_str = post.date.strftime('%d %B %Y')
        date_item = QtWidgets.QTableWidgetItem(date_str)
        date_item.referenced_post = post

        title_item = QtWidgets.QTableWidgetItem(post.title)

        tags_item = QtWidgets.QTableWidgetItem(post.get_tags())

        self.TwArtPosts.setItem(new_row, 0, date_item)
        self.TwArtPosts.setItem(new_row, 1, title_item)
        self.TwArtPosts.setItem(new_row, 2, tags_item)

    # Selection management
    def toggle_selection(self, post):
        if post in self.selection:
            self.selection.remove(post)
        else:
            self.selection.append(post)
        self.update_selection_table()

    def clear_selection(self):
        self.selection.clear()
        self.update_selection_table()

    def update_selection_table(self):
        self.TwSelection.clearContents()
        self.TwSelection.setRowCount(0)

        print(self.selection)

        for post in self.selection:
            new_row = self.TwSelection.rowCount()

            self.TwSelection.insertRow(new_row)

            date_str = post.date.strftime('%d %B %Y')
            date_item = QtWidgets.QTableWidgetItem(date_str)
            date_item.referenced_post = post

            title_item = QtWidgets.QTableWidgetItem(post.title)

            tags_item = QtWidgets.QTableWidgetItem(post.get_tags())

            self.TwSelection.setItem(new_row, 0, date_item)
            self.TwSelection.setItem(new_row, 1, title_item)
            self.TwSelection.setItem(new_row, 2, tags_item)

    # Tags management
    def add_tags(self):
        new_tags = self.LeTags.text().split(",")

        for id in self.selection:
            post = self.selection[id]

            for tag in new_tags:
                if tag not in post.tags:
                    post.tags.append(tag.strip())

    def remove_tags(self):
        removed_tags = self.LeTags.text().split(",")

        for id in self.selection:
            post = self.selection[id]

            for tag in removed_tags:
                if tag in post.tags:
                    post.tags.remove(tag)
