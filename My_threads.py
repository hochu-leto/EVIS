import datetime
import time

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop
from PyQt5.QtWidgets import QMessageBox

from EVONode import EVONode, invertor_command_dict
from Parametr import Parametr
from helper import empty_par, buf_to_string


# поток для сохранения в файл настроек блока
# возвращает сигналу о процентах выполнения, сигнал ошибки - не пустая строка и сигнал окончания сохранения - булево

class SaveToFileThread(QThread):
    SignalOfReady = pyqtSignal(int, str, bool)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    ready_persent = 0
    adapter = None  # CANAdapter()

    def __init__(self):
        super().__init__()
        self.max_errors = 30
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
        df.to_excel(file_name, index=False)  # , sheet_name=self.node_to_save.name, encoding='windows-1251')
        # вместо строки ошибки отправляем название файла,куда сохранил настройки
        self.SignalOfReady.emit(100, file_name, True)


# поток для опроса параметров и ошибок
class MainThread(QThread):
    # сигнал со списком параметров из текущей группы
    threadSignalAThread = pyqtSignal(list)
    # сигнал с ошибками
    err_thread_signal = pyqtSignal(dict)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    current_node = EVONode()
    adapter = None  # CANAdapter()
    magic_word = 100794368

    def __init__(self):
        super().__init__()
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
            current_param = self.current_params_list[self.params_counter]
            if not self.iter_count == 1:
                while not self.iter_count % current_param.period == 0:
                    # если период опроса текущего параметра не кратен текущей итерации,
                    # заполняем его нулями, чтоб в таблице осталось его старое значение
                    # и запрашиваем следующий параметр. Это ускоряет опрос параметров с малым периодом опроса
                    self.ans_list.append(bytearray([0, 0, 0, 0, 0, 0, 0, 0]))
                    self.params_counter += 1
                    if self.params_counter >= self.len_param_list:
                        self.params_counter = 0
                        emitting()
                        return
            if current_param.node.name in (node.name for node in self.current_nodes_list):
                param = current_param.get_value(self.adapter)
                # если строка - значит ошибка
                if isinstance(param, str):
                    self.errors_counter += 1
                    if self.errors_counter >= self.max_errors:
                        self.threadSignalAThread.emit([param])
                        return
                else:
                    self.errors_counter = 0
                    if param == self.magic_word:
                        current_param.period = 1001
                        current_param.value = 'Параметр \nотсутствует'
            else:
                param = 'Блок не подключен'
                current_param.value = param
            # тут всё просто, собираем весь список и отправляем кучкой
            # какая-то херня. мне, по-факту этот список вообще нахер не нужен, сюда можно чисто ошибки пихать
            # , значения всё равно в текущем списке параметров
            self.ans_list.append(param)
            self.params_counter += 1
            if self.params_counter >= self.len_param_list:
                self.params_counter = 0
                emitting()

        def request_errors():
            # опрос ошибок, на это время опрос параметров отключается
            timer.stop()
            err_dict = {}
            has_new_err = False
            for nd in self.current_nodes_list:
                old_e_len = len(nd.current_errors_list)
                old_w_len = len(nd.current_warnings_list)

                nd.current_errors_list = nd.check_errors(self.adapter).copy()
                nd.current_warnings_list = nd.check_errors(self.adapter, 'warnings').copy()
                if len(nd.current_errors_list) != old_e_len or len(nd.current_warnings_list) != old_w_len:
                    has_new_err = True
                err_dict[nd.name] = sorted(list(nd.current_errors_list.union(nd.current_warnings_list)))

            if has_new_err:
                self.err_thread_signal.emit(err_dict)
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

    def send_to_mpei(self, command):
        answer = 'Команда не прошла'
        for node in self.current_nodes_list:
            if node.name == 'Инвертор_МЭИ':
                # передавать надо исключительно в первый кан
                if node.request_id in self.adapter.id_nodes_dict.keys():
                    adapter_can1 = self.adapter.id_nodes_dict[node.request_id]
                    if self.isRunning():
                        self.wait(100)
                    answer = node.send_val(invertor_command_dict[command][0], adapter_can1)
                else:
                    answer = 'Нет связи с CAN1-адаптером'
        return answer

    def invertor_command(self, command: str, tr=None):
        w = None
        if command not in invertor_command_dict.keys():
            return 'Неверная Команда'

        warn_str = invertor_command_dict[command][2]
        if not warn_str or \
                QMessageBox.information(w, "Информация", warn_str,
                                        QMessageBox.Ok, QMessageBox.Cancel) == QMessageBox.Ok:
            answer = self.send_to_mpei(command)
            if answer:
                answer = 'Команду выполнить не удалось\n' + answer
                QMessageBox.critical(w, "Ошибка", answer, QMessageBox.Ok)
            else:
                if tr is not None:
                    return ''
                answer = invertor_command_dict[command][1]
                QMessageBox.information(w, "Успешный успех!", answer, QMessageBox.Ok)
            return answer
        return 'Команда отменена пользователем'


class WaitCanAnswerThread(QThread):
    SignalOfProcess = pyqtSignal(list, list)

    def __init__(self):
        super().__init__()
        self.finished_tread()
        self.finished.connect(self.finished_tread)

    def finished_tread(self):
        self.adapter = None
        self.id_for_read = 0
        self.answer_byte = 0
        self.answer_dict = {}
        self.wait_time = 15  # максимальное время в секундах, через которое поток отключится
        self.max_err = 20
        self.req_delay = 100
        self.imp_par_list = []

    def run(self):
        self.err_count = 0
        self.end_time = time.perf_counter() + self.wait_time
        self.old_ti = 0

        def request_ans():
            answer = []
            if (time.perf_counter() > self.end_time) or \
                    self.err_count > self.max_err:
                self.quit()
                self.wait()
                self.SignalOfProcess.emit(['Время закончилось'], self.imp_par_list)
                return

            if self.id_for_read:
                ans = self.adapter.can_read(self.id_for_read)   # приходит список кадров, если всё хорошо

                if isinstance(ans, dict):
                    for ti, a in ans.items():
                        # print(ti - self.old_ti, buf_to_string(a))
                        self.old_ti = ti
                        byte_a = a[self.answer_byte]
                        self.err_count = 0
                        if byte_a in self.answer_dict:
                            answer.append(self.answer_dict[byte_a])
                else:
                    # print(ans)
                    self.err_count += 1

            if self.imp_par_list:
                for param in self.imp_par_list:
                    param.get_value(self.adapter)
            self.SignalOfProcess.emit(answer, self.imp_par_list)

        timer = QTimer()
        timer.timeout.connect(request_ans)
        timer.start(self.req_delay)

        loop = QEventLoop()
        loop.exec_()


class SleepThread(QThread):
    SignalOfProcess = pyqtSignal(int, str, bool)
    ready_persent = 0

    def __init__(self, tme: int):
        super().__init__()
        self.time = tme

    def run(self):
        end_time = time.perf_counter() + self.time
        while time.perf_counter() < end_time:
            self.ready_persent = (end_time - time.perf_counter()) * 100 / self.time
            self.SignalOfProcess.emit(self.ready_persent, '', False)
        self.quit()
        self.wait()
