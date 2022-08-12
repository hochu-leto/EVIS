import time

from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot
from PyQt5.QtGui import QTextCursor
from PyQt5.QtWidgets import QApplication, QMainWindow
import two_chanell_ui
from Dinostend import VMU_ID_PDO
from marathon_power import CANMarathon
from work_with_file import adding_to_csv_file

marathon = CANMarathon()
marathon2 = CANMarathon()
marathon2.can_canal_number = 1
marathon2.BCI_bt0 = marathon2.BCI_250K_bt0


def read_can1():
    window.thread_for_first_canal.start()


def read_can2():
    window.thread_for_second_canal.start()


class CANSaveToFileThread(QObject):
    mar = marathon
    running = False
    new_can_frame = pyqtSignal(str)
    recording_file_name = ''
    start_time = int(round(time.time() * 1000))
    time_for_request = start_time
    time_for_send = start_time
    send_delay = 50  # задержка отправки в кан сообщений

    # метод, который будет выполнять алгоритм в другом потоке
    def run(self):
        # current_time = self.start_time
        # front_steer_data = 15000
        # can_receive_list = []
        # torque_data_list = [0b10001, 0, 0, front_steer_data & 0xFF,
        #                     ((front_steer_data & 0xFF00) >> 8), 0, 0, 0]

        while True:
            can_receive_list = self.mar.can_read_all()
            if isinstance(can_receive_list, list):
                # adding_to_csv_file('value', can_receive_list, self.recording_file_name)
                strn = can_receive_list[0] + '    '
                for i in range(can_receive_list[1]):
                    strn += (hex(can_receive_list[3][i])[2:].zfill(2) + ' ')
                self.new_can_frame.emit(strn)

            # проверяем что время передачи пришло и отправляю управление по 401 адресу
            # if (current_time - self.start_time) > self.send_delay:
            #     self.start_time = current_time
            #     marathon.can_write(VMU_ID_PDO, torque_data_list)
            #
            # current_time = int(round(time.time() * 1000))


class CANMonitorApp(QMainWindow, two_chanell_ui.Ui_MainWindow):
    record_vmu_params = False

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.setupUi(self)
        #  иконку пока не надо
        # self.setWindowIcon(QIcon('icons_speed.png'))
        #  Создаю поток для опроса параметров кву
        self.thread_for_first_canal = QThread()
        # создадим объект для выполнения кода в другом потоке
        self.first_canal = CANSaveToFileThread()
        # перенесём объект в другой поток
        self.first_canal.moveToThread(self.thread_for_first_canal)
        # после чего подключим все сигналы и слоты
        self.first_canal.new_can_frame.connect(self.add_new_frame)
        # подключим сигнал старта потока к методу run у объекта, который должен выполнять код в другом потоке
        self.thread_for_first_canal.started.connect(self.first_canal.run)

        self.thread_for_second_canal = QThread()
        # создадим объект для выполнения кода в другом потоке
        self.second_canal = CANSaveToFileThread()
        self.second_canal.mar = marathon2
        # перенесём объект в другой поток
        self.second_canal.moveToThread(self.thread_for_second_canal)
        # после чего подключим все сигналы и слоты
        self.second_canal.new_can_frame.connect(self.add_new_frame2)
        # подключим сигнал старта потока к методу run у объекта, который должен выполнять код в другом потоке
        self.thread_for_second_canal.started.connect(self.second_canal.run)

    @pyqtSlot(str)
    def add_new_frame(self, frame: str):
        self.textBrowser_1.append(frame)
        cursor = self.textBrowser_1.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.textBrowser_1.setTextCursor(cursor)

    @pyqtSlot(str)
    def add_new_frame2(self, frame: str):
        self.textBrowser_2.append(frame)
        cursor = self.textBrowser_2.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.textBrowser_2.setTextCursor(cursor)


app = QApplication([])
window = CANMonitorApp()
window.read1_btn.clicked.connect(read_can1)
window.read2_btn.clicked.connect(read_can2)
window.show()  # Показываем окно
app.exec_()  # и запускаем приложение
