import datetime
import pathlib
import time
import yaml
from PyQt6.QtCore import QThread, pyqtSignal, QTimer, QEventLoop
from PyQt6.QtWidgets import QMessageBox
from EVONode import EVONode, invertor_command_dict
from EVOParametr import readme, Parametr
from helper import buf_to_string, find_param, DialogChange
from work_with_file import SETTINGS_DIR


# поток для сохранения в файл настроек блока
# возвращает сигнал о процентах выполнения,
# сигнал ошибки - не пустая строка и сигнал окончания сохранения - булево
class SaveToFileThread(QThread):
    SignalOfReady = pyqtSignal(int, str, bool)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    ready_percent = 0
    adapter = None

    def __init__(self, node_for_save=EVONode()):
        super().__init__()
        self.all_params_list = []
        self.ms_box = QMessageBox()
        self.ms_box.setWindowTitle('Сохранение')
        self.ms_box.setText('Идёт сохранение параметров в файл, ждите')
        self.group_counter = 0
        self.params_counter = 0
        self.errors_counter = 0
        self.current_parametr = None
        self.one_parametr_percent = 1
        self.max_errors = 30
        self.node_to_save = node_for_save

    def run(self):
        self.errors_counter = 0
        self.params_counter = 0
        self.group_counter = 0
        self.ready_percent = 0
        send_delay = 3  # задержка отправки в кан сообщений
        params_dict = self.node_to_save.group_params_dict.copy()
        # ставлю текущий параметр - самый первый в первом списке параметров
        self.current_params_list = params_dict[list(params_dict.keys())[self.group_counter]]
        self.current_parametr = self.current_params_list[self.params_counter]
        self.one_parametr_percent = 90 / sum([len(group) for group in params_dict.values()])
        self.all_params_list = [parametr for group_list in self.node_to_save.group_params_dict.values()
                                for parametr in group_list]

        #  подфункция, конечно же это неправильно. но пока работает, не буду это трогать пока не поумнею
        def check_par():
            param = self.current_parametr.get_value(self.adapter)
            while isinstance(param, str):
                self.errors_counter += 1
                param = self.current_parametr.get_value(self.adapter)
                # если max_errors раз во время опроса вылезла строковая ошибка, нас отключили, вываливаемся
                if self.errors_counter >= self.max_errors:
                    self.errors_counter = 0
                    self.params_counter = 0
                    self.SignalOfReady.emit(int(self.ready_percent),
                                            f'{param} \n'
                                            f'поток сохранения прерван,повторите ', False)
                    timer.stop()
                    return False
            # если величина параметра считана, выходим из функции до следующего запуска таймера
            return True

        def request_param():
            # я проверяю, если  величина параметра уже известна, его опрашивать не надо, - это НЕПРАВИЛЬНО FIXME
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
                        return
                    else:
                        self.current_params_list = params_dict[list(params_dict.keys())[self.group_counter]]

                self.current_parametr = self.current_params_list[self.params_counter]
                self.ready_percent += self.one_parametr_percent
                self.SignalOfReady.emit(int(self.ready_percent), '', False)

        def get_param():
            self.current_parametr = self.all_params_list[self.params_counter]
            check_par()
            self.ready_percent += self.one_parametr_percent
            self.SignalOfReady.emit(int(self.ready_percent), '', False)
            self.params_counter += 1
            if self.params_counter > len(self.all_params_list) - 1:
                timer.stop()
                self.save_file()
                return

        timer = QTimer()
        timer.timeout.connect(get_param)
        timer.start(send_delay)

        loop = QEventLoop()
        loop.exec()

    def save_file(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        node_yaml_dict = dict(
            date_time=now,
            readme=readme,
            device=self.node_to_save.to_dict())

        file_name = f'{self.node_to_save.name}_{self.node_to_save.serial_number}_{now}.yaml'
        file_name = pathlib.Path(SETTINGS_DIR, file_name)
        self.SignalOfReady.emit(95, '', False)
        with open(file_name, 'w', encoding='UTF-8') as file:
            yaml.dump(node_yaml_dict, file,
                      default_flow_style=False,
                      sort_keys=False,
                      allow_unicode=True)
        # вместо строки ошибки отправляем название файла, куда сохранил настройки
        self.ms_box.hide()
        self.SignalOfReady.emit(100, str(file_name), True)


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

    def __init__(self, parent=None):
        super().__init__()
        self.max_errors = 3
        self.current_nodes_dict = {}
        self.parent = parent
        self.make_plot = []

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
            try:
                current_param = self.current_params_list[self.params_counter]
                if not self.iter_count == 1:
                    while not self.iter_count % current_param.period == 0:
                        # если период опроса текущего параметра не кратен текущей итерации,
                        # и запрашиваем следующий параметр. Это ускоряет опрос параметров с малым периодом опроса
                        self.params_counter += 1
                        if self.params_counter >= len(self.current_params_list):
                            self.params_counter = 0
                            emitting(self.make_plot)
                            return
                        current_param = self.current_params_list[self.params_counter]
            except IndexError:
                print(f'Ошибка!!!!!!! Счётчик = {self.params_counter}, а длина списка параметров = '
                      f'{len(self.current_params_list)}, придётся брать параметр = {self.current_params_list[0].name}')
                current_param = self.current_params_list[0]

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
                emitting(self.make_plot)
                if self.is_recording:
                    dt = datetime.datetime.now()
                    dt = dt.strftime("%H:%M:%S.%f")
                    now_values_dict = {}
                    for par in self.current_params_list:
                        if par.value_string:
                            val = par.value_string
                        elif par.value_table:
                            val = par.value_table[int(par.value)]
                        else:
                            val = par.value
                        now_values_dict[par.name] = val
                    self.record_dict[dt] = now_values_dict.copy()
                elif not self.make_plot:
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
        loop.exec()

    def send_to_mpei(self, command):
        node = self.current_nodes_dict['Инвертор_МЭИ']
        # передавать надо исключительно в первый кан
        # есть же функция определения адаптера для блока, следует здесь использовать её
        if node.request_id in self.adapter.id_nodes_dict.keys():
            adapter_can1 = self.adapter.id_nodes_dict[node.request_id]
            if self.isRunning():
                self.wait(100)
            answer = node.send_val(invertor_command_dict[command][0], adapter_can1)
        else:
            answer = 'Нет связи с CAN1-адаптером'
        return answer

    def invertor_command(self, command: str, tr=None):
        w = self.parent
        if command not in invertor_command_dict.keys():
            return 'Неверная Команда'

        warn_str = invertor_command_dict[command][2]
        if warn_str:
            points_list = None
            if '-' in warn_str:
                points_list = warn_str.split('-')
                warn_str = points_list.pop(0)
            dialog = DialogChange(label=warn_str, check_boxes=points_list)
            dialog.setWindowTitle('Управление Инвертором МЭИ')
            if not dialog.exec():
                return 'Команда отменена пользователем'
        answer = self.send_to_mpei(command)
        if answer:
            answer = 'Команду выполнить не удалось\n' + answer
            QMessageBox.critical(w, "Ошибка", answer, QMessageBox.StandardButton.Ok)
        else:
            if tr is not None:
                return ''
            answer = invertor_command_dict[command][1]
            QMessageBox.information(w, "Успешный успех!", answer, QMessageBox.StandardButton.Ok)
        return answer


class WaitCanAnswerThread(QThread):
    SignalOfProcess = pyqtSignal(list, list, int)
    FinishedSignal = pyqtSignal()

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
        self.imp_par_set = set()
        self.command_list = []
        self.FinishedSignal.emit()

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
                self.SignalOfProcess.emit(['Время закончилось'], list(self.imp_par_set), self.iter)
                return
            # когда нужно ждать ответ от конкретного адреса, как джойстик или инвертор
            if self.id_for_read:
                ans = self.adapter.can_read(self.id_for_read)  # приходит список кадров, если всё хорошо

                if isinstance(ans, dict):
                    for ti, a in ans.items():  # давно было, похоже ключ-это время принятия фрейма
                        print(ti - self.old_ti, buf_to_string(a))
                        self.old_ti = ti
                        byte_a = a[self.answer_byte]
                        self.err_count = 0
                        if byte_a in self.answer_dict:
                            answer.append(self.answer_dict[byte_a])
                else:
                    print(ans, hex(self.id_for_read))
                    self.err_count += 1
            # случай когда нужно опрашивать параметры из блоков
            if self.imp_par_set:
                try:
                    list(self.imp_par_set)[self.iter].get_value(self.adapter)
                    self.iter += 1
                except IndexError:
                    self.iter = 0
            # противоположный случай, когда нужно задавать параметры с определёнными значениями
            elif self.command_list:
                try:
                    it = list(self.command_list)[self.iter]
                    if isinstance(it, Parametr):
                        it.set_value(self.adapter, it.value)
                    else:
                        try:
                            self.adapter.can_write(it.id, it.data)
                            self.SignalOfProcess.emit([], [], self.iter)
                        except Exception as e:
                            self.err_count += 1
                            print(f'Что-то пошло не по плану - ошибка {e}')
                    self.iter += 1
                except IndexError:
                    self.iter = 0
            if answer or self.imp_par_set:
                self.SignalOfProcess.emit(answer, list(self.imp_par_set), None)

        request_ans()
        timer = QTimer()
        timer.timeout.connect(request_ans)
        timer.start(self.req_delay)

        loop = QEventLoop()
        loop.exec()


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


class SteerParametr:

    def __init__(self, name: str, warning='', nominal_value=0, min_value=0, max_value=0):
        self.name = name
        self.parametr = None
        self.warning = warning
        self.nominal_value = nominal_value
        self.current_value = 0
        self.max_value = max_value
        self.min_value = min_value

    def check(self):
        if self.max_value and self.min_value:
            if self.min_value < self.current_value < self.max_value:
                return True
        elif self.current_value == self.nominal_value:
            return True
        if self.warning:
            QMessageBox.critical(None, "Ошибка ", self.warning,
                                 QMessageBox.StandardButton.Ok)
        return False


class SteerMoveThread(QThread):
    SignalOfProcess = pyqtSignal(list, list, int)

    def __init__(self, steer: EVONode, adapter):
        super().__init__()
        # словарь с параметрами, которые опрашиваем
        self.success_counter = 0
        self.result = None
        self.err_counter = None
        self.parameters_get = dict(
            status=SteerParametr(name='A0.1 Status', warning='БУРР должен быть неактивен'),
            alarms=SteerParametr(name='A0.0 Alarms', warning='В блоке есть ошибки'),
            position=SteerParametr(name='A0.3 ActSteerPos', warning='Рейка НЕ в нулевом положении', min_value=-7,
                                   max_value=7),
            current=SteerParametr(name='A1.7 CurrentRMS', min_value=1, max_value=100),
            serial=SteerParametr(name='B0.9 Serial_Number', min_value=1, max_value=1000))
        # словарь с параметрами, которые задаём
        self.parameters_set = dict(
            current=SteerParametr(name='C5.3 rxSetCurr', warning='Ток ограничения рейки задан неверно',
                                  nominal_value=70, min_value=1, max_value=90),
            command=SteerParametr(name='D0.0 ComandSet', max_value=5),
            control=SteerParametr(name='D0.6 CAN_Control', nominal_value=2, max_value=2),
            position=SteerParametr(name='A0.2 SetSteerPos', min_value=-1000, max_value=1000))
        self.node = steer
        self.adapter = adapter
        self.max_iteration = 7
        self.time_for_moving = 17  # время для движения в секундах
        self.time_for_request = 0.02  # время опроса - 20мс
        self.time_for_set = 0.2  # время наращивания тока - 200мс
        self.delta_current = 0.5  # кусочки тока для добавления
        # определяем все параметры
        for par in list(self.parameters_get.values()) + list(self.parameters_set.values()):
            par.parametr = find_param(par.name, self.node)[0]
            if not par.parametr:
                print(f'Не найден параметр{par.name}')

        self.current_position = self.parameters_set['position'].nominal_value
        self.min_position = self.parameters_set['position'].min_value
        self.max_position = self.parameters_set['position'].max_value
        self.max_current = self.parameters_get['current'].max_value
        self.params_for_view = [self.parameters_get['current'].parametr, self.parameters_get['position'].parametr]
        self.progress = 0
        self.percent_of_progress = 1

    def get_param(self, param: SteerParametr):
        for i in range(self.max_iteration):
            value = param.parametr.get_value(self.adapter)
            if not isinstance(value, str):
                return value
        print(f'Запросить {param.name} не удалось')
        self.err_counter += 1
        return None

    def set_param(self, param: SteerParametr, value: int):
        err = 'Неизвестная ошибка'
        if value > param.max_value:
            value = param.max_value
        if value < param.min_value:
            value = param.min_value
        for i in range(self.max_iteration):
            err = param.parametr.set_value(self.adapter, value)
            if not err:
                compare = self.get_param(param)
                if int(compare) == int(value):
                    return True
        self.err_counter += 1
        print(f'Задать {value} для {param.name} не удалось', err)
        return False

    def actual_position(self):
        self.current_position = self.get_param(self.parameters_get['position'])
        return self.current_position

    def actual_current(self):
        return self.get_param(self.parameters_get['current'])

    # это только задание положения, ещё не вращение
    def set_position(self, value: int):
        if value > self.max_position:
            value = self.max_position
        elif value < self.min_position:
            value = self.min_position
        if not self.set_param(self.parameters_set['position'], value):
            return False
        return True

    # задаём максимальный рабочий ток
    def set_current(self, value: int):
        if value > self.max_current:
            value = self.max_current
        if not self.set_param(self.parameters_set['current'], value):
            return False
        return True

    # задание движения, за показаниями не следим, мотор не выключаем
    def move_to(self, value: int):
        # если есть ошибки, не включаем
        err = list([error.name for error in self.node.check_errors(self.adapter)])
        if err:
            errs = "\n - ".join(err)
            print(f' В блоке ошибки {errs}')
            return False

        return self.set_position(value)

    # задаю команду на местное управление
    def switch_mode_on(self):
        if not self.set_param(self.parameters_set['control'], 0):
            print(f'Не удалось перейти в тестовый режим')
            return False
        return True

    # включаю мотор
    def turn_on_motor(self):
        if not self.set_param(self.parameters_set['command'], 1):
            print(f'Не удалось включить мотор')
            return False
        return True

    # возвращаю всё на штатные значения
    def stop(self):
        result = False
        iterator = 0
        while not result:
            for par in self.parameters_set.values():
                self.set_param(par, par.nominal_value)
            time.sleep(0.5)
            result = True
            for par in self.parameters_set.values():
                compare = self.get_param(par)
                if compare is None:
                    result = False
                elif int(compare) != int(par.nominal_value):
                    print(f'Не удалось задать {par.name} получилось {compare}, а должно быть {par.nominal_value}')
                    result = False
            iterator += 1
            if iterator > self.max_iteration:
                return False
        return True

    def set_straight_sharp(self):
        # нужно усовершенствовать процедуру приведения в ноль
        # - подвели к нулю, отключили мотор, проверили остаточное,
        # если больше дельты, переводим не в ноль,
        # а в остаточное с обратным знаком, выключаем мотор и снова смотрим остаточное
        # и так несколько итераций, пока при отключенном моторе остаточное не будет в пределах дельты
        # перепробовал разные коэффициенты для дельты, не выходит она в ноль,
        # резина не даёт нужно по другому как-то сейчас не использую эту функцию, потому что вечный цикл возможен
        time.sleep(0.5)
        self.current_position = self.actual_position()
        while self.current_position > self.parameters_get['position'].max_value or \
                self.current_position < self.parameters_get['position'].min_value:
            self.set_straight()
            time.sleep(0.5)
            self.current_position = self.actual_position()

    def set_straight(self):
        self.actual_position()
        # задаём команду на поворот в ноль, ставим номинальный ток
        if self.move_to(self.parameters_set['position'].nominal_value) and \
                self.set_param(self.parameters_set['current'], self.parameters_set['current'].nominal_value):
            current_time = start_time = time.perf_counter()
            # а дальше смотрим за текущими параметрами пока не вышло время
            while time.perf_counter() < start_time + self.time_for_moving:
                # регулярно опрашиваем текущее положение
                if time.perf_counter() > current_time + self.time_for_request:
                    current_time = time.perf_counter()
                    self.actual_position()
                #  выходим с победой если попали в нужный диапазон
                if self.parameters_get['position'].min_value < \
                        self.current_position < self.parameters_get['position'].max_value:
                    return True
        return False

    def define_current(self, value: int, current=None):
        result = f'Упёрлись в ограничение по времени {self.time_for_moving}с '
        # задаём минимальный ток для начала вращения
        if current is None:
            current = self.parameters_get['current'].min_value
        cur = self.set_current(current)
        # и задаём команду на вращение
        move = self.move_to(value)
        if move and cur:
            current_set_time = current_time = start_time = time.perf_counter()
            # а дальше смотрим за текущими параметрами пока не вышло время
            while time.perf_counter() < start_time + self.time_for_moving:
                if time.perf_counter() > current_time + self.time_for_request:
                    current_time = time.perf_counter()
                    self.actual_current()
                    if self.actual_position() is not None:
                        progress = abs(self.current_position) * self.percent_of_progress
                        self.SignalOfProcess.emit([], self.params_for_view, int(self.progress + progress))
                    else:
                        self.current_position = 0
                        print(' Неудачный опрос текущей позиции')
                # регулярно добавляем ток если рейка не движется
                if time.perf_counter() > current_set_time + self.time_for_set:
                    current_set_time = time.perf_counter()
                    current += self.delta_current
                    self.set_current(current)
                    if current > self.max_current:
                        result = f'Упёрлись в ограничение по току {round(current, 2)}'
                        break

                if value + self.parameters_get['position'].min_value < \
                        self.current_position < value + self.parameters_get['position'].max_value:
                    result = round(current, 2)
                    self.success_counter += 1
                    break

                if self.err_counter > self.max_iteration:
                    self.SignalOfProcess.emit(['Слишком много ошибок, повторите процедуру'], self.params_for_view, 0)
                    self.stop()
                    self.wait()
                    self.quit()
                    return 'Много ошибок'
        else:
            print(f"Не удалось или задать ток {cur=} или перейти в тестовый режим {move=}")
        return result

    def run(self):
        self.result = []
        self.err_counter = 0
        self.success_counter = 0
        divider = 10
        full_progress = abs(self.min_position + self.min_position / divider) + \
                        abs(self.max_position + self.max_position / divider)
        self.percent_of_progress = 100 / full_progress

        self.switch_mode_on()
        self.turn_on_motor()

        self.set_straight()
        self.SignalOfProcess.emit(['Страгиваем влево...'], [], int(self.progress))
        min_go = self.min_position / divider
        start_current_left = self.define_current(int(min_go))
        text = f'Ток страгивания влево на величину {min_go} = {start_current_left}А'
        self.result.append(text)
        print(text)

        self.set_straight()
        self.progress += abs(min_go) * self.percent_of_progress
        self.SignalOfProcess.emit([text, 'Страгиваем вправо...'], [], int(self.progress))
        min_go = self.max_position / divider
        start_current_right = self.define_current(int(min_go))
        text = f'Ток страгивания вправо на величину {min_go} = {start_current_right}А'
        self.result.append(text)
        print(text)

        self.set_straight()
        self.progress += abs(min_go) * self.percent_of_progress
        self.time_for_moving = 30
        self.SignalOfProcess.emit([text, 'Выворачиваем полностью влево...'], [], int(self.progress))
        if isinstance(start_current_left, str):
            start_current_left = self.max_current / 5
        self.delta_current = start_current_left / 5
        self.time_for_set = start_current_left / 5
        full_current_left = self.define_current(self.min_position, start_current_left * 1.2)
        text = f'Ток максимального выворота влево = {full_current_left}А'
        self.result.append(text)
        print(text)

        self.set_straight()
        self.progress += abs(self.min_position) * self.percent_of_progress
        self.SignalOfProcess.emit([text, 'Выворачиваем полностью вправо...'], [], int(self.progress))
        if isinstance(start_current_right, str):
            start_current_right = self.max_current / 5
        self.delta_current = start_current_right / 5
        self.time_for_set = start_current_right / 5
        full_current_right = self.define_current(self.max_position, start_current_right * 1.2)
        text = f'Ток максимального выворота вправо = {full_current_right}А'
        self.result.append(text)
        print(text)

        self.set_straight_sharp()
        self.progress += abs(self.max_position) * self.percent_of_progress
        suc = ' УСПЕШНО' if self.success_counter >= 4 else ' НЕУДАЧНО, рекомендуется повторить'
        self.result.append(suc)
        self.SignalOfProcess.emit([text, f'Процедура завершена{suc}',
                                   'Файл проверки сохранён в папку /BURR_current/'], [], int(self.progress))
        self.stop()
        self.quit()
        self.wait()
        self.save_to_file()

    def save_to_file(self):
        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        serial = self.get_param(self.parameters_get['serial'])
        if not isinstance(serial, str):
            serial = int(serial)
        node_yaml_dict = dict(
            date_time=now,
            burr_name=self.node.name,
            serial_number=serial,
            result=self.result)
        file_name = f'BURR_current/{serial}_{now}.yaml'
        with open(file_name, 'w', encoding='UTF-8') as file:
            yaml.dump(node_yaml_dict, file,
                      default_flow_style=False,
                      sort_keys=False,
                      allow_unicode=True)
