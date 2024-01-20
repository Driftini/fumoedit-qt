from datetime import date
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

        post_dir = settings['site_path']+fumoedit.COLLECTIONS['posts'].get_post_path()

        self.TwBlogPosts.clearContents()
        self.TwBlogPosts.setRowCount(0)

        for filename in sorted(listdir(post_dir), reverse=True):
            filepath = f"{post_dir}/{filename}"

            post = fumoedit.post_from_file(filepath)
            self.append_blogpost(post)

        post_dir = settings["site_path"]+fumoedit.COLLECTIONS["artwork"].get_post_path()

        for filename in sorted(listdir(post_dir), reverse=True):
            filepath = f"{post_dir}/{filename}"

            post = fumoedit.post_from_file(filepath)
            self.append_artpost(post)

    def connect_signals(self):
        pass

    def append_blogpost(self, post):
        new_row = self.TwBlogPosts.rowCount()

        self.TwBlogPosts.insertRow(new_row)

        date_str = post.date.strftime('%-d %B %Y')
        self.TwBlogPosts.setItem(new_row, 0, QtWidgets.QTableWidgetItem(date_str))
        self.TwBlogPosts.setItem(new_row, 1, QtWidgets.QTableWidgetItem(post.title))

    def append_artpost(self, post):
        post_count = self.GlArtPosts.count()

        w = ThumbnailPreview(self.centralwidget)
        self.GlArtPosts.addWidget(w, post_count // 5, post_count % 5)

        w.setFixedWidth(104)
        w.setFixedHeight(78)
        w.setTransformationAnchor(QtWidgets.QGraphicsView.NoAnchor)
        w.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        w.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        thumb_path = post.pictures[0].get_thumbnail_path()

        print(thumb_path)

        w.update_preview(thumb_path, post.pictures[0].thumbnail_offset)
