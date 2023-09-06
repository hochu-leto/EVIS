import sys

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton

import dia_ui


class DialApp(QMainWindow, dia_ui.Ui_Dialog):

    def __init__(self):
        super().__init__()

        self.setupUi(self)


def restart():
    QtCore.QCoreApplication.quit()
    status = QtCore.QProcess.startDetached(sys.executable, sys.argv)
    print(status)


def main():
    app = QApplication(sys.argv)

    print("[PID]:", QtCore.QCoreApplication.applicationPid())

    window = QMainWindow()
    window.show()

    button = QPushButton("Restart")
    button.clicked.connect(restart)

    window.setCentralWidget(button)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
# if __name__ == '__main__':
#     app = QApplication(sys.argv)
#     window = DialApp()
#     window.show()  # Показываем окно
#     sys.exit(app.exec())
