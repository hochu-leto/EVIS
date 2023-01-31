from time import sleep

from PyQt6.QtCore import pyqtSlot
from PyQt6.QtWidgets import QMessageBox

from My_threads import WaitCanAnswerThread, SleepThread
from helper import find_param, DialogChange

wait_thread = WaitCanAnswerThread()
sleep_thread = SleepThread(3)


def save_to_eeprom(window, node=None):
    if not node:
        node = window.thread.current_node

    if node.save_to_eeprom:
        if window.thread.isRunning():
            window.connect_to_node()
            isRun = True
        else:
            isRun = False
        if not window.thread.adapter.isDefined:
            if not window.thread.adapter.find_adapters():
                return
        if node.request_id in window.thread.adapter.id_nodes_dict.keys():
            adapter = window.thread.adapter.id_nodes_dict[node.request_id]

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
    voltage = find_param(window.thread.current_nodes_dict, 'DC_VOLTAGE', node_name=node.name)[0]
    err = voltage.get_value(adapter)  # ---!!!если параметр строковый, будет None!!---
    if not isinstance(err, str):
        # Сохраняем в ЕЕПРОМ Инвертора МЭИ только если выключено высокое - напряжение ниже 30В
        if err < 30:
            err = node.send_val(node.save_to_eeprom, adapter)  # неправильно
            sleep_thread.start()
            err = ''
        else:
            err = 'Высокое напряжение не выключено\nВыключи высокое напряжение и повтори сохранение'
    else:
        err = f'Некорректный ответ от инвертора\n{err}'
    return err


# --------------------------------------------------- кнопки управления ----------------------------------------------
def load_from_eeprom(window):
    node = window.thread.current_nodes_dict['КВУ_ТТС']
    if node.request_id in window.thread.adapter.id_nodes_dict.keys():
        adapter_can2 = window.thread.adapter.id_nodes_dict[node.request_id]
        print('Отправляю команду на запрос из еепром')
        # такое чувство что функция полное говно и пора бы уже сделать её универсальной для всех блоков
        answer = node.send_val(0x210201, adapter_can2, value=0x01)  # это адрес вытащить из еепром для кву ттс
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
            # передавать надо исключительно в первый кан
            if node.request_id in window.thread.adapter.id_nodes_dict.keys():
                adapter = window.thread.adapter.id_nodes_dict[node.request_id]
                faults = list(node.check_errors(adapter=adapter))
                if not faults:
                    st.append('Ошибок во время калибровки не появилось')
                else:
                    faults.insert(0, 'Во время калибровки возникли ошибки: ')
                    st += faults
                dialog.change_mess(st)

    param_list_for_calibrate = ['FAULTS', 'DC_VOLTAGE', 'SPEED_RPM', 'FIELD_CURRENT',
                                'PHA_CURRENT', 'PHB_CURRENT', 'PHC_CURRENT']  # 'STATOR_CURRENT', 'TORQUE',
    for p_name in param_list_for_calibrate:
        wait_thread.imp_par_set.add(
            find_param(window.thread.current_nodes_dict, p_name, node_name='Инвертор_МЭИ')[0])

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
    if not window.thread.adapter.isDefined:
        if not window.thread.adapter.find_adapters():
            return
    if 250 in window.thread.adapter.adapters_dict:
        QMessageBox.information(window, "Информация", 'Перед привязкой проверь:\n'
                                                      ' - что джойстик ВЫКЛЮЧЕН\n'
                                                      ' - высокое напряжение ВКЛЮЧЕНО',
                                QMessageBox.StandardButton.Ok)
        adapter = window.thread.adapter.adapters_dict[250]

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
    par_list = find_param(window.thread.current_nodes_dict, 'SUSPENSION_')
    p_list = par_list[:9] if par_list and len(par_list) >= 9 else []
    wait_thread.imp_par_set = set(p_list)
    if not window.thread.adapter.isDefined:
        if not window.thread.adapter.find_adapters():
            return
    if 250 in window.thread.adapter.adapters_dict:
        QMessageBox.information(window, "Информация", 'Перед выравниванием проверь что:\n'
                                                      ' - тумблер режима подвески в положении АВТО КВУ\n'
                                                      ' - остальные тумблеры в нейтральном положении',
                                QMessageBox.StandardButton.Ok)
        adapter = window.thread.adapter.adapters_dict[250]
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
        is_motor_max.set_value(adapter_inv, 270)
        speed_max.set_value(adapter_inv, 8000)
        # тушу высокое и сохраняю их в еепром
        window.thread.invertor_command('POWER_OFF', True)
        save_to_eeprom_mpei(window, node_inv, adapter_inv)

    # ограничения по инвертору
    max_moment = 10
    max_speed = 1200
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
            find_param(window.thread.current_nodes_dict, p_name, node_name=node_inv.name)[0])
    wait_thread.imp_par_set.add(find_param(window.thread.current_nodes_dict, 'TORQUE', node_name=node_inv.name)[2])
    wait_thread.imp_par_set.add(find_param(window.thread.current_nodes_dict, 'SPEED_RPM',
                                           node_name=node_inv.name)[1])
    # ищу адаптер
    if not window.thread.adapter.isDefined:
        if not window.thread.adapter.find_adapters():
            return
    if node_inv.request_id in window.thread.adapter.id_nodes_dict.keys() and \
            node_vmu.request_id in window.thread.adapter.id_nodes_dict.keys():
        # определяю адаптеры для работы с инвертором и кву
        adapter_inv = window.thread.adapter.id_nodes_dict[node_inv.request_id]
        adapter_vmu = window.thread.adapter.id_nodes_dict[node_vmu.request_id]

        QMessageBox.information(window, "Информация", 'Перед запуском проверь что:\n'
                                                      ' - стояночный тормоз отпущен\n'
                                                      ' - приводная ось вывешена\n'
                                                      ' - высокое напряжение ВЫКЛЮЧЕНО',
                                QMessageBox.StandardButton.Ok)
        dialog = DialogChange(text='Команда на вращение отправлена',
                              table=list(wait_thread.imp_par_set))
        dialog.setWindowTitle('Вращение двигателя')

        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.FinishedSignal.connect(finish)
        wait_thread.wait_time = 10  # время в секундах для вращения
        wait_thread.req_delay = 50  # время в миллисекундах на опрос параметров
        wait_thread.adapter = adapter_inv
        # Нахожу нужные параметры от инвертора и кву
        is_motor_max = find_param(window.thread.current_nodes_dict, 'IS_MOTOR_MAX', node_name=node_inv.name)[0]
        speed_max = find_param(window.thread.current_nodes_dict, 'SPEED_MAX', node_name=node_inv.name)[0]
        man_control = find_param(window.thread.current_nodes_dict, 'MANUAL_CONTROL', node_name=node_vmu.name)[0]
        ref_torque = find_param(window.thread.current_nodes_dict, 'PSTED_MANUAL_CONTROL_REF_TORQUE',
                                node_name=node_vmu.name)[0]
        if not is_motor_max or not speed_max or not man_control or not ref_torque:
            QMessageBox.critical(window, "Ошибка ", 'Не найдены нужные параметры', QMessageBox.StandardButton.Ok)
            return
        # Запрашиваю текущие их значения
        start_max_i = is_motor_max.get_value(adapter_inv)
        start_max_speed = speed_max.get_value(adapter_inv)
        if isinstance(start_max_i, str) or isinstance(start_max_speed, str):
            QMessageBox.critical(window, "Ошибка ", 'Инвертор не отвечает', QMessageBox.StandardButton.Ok)
            return
        # ручной контроль должен быть отключен и момент должен быть нулевым
        cur_man = man_control.get_value(adapter_vmu)
        cur_tor = ref_torque.get_value(adapter_vmu)
        if isinstance(cur_man, str) or isinstance(cur_tor, str):
            QMessageBox.critical(window, "Ошибка ", 'КВУ не отвечает', QMessageBox.StandardButton.Ok)
            return
        if cur_tor != 0 or cur_man != 0:
            QMessageBox.critical(window, "Ошибка ", 'Включен ручной режим КВУ'
                                                    'Или ненулевой момент', QMessageBox.StandardButton.Ok)
            return
        # Устанавливаю ограничения для вращения
        set_max_i = is_motor_max.set_value(adapter_inv, 130)  # меньше 100А не крутится
        set_max_speed = speed_max.set_value(adapter_inv, max_speed)
        if set_max_speed or set_max_i:
            QMessageBox.critical(window, "Ошибка ", 'Не удалось задать значения в инвертор',
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
                ref_torque.set_value(adapter_vmu, max_moment)
            if dialog.exec():
                finish()
        else:
            QMessageBox.critical(window, "Ошибка ", f'Команда не отправлена\n{man_c}',
                                 QMessageBox.StandardButton.Ok)
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине', QMessageBox.StandardButton.Ok)
