import time

from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread, pyqtSlot, QRegularExpression
from PyQt6.QtGui import QTextCursor, QRegularExpressionValidator
from PyQt6.QtWidgets import QMainWindow, QApplication

# from PyQt5.QtCore import QThread, QObject, pyqtSignal, pyqtSlot, QRegularExpression, QTimer
# from PyQt5.QtGui import QTextCursor, QRegularExpressionValidator
# from PyQt5.QtWidgets import QApplication, QMainWindow
import two_chanell_ui
from marathon_power import CANMarathon

VMU_ID_PDO = 0x00000403

marathon = CANMarathon()
marathon2 = CANMarathon()
marathon2.can_canal_number = 1
marathon2.BCI_bt0 = marathon2.BCI_250K_bt0
timer = QTimer()
timer_send = QTimer()


def read_can1():
    if window.thread_for_first_canal.isRunning():
        window.thread_for_first_canal.terminate()
        # window.thread_for_first_canal.wait()
        # window.thread_for_first_canal.quit()
    else:
        window.thread_for_first_canal.start()


def read_can2():
    window.thread_for_second_canal.start()


def get_ID() -> int:
    text_ID = window.ID_le.text()
    return 0 if not text_ID else int(text_ID, 16)


def get_data() -> list[int]:
    text_data = window.data_le.text()
    if not text_data:
        return [0]
    f_list = []
    for i in range(0, len(text_data), 2):
        f_list.append(int(text_data[i:i + 2], 16))
    return f_list


class CANSaveToFileThread(QObject):
    mar = marathon
    running = False
    new_can_frame = pyqtSignal(str)

    # метод, который будет выполнять алгоритм в другом потоке
    def run(self):
        while True:
            can_receive_list = self.mar.can_read_all()
            if isinstance(can_receive_list, list):
                # adding_to_csv_file('value', can_receive_list, self.recording_file_name)
                strn = can_receive_list[0] + '    '
                for i in range(can_receive_list[1]):
                    strn += (hex(can_receive_list[3][i])[2:].zfill(2) + ' ')
                self.new_can_frame.emit(strn)
            #
            # if window.send_chbox.isChecked():
            #     # проверяем что время передачи пришло и отправляю
            #     if time.perf_counter_ns() > self.start_time + self.send_delay:
            #         self.start_time = time.perf_counter_ns()
            #         marathon.can_write(get_ID(), get_data())


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
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.textBrowser_1.setTextCursor(cursor)

    @pyqtSlot(str)
    def add_new_frame2(self, frame: str):
        self.textBrowser_2.append(frame)
        cursor = self.textBrowser_2.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.textBrowser_2.setTextCursor(cursor)


def send_can1():
    marathon.can_write(get_ID(), get_data())


def change_id():
    current_ID = get_ID()
    window.ID_le.setText(hex(current_ID + 1)[2:].upper())


def periodic_change():
    if timer.isActive():
        timer.stop()
    else:
        timer.start(300)


def periodic_send():
    if timer_send.isActive():
        timer_send.stop()
    else:
        timer_send.start(50)


app = QApplication([])
window = CANMonitorApp()
reg_ex = QRegularExpression("^[0-9a-fA-F]+$")
window.ID_le.setValidator(QRegularExpressionValidator(reg_ex))
reg_ex = QRegularExpression("^[0-9A-F]+$")
window.data_le.setValidator(QRegularExpressionValidator(reg_ex))

window.read1_chbox.clicked.connect(read_can1)
window.send1_btn.clicked.connect(send_can1)
window.periodic_change_btn.clicked.connect(change_id)
window.periodic_change_id_chbox.clicked.connect(periodic_change)
window.send_chbox.clicked.connect(periodic_send)

timer.timeout.connect(change_id)
timer_send.timeout.connect(send_can1)

window.read2_btn.clicked.connect(read_can2)
window.show()  # Показываем окно
app.exec()  # и запускаем приложение
