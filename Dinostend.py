'''
- как сделать нормальную размерность в таблице
- раздвигать таблицу по окну
- складывать параметр в две строки

- сделать несколько блоков по ИД - как их запихнуть в эксель

'''
from pprint import pprint

from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication, QMainWindow
import datetime
import pathlib
import pandas
import ctypes
import struct
import time
import VMU_monitor_ui
from dll_power import CANMarathon
from work_with_file import fill_vmu_list, make_vmu_error_dict, feel_req_list, adding_to_csv_file, fill_bookmarks_list, \
    fill_node_list

suspension_stroke = 100
drive_limit = 30000 * 0.2  # 20% момента - достаточно, чтоб заехать на горку у выхода и не разложиться без тормозов
ref_torque = 0
# // включение стояночного тормоза
HANDBRAKE = 2
# // сброс ошибок
RESET_FAULTS = 8
#
BRAKE_TIMER = 4000  # 4 секунды
# from keyboard_handler import KeyboardHandler

marathon = CANMarathon()
#  и чтоб слать по второму кану управление пневмой
marathon2 = CANMarathon()
marathon2.can_canal_number = 1
marathon2.BCI_bt0 = marathon2.BCI_250K_bt0

dir_path = str(pathlib.Path.cwd())
vmu_param_file = 'table_for_params_new_VMU.xlsx'
vmu_errors_file = 'kvu_error_codes_my.xlsx'
VMU_ID_PDO = 0x00000403
# rtcon_vmu = 0x1850460E
# vmu_rtcon = 0x594
rtcon_vmu = 0x00000603
vmu_rtcon = 0x00000583
invertor_set = 0x00000499
bku_vmu_suspension = 0x18FF83A5
command_list = {'power', 'speed', 'front_steer', 'rear_steer', 'fl_sus', 'fr_sus', 'rr_sus', 'rl_sus'}


# запросить у мэишного инвертора параметр 00000601 8 HEX   40  01  21  00
# записать в мэишный инвертор параметр    00000601 8 HEX   20  01  21  00
# есть подозрения, что последний байт - номер параметра из файла пдф


def warning_message():
    QMessageBox.warning(window, "УВАГА!!!", 'Для смены типа управления нужно: \n - ВЫКЛЮЧИТЬ START ПСТЭД\n - нажать '
                                            'кнопку Подключиться\n - подождать 10 секунд\n - ВКЛЮЧИТЬ START ПСТЭД',
                        QMessageBox.Ok)


def params_list_changed():
    global vmu_params_list, req_list
    vmu_params_list = fill_vmu_list(bookmark_dict[window.blocks_list.currentItem().text()])
    req_list = feel_req_list(vmu_params_list)
    show_empty_params_list(vmu_params_list, 'vmu_param_table')


def steer_allowed_changed(item):
    window.steer_mode_box.setEnabled(item)
    window.front_steer_box.setEnabled(item)
    window.rear_steer_box.setEnabled((not window.front_mode_rb.isChecked()) and item)
    window.front_steer_slider.setValue(0)
    window.rear_steer_slider.setValue(0)


def suspension_allowed_changed(item):
    window.suspesion_box.setEnabled(item)


def steer_mode_changed():
    window.rear_steer_box.setEnabled((not window.front_mode_rb.isChecked()))
    window.front_steer_slider.setValue(0)
    window.rear_steer_slider.setValue(0)


def show_empty_params_list(list_of_params: list, table: str):
    show_table = getattr(window, table)
    show_table.setRowCount(0)
    show_table.setRowCount(len(list_of_params))
    row = 0

    for par in list_of_params:
        name_item = QTableWidgetItem(par['name'])
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, 0, name_item)

        value_item = QTableWidgetItem('')
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, 1, value_item)

        if str(par['unit']) != 'nan':
            unit = str(par['unit'])
        else:
            unit = ''
        unit_item = QTableWidgetItem(unit)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, show_table.columnCount() - 1, unit_item)

        row += 1
    show_table.resizeColumnsToContents()


def connect_vmu():
    if not window.record_vmu_params:
        window.vmu_req_thread.recording_file_name = pathlib.Path(pathlib.Path.cwd(),
                                                                 'VMU records', 'vmu_record_' +
                                                                 datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") +
                                                                 '.csv')
        adding_to_csv_file('name', vmu_params_list, window.vmu_req_thread.recording_file_name)
        # разблокирую все кнопки и чекбоксы
        window.connect_btn.setText('Отключиться')
        window.blocks_list.setEnabled(False)
        # ------------------------------------------------------с новой прошивкой мэи это не работает-----------------
        if window.speed_rb.isChecked():
            window.speed_box.setEnabled(True)
            window.speed_slider.setEnabled(True)
            window.speed_spinbox.setEnabled(True)
            window.power_rb.setEnabled(False)
            control_byte = 0
        else:
            window.power_box.setEnabled(True)
            window.power_slider.setEnabled(True)
            window.power_spinbox.setEnabled(True)
            window.speed_rb.setEnabled(False)
            control_byte = 1

        marathon.can_write(invertor_set, [control_byte, 0, 0, 0, 0, 0, 2, 0])
        time.sleep(1)
        marathon.can_write(invertor_set, [0, 0, 0, 0, 0, 0, 3, 0])
        # ----------------------------------------------------------------------------------------------

        window.power_slider.setValue(0)
        window.speed_slider.setValue(0)
        window.reset_faults.setEnabled(True)
        window.vmu_req_thread.running = True
        window.record_vmu_params = True
        window.thread_to_record.start()
    else:
        # поток останавливаем
        window.vmu_req_thread.running = False
        window.thread_to_record.terminate()
        window.record_vmu_params = False
        window.connect_btn.setText('Подключиться')
        window.power_box.setEnabled(False)
        window.speed_box.setEnabled(False)
        window.reset_faults.setEnabled(False)
        window.power_rb.setEnabled(True)
        window.speed_rb.setEnabled(True)
        window.blocks_list.setEnabled(True)

        marathon.close_marathon_canal()
        # Reading the csv file
        file_name = str(window.vmu_req_thread.recording_file_name)
        df_new = pandas.read_csv(file_name, encoding='windows-1251')
        file_name = file_name.replace('.csv', '_excel.xlsx', 1)
        # saving xlsx file
        GFG = pandas.ExcelWriter(file_name)
        df_new.to_excel(GFG, index=False)
        GFG.save()
        QMessageBox.information(window, "Успешный Успех", 'Файл с записью параметров КВУ\n' +
                                'ищи в папке "VMU records"',
                                QMessageBox.Ok)

    return True


def zero_del(s):
    s = '{:g}'.format(s)    # '{:.5f}'.format(s)
    # s = s.rstrip('0')
    # if len(s) > 0 and s[-1] == '.':
    #     s = s[:-1]
    return s


def fill_vmu_params_values(ans_list: list):
    i = 0
    for par in vmu_params_list:
        message = ans_list[i]
        if not isinstance(message, str):
            value = (message[7] << 24) + \
                    (message[6] << 16) + \
                    (message[5] << 8) + message[4]
            if par['type'] == 'UNSIGNED8':
                par['value'] = ctypes.c_uint8(value).value
            elif par['type'] == 'UNSIGNED16':
                par['value'] = ctypes.c_uint16(value).value
            elif par['type'] == 'UNSIGNED32':
                par['value'] = ctypes.c_uint32(value).value
            elif par['type'] == 'SIGNED8':
                par['value'] = ctypes.c_int8(value).value
            elif par['type'] == 'SIGNED16':
                par['value'] = ctypes.c_int16(value).value
            elif par['type'] == 'SIGNED32':
                par['value'] = ctypes.c_int32(value).value
            elif par['type'] == 'FLOAT':
                par['value'] = bytes_to_float(message[-4:])
            # print(par['value'])
            par['value'] = (par['value'] / par['scale'] - par['scaleB'])

            par['value'] = zero_del(par['value'])
        i += 1
    # здесь не проверяется что принятый параметр соответствует запрошенному. а было бы правильно так


def reset_fault_btn_pressed():
    window.vmu_req_thread.reset_fault_timer = 5
    window.vmu_req_thread.errors = []


def spinbox_changed(item):
    spinbox = QApplication.instance().sender()
    spinbox_name = spinbox.objectName()
    slider_name = spinbox_name.replace('spinbox', 'slider')
    slider = getattr(window, slider_name)
    slider.setValue(item)


def slider_changed(item):
    slider = QApplication.instance().sender()
    slider_name = slider.objectName()
    spinbox_name = slider_name.replace('slider', 'spinbox')
    spinbox = getattr(window, spinbox_name)
    spinbox.setValue(item)


def float_to_int(f):
    return int(struct.unpack('<I', struct.pack('<f', f))[0])


def bytes_to_float(b: list):
    return struct.unpack('<f', bytearray(b))[0]


class NodeOfEVO(object):
    def __init__(self, *initial_data, **kwargs):
        for dictionary in initial_data:
            for key in dictionary:
                setattr(self, key, dictionary[key])
        for key in kwargs:
            setattr(self, key, kwargs[key])


#  поток для опроса и записи в файл параметров кву
class VMUSaveToFileThread(QObject):
    running = False
    new_vmu_params = pyqtSignal(list)
    new_vmu_errors = pyqtSignal(list)
    recording_file_name = ''
    start_time = int(round(time.time() * 1000))
    time_for_request = start_time
    time_for_errors = start_time
    errors = []
    send_delay = 50  # задержка отправки в кан сообщений
    r_fault = RESET_FAULTS
    reset_fault_timer = 0
    h_brake = HANDBRAKE
    brake_timer = 0

    # метод, который будет выполнять алгоритм в другом потоке
    def run(self):
        len_param_list = len(req_list)
        errors_counter = 0
        params_counter = 0
        ans_list = []
        current_time = self.start_time
        no_answer_counter = 0
        no_can_counter = 0
        while True:
            adding_to_csv_file('value', vmu_params_list, window.vmu_req_thread.recording_file_name)

            if self.reset_fault_timer:
                self.r_fault = RESET_FAULTS
                self.reset_fault_timer -= 1
            else:
                self.r_fault = 0

            if (self.brake_timer - current_time) > 0:
                self.h_brake = HANDBRAKE
                self.brake_timer -= 1
            else:
                self.h_brake = 0

            front_steer_data = int(window.front_steer_slider.value()) * 30
            rear_steer_data = int(window.rear_steer_slider.value()) * 30

            torque_data = int(window.power_slider.value()) * 300
            torque_data_list = [self.r_fault | self.h_brake + 0b10001,
                                torque_data & 0xFF, ((torque_data & 0xFF00) >> 8),
                                front_steer_data & 0xFF, ((front_steer_data & 0xFF00) >> 8),
                                rear_steer_data & 0xFF, ((rear_steer_data & 0xFF00) >> 8), 0]

            speed = float(window.speed_slider.value())
            speed_data = float_to_int(speed)
            speed_data_list = [speed_data & 0xFF, ((speed_data & 0xFF00) >> 8),
                               ((speed_data & 0xFF0000) >> 16), ((speed_data & 0xFF000000) >> 24), 0, 0, 8, 0]

            # проверяем что время передачи пришло и отправляю управление по 401 адресу
            if (current_time - self.start_time) > self.send_delay:
                self.start_time = current_time

                marathon.can_write(VMU_ID_PDO, torque_data_list)

                # управление оборотами - напрямую в инвертор МЭИ по 499 адресу
                if window.speed_rb.isChecked():
                    marathon.can_write(invertor_set, speed_data_list)

            # попытаюсь за каждый прогон опрашивать один параметр
            # - думается, это не даст КВУ потерять связь с программой
            param = marathon.can_request(rtcon_vmu, vmu_rtcon, req_list[params_counter])
            ans_list.append(param)
            if isinstance(param, str):
                errors_counter += 1
            params_counter += 1
            if params_counter == len_param_list:
                if errors_counter > len_param_list / 3:
                    self.new_vmu_params.emit(ans_list[:1])
                else:
                    self.new_vmu_params.emit(ans_list)
                errors_counter = 0
                params_counter = 0
                ans_list = []

            if (current_time - self.time_for_errors) > self.send_delay * 50:
                self.time_for_errors = current_time
                if no_answer_counter < 3:
                    error = marathon.can_request(rtcon_vmu, vmu_rtcon, [0x40, 0x15, 0x21, 0x01, 0, 0, 0, 0])
                    if not isinstance(error, str):
                        value = (error[5] << 8) + error[4]
                        error = ctypes.c_uint16(value).value
                    else:
                        no_answer_counter += 1

                    if error not in self.errors:
                        self.errors.append(error)
                else:
                    self.errors = ['КВУ не отвечает на запрос ошибок']

                FL_height = int((window.fl_sus_slider.value() + 250) / 2)
                FR_height = int((window.fr_sus_slider.value() + 250) / 2)
                RL_height = int((window.rl_sus_slider.value() + 250) / 2)
                RR_height = int((window.rr_sus_slider.value() + 250) / 2)
                sus_data = [not window.sus_off_rb.isChecked(), FL_height, FR_height, RL_height, RR_height, 0, 0, 0]
                # каждые 2,5 сек если отмечена подвеска, шлём по кан2
                if no_can_counter < 3:
                    can_answer = 0  # marathon2.can_write(bku_vmu_suspension, sus_data)
                    if can_answer:
                        no_answer_counter += 1
                else:
                    self.errors += ['CAN2 не отвечает']

                self.new_vmu_errors.emit(self.errors)

            current_time = int(round(time.time() * 1000))


class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow):
    record_vmu_params = False

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.setupUi(self)
        #  иконку пока не надо
        self.setWindowIcon(QIcon('icons_speed.png'))
        #  Создаю поток для опроса параметров кву
        self.thread_to_record = QThread()
        # создадим объект для выполнения кода в другом потоке
        self.vmu_req_thread = VMUSaveToFileThread()
        # перенесём объект в другой поток
        self.vmu_req_thread.moveToThread(self.thread_to_record)
        # после чего подключим все сигналы и слоты
        self.vmu_req_thread.new_vmu_params.connect(self.add_new_vmu_params)
        self.vmu_req_thread.new_vmu_errors.connect(self.add_new_vmu_errors)
        # подключим сигнал старта потока к методу run у объекта, который должен выполнять код в другом потоке
        self.thread_to_record.started.connect(self.vmu_req_thread.run)

    @pyqtSlot(list)
    def add_new_vmu_params(self, list_of_params: list):
        # если в списке строка - нахер такой список, похоже, нас отсоединили
        # но бывает, что параметр не прилетел в первый пункт списка, тогда нужно проверить,
        # что хотя бы два пункта списка - строки( или придумать более изощерённую проверку)
        if len(list_of_params) == 1:
            window.connect_btn.setText('Подключиться')
            window.power_box.setEnabled(False)
            window.speed_box.setEnabled(False)
            window.power_rb.setEnabled(True)
            window.speed_rb.setEnabled(True)
            window.blocks_list.setEnabled(True)
            window.reset_faults.setEnabled(False)
            window.record_vmu_params = False
            window.thread_to_record.running = False
            window.thread_to_record.terminate()
            marathon.close_marathon_canal()
            QMessageBox.critical(window, "Ошибка ", 'Нет подключения' + '\n' + str(list_of_params[0]), QMessageBox.Ok)
        else:
            fill_vmu_params_values(list_of_params)
            self.show_new_vmu_params()

    @pyqtSlot(list)
    def add_new_vmu_errors(self, list_of_errors: list):
        err = ''
        for er in list_of_errors:
            if er in vmu_errors_dict.keys():
                err += vmu_errors_dict[er] + '\n'
            else:
                err += 'Неизведанная ошибка номер ' + str(er) + '\n'
        window.errors_browser.setText(err)

    def show_new_vmu_params(self):
        row = 0
        for par in vmu_params_list:
            value_item = QTableWidgetItem(str(par['value']))
            value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
            self.vmu_param_table.setItem(row, 1, value_item)
            row += 1


if __name__ == '__main__':
    app = QApplication([])
    window = VMUMonitorApp()

    window.connect_btn.clicked.connect(connect_vmu)
    window.reset_faults.clicked.connect(reset_fault_btn_pressed)
    # window.steer_allow_cb.stateChanged.connect(steer_allowed_changed)
    # window.suspesion_allow_cb.stateChanged.connect(suspension_allowed_changed)
    window.blocks_list.currentItemChanged.connect(params_list_changed)

    window.front_mode_rb.toggled.connect(steer_mode_changed)
    window.circle_mode_rb.toggled.connect(steer_mode_changed)
    window.crab_mode_rb.toggled.connect(steer_mode_changed)

    window.speed_rb.toggled.connect(warning_message)
    window.power_rb.toggled.connect(warning_message)

    for name in command_list:
        spinbox_name = name + '_spinbox'
        spinbox = getattr(window, spinbox_name)
        spinbox.valueChanged.connect(spinbox_changed)
        spinbox.setEnabled(True)

        slider_name = name + '_slider'
        slider = getattr(window, slider_name)
        slider.valueChanged.connect(slider_changed)
        slider.setEnabled(True)

        if 'sus' in name:
            box_name = name + '_box'
            box = getattr(window, box_name)
            box.setEnabled(True)
            slider.setMinimum(-1 * suspension_stroke)
            slider.setMaximum(suspension_stroke)
            spinbox.setMinimum(-1 * suspension_stroke)
            spinbox.setMaximum(suspension_stroke)

    # window.buttonGroup_2.
    # Красота
    window.max_pos_sus_rb.setFont(QFont('MS Shell Dlg 2', 20))
    window.max_pos_sus_rb.setText(u'\u21E7')
    window.min_pos_sus_rb.setFont(QFont('MS Shell Dlg 2', 20))
    window.min_pos_sus_rb.setText(u'\u21E9')

    # kh = KeyboardHandler(window)
    # window.hook = keyboard.on_press(kh.keyboard_event_received)
    # keyboard.add_hotkey('ctrl + up', ctrl_up)
    # keyboard.add_hotkey('ctrl + down', ctrl_down)
    # keyboard.add_hotkey('ctrl + left', ctrl_left)
    # keyboard.add_hotkey('ctrl + right', ctrl_right)
    node_list = fill_node_list(pathlib.Path(dir_path, 'Tables', vmu_param_file))
    evo_nodes = {}
    for node in node_list:
        evo_nodes[node['name']] = NodeOfEVO(node)
    pprint(evo_nodes[list(evo_nodes.keys())[1]].params_list)
    bookmark_dict = fill_bookmarks_list(pathlib.Path(dir_path, 'Tables', vmu_param_file))

    if bookmark_dict:
        window.blocks_list.addItems(list(bookmark_dict))
        window.blocks_list.setCurrentRow(0)
        vmu_params_list = fill_vmu_list(bookmark_dict[list(bookmark_dict.keys())[0]])
        vmu_errors_dict = make_vmu_error_dict(pathlib.Path(dir_path, 'Tables', vmu_errors_file))

        req_list = feel_req_list(vmu_params_list)
        show_empty_params_list(vmu_params_list, 'vmu_param_table')

        window.show()  # Показываем окно
        app.exec_()  # и запускаем приложение
