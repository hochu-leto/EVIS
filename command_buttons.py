import time

from PyQt6.QtCore import pyqtSlot, QTimer, QEventLoop
from PyQt6.QtWidgets import QMessageBox, QDialogButtonBox

import CANAdater
from EVONode import EVONode
from EVOThreads import WaitCanAnswerThread, SleepThread, SteerMoveThread
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


def warning_dialog(title: str, warn_str: str):
    points_list = None
    if '-' in warn_str:
        points_list = warn_str.split('-')
        warn_str = points_list.pop(0)
    dialog = DialogChange(label=warn_str, check_boxes=points_list)
    dialog.setWindowTitle(title)
    return dialog.exec()


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


def mpei_iso_off(window):
    m = window.thread.invertor_command('ISOLATION_MONITORING_OFF')
    window.log_lbl.setText(m)


def mpei_iso_on(window):
    m = window.thread.invertor_command('ISOLATION_MONITORING_ON')
    window.log_lbl.setText(m)


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
    wait_thread.adapter = adapter_for_node(window.thread.adapter, 125)
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
    tit = 'Привязка джойстика'
    if adapter and warning_dialog(tit,
                                  'Перед привязкой проверь что:'
                                  ' - джойстик ВЫКЛЮЧЕН'
                                  ' - высокое напряжение ВКЛЮЧЕНО'):
        dialog = DialogChange(text='Команда на привязку отправлена')
        dialog.setWindowTitle(tit)

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
    tit = 'Установка подвески v ноль'
    if adapter and warning_dialog(tit, 'Перед выравниванием проверь что:'
                                       ' - тумблер режима подвески в положении АВТО КВУ'
                                       ' - остальные тумблеры в нейтральном положении'):
        dialog = DialogChange(text='Команда на установку отправлена',
                              table=list(wait_thread.imp_par_set))
        dialog.setWindowTitle(tit)

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
        voltage = high_voltage.get_value(adapter_inv)
        # тушу высокое и сохраняю их в еепром
        window.thread.invertor_command('POWER_OFF', True)
        save_to_eeprom_mpei(window, node_inv, adapter_inv)
        # снова поднимаю высокое
        if not isinstance(voltage, str) and voltage > 300:
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
    # Нахожу нужные параметры от инвертора и кву
    is_motor_max = find_param('IS_MOTOR_MAX', node=node_inv.name,
                              nodes_dict=window.thread.current_nodes_dict)[0]
    speed_max = find_param('SPEED_MAX', node=node_inv.name,
                           nodes_dict=window.thread.current_nodes_dict)[0]
    man_control = find_param('MANUAL_CONTROL', node=node_vmu.name,
                             nodes_dict=window.thread.current_nodes_dict)[0]
    ref_torque = find_param('PSTED_MANUAL_CONTROL_REF_TORQUE', node=node_vmu.name,
                            nodes_dict=window.thread.current_nodes_dict)[0]
    high_voltage = find_param('DC_VOLTAGE', node=node_inv.name,
                              nodes_dict=window.thread.current_nodes_dict)[0]
    if not is_motor_max or not speed_max or not man_control or not ref_torque:
        err = 'Не найдены нужные параметры'
    else:
        # ищу адаптеры
        adapter_inv = adapter_for_node(window.thread.adapter, node_inv)
        adapter_vmu = adapter_for_node(window.thread.adapter, node_vmu)
        if not adapter_inv or not adapter_vmu:
            err = 'Нет адаптера на шине'
        else:
            tit = 'Вращение двигателя'
            if not warning_dialog(tit, 'Перед запуском проверь что:'
                                       ' - стояночный тормоз отпущен'
                                       ' - приводная ось вывешена'
                                       ' - высокое напряжение ВЫКЛЮЧЕНО'):
                err = 'Отказ пользователя'
            else:
                dialog = DialogChange(text='Команда на вращение отправлена',
                                      table=list(wait_thread.imp_par_set))
                dialog.setWindowTitle(tit)
                dialog.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).hide()
                wait_thread.SignalOfProcess.connect(dialog.change_mess)
                wait_thread.FinishedSignal.connect(finish)
                wait_thread.wait_time = 10  # время в секундах для вращения
                wait_thread.req_delay = 50  # время в миллисекундах на опрос параметров
                wait_thread.adapter = adapter_inv
                # Запрашиваю текущие значения нужных параметров
                start_max_i = is_motor_max.get_value(adapter_inv)
                start_max_speed = speed_max.get_value(adapter_inv)
                if isinstance(start_max_i, str) or isinstance(start_max_speed, str):
                    err = 'Инвертор не отвечает,\nПопробуй заново к нему подключиться'
                else:
                    cur_man = man_control.get_value(adapter_vmu)
                    cur_tor = ref_torque.get_value(adapter_vmu)
                    if isinstance(cur_man, str) or isinstance(cur_tor, str):
                        err = 'КВУ не отвечает\nПопробуй ещё раз'
                    else:
                        # ручной контроль должен быть отключен и момент должен быть нулевым
                        if cur_tor != 0 or cur_man != 0:
                            err = 'Включен ручной режим КВУ\nИли ненулевой момент'
                        else:
                            # Устанавливаю ограничения для вращения
                            set_max_i = is_motor_max.set_value(adapter_inv, limit_current)
                            set_max_speed = speed_max.set_value(adapter_inv, limit_speed)
                            if set_max_speed or set_max_i:
                                err = 'Не удалось задать значения в инвертор\nПопробуй ещё раз',
                            else:
                                # Сохраняю ограничения в еепром инвертора
                                err = save_to_eeprom_mpei(window, node_inv, adapter_inv)
                                if err:
                                    err = 'Не удалось сохранить значения в инвертор\nВыключи высокое и повтори'
                                else:
                                    man_c = man_control.set_value(adapter_vmu, 1)
                                    if man_c:
                                        err = f'Команда не отправлена\n{man_c}'
                                    else:  # если передача прошла успешно
                                        if QMessageBox.information(window,
                                                                   "Информация",
                                                                   '<b>Включи</b> ВЫСОКОЕ напряжение\n'
                                                                   '     и нажми ОК\n'
                                                                   '     <b>ОСТОРОЖНО!!!!</b>\n'
                                                                   'Сейчас мотор начнёт вращаться',
                                                                   QMessageBox.StandardButton.Ok,
                                                                   QMessageBox.StandardButton.Cancel) == \
                                                QMessageBox.StandardButton.Ok:
                                            err = high_voltage.get_value(adapter_inv)
                                            if isinstance(err, str):
                                                err = f'Некорректный ответ от инвертора\n{err}'
                                            else:
                                                if err < 300:
                                                    err = f'Высокое напряжение не включено, сейчас {err}В'
                                                    finish()
                                                else:
                                                    wait_thread.start()
                                                    ref_torque.set_value(adapter_vmu, limit_moment)
                                                    if dialog.exec():
                                                        finish()
    if err:
        QMessageBox.critical(window, "Ошибка ", err,
                             QMessageBox.StandardButton.Ok)


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


def check_steering_current(window):
    rb_steer_dict = dict(
        front_steer_rbtn='Рулевая_перед_Томск',
        rear_steer_rbtn='Рулевая_зад_Томск')
    current_steer = None
    for current_rb in rb_steer_dict.keys():
        tr = getattr(window, current_rb)
        if tr.isChecked():
            current_steer = window.thread.current_nodes_dict[rb_steer_dict[current_rb]]
    if not current_steer:
        print('Странное, ни один рулевой блок не выбран')
        return
    print(current_steer.name)

    adapter = adapter_for_node(window.thread.adapter, current_steer)
    if not adapter:
        return False
    steer = SteerMoveThread(current_steer, adapter)
    # определяем заданный пользователем максимальный ток (возможно, это нужно изменять)
    steer.max_current = steer.get_param(steer.parameters_set['current'])
    if steer.max_current:
        dialog = DialogChange(text='Начало процедуры',
                              table=steer.params_for_view, process=steer.progress)
        dialog.setWindowTitle('Определение токов рейки')
        dialog.setMinimumWidth(int(window.width() * 0.7))
        steer.SignalOfProcess.connect(dialog.change_mess)
        if QMessageBox.information(window, "Информация",
                                   f'Всё готово для определения токов рейки <b>{current_steer.name}.</b>\n'
                                   f' Сейчас её максимальный ток <b>{steer.max_current}А.</b>\n'
                                   f' После нажатия кнопки Ок <b>{current_steer.name}</b>\n'
                                   f'начнёт движение, лучше убрать всё, что может помешать ей\n'
                                   f' двигаться, потому как <b>НИКАКИЕ ЗАЩИТЫ НЕ РАБОТАЮТ!!!</b>',
                                   QMessageBox.StandardButton.Ok,
                                   QMessageBox.StandardButton.Cancel) == QMessageBox.StandardButton.Ok:
            steer.start()

            if dialog.exec():
                steer.set_straight()
                steer.quit()
                steer.wait()
                print('Поток остановлен')
    return True
