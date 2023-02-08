import time

from PyQt6.QtCore import pyqtSlot, QTimer, QEventLoop
from PyQt6.QtWidgets import QMessageBox, QDialogButtonBox

import CANAdater
from EVONode import EVONode
from EVOThreads import WaitCanAnswerThread, SleepThread
from helper import find_param, DialogChange

'''
0х18FF82A5  
1.1-2 Управление левым поворотником (1 - горит, 0 - погашен) 
1.3-4 Управление правым поворотником (1 - горит, 0 - погашен) 
1.5-6 Команда управления стоп-сигналами  
1.7-8 Команда управления сигналом заднего хода 
2.1-2 Команда управления фонарями ближнего света  
2.3-4 Команда управления фонарями дальнего света  
'''
wait_thread = WaitCanAnswerThread()
sleep_thread = SleepThread(3)
light_id_vmu = 0x18FF82A5

light_commamd_dict = dict(
    off_rbtn=[0b00000000, 0b00000000],
    left_side_rbtn=[0b00000001, 0b00000000],
    right_side_rbtn=[0b00000100, 0b00000000],
    stop_light_rbtn=[0b00010000, 0b00000000],
    rear_light_rbtn=[0b01000000, 0b00000000],
    low_beam_rbtn=[0b00000000, 0b00000001],
    high_beam_rbtn=[0b00000000, 0b00000100],
)


def save_to_eeprom(window, node=None):
    if not node:
        node = window.thread.current_node

    if node.save_to_eeprom:
        if window.thread.isRunning():
            window.connect_to_node()
            isRun = True
        else:
            isRun = False

        adapter = adapter_for_node(window.thread.adapter, node)
        if adapter:
            if node.name == 'Инвертор_МЭИ':
                err = save_to_eeprom_mpei(window, node, adapter)
            else:
                err = node.send_val(node.save_to_eeprom, adapter, value=1)
        else:
            err = 'Нет адаптера для этого блока'

        if err:
            QMessageBox.critical(window, "Ошибка ", f'Настройки сохранить не удалось\n{err}',
                                 QMessageBox.StandardButton.Ok)
            window.log_lbl.setText('Настройки в память НЕ сохранены, ошибка ' + err)
        else:
            QMessageBox.information(window, "Успешный успех!", 'Текущие настройки сохраняются в EEPROM',
                                    QMessageBox.StandardButton.Ok)
            window.log_lbl.setText('Настройки сохранены в EEPROM')
            node.param_was_changed = False
            # erase_errors()
            window.save_eeprom_btn.setEnabled(False)

        if window.thread.isFinished() and isRun:
            window.connect_to_node()
    else:
        QMessageBox.information(window, "Информация", f'В {node.name} параметры сохранять не нужно',
                                QMessageBox.StandardButton.Ok)
        window.save_eeprom_btn.setEnabled(False)


def save_to_eeprom_mpei(window, node, adapter):
    sleep_thread.SignalOfProcess.connect(window.progress_bar_fulling)
    voltage = find_param('DC_VOLTAGE', node=node.name,
                         nodes_dict=window.thread.current_nodes_dict)[0]
    err = voltage.get_value(adapter)
    if not isinstance(err, str):
        # Сохраняем в ЕЕПРОМ Инвертора МЭИ только если выключено высокое - напряжение ниже 30В
        if err < 30:
            err = node.send_val(node.save_to_eeprom, adapter)
            sleep_thread.start()
        else:
            err = 'Высокое напряжение не выключено\nВыключи высокое напряжение и повтори сохранение'
    else:
        err = f'Некорректный ответ от инвертора\n{err}'
    return err


# --------------------------------------------------- кнопки управления ----------------------------------------------
def load_from_eeprom(window):
    node = window.thread.current_nodes_dict['КВУ_ТТС']
    adapter = adapter_for_node(window.thread.adapter, node)
    if adapter:
        print('Отправляю команду на запрос из еепром')
        # такое чувство что функция полное говно и пора бы уже сделать её универсальной для всех блоков
        answer = node.send_val(0x210201, adapter, value=0x01)  # это адрес вытащить из еепром для кву ттс
        if answer:
            answer = 'Команду выполнить не удалось\n' + answer
        else:
            QMessageBox.information(window, "Успешный успех!", 'Параметры загружены из ЕЕПРОМ',
                                    QMessageBox.StandardButton.Ok)
            node.param_was_changed = False
            return
    else:
        answer = 'В списке адаптеров канал 250 не найден'

    QMessageBox.critical(window, "Ошибка", answer, QMessageBox.StandardButton.Ok)


def mpei_invert(window):
    m = window.thread.invertor_command('INVERT_ROTATION')
    window.log_lbl.setText(m)


def mpei_power_on(window):
    m = window.thread.invertor_command('POWER_ON')
    window.log_lbl.setText(m)


def mpei_power_off(window):
    m = window.thread.invertor_command('POWER_OFF')
    window.log_lbl.setText(m)


def mpei_reset_device(window):
    m = window.thread.invertor_command('RESET_DEVICE')
    window.log_lbl.setText(m)


def mpei_reset_params(window):
    m = window.thread.invertor_command('RESET_PARAMETERS')
    window.log_lbl.setText(m.replace('\n', ''))


# ---------------------------------------------- кнопки с диалогом ----------------------------------------------------
def mpei_calibrate(window):
    @pyqtSlot(list, list)
    def check_dialog_mess(st, list_of_params):
        if wait_thread.isRunning():
            dialog.change_mess(st, list_of_params)
        else:
            print('Поток калибровки остановлен')
            node = window.thread.current_nodes_dict['Инвертор_МЭИ']
            adapter = adapter_for_node(window.thread.adapter, node)
            if adapter:
                faults = list(node.check_errors(adapter=adapter))
                if not faults:
                    st.append('Ошибок во время калибровки не появилось')
                else:
                    faults.insert(0, 'Во время калибровки возникли ошибки: ')
                    st += faults
                dialog.change_mess(st)

    param_list_for_calibrate = ['FAULTS', 'DC_VOLTAGE', 'DC_CURRENT',
                                'PHA_CURRENT', 'PHB_CURRENT', 'PHC_CURRENT']
    n_name = 'Инвертор_МЭИ'
    for p_name in param_list_for_calibrate:
        wait_thread.imp_par_set.add(
            find_param(p_name, node=n_name,
                       nodes_dict=window.thread.current_nodes_dict)[0])
    wait_thread.imp_par_set.add(find_param('TORQUE', node=n_name,
                                           nodes_dict=window.thread.current_nodes_dict)[2])
    wait_thread.imp_par_set.add(find_param('SPEED_RPM', node=n_name,
                                           nodes_dict=window.thread.current_nodes_dict)[1])

    wait_thread.req_delay = 50
    wait_thread.adapter = window.thread.adapter.adapters_dict[125]
    wait_thread.id_for_read = 0x381
    wait_thread.answer_byte = 4
    wait_thread.answer_dict = {0x0A: 'Калибровка прошла успешно!',
                               0x0B: 'Калибровка не удалась',
                               0x0C: 'Настройки сохранены в ЕЕПРОМ'}

    dialog = DialogChange(label='Процесс калибровки',
                          text='Команда на калибровку отправлена',
                          table=list(wait_thread.imp_par_set))
    dialog.setWindowTitle('Калибровка Инвертора МЭИ')

    wait_thread.SignalOfProcess.connect(check_dialog_mess)

    s = window.thread.invertor_command('BEGIN_POSITION_SENSOR_CALIBRATION', wait_thread)
    if not s:
        wait_thread.start()
        if dialog.exec():
            wait_thread.quit()
            wait_thread.wait()
            print('Поток калибровки остановлен')


def joystick_bind(window):
    adapter = adapter_for_node(window.thread.adapter, 250)
    if adapter:
        QMessageBox.information(window, "Информация", 'Перед привязкой проверь:\n'
                                                      ' - что джойстик ВЫКЛЮЧЕН\n'
                                                      ' - высокое напряжение ВКЛЮЧЕНО',
                                QMessageBox.StandardButton.Ok)
        dialog = DialogChange(text='Команда на привязку отправлена')
        dialog.setWindowTitle('Привязка джойстика')

        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.wait_time = 20  # время в секундах для включения и прописки джойстика
        wait_thread.req_delay = 250  # время в миллисекундах на опрос параметров
        wait_thread.max_err = 80  # потому что приёмник джойстика не отвечает постоянно, а только трижды
        wait_thread.adapter = adapter
        wait_thread.id_for_read = 0x18FF87A7
        wait_thread.answer_dict = {
            0: 'принята команда привязки',
            1: 'приемник переведен в режим привязки, ожидание включения пульта ДУ',
            2: 'привязка завершена',
            254: 'ошибка',
            255: 'команда недоступна'}

        bind_command = adapter.can_write(0x18FF86A5, [0] * 8)

        if not bind_command:
            wait_thread.start()
            if dialog.exec():
                wait_thread.quit()
                wait_thread.wait()
                print('Поток остановлен')
        else:
            QMessageBox.critical(window, "Ошибка ", 'Команда привязки не отправлена\n' + bind_command,
                                 QMessageBox.StandardButton.Ok)
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.StandardButton.Ok)


def suspension_to_zero(window):
    par_list = find_param('SUSPENSION_', nodes_dict=window.thread.current_nodes_dict)
    p_list = par_list[:9] if par_list and len(par_list) >= 9 else []
    wait_thread.imp_par_set = set(p_list)
    adapter = adapter_for_node(window.thread.adapter, 250)
    if adapter:
        QMessageBox.information(window, "Информация", 'Перед выравниванием проверь что:\n'
                                                      ' - тумблер режима подвески в положении АВТО КВУ\n'
                                                      ' - остальные тумблеры в нейтральном положении',
                                QMessageBox.StandardButton.Ok)
        dialog = DialogChange(text='Команда на установку отправлена',
                              table=list(wait_thread.imp_par_set))
        dialog.setWindowTitle('Установка подвески v ноль')

        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.wait_time = 20  # время в секундах для установки подвески
        wait_thread.req_delay = 50  # время в миллисекундах на опрос параметров
        wait_thread.adapter = adapter

        command_zero_suspension = adapter.can_write(0x18FF83A5, [1, 0x7D, 0x7D, 0x7D, 0x7D])
        if not command_zero_suspension:  # если передача прошла успешно
            wait_thread.start()
            if dialog.exec():
                wait_thread.quit()
                wait_thread.wait()
                print('Поток остановлен')

        else:
            QMessageBox.critical(window, "Ошибка ", f'Команда не отправлена\n{command_zero_suspension}',
                                 QMessageBox.StandardButton.Ok)
            window.log_lbl.setText(command_zero_suspension.replace('\n', ''))
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.StandardButton.Ok)


def let_moment_mpei(window):
    @pyqtSlot()
    def finish():
        wait_thread.quit()
        wait_thread.wait()
        # выставляю стандартные значения параметров
        ref_torque.set_value(adapter_vmu, 0)
        man_control.set_value(adapter_vmu, 0)
        is_motor_max.set_value(adapter_inv, standart_current)
        speed_max.set_value(adapter_inv, standart_speed)
        # тушу высокое и сохраняю их в еепром
        window.thread.invertor_command('POWER_OFF', True)
        save_to_eeprom_mpei(window, node_inv, adapter_inv)
        window.thread.invertor_command('POWER_ON_SILENT', True)

    # стандартные значения инвертора
    standart_current = 270
    standart_speed = 8000
    # ограничения по инвертору
    limit_current = 130  # меньше 100А не крутится
    limit_moment = 10
    limit_speed = 1200
    # определяю рабочие блоки из общего списка
    if 'Инвертор_МЭИ' not in window.thread.current_nodes_dict.keys() or \
            'КВУ_ТТС' not in window.thread.current_nodes_dict.keys():
        return
    node_inv = window.thread.current_nodes_dict['Инвертор_МЭИ']
    node_vmu = window.thread.current_nodes_dict['КВУ_ТТС']
    # заполняю список просматриваемых параметров
    param_list_for_calibrate = ['FAULTS', 'DC_VOLTAGE', 'DC_CURRENT', 'DRIVE_STATE']
    for p_name in param_list_for_calibrate:
        wait_thread.imp_par_set.add(
            find_param(p_name, node=node_inv.name, nodes_dict=window.thread.current_nodes_dict)[0])
    wait_thread.imp_par_set.add(find_param('TORQUE', node=node_inv.name,
                                           nodes_dict=window.thread.current_nodes_dict)[2])
    wait_thread.imp_par_set.add(find_param('SPEED_RPM', node=node_inv.name,
                                           nodes_dict=window.thread.current_nodes_dict)[1])
    # ищу адаптеры
    adapter_inv = adapter_for_node(window.thread.adapter, node_inv)
    adapter_vmu = adapter_for_node(window.thread.adapter, node_vmu)
    if adapter_inv and adapter_vmu:
        QMessageBox.information(window, "Информация", 'Перед запуском проверь что:\n'
                                                      ' - стояночный тормоз отпущен\n'
                                                      ' - приводная ось вывешена\n'
                                                      ' - высокое напряжение ВЫКЛЮЧЕНО',
                                QMessageBox.StandardButton.Ok)
        dialog = DialogChange(text='Команда на вращение отправлена',
                              table=list(wait_thread.imp_par_set))
        dialog.setWindowTitle('Вращение двигателя')
        dialog.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).hide()
        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.FinishedSignal.connect(finish)
        wait_thread.wait_time = 10  # время в секундах для вращения
        wait_thread.req_delay = 50  # время в миллисекундах на опрос параметров
        wait_thread.adapter = adapter_inv
        # Нахожу нужные параметры от инвертора и кву
        is_motor_max = find_param('IS_MOTOR_MAX', node=node_inv.name,
                                  nodes_dict=window.thread.current_nodes_dict)[0]
        speed_max = find_param('SPEED_MAX', node=node_inv.name,
                               nodes_dict=window.thread.current_nodes_dict)[0]
        man_control = find_param('MANUAL_CONTROL', node=node_vmu.name,
                                 nodes_dict=window.thread.current_nodes_dict)[0]
        ref_torque = find_param('PSTED_MANUAL_CONTROL_REF_TORQUE', node=node_vmu.name,
                                nodes_dict=window.thread.current_nodes_dict)[0]
        if not is_motor_max or not speed_max or not man_control or not ref_torque:
            QMessageBox.critical(window, "Ошибка ", 'Не найдены нужные параметры', QMessageBox.StandardButton.Ok)
            return
        # Запрашиваю текущие их значения
        start_max_i = is_motor_max.get_value(adapter_inv)
        start_max_speed = speed_max.get_value(adapter_inv)
        print(f'{start_max_i=}, {start_max_speed=}')
        if isinstance(start_max_i, str) or isinstance(start_max_speed, str):
            QMessageBox.critical(window, "Ошибка ", 'Инвертор не отвечает,\n'
                                                    'Попробуй заново к нему подключиться',
                                 QMessageBox.StandardButton.Ok)
            return
        # ручной контроль должен быть отключен и момент должен быть нулевым
        cur_man = man_control.get_value(adapter_vmu)
        cur_tor = ref_torque.get_value(adapter_vmu)
        print(f'{cur_man=}, {cur_tor=}')
        if isinstance(cur_man, str) or isinstance(cur_tor, str):
            QMessageBox.critical(window, "Ошибка ", 'КВУ не отвечает\n'
                                                    'Попробуй ещё раз', QMessageBox.StandardButton.Ok)
            return
        if cur_tor != 0 or cur_man != 0:
            QMessageBox.critical(window, "Ошибка ", 'Включен ручной режим КВУ\n'
                                                    'Или ненулевой момент', QMessageBox.StandardButton.Ok)
            return
        # Устанавливаю ограничения для вращения
        set_max_i = is_motor_max.set_value(adapter_inv, limit_current)
        set_max_speed = speed_max.set_value(adapter_inv, limit_speed)
        if set_max_speed or set_max_i:
            QMessageBox.critical(window, "Ошибка ", 'Не удалось задать значения в инвертор\n'
                                                    'Попробуй ещё раз',
                                 QMessageBox.StandardButton.Ok)
            return
        # Сохраняю ограничения в еепром инвертора
        err = save_to_eeprom_mpei(window, node_inv, adapter_inv)
        if err:
            QMessageBox.critical(window, "Ошибка ", 'Выключи высокое и повтори', QMessageBox.StandardButton.Ok)
            return
        man_c = man_control.set_value(adapter_vmu, 1)
        if not man_c:  # если передача прошла успешно
            if QMessageBox.information(window,
                                       "Информация",
                                       'Включи ВЫСОКОЕ напряжение\n'
                                       '     и нажми ОК\n'
                                       '     ОСТОРОЖНО!!!!\n'
                                       'Сейчас мотор начнёт вращаться',
                                       QMessageBox.StandardButton.Ok,
                                       QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Ok:
                wait_thread.start()
                ref_torque.set_value(adapter_vmu, limit_moment)
            if dialog.exec():
                finish()
        else:
            QMessageBox.critical(window, "Ошибка ", f'Команда не отправлена\n{man_c}',
                                 QMessageBox.StandardButton.Ok)
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине', QMessageBox.StandardButton.Ok)


def rb_togled(window):
    rb_name = window.sender().objectName()
    print(rb_name)
    if rb_name not in light_commamd_dict.keys():
        return
    adapter = adapter_for_node(window.thread.adapter, value=250)
    if adapter:
        light_on = adapter.can_write(light_id_vmu, light_commamd_dict[rb_name])
        if light_on:
            QMessageBox.critical(window, "Ошибка ", f'Команда не отправлена\n{light_on}',
                                 QMessageBox.StandardButton.Ok)
            window.log_lbl.setText(light_on.replace('\n', ''))
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.StandardButton.Ok)


def adapter_for_node(ad: CANAdater, value=None) -> CANAdater:
    adapter = False
    n_id = False
    if isinstance(value, int):
        if value not in ad.can_bitrate.keys():
            n_id = value
    elif isinstance(value, EVONode):
        n_id = value.request_id
    else:
        return adapter

    if not ad.isDefined:
        if not ad.find_adapters():
            return
    if n_id:
        if n_id in ad.id_nodes_dict.keys():
            adapter = ad.id_nodes_dict[n_id]
    else:
        if value in ad.adapters_dict:
            adapter = ad.adapters_dict[value]
    return adapter


class SteerParametr:

    def __init__(self, name: str, warning='', nominal_value=0, min_value=None, max_value=None):
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


class Steer:

    def __init__(self, steer: EVONode, adapter):
        # словарь с параметрами, которые опрашиваем
        self.parameters_get = dict(
            status=SteerParametr(name='A0.1 Status', warning='БУРР должен быть неактивен',
                                 min_value=0, max_value=0),
            alarms=SteerParametr(name='A0.0 Alarms', warning='В блоке есть ошибки'),
            position=SteerParametr(name='A0.3 ActSteerPos', warning='Рейка НЕ в нулевом положении',
                                   nominal_value=0, min_value=-30, max_value=30),
            current=SteerParametr(name='A1.7 CurrentRMS',
                                  min_value=1, max_value=100))
        # словарь с параметрами, которые задаём
        self.parameters_set = dict(
            current=SteerParametr(name='C5.3 rxSetCurr', warning='Ток ограничения рейки задан неверно',
                                  nominal_value=70, min_value=1, max_value=90),
            command=SteerParametr(name='D0.0 ComandSet', nominal_value=0,
                                  min_value=1, max_value=1),
            control=SteerParametr(name='D0.6 CAN_Control', nominal_value=2,
                                  min_value=0, max_value=0),
            position=SteerParametr(name='A0.2 SetSteerPos', nominal_value=0,
                                   min_value=-1000, max_value=1000))
        self.node = steer
        self.adapter = adapter
        self.max_iteration = 3
        self.time_for_moving = 3    # время для движения в секундах
        self.time_for_request = 0.02    # время опроса - 20мс
        self.time_for_set = 0.2    # время наращивания тока - 200мс
        self.delta_current = 0.3
        # определяем все параметры
        for par in list(self.parameters_get.values()) + list(self.parameters_set.values()):
            par.parametr = find_param(par.name, self.node)[0]
            if not par.parametr:
                QMessageBox.critical(None, "Ошибка ", f'Не найден параметр{par.name}', QMessageBox.StandardButton.Ok)

        self.current_position = self.parameters_get['position'].nominal_value
        self.min_position = self.parameters_get['position'].min_value
        self.max_position = self.parameters_get['position'].max_value
        self.max_current = self.parameters_get['current'].max_value

    def get_param(self, param: SteerParametr):
        for i in range(self.max_iteration):
            value = param.parametr.get_value(self.adapter)
            if not isinstance(value, str):
                return value
        QMessageBox.critical(None, "Ошибка ", f'Запросить {param.name} не удалось', QMessageBox.StandardButton.Ok)
        return None

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
        if self.parameters_set['position'].parametr.set_value(self.adapter, value):
            QMessageBox.critical(None, "Ошибка ", f'Задать положение {value} не удалось', QMessageBox.StandardButton.Ok)
            return False
        return True

    # задаём максимальный рабочий ток
    def set_current(self, value: int):
        if value > self.max_current:
            value = self.max_current
        if self.parameters_set['current'].parametr.set_value(self.adapter, value):
            QMessageBox.critical(None, "Ошибка ", f'Задать ток {value} не удалось', QMessageBox.StandardButton.Ok)
            return False
        return True

    # задание движения, за показаниями не следим, мотор не выключаем
    def move_to(self, value: int):
        if value > self.max_position:
            value = self.max_position
        elif value < self.min_position:
            value = self.min_position
        # если есть ошибки, не включаем
        err = self.node.check_errors(self.adapter)
        if err:
            errs = "\n - ".join(err)
            QMessageBox.critical(None, "Ошибка ", f' В блоке ошибки {errs}', QMessageBox.StandardButton.Ok)
            return False

        if not self.set_position(value) or not self.turn_on_motor():
            self.stop()
            return False

        return True

    #
    def turn_on_motor(self):
        if self.parameters_set['control'].parametr.set_value(self.adapter,
                                                             self.parameters_set['control'].min_value):
            QMessageBox.critical(None, "Ошибка ", f'Не удалось перейти в тестовый режим', QMessageBox.StandardButton.Ok)
            return False
        if self.parameters_set['command'].parametr.set_value(self.adapter,
                                                             self.parameters_set['command'].min_value):
            QMessageBox.critical(None, "Ошибка ", f'Не удалось включить мотор', QMessageBox.StandardButton.Ok)
            return False
        return True

    #
    def stop(self):
        for par in self.parameters_set.values():
            err = par.parametr.set_value(self.adapter, par.nominal_value)
            if err:
                QMessageBox.critical(None, "Ошибка ", f'Не могу установить параметр{par.name}',
                                     QMessageBox.StandardButton.Ok)
                return False
        return True

    def set_straight(self):
        result = False
        # определяем заданный пользователем максимальный ток (возможно, это нужно изменять)
        # и задаём команду на вращение
        self.max_current = self.get_param(self.parameters_set['current'])
        move = self.move_to(self.parameters_get['position'].nominal_value)
        if move and self.max_current:
            self.parameters_set['current'].nominal_value = self.max_current
            current_time = start_time = time.perf_counter()
            # а дальше смотрим за текущими параметрами пока не вышло время
            while time.perf_counter() < start_time + self.time_for_moving:
                print(f'\rТекущее положение {self.current_position} ток сейчас {self.actual_current()}', end='', flush=True)
                # регулярно опрашиваем текущее положение
                if time.perf_counter() > current_time + self.time_for_request:
                    current_time = time.perf_counter()
                    self.actual_position()
                #  выходим с победой если попали в нужный диапазон
                if self.parameters_get['position'].min_value < \
                        self.current_position < self.parameters_get['position'].max_value:
                    result = True
                    break
        # отключаем мотор и все параметры возвращаем к номинальным
        self.stop()
        return result

    def define_current(self, value: int):
        result = None
        # определяем заданный пользователем максимальный ток (возможно, это нужно изменять)
        # и задаём команду на вращение
        self.max_current = self.get_param(self.parameters_set['current'])
        move = self.move_to(value)
        current = self.parameters_get['current'].min_value
        cur = self.set_current(current)
        if move and cur and self.max_current:
            self.parameters_set['current'].nominal_value = self.max_current
            current_set_time = current_time = start_time = time.perf_counter()
            # а дальше смотрим за текущими параметрами пока не вышло время
            while time.perf_counter() < start_time + self.time_for_moving:
                print(f'\rТекущее положение {self.current_position} ток сейчас {self.actual_current()} '
                      f'максимальный ток {self.max_current}', end='', flush=True)
                # регулярно опрашиваем текущее положение
                if time.perf_counter() > current_time + self.time_for_request:
                    current_time = time.perf_counter()
                    self.actual_position()
                # регулярно добавляем ток
                if time.perf_counter() > current_set_time + self.time_for_set:
                    current_set_time = time.perf_counter()
                    current += self.delta_current
                    self.set_current(current)
                #  надо ещё добавить контроль за тем, что рейка идёт в нужную сторону
                #  выходим с победой если попали в нужный диапазон
                if value + self.parameters_get['position'].min_value < \
                        self.current_position < value + self.parameters_get['position'].max_value:
                    result = current
                    break
        # отключаем мотор и все параметры возвращаем к номинальным
        self.stop()
        return result


def check_steering_current(window):
    # def end_func():
    #     timer.stop()
    #     current.parametr.set_value(adapter, current.max_value)
    #     for par in list(parametr_dict.values())[4:]:
    #         if par.parametr.set_value(adapter, par.nominal_value):
    #             QMessageBox.critical(window, "Ошибка ",
    #                                  f'Не могу установить значение по умолчанию параметра {par.name}',
    #                                  QMessageBox.StandardButton.Ok)
    #             return False
    #     if currents.max_value:
    #         QMessageBox.information(window,
    #                                 "Информация",
    #                                 f'Ток страгивания = {currents.min_value}\n'
    #                                 f'Ток максимального выворота = {currents.max_value}',
    #                                 QMessageBox.StandardButton.Ok)
    #     return True
    #
    # def moving_steer():
    #     old_delta = target_position - position.current_value
    #     position.current_value = position.parametr.get_value(adapter)
    #     new_delta = target_position - position.current_value
    #
    #     if abs(new_delta) > abs(old_delta) + abs(target_position / 100):
    #         QMessageBox.critical(window, "Ошибка ", f'Рейка движется не в том направлении',
    #                              QMessageBox.StandardButton.Ok)
    #         end_func()
    #         return
    #     if not currents.min_value:
    #         if abs(position.current_value) >= abs(target_position / 10):
    #             currents.min_value = current.current_value
    #
    #     if abs(position.current_value) >= abs(target_position):
    #         currents.max_value = current.current_value
    #         end_func()
    #         return
    #     else:
    #         if current.current_value < current.max_value:
    #             current.current_value += delta_current
    #             current.parametr.set_value(adapter, current.current_value)
    #         else:
    #             QMessageBox.critical(window, "Ошибка ", f'Достигнут предел тока', QMessageBox.StandardButton.Ok)
    #             end_func()
    #             return
    #
    # delay = 500
    # delta_current = 0.5
    rb_steer_dict = dict(
        front_steer_rbtn='Рулевая_перед_Томск',
        rear_steer_rbtn='Рулевая_зад_Томск'
    )
    current_steer = None
    for current_rb in rb_steer_dict.keys():
        tr = getattr(window, current_rb)
        if tr.isChecked():
            current_steer = window.thread.current_nodes_dict[rb_steer_dict[current_rb]]
    if not current_steer:
        print('Странное, ни один рулевой блок не выбран')
        return
    print(current_steer.name)

    # parametr_dict = dict(
    #     st_status=SteerParametr(name='A0.1 Status', warning='БУРР должен быть неактивен',
    #                             min_value=0, max_value=0),
    #     st_alarms=SteerParametr(name='A0.0 Alarms', warning='В блоке есть ошибки'),
    #     st_act_pos=SteerParametr(name='A0.3 ActSteerPos', warning='Рейка НЕ в нулевом положении',
    #                              min_value=-30, max_value=30),
    #     st_set_curr=SteerParametr(name='C5.3 rxSetCurr', warning='Ток ограничения рейки задан неверно',
    #                               min_value=1, max_value=100),
    #     st_motor_command=SteerParametr(name='D0.0 ComandSet',
    #                                    min_value=1, max_value=1),
    #     st_control=SteerParametr(name='D0.6 CAN_Control', nominal_value=2,
    #                              min_value=0, max_value=0),
    #     st_set_pos=SteerParametr(name='A0.2 SetSteerPos',
    #                              min_value=-1000, max_value=1000)
    # )
    #
    # for par in parametr_dict.values():
    #     par.parametr = find_param(window.thread.current_nodes_dict, par.name, current_steer.name)[0]
    #     if not par.parametr:
    #         QMessageBox.critical(window, "Ошибка ", f'Не найден параметр{par.name}', QMessageBox.StandardButton.Ok)
    #         return False
    #     print(par.parametr.description)
    adapter = adapter_for_node(window.thread.adapter, current_steer)
    if not adapter:
        return False
    steer = Steer(current_steer, adapter)
    print(steer.actual_position(), steer.max_current)
    steer.set_straight()
    print()
    print(steer.actual_position(), steer.max_current)
    # for par in list(parametr_dict.values())[:4]:
    #     par.current_value = par.parametr.get_value(adapter)
    #     if isinstance(par.current_value, str):
    #         QMessageBox.critical(window, "Ошибка ", f'Не удалось считать параметр {par.name}',
    #                              QMessageBox.StandardButton.Ok)
    #         return False
    #     elif not par.check():
    #         return False
    #     print(par.name, par.current_value)
    #
    # position = parametr_dict['st_act_pos']
    # current = parametr_dict['st_set_curr']
    # currents = parametr_dict['st_status']
    # current.max_value = current.current_value
    # timer = QTimer()
    # timer.timeout.connect(moving_steer)
    #
    # if QMessageBox.information(window,
    #                            "Информация",
    #                            'Сейчас рейка начнёт движение, лучше убрать всё лишнее, что может помешать движению',
    #                            QMessageBox.StandardButton.Ok,
    #                            QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Ok:
    #
    #     target_position = parametr_dict['st_set_pos'].min_value
    #     current.current_value = current.min_value
    #     for par in list(parametr_dict.values())[3:]:
    #         if par.parametr.set_value(adapter, par.min_value):
    #             QMessageBox.critical(window, "Ошибка ", f'Не могу установить значение параметра {par.name}'
    #                                                     f' повтори ещё раз', QMessageBox.StandardButton.Ok)
    #             end_func()
    #             return False
    #     timer.start(delay)
    #     loop = QEventLoop()
    #     loop.exec()

    return True
