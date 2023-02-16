import time

from PyQt5.QtCore import QThread, pyqtSignal, QDateTime
from PyQt5.QtWidgets import QWidget, QLineEdit, QListWidget, QPushButton, \
    QVBoxLayout, QLabel

'''
 Объявить класс потока
'''


class addItemThread(QThread):
    add_item = pyqtSignal(str)
    show_time = pyqtSignal(str)

    '''
                         Добавить элементы управления
    '''

    def __init__(self, *args, **kwargs):
        super(addItemThread, self).__init__(*args, **kwargs)
        self.num = 0

    def run(self, *args, **kwargs):
        while True:
            file_str = 'File index{0}'.format(self.num, *args, **kwargs)
            self.num += 1

            # Отправить сигнал добавления
            self.add_item.emit(file_str)

            date = QDateTime.currentDateTime()
            currtime = date.toString('yyyy-MM-dd hh:mm:ss')
            print(currtime)
            self.show_time.emit(str(currtime))

            time.sleep(1)


class Window(QWidget):

    def __init__(self, *args, **kwargs):
        super(Window, self).__init__(*args, **kwargs)
        self.setWindowTitle('Многопоточное динамическое добавление элементов управления')

        # x,y,w,h
        self.setGeometry(800, 100, 500, 750)
        # Create QListWidget control
        self.listWidget = QListWidget()
        # Создать элемент управления кнопкой
        self.btn = QPushButton('начало', self)
        self.lb = QLabel('Отображать время', self)
        # Создание элементов управления макетом


        self.vlayout = QVBoxLayout()
        # Добавить кнопки и элементы управления списком в макет
        self.vlayout.addWidget(self.btn)
        self.vlayout.addWidget(self.lb)
        self.vlayout.addWidget(self.listWidget)
        # Установить макет формы
        self.setLayout(self.vlayout)

        # Функция слота кнопки привязки
        self.btn.clicked.connect(self.startThread)

        # Объявить экземпляр потока
        self.additemthread = addItemThread()

        # Функция управления увеличением привязки
        self.additemthread.add_item.connect(self.addItem)

        # Функция привязки отображения времени

        self.additemthread.show_time.connect(self.showTime)

    '''
         @description: кнопка запуска, начало обсуждения
    '''

    def startThread(self):
        # Кнопка недоступна
        self.btn.setEnabled(False)
        # Начать обсуждение
        self.additemthread.start()


    '''
         @description: добавить элементы в listwidget
         @param: значение элемента 
    '''

    def addItem(self, file_str):
        self.listWidget.addItem(file_str)


    '''
         @description: время отображения
         @param: значение элемента 
    '''

    def showTime(self, time):
        self.lb.setText(time)


if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    w = Window()
    w.show()
    sys.exit(app.exec_())