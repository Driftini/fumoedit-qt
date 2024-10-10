from os import path
from PyQt5 import QtGui, QtWidgets
from PyQt5.QtCore import Qt
from settings import *


class ThumbnailPreview(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # self.setStyleSheet("ThumbnailPreview:focus { border: 5px solid #f83 }")

    def update_preview(self, picture_path, offset_percent=50):
        # Update the picture shown,
        # while scaling and applying the vertical offset

        # I don't think I should instance a new scene every time
        scene = QtWidgets.QGraphicsScene()

        actual_path = path.join(
            settings["site_path"],
            picture_path[1:]
        )
        absolute = path.abspath(actual_path)

        # If the file exists...
        if path.exists(absolute):
            pixmap = QtGui.QPixmap(absolute)
            pixmap = pixmap.scaled(
                self.width() * 2, pixmap.height() * 2,
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )

            # Prepare offsets
            offset_x = (pixmap.width() / 2) - self.width() / 2
            offset_y = (self.height() - pixmap.height()) * offset_percent / 100

            # Apply offsets
            pixmap_item = scene.addPixmap(pixmap)
            pixmap_item.setOffset(-offset_x, offset_y)

        # This can be reached even if the file doesn't exist
        # or if there's no selected picture
        self.setScene(scene)
