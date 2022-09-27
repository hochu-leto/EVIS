# поток для опроса параметров и ошибок
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop
import CANAdater
from EVONode import EVONode


class MyThread(QThread):
    SignalOfReady = pyqtSignal(int)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    ready_persent = 0

    def __init__(self, node: EVONode, adapter: CANAdater):
        super().__init__()
        self.errors_counter = 0
        self.params_counter = 0
        self.max_errors = 3
        self.adapter = adapter

    def run(self):
        def emitting():  # передача заполненного списка параметров
            self.SignalOfReady.emit(self.ready_persent)
            self.params_counter = 0
            self.errors_counter = 0

        def request_param():
            param = self.current_params_list[self.params_counter].get_value(self.adapter)

            if isinstance(param, str):
                self.errors_counter += 1
                if self.errors_counter >= self.max_errors:
                    self.SignalOfReady.emit([param])
                    return
            else:
                self.errors_counter = 0
            self.ans_list.append(param)
            self.params_counter += 1
            if self.params_counter >= self.len_param_list:
                self.params_counter = 0
                emitting()

        send_delay = 10  # задержка отправки в кан сообщений
        timer = QTimer()
        timer.timeout.connect(request_param)
        timer.start(send_delay)

        loop = QEventLoop()
        loop.exec_()
