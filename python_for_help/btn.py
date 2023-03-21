import sys

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QWidget, QPushButton, QApplication, QMenu
from PyQt6.QtCore import QSize, pyqtSlot


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.resize(QSize(100, 100))
        self.btn = QPushButton("TEST BUTTON", self)
        list_items = ['one', 'two', 'three']
        menu = QMenu()
        for i in list_items:
            menu.addAction(i)
        menu.triggered.connect(do_smf)
        self.btn.setMenu(menu)
        self.btn.clicked.connect(self.on_click)  # соединение сигнала и слота (сигнал clicked и слот on_click)

    def on_click(self):
        print('Clicked!')


@pyqtSlot(QAction)
def do_smf(smth):
    print('hello', smth.text())


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec())
