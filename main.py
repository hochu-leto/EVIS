from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, Qt
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication, QMainWindow
import datetime
import pathlib
import pandas
import ctypes
import time
import VMU_monitor_ui
from dll_power import CANMarathon

drive_limit = 30000 * 0.2  # 20% момента - достаточно, чтоб заехать на горку у выхода и не разложиться без тормозов
ref_torque = 0
start_time = int(round(time.time() * 1000))
send_delay = 50  # задержка отправки в кан сообщений
# // сброс ошибок
RESET_FAULTS = 8
marathon = CANMarathon()
dir_path = str(pathlib.Path.cwd())
vmu_param_file = 'table_for_params.xlsx'
VMU_ID_PDO = 0x00000401
rtcon_vmu = 0x00000601
vmu_rtcon = 0x00000581


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


def feel_req_list(p_list: list):
    req_list = []
    for par in p_list:
        address = par['address']
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        data = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
        req_list.append(data)
    return req_list


def fill_vmu_list(file_name):
    excel_data_df = pandas.read_excel(file_name)
    vmu_params_list = excel_data_df.to_dict(orient='records')
    exit_list = []
    for par in vmu_params_list:
        if str(par['name']) != 'nan':
            if str(par['address']) != 'nan':
                if isinstance(par['address'], str):
                    if '0x' in par['address']:
                        par['address'] = par['address'].rsplit('x')[1]
                    par['address'] = int(par['address'], 16)
                if str(par['scale']) == 'nan':
                    par['scale'] = 1
                if str(par['scaleB']) == 'nan':
                    par['scaleB'] = 0
                exit_list.append(par)
    return exit_list


def adding_to_csv_file(name_or_value: str):
    data = []
    data_string = []
    for par in vmu_params_list:
        data_string.append(par[name_or_value])
    dt = datetime.datetime.now()
    dt = dt.strftime("%H:%M:%S.%f")
    if name_or_value == 'name':
        dt = 'time'
    data_string.append(dt)
    data.append(data_string)
    df = pandas.DataFrame(data)
    df.to_csv(window.vmu_req_thread.recording_file_name,
              mode='a',
              header=False,
              index=False,
              encoding='windows-1251')


def connect_vmu():
    param_list = [[0x40, 0x18, 0x10, 0x02, 0x00, 0x00, 0x00, 0x00]]
    # Проверяю, есть ли подключение к кву
    check = marathon.can_request_many(rtcon_vmu, vmu_rtcon, param_list)
    if isinstance(check, list):
        check = check[0]
    if isinstance(check, str):
        QMessageBox.critical(window, "Ошибка ", 'Нет подключения' + '\n' + check, QMessageBox.Ok)
        window.connect_btn.setText('Подключиться')
        window.start_btn.setEnabled(False)
        window.power_box.setEnabled(False)
        window.reset_faults.setEnabled(False)
        return False

    # запрашиваю список полученных ответов
    ans_list = marathon.can_request_many(rtcon_vmu, vmu_rtcon, req_list)
    fill_vmu_params_values(ans_list)
    # отображаю сообщения из списка
    window.show_new_vmu_params()
    # разблокирую все кнопки и чекбоксы
    window.connect_btn.setText('Отключиться')
    window.start_btn.setEnabled(True)
    window.power_box.setEnabled(True)
    window.reset_faults.setEnabled(True)
    return True


def const_req_vmu_params():
    if not window.vmu_req_thread.running:
        window.vmu_req_thread.running = True
        window.thread_to_record.start()
    else:
        window.vmu_req_thread.running = False
        window.thread_to_record.terminate()


def start_btn_pressed():
    # если записи параметров ещё нет, включаю ее
    if not window.record_vmu_params:
        window.vmu_req_thread.recording_file_name = pathlib.Path(pathlib.Path.cwd(),
                                                                 'VMU records',
                                                                 'vmu_record_' +
                                                                 datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") +
                                                                 '.csv')

        window.connect_btn.setEnabled(False)
        window.record_vmu_params = True
        window.start_btn.setText('Стоп')
        adding_to_csv_file('name')
    #  если запись параметров ведётся, отключаю её и сохраняю файл
    else:
        window.record_vmu_params = False
        window.start_record.setText('Начать запись')
        window.connect_btn.setEnabled(True)
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


def fill_vmu_params_values(ans_list: list):
    i = 0
    for par in vmu_params_list:
        message = ans_list[i]
        if not isinstance(message, str):
            value = (message[7] << 24) + \
                    (message[6] << 16) + \
                    (message[5] << 8) + message[4]
            #  вывод на печать полученных ответов
            # print(par['name'])
            # for j in message:
            #     print(hex(j), end=' ')
            # если множителя нет, то берём знаковое int16
            if par['scale'] == 1:
                par['value'] = ctypes.c_int16(value).value
            # возможно, здесь тоже нужно вытаскивать знаковое int, ага, int32
            else:
                value = ctypes.c_int32(value).value
                par['value'] = (value / par['scale'])
            par['value'] = float('{:.2f}'.format(par['value']))
        i += 1
    print('Новые параметры КВУ записаны ')


#  поток для опроса и записи в файл параметров кву
class VMUSaveToFileThread(QObject):
    running = False
    new_vmu_params = pyqtSignal(list)
    recording_file_name = ''

    # метод, который будет выполнять алгоритм в другом потоке
    def run(self):
        while True:
            if window.record_vmu_params:
                adding_to_csv_file('value')
            #  Получаю новые параметры от КВУ
            ans_list = []
            answer = marathon.can_request_many(rtcon_vmu, vmu_rtcon, req_list)
            # Если происходит разрыв связи в блоком во время чтения
            #  И прилетает строка ошибки, то надо запихнуть её в список
            if isinstance(answer, str):
                ans_list.append(answer)
            else:
                ans_list = answer.copy()
            #  И отправляю их в основной поток для обновления
            self.new_vmu_params.emit(ans_list)

            QThread.msleep(100)


class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow):
    record_vmu_params = False

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.setupUi(self)
        #  иконку пока не надо
        # self.setWindowIcon(QIcon('icon.png'))
        #  Создаю поток для опроса параметров кву
        self.thread_to_record = QThread()
        # создадим объект для выполнения кода в другом потоке
        self.vmu_req_thread = VMUSaveToFileThread()
        # перенесём объект в другой поток
        self.vmu_req_thread.moveToThread(self.thread_to_record)
        # после чего подключим все сигналы и слоты
        self.vmu_req_thread.new_vmu_params.connect(self.add_new_vmu_params)
        # подключим сигнал старта потока к методу run у объекта, который должен выполнять код в другом потоке
        self.thread_to_record.started.connect(self.vmu_req_thread.run)

    @pyqtSlot(list)
    def add_new_vmu_params(self, list_of_params: list):
        # если в списке строка - нахер такой список, похоже, нас отсоединили
        # но бывает, что параметр не прилетел в первый пункт списка, тогда нужно проверить,
        # что хотя бы два пункта списка - строки( или придумать более изощерённую проверку)
        if len(list_of_params) == 1:
            window.connect_btn.setText('Подключиться')
            window.connect_btn.setEnabled(True)
            window.start_btn.setText('Начать запись')
            window.start_btn.setEnabled(False)
            window.record_vmu_params = False
            window.thread_to_record.running = False
            window.thread_to_record.terminate()
            QMessageBox.critical(window, "Ошибка ", 'Нет подключения' + '\n' + list_of_params[0], QMessageBox.Ok)
        else:
            fill_vmu_params_values(list_of_params)
            self.show_new_vmu_params()

    def show_new_vmu_params(self):
        row = 0
        for par in vmu_params_list:
            value_Item = QTableWidgetItem(str(par['value']))
            # value_Item.setFlags(value_Item.flags() & ~Qt.ItemIsEditable)
            self.vmu_param_table.setItem(row, window.value_col, value_Item)
            row += 1


r_fault = RESET_FAULTS  # сбрасываем ошибки - сбросить в 0 при следующей итерации

current_time = int(round(time.time() * 1000))

torque_data = int(ref_torque)
data = [r_fault + 0b10001,
        torque_data & 0xFF, ((torque_data & 0xFF00) >> 8),
        0, 0, 0, 0, 0]

if (current_time - start_time) > send_delay:
    start_time = current_time
    marathon.can_write(VMU_ID_PDO, data)

app = QApplication([])
window = VMUMonitorApp()

vmu_params_list = fill_vmu_list(pathlib.Path(dir_path, 'Tables', vmu_param_file))
req_list = feel_req_list(vmu_params_list)
show_empty_params_list(vmu_params_list, 'vmu_param_table')

window.show()  # Показываем окно
app.exec_()  # и запускаем приложение
