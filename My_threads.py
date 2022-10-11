import datetime

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop
import CANAdater
from EVONode import EVONode
from Parametr import Parametr, empty_par


# поток для сохранения в файл настроек блока
# возвращает сигналу о процентах выполнения, сигнал ошибки - не пустая строка и сигнал окончания сохранения - булево


class SaveToFileThread(QThread):
    SignalOfReady = pyqtSignal(int, str, bool)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    ready_persent = 0

    def __init__(self):
        super().__init__()
        self.max_errors = 30
        self.adapter = CANAdater
        self.node_to_save = EVONode
        self.finished.connect(self.finished_tread)

    def finished_tread(self):
        self.killTimer(self.num_timer)

    def run(self):
        self.errors_counter = 0
        self.params_counter = 0

        def request_param():
            param = all_params_list[self.params_counter]
            # я проверяю, если параметр уже известен, его опрашивать не надо,
            # но если они все известны, возникает выход за пределы словаря
            # while param.value:
            #     self.params_counter += 1
            #     param = all_params_list[self.params_counter]
            if not param.value:
                if param.address and int(param.address, 16) > 0:  # нужно чтоб параметр группы не проскочил
                    param = all_params_list[self.params_counter].get_value(self.adapter)

                    while isinstance(param, str):
                        self.errors_counter += 1
                        param = all_params_list[self.params_counter].get_value(self.adapter)
                        if self.errors_counter >= self.max_errors:
                            self.errors_counter = 0
                            self.params_counter = 0
                            self.SignalOfReady.emit(self.ready_persent,
                                                    f'{param} \n'
                                                    f'поток сохранения прерван,повторите ', False)
                            timer.stop()
                            return

            self.errors_counter = 0
            self.params_counter += 1
            self.ready_persent = int(90 * self.params_counter / len_param_list)
            self.SignalOfReady.emit(self.ready_persent, '', False)
            if self.params_counter >= len_param_list:
                timer.stop()
                self.save_file(all_params_list)

        send_delay = 3  # задержка отправки в кан сообщений
        all_params_list = []
        param_dict = self.node_to_save.group_params_dict.copy()
        for group_name, param_list in param_dict.items():
            e_par = Parametr()
            e_par.name = f'group {group_name}'
            all_params_list.append(e_par)
            for param in param_list:
                all_params_list.append(param)
        len_param_list = len(all_params_list)

        timer = QTimer()
        timer.timeout.connect(request_param)
        self.num_timer = timer.start(send_delay)

        loop = QEventLoop()
        loop.exec_()

    def save_file(self, all_params_list):
        self.errors_counter = 0
        self.params_counter = 0
        save_list = []
        l = 10 / len(all_params_list)
        for p in all_params_list:
            if 'group' in p.name:
                par = empty_par.copy()
                par['name'] = p.name
            else:
                par = p.to_dict().copy()
            self.ready_persent += l
            self.SignalOfReady.emit(self.ready_persent, '', False)

            save_list.append(par.copy())

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f'ECU_Settings/{self.node_to_save.name}_{self.node_to_save.serial_number}_{now}.xlsx'
        df = pd.DataFrame(save_list, columns=p.to_dict().keys())
        df.to_excel(file_name, index=False)
        # вместо строки ошибки отправляем название файла,куда сохранил настройки
        self.SignalOfReady.emit(100, file_name, True)


# поток для опроса параметров и ошибок
class MainThread(QThread):
    # сигнал со списком параметров из текущей группы
    threadSignalAThread = pyqtSignal(list)
    # сигнал с ошибками
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    current_node = EVONode()

    def __init__(self):
        super().__init__()
        self.adapter = CANAdater
        self.errors_str = ''
        self.current_nodes_list = []

    def run(self):
        def emitting():  # передача заполненного списка параметров
            self.threadSignalAThread.emit(self.ans_list)
            self.params_counter = 0
            self.errors_counter = 0
            self.ans_list = []
            self.iter_count += 1
            if self.iter_count > self.max_iteration:  # это нужно для периода опроса от 1 до 1000 и снова
                self.iter_count = 1

        def request_node():
            if not self.len_param_list:
                self.threadSignalAThread.emit(['Пустой список \n Сюда можно добавить параметры двойным кликом по '
                                               'названию нужного параметра'])
                return
            if not self.iter_count == 1:
                while not self.iter_count % self.current_params_list[self.params_counter].period == 0:
                    # если период опроса текущего параметра не кратен текущей итерации,
                    # заполняем его нулями, чтоб в таблице осталось его старое значение
                    # и запрашиваем следующий параметр. Это ускоряет опрос параметров с малым периодом опроса
                    self.ans_list.append(bytearray([0, 0, 0, 0, 0, 0, 0, 0]))
                    self.params_counter += 1
                    if self.params_counter >= self.len_param_list:
                        self.params_counter = 0
                        emitting()
                        return
            param = self.current_params_list[self.params_counter].get_value(self.adapter)
            # если строка - значит ошибка
            if isinstance(param, str):
                self.errors_counter += 1
                if self.errors_counter >= self.max_errors:
                    self.threadSignalAThread.emit([param])
                    return
            else:
                self.errors_counter = 0
            # тут всё просто, собираем весь список и отправляем кучкой
            self.ans_list.append(param)
            self.params_counter += 1
            if self.params_counter >= self.len_param_list:
                self.params_counter = 0
                emitting()

        def request_errors():

            # опрос ошибок, на это время опрос параметров отключается
            timer.stop()
            for nd in self.current_nodes_list:
                errors = nd.check_errors(self.adapter)
                for error in errors:
                    if error and error not in self.errors_str:
                        self.errors_str += f'{nd.name} : {error} \n'
            self.err_thread_signal.emit(self.errors_str)
            timer.start(send_delay)

        send_delay = 13  # задержка отправки в кан сообщений методом подбора с таким не зависает
        err_req_delay = 500
        self.max_errors = 3
        self.len_param_list = len(self.current_params_list)
        if self.len_param_list < self.max_errors:
            self.max_errors = self.len_param_list
        self.ans_list = []
        self.params_counter = 0
        self.errors_counter = 0

        timer = QTimer()
        timer.timeout.connect(request_node)
        timer.start(send_delay)

        err_timer = QTimer()
        err_timer.timeout.connect(request_errors)
        err_timer.start(err_req_delay)

        loop = QEventLoop()
        loop.exec_()
