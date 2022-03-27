from PyQt5.QtCore import QObject, pyqtSignal, QThread, pyqtSlot
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QMainWindow, QApplication

import can_monitor_ui
from dll_power import CANMarathon

marathon = CANMarathon


def read_can1():
    window.thread_for_first_canal.start()


class CANReadAndAnswerThread(QObject):
    mar = marathon
    running = False
    new_can_frame = pyqtSignal(str)

    # метод, который будет выполнять алгоритм в другом потоке
    def run(self):
        while True:
            can_receive_list = self.mar.can_read_all
            #  если в ответе не список, значит, там ошибка связи
            if isinstance(can_receive_list, list):
                # логику нахрен поменять
                if can_receive_list[0] == hex(window.listen_ID_spinbox.value()):
                    bats = [0, 0, 0, 0]
                    string = ''
                    for i in range(2):
                        string += (hex(can_receive_list[3][i + 1])[2:].zfill(2) + ' ')
                    cur_item = window.read_byte_list.currentItem()
                    if cur_item:
                        if string == cur_item.text():
                            bats = [window.byte1_spinBox.value(),
                                    window.byte2_spinBox.value(),
                                    window.byte3_spinBox.value(),
                                    window.byte4_spinBox.value(),
                                    ]
                    self.mar.can_write(window.answer_ID_spinbox.value(), [0x43,
                                                                          can_receive_list[3][0],
                                                                          can_receive_list[3][1],
                                                                          can_receive_list[3][2]] +
                                       bats)

                    self.new_can_frame.emit(string)


class CANMonitorApp(QMainWindow, can_monitor_ui.Ui_MainWindow):
    record_vmu_params = False

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.setupUi(self)
        #  Создаю поток для опроса кан
        self.thread_for_first_canal = QThread()
        # создадим объект для выполнения кода в другом потоке
        self.first_canal = CANReadAndAnswerThread()
        # перенесём объект в другой поток
        self.first_canal.moveToThread(self.thread_for_first_canal)
        # после чего подключим все сигналы и слоты
        self.first_canal.new_can_frame.connect(self.add_new_frame)
        # подключим сигнал старта потока к методу run у объекта, который должен выполнять код в другом потоке
        self.thread_for_first_canal.started.connect(self.first_canal.run)

    @pyqtSlot(str)
    def add_new_frame(self, frame: str):
        items = [window.read_byte_list.item(x).text() for x in range(window.read_byte_list.count())]
        if frame not in items:
            self.read_byte_list.append(frame)
            cursor = self.read_byte_list.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.read_byte_list.setTextCursor(cursor)


app = QApplication([])
window = CANMonitorApp()

window.connect_button.clicked.connect(read_can1)

window.show()  # Показываем окно
app.exec_()  # и запускаем приложение
