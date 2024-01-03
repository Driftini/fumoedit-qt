from os import path
from PyQt5 import QtWidgets


class ThumbnailPreview(QtWidgets.QGraphicsView):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
