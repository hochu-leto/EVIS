import sys

import typing
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QStandardItemModel
from PyQt6.QtWidgets import QComboBox, QMainWindow, QLabel, QApplication


# new check-able combo box
class CheckableComboBox(QComboBox):

    # constructor
    def __init__(self, parent=None):
        super(CheckableComboBox, self).__init__(parent)
        self.view().pressed.connect(self.handleItemPressed)
        self.setModel(QStandardItemModel(self))

    count = 0

    def addItems(self, texts: typing.Iterable[str]) -> None:
        for count, item in enumerate(texts):
            super(CheckableComboBox, self).addItem(item)

            it = self.model().item(count)
            # it.setFlags(Qt.ItemFlag.ItemIsUserCheckable | Qt.ItemFlag.ItemIsEnabled)
            it.setFlags( Qt.ItemFlag.ItemIsEnabled)
            it.setCheckState(Qt.CheckState.Unchecked)
            # it.emitDataChanged()
    # action called when item get checked

    def do_action(self):

        window.label.setText("Checked number : " + str(self.count))

    # when any item get pressed
    def handleItemPressed(self, index):

        # getting the item
        item = self.model().itemFromIndex(index)

        # checking if item is checked
        if item.checkState() == Qt.CheckState.Checked:

            # making it unchecked
            item.setCheckState(Qt.CheckState.Unchecked)
            self.count -= 1

            # call the action
            self.do_action()

        # if not checked
        else:
            # making the item checked
            item.setCheckState(Qt.CheckState.Checked)

            self.count += 1

            # call the action
            self.do_action()


class Window(QMainWindow):

    def __init__(self):
        super().__init__()

        # setting title
        self.setWindowTitle("Python ")

        # setting geometry
        self.setGeometry(100, 100, 600, 400)

        # calling method
        self.UiComponents()

        # showing all the widgets
        self.show()

    # method for widgets
    def UiComponents(self):
        # creating a check-able combo box object
        self.combo_box = CheckableComboBox(self)

        # setting geometry of combo box
        self.combo_box.setGeometry(200, 150, 150, 30)

        # geek list
        geek_list = ["Sayian", "Super Sayian", "Super Sayian 2", "Super Sayian B"]

        # adding list of items to combo box
        self.combo_box.addItems(geek_list)

        # create label to show to text
        self.label = QLabel("Not checked", self)

        # setting geometry of label
        self.label.setGeometry(200, 100, 200, 30)


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
window = Window()

window.show()

# start the app
sys.exit(App.exec())
