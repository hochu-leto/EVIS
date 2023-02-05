import sys

from PyQt5.QtWidgets import QWidget, QPushButton, QApplication
from PyQt5.QtCore import QSize


class Main(QWidget):
    def __init__(self):
        super(Main, self).__init__()
        self.resize(QSize(100, 100))
        self.btn = QPushButton("TEST BUTTON", self)

        self.btn.clicked.connect(self.on_click)  # соединение сигнала и слота (сигнал clicked и слот on_click)

    def on_click(self):
        print('Clicked!')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    ex.show()
    sys.exit(app.exec_())