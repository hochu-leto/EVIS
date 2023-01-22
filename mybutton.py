from PyQt5.QtWidgets import QPushButton


class MyButton(QPushButton):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("QPushButton{"
                           "    background-color: red;"
                           "    border-style: outset;"
                           "    border-width: 2px;"
                           "    border-radius: 10px;"
                           "    border-color: beige;"
                           "    font: bold 14px;"
                           "    min-width: 10em;"
                           "    padding: 6px;"
                           "}")
        self.setMinimumHeight(148)