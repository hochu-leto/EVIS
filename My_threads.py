import datetime
import time

import yaml
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop
from PyQt5.QtWidgets import QMessageBox

from EVONode import EVONode, invertor_command_dict
from Parametr import readme
from helper import buf_to_string


# поток для сохранения в файл настроек блока
# возвращает сигналу о процентах выполнения, сигнал ошибки - не пустая строка и сигнал окончания сохранения - булево
class SaveToFileThread(QThread):
    SignalOfReady = pyqtSignal(int, str, bool)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    ready_persent = 0
    adapter = None

    def __init__(self):
        super().__init__()
        self.max_errors = 30
        self.node_to_save = EVONode()
        self.finished.connect(self.finished_tread)

    def finished_tread(self):
        self.killTimer(self.num_timer)

    def run(self):
        self.errors_counter = 0
        self.params_counter = 0
        self.group_counter = 0
        send_delay = 3  # задержка отправки в кан сообщений
        params_dict = self.node_to_save.group_params_dict.copy()
        # ставлю текущий параметр - самый первый в первом списке параметров
        self.current_params_list = params_dict[list(params_dict.keys())[self.group_counter]]
        self.current_parametr = self.current_params_list[self.params_counter]
        self.one_parametr_percent = 90 / sum([len(group) for group in params_dict.values()])

        def check_par():
            param = self.current_parametr.get_value(self.adapter)
            while isinstance(param, str):
                self.errors_counter += 1
                param = self.current_parametr.get_value(self.adapter)
                # если max_errors раз во время опроса вылезла строковая ошибка, нас отключили, вываливаемся
                if self.errors_counter >= self.max_errors:
                    self.errors_counter = 0
                    self.params_counter = 0
                    self.SignalOfReady.emit(self.ready_persent,
                                            f'{param} \n'
                                            f'поток сохранения прерван,повторите ', False)
                    timer.stop()
                    return False
            # если величина параметра считана, выходим из функции до следующего запуска таймера
            return True

        def request_param():
            # я проверяю, если  величина параметра уже известна, его опрашивать не надо,
            # но если они все известны, возникает выход за пределы словаря
            catch_empty_params = False
            while not catch_empty_params:
                if not self.current_parametr.value and not self.current_parametr.value_string:
                    if not check_par():
                        return
                    catch_empty_params = True
                self.errors_counter = 0
                self.params_counter += 1
                # если опросили все параметры из списка этой группы, переходим к следующей группе
                if self.params_counter > len(self.current_params_list) - 1:
                    self.params_counter = 0
                    self.group_counter += 1
                    # если больше нет групп, выходим с победой, всё опросили, сохраняем
                    if self.group_counter > len(self.node_to_save.group_params_dict.items()) - 1:
                        timer.stop()
                        self.save_file()
                        catch_empty_params = True
                    else:
                        self.current_params_list = params_dict[list(params_dict.keys())[self.group_counter]]

                self.current_parametr = self.current_params_list[self.params_counter]
                self.ready_persent += self.one_parametr_percent
                self.SignalOfReady.emit(int(self.ready_persent), '', False)

        timer = QTimer()
        timer.timeout.connect(request_param)
        timer.start(send_delay)

        loop = QEventLoop()
        loop.exec_()

    def save_file(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        node_yaml_dict = dict(
            date_time=now,
            readme=readme,
            device=self.node_to_save.to_dict())

        file_name = f'ECU_Settings/{self.node_to_save.name}_{self.node_to_save.serial_number}_{now}.yaml'

        with open(file_name, 'w', encoding='UTF-8') as file:
            yaml.dump(node_yaml_dict, file,
                      default_flow_style=False,
                      sort_keys=False,
                      allow_unicode=True)
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
    adapter = None
    is_recording = False
    record_dict = {}
    thread_timer = 0

    def __init__(self):
        super().__init__()
        self.max_errors = 3
        self.current_nodes_dict = {}

    def run(self):
        def emitting(ans_list):
            # передача пустого списка если всё хорошо
            # и строки ошибки в списке если проблемы
            self.thread_timer = time.perf_counter_ns()
            self.threadSignalAThread.emit(ans_list)
            self.params_counter = 0
            self.errors_counter = 0
            self.ans_list = []
            self.iter_count += 1
            if self.iter_count > self.max_iteration:  # это нужно для периода опроса от 1 до 1000 и снова
                self.iter_count = 1

        def request_node():
            if not self.current_params_list:
                emitting(['Пустой список \n Сюда можно добавить параметры двойным кликом по '
                          'названию нужного параметра'])
                return
            current_param = self.current_params_list[self.params_counter]
            if not self.iter_count == 1:
                while not self.iter_count % current_param.period == 0:
                    # если период опроса текущего параметра не кратен текущей итерации,
                    # и запрашиваем следующий параметр. Это ускоряет опрос параметров с малым периодом опроса
                    self.params_counter += 1
                    if self.params_counter >= len(self.current_params_list):
                        self.params_counter = 0
                        emitting([])
                        return
                    current_param = self.current_params_list[self.params_counter]

            param = current_param.get_value(self.adapter)  # ---!!!если параметр строковый, будет None!!---
            # если строка - значит ошибка
            if isinstance(param, str):
                self.errors_counter += 1
            else:
                self.errors_counter = 0

            if self.errors_counter >= self.max_errors:
                self.threadSignalAThread.emit([param])
                return

            self.params_counter += 1
            if self.params_counter >= len(self.current_params_list):
                self.params_counter = 0
                emitting([])
                if self.is_recording:
                    dt = datetime.datetime.now()
                    dt = dt.strftime("%H:%M:%S.%f")
                    self.record_dict[dt] = {par.name: par.value for par in self.current_params_list}
                else:
                    request_errors()

        def request_errors():
            errors_old = self.err_dict.copy()
            for nd in self.current_nodes_dict.values():
                nd.current_errors_list = nd.check_errors(self.adapter).copy()
                nd.current_warnings_list = nd.check_errors(self.adapter, False).copy()
                self.err_dict[nd.name] = list(nd.current_errors_list.union(nd.current_warnings_list))

            if self.err_dict != errors_old:
                self.err_thread_signal.emit(self.err_dict)

        send_delay = 5  # задержка отправки в кан сообщений методом подбора с таким не зависает
        self.params_counter = 0
        self.errors_counter = 0
        self.err_dict = {}

        timer = QTimer()
        timer.timeout.connect(request_node)
        timer.start(send_delay)

        loop = QEventLoop()
        loop.exec_()

    def send_to_mpei(self, command):
        node = self.current_nodes_dict['Инвертор_МЭИ']
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
    SignalOfProcess = pyqtSignal(list, list, int)

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
        self.iter = 0

        def request_ans():
            answer = []
            if (time.perf_counter() > self.end_time) or \
                    self.err_count > self.max_err:
                self.quit()
                self.wait()
                self.SignalOfProcess.emit(['Время закончилось'], self.imp_par_list, None)
                return

            if self.id_for_read:
                ans = self.adapter.can_read(self.id_for_read)  # приходит список кадров, если всё хорошо

                if isinstance(ans, dict):
                    for ti, a in ans.items():
                        print(ti - self.old_ti, buf_to_string(a))
                        self.old_ti = ti
                        byte_a = a[self.answer_byte]
                        self.err_count = 0
                        if byte_a in self.answer_dict:
                            answer.append(self.answer_dict[byte_a])
                else:
                    print(ans, hex(self.id_for_read))
                    self.err_count += 1

            if self.imp_par_list:
                try:
                    self.imp_par_list[self.iter].get_value(self.adapter)
                    self.iter += 1
                except IndexError:
                    self.iter = 0

            self.SignalOfProcess.emit(answer, self.imp_par_list, None)

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
