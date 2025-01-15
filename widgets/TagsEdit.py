from PyQt5 import QtWidgets
from PyQt5.QtCore import Qt
from settings import *


class TagsEdit(QtWidgets.QLineEdit):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        #self.keyPressEvent.connect(self.autocomplete_tag)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.autocomplete_tag()
        else:
            super().keyPressEvent(event)

    def autocomplete_tag(self):
        # Attempt to autocomplete the last tag in the widget
        if self.isEnabled():
            tags_trimmed = self.text().strip()

            # Tags field validation (starts/ends with commas?)
            if len(tags_trimmed)>0:
                if tags_trimmed[0]!="," and tags_trimmed[-1]!=",":
                    tags_list = tags_trimmed.split(",")

                    # Lowercase copy needed for case insensitive searching,
                    # normal case copy needed for the actual autocompletion 
                    known_tags = settings["tag_priority"]
                    known_tags_lower = [tag.lower() for tag in known_tags]
                    
                    # Same from above goes here
                    incomplete = tags_list[-1].strip()
                    incomplete_lower = incomplete.lower()

                    completion_matches = list(
                        filter(lambda t: t.startswith(incomplete_lower), known_tags_lower)
                    )

                    if len(completion_matches)>0:
                        # overengineered much?
                        completion_lower = completion_matches[0]
                        completion_index = known_tags_lower.index(completion_lower)
                        completion = known_tags[completion_index]
                        tags_list[-1]=completion

                        # Put the widget's content back together
                        tags_final = ""
                        for t in tags_list:
                            t = t.strip()
                            tags_final += t

                            if t is not tags_list[-1]:
                                tags_final += ", "

                        self.setText(tags_final)

    def setEnabled(self, bool):
        # Clear tooltip if widget gets disabled
        if not bool:
            self.setToolTip("")

        super().setEnabled(bool)
