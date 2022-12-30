# importing libraries
from PyQt5.QtWidgets import *
from PyQt5 import QtCore, QtGui
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import sys

type_dict = dict(
    UINT32='UNSIGNED32',
    UINT16='UNSIGNED16',
    ENUM='UNSIGNED16',
    INT16='SIGNED16',
    UNION='SIGNED16',
    STR='SIGNED16',
    STRING='VISIBLE_STRING',
    INT32='SIGNED32',
    DATE='DATE',
    FLOAT32='FLOAT'
)


class MyComboBox(QComboBox):
    clicked = pyqtSignal(bool)  # Create a signal
    isRevealed = False

    def showPopup(self):  # sPopup function
        self.isRevealed = True
        self.clicked.emit(self.isRevealed)  # Send signal
        super(MyComboBox, self).showPopup()  # 's showPopup ()

    def hidePopup(self):
        self.isRevealed = False
        self.clicked.emit(self.isRevealed)
        super(MyComboBox, self).hidePopup()


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
        # creating a combo box widget
        self.combo_box = MyComboBox(self)

        # setting geometry of combo box
        self.combo_box.setGeometry(200, 150, 150, 30)
        # geek list
        geek_list = list(type_dict.values())

        # making it editable
        # self.combo_box.setEditable(True)

        # adding list of items to combo box
        self.combo_box.addItems(geek_list)
        self.combo_box.setCurrentText(type_dict['UNION'])
        self.combo_box.currentTextChanged.connect(some_def2)
        self.combo_box.currentIndexChanged.connect(some_def)
        self.combo_box.clicked.connect(some_click)
        # getting view part of combo box
        view = self.combo_box.view()

        # making view box hidden
        # view.setHidden(True)

        # checking if the view object is hidden or not
        # view.entered.connect(some_def)
        status = view.isHidden()

        # creating label to show the status
        label = QLabel("Hidden ?: " + str(status), self)

        # setting geometry of the label
        label.setGeometry(200, 100, 300, 30)


def some_def(index):
    key = list(type_dict.keys())[index]
    print(f'index changed {index=} {key=} {type_dict[key]=}')


def some_def2(text):
    print(f'text changed {text}')


@pyqtSlot(bool)
def some_click(state):
    print(f'состояние комбо-бокса - открыт? {state}')


# create pyqt5 app
App = QApplication(sys.argv)

# create the instance of our Window
window = Window()

# start the app
sys.exit(App.exec())
