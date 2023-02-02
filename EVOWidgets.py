from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QLabel, QLineEdit, QProgressBar, QSlider, QDoubleSpinBox, QPushButton


class GreenLabel(QLabel):
    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)
        self.setStyleSheet('{background-color: rgba(0, 200, 0, 50);}')


class RedLabel(QLabel):
    def __init__(self, parent=None):
        super(QLabel, self).__init__(parent)
        self.setStyleSheet('{background-color: rgba(200, 0, 0, 50);}')


class MyComboBox(QComboBox):
    ItemSelected = pyqtSignal(list)
    isInFocus = False
    # parametr = None

    def __init__(self, parent=None, parametr=None):
        super(MyComboBox, self).__init__(parent)
        self.parametr = parametr
        self.currentIndexChanged.connect(self.item_selected_handle)

    def item_selected_handle(self, index):
        lst = []
        if self.parametr is not None:
            key = list(self.parametr.value_table.keys())[index]
            lst = [self.parametr, key]
        self.ItemSelected.emit(lst)

    def showPopup(self):  # sPopup function
        self.isInFocus = True
        super(MyComboBox, self).showPopup()

    def hidePopup(self):
        self.isInFocus = False
        super(MyComboBox, self).hidePopup()


class MyEditLine(QLineEdit):

    def __init__(self, parent=None, parametr=None):
        super(QLineEdit, self).__init__(parent)
        self.parametr = parametr


class MyColorBar(QProgressBar):

    def __init__(self, parent=None, parametr=None, max_limit=None, min_limit=None, color_bar=None):
        super(QProgressBar, self).__init__(parent)
        self.parametr = parametr
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.color_bar = color_bar


class MySlider(QSlider, QDoubleSpinBox):

    def __init__(self, parent=None, parametr=None, max_limit=None, min_limit=None, color_bar=None):
        super(QSlider, self).__init__(parent)
        super(QDoubleSpinBox, self).__init__(parent)
        self.parametr = parametr
        self.max_limit = max_limit
        self.min_limit = min_limit
        self.color_bar = color_bar


class MyButton(QPushButton):

    def __init__(self, parent=None, parametr=None, active_value=None, button_text=None):
        super(QPushButton, self).__init__(parent)
        self.parametr = parametr
        self.active_value = active_value
        self.button_text = button_text
        if self.button_text:
            self.setText(self.button_text)


class MySwitch():
    pass


