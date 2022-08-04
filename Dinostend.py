"""
на сегодня28.07.22:
- сделать модуль определения адаптера, если его нет, то и не включаться вовсе
- сделать максимально быстрое определение
-отключился блок(нет ответа на более 3х обязательных запросов),
-отключили шину(нет вообще никаких сообщений),
-отключили адаптер
--- нужно отваливаться

- задать частоту опроса параметра, серийники не надо постоянно опрашивать, вялотекущий типа температуры не нужно
 так часто как ток или угол поворота - это должно быть редактируемо
-- по поводу частоты опроса параметра, если поле ref_rate отсутствует или рано 0 или равно Nan (тогда ref_rate = 1)
 то принимаем максимальное  время опроса = 10с = 10 000мс, самое быстрое, что я могу опросить - это 50мс -
 значит максимальное значение при этом будет 2000, т.е. частота опроса(мс) = 10000/ref_rate

- на основе блока ево создать 3 сущности кву + инвертор + руль
-- на основе сущностей создавать все возможные кву,
инверторы и рули - НЕВЕРНО - могут быть ещё и БМС БЗУ ИСН и иже с ними, хрен знает какие ещё блоки могут быть
использованы,  какими протоколами. Это должна быть расширяемая тема - объект EVO_Node
- у сущности должны быть свойства - ключевые параметры, описаны в листе с названием, размерностями и используемым виджетом
- должен быть серийный номер,
- версия ПО,
- адрес по которому запрашиваются ошибки,
- адрес по которому сбрасываются ошибки
- на отдельном листе список ошибок, и что с ними делать, возможно даже список параметров,
которые следует проверять при этой ошибке, какие-то рекомендации по ремонту, схемы, ссылки
- на отдельном листе управление для этого блока с виджетами типами - слайдеры, кнопки, чекбоксы - по каким адресам,
  название и так далее.
- Программа должна опрашивать на ID серийный номер или версию прошивки , если есть - добавлять блок в список имеющихся и
выводить в соседнем окошке список определённых для этого блока виджетов (слайдеры, кнопки) + количество этих окошек с
виджетами для каждого блока задаёт пользователь, т.е. он может создать свои нужные виджеты и сохранить их в профиль к
этому блоки, а при загрузке это должно подгрузится - и стандартные и выбранные для того блока пользователем -
полагаю отдельный лист Экселя с выбранными параметрами - виджетами
- Должно быть две кнопки - запись текущих параметров в Эксель файл и запись всех параметров текущего блока
- ещё кнопка - загрузка параметров из файла - здесь должна быть жёсткая защита - не все редактируемые параметры
 из одного блока можно напрямую заливать в другой. Или их ограничить до минимума или предлагать делать изменение вручную

СДЕЛАНО
- сделать несколько блоков по ИД - как их запихнуть в эксель
- как сделать нормальную размерность в таблице
- раздвигать таблицу по окну
- На каждый блок в экселе - лист со свойствами, лист со всеми возможными параметрами + один лист с заголовками
и подзаголовком параметры для каждой страницы - парсить как для БУРР
- парсить файлы настроек старого кву и инвертора

ПОКА НЕ НАДО, НО МОЖНО ПОДУМАТЬ
- ВОЧДОГ адатера
--наличия КАН шины,
--наличия нужного блока,
--что адаптер подключен
----если что-то из этого не срабатывает (
 - полагаю это отдельный поток, раз в 500 мс после запуска программы должен опрашивать наличие
адаптера и наличие сообщений в шине, он главнее остального. А в потоке опроса параметров должен периодически(когда нет 3х подряд ответов) посылать
(но не отображать) несколько обязательных параметров
марафон очень долго отдупляет что нет шины - по такой ошибке следует прерывать опрос и сразу выдавать предупреждение

"""
from pprint import pprint

from PyQt5.QtCore import QThread, pyqtSignal, QObject, pyqtSlot, Qt
from PyQt5.QtGui import QIcon, QFont
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication, QMainWindow, QTreeWidgetItem, QTreeWidget
import datetime
import pathlib
import ctypes
import struct
import time
import VMU_monitor_ui
from kvaser_power import Kvaser
from marathon_power import CANMarathon
from work_with_file import fill_vmu_list, make_vmu_error_dict, feel_req_list, adding_to_csv_file, fill_bookmarks_list, \
    fill_node_list
from sys import platform

if platform == "linux" or platform == "linux2":
    can_adapter = Kvaser(0, 125)
    # linux
elif platform == "darwin":
    print("Ошибка " + 'С таким говном не работаем' + '\n' + "Вон ОТСЮДА!!!")
    pass
    # OS X
elif platform == "win32":
    can_adapter = Kvaser(0, 125)
    # can_adapter = CANMarathon()
    # Windows...

dir_path = str(pathlib.Path.cwd())
vmu_param_file = 'table_for_params_new_VMU1.xlsx'
vmu_errors_file = 'kvu_error_codes_my.xlsx'
VMU_ID_PDO = 0x00000403
command_list = {'power', 'speed', 'front_steer', 'rear_steer', 'fl_sus', 'fr_sus', 'rr_sus', 'rl_sus'}


# запросить у мэишного инвертора параметр 00000601 8 HEX   40  01  21  00
# записать в мэишный инвертор параметр    00000601 8 HEX   20  01  21  00
# есть подозрения, что последний байт - номер параметра из файла пдф

def params_list_changed():
    global vmu_params_list, req_list
    param_list = window.nodes_tree.currentItem().text(0)
    if param_list in list(evo_nodes.keys()):
        return False
    else:
        node = window.nodes_tree.currentItem().parent().text(0)
        param_list = window.nodes_tree.currentItem().text(0)
        if hasattr(evo_nodes[node], 'params_list'):
            vmu_params_list = fill_vmu_list(evo_nodes[node].params_list[param_list])
            req_list = feel_req_list(vmu_params_list)
            show_empty_params_list(vmu_params_list, 'vmu_param_table')
            return True
        else:
            QMessageBox.critical(None, "Ошибка ", 'В этом блоке нет параметров\n Проверь файл с блоками',
                                 QMessageBox.Ok)
            return False


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
        # window.vmu_req_thread.recording_file_name = pathlib.Path(pathlib.Path.cwd(), 'VMU_records', 'vmu_record_' +
        # datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + '.csv') adding_to_csv_file('name', vmu_params_list,
        # window.vmu_req_thread.recording_file_name) разблокирую все кнопки и чекбоксы
        window.connect_btn.setText('Отключиться')
        window.nodes_tree.setEnabled(False)
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
        window.nodes_tree.setEnabled(True)
        print('Останавливаю канал 1 марафона')
        can_adapter.close_canal_can()
    return True


def zero_del(s):
    return '{:g}'.format(s)


def fill_vmu_params_values(ans_list: list):
    for message in ans_list:
        if message:
            if not isinstance(message, str):
                #  это работает для протокола CANOpen, где значение параметра прописано в последних 4 байтах
                address_ans = '0x' \
                              + int_to_hex_str(message[2]) \
                              + int_to_hex_str(message[1]) \
                              + int_to_hex_str(message[3])

                value = (message[7] << 24) + \
                        (message[6] << 16) + \
                        (message[5] << 8) + message[4]
                # ищу в списке параметров како-то с тем же адресом, что в ответе
                for par in vmu_params_list:
                    if hex(par["address"]) == address_ans:
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
                        break


def int_to_hex_str(x: int):
    return hex(x)[2:].zfill(2)


def reset_fault_btn_pressed():
    window.vmu_req_thread.reset_fault_timer = 5
    window.vmu_req_thread.errors = []


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


# поток для отслеживания подключения адаптера и кан-шины
class CANAdapterWatchDog(QObject):
    adapter_connected = pyqtSignal(bool)
    CAN_bus_connected = pyqtSignal(bool)
    start_time = int(round(time.time() * 1000))
    time_for_check_adapter = start_time
    check_period = 250

    @pyqtSlot()
    def run(self):
        while True:
            if (current_time - self.time_for_check_adapter) > self.check_period:
                self.time_for_check_adapter = current_time
                self.adapter_connected.emit(True)
                self.CAN_bus_connected.emit(True)
            current_time = int(round(time.time() * 1000))

# поток для сохранения настроечных параметров блока в файл
# поток для ответа на апи
#  поток для опроса и записи текущих в файл параметров кву
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
    reset_fault_timer = 0
    brake_timer = 0

    # метод, который будет выполнять алгоритм в другом потоке
    def run(self):
        len_param_list = len(req_list)
        errors_counter = 0
        params_counter = 0
        ans_list = []
        while True:
            # adding_to_csv_file('value', vmu_params_list, window.vmu_req_thread.recording_file_name)

            # попытаюсь за каждый прогон опрашивать один параметр
            # - думается, это не даст КВУ потерять связь с программой
            current_node = evo_nodes[window.nodes_tree.currentItem().parent().text(0)]
            param = can_adapter.can_request(current_node.req_id, current_node.ans_id, req_list[params_counter])
            ans_list.append(param)
            if isinstance(param, str):
                # if param == 'Нет CAN шины больше секунды ' or param == 'Адаптер не подключен':
                #     self.new_vmu_params.emit([param])
                errors_counter += 1
            params_counter += 1
            # неправильно - если три подряд значения - текстовые - значит обрыв связи с блоком,
            # следует послать запрос на обязательное сообщение( трижды на всякий случай),если нет - ошибка, стоп поток
            if errors_counter > len_param_list / 3:
                self.new_vmu_params.emit(ans_list[:1])
            if params_counter == len_param_list:
                self.new_vmu_params.emit(ans_list)
                errors_counter = 0
                params_counter = 0
                ans_list = []

            # if (current_time - self.time_for_errors) > self.send_delay * 10:
            #     self.time_for_errors = current_time
            #     if no_answer_counter < 10:
            #         error = marathon.can_request(rtcon_vmu, vmu_rtcon, [0x40, 0x15, 0x21, 0x01, 0, 0, 0, 0])
            #         pprint(error)
            #         if not isinstance(error, str):
            #             value = (error[5] << 8) + error[4]
            #             error = ctypes.c_uint16(value).value
            #         else:
            #             no_answer_counter += 1
            #
            #         if error not in self.errors:
            #             self.errors.append(error)
            #     else:
            #         self.errors = ['КВУ не отвечает на запрос ошибок']
            #
            #     self.new_vmu_errors.emit(self.errors)
            # current_time = int(round(time.time() * 1000))


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
        if len(list_of_params) < 2:
            window.connect_btn.setText('Подключиться')
            window.nodes_tree.setEnabled(True)
            window.reset_faults.setEnabled(False)
            window.record_vmu_params = False
            window.thread_to_record.running = False
            window.thread_to_record.terminate()
            can_adapter.close_canal_can()

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
                err += 'Неизведанная ошибка ' + str(er) + '\n'
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
    window.nodes_tree.currentItemChanged.connect(params_list_changed)

    node_list = fill_node_list(pathlib.Path(dir_path, 'Tables', vmu_param_file))
    vmu_errors_dict = make_vmu_error_dict(pathlib.Path(dir_path, 'Tables', vmu_errors_file))

    evo_nodes = {}
    # бахаю словарь всех объектов узлов, впоследствии необходимо научить их как-то определяться на машине
    for node in node_list:
        evo_nodes[node['name']] = NodeOfEVO(node)

    window.nodes_tree.setColumnCount(1)
    window.nodes_tree.header().close()
    items = []
    for node in evo_nodes.values():
        item = QTreeWidgetItem()
        item.setText(0, node.name)
        if hasattr(node, 'params_list'):
            for param_list in node.params_list.keys():
                child_item = QTreeWidgetItem()
                child_item.setText(0, str(param_list))
                item.addChild(child_item)
        items.append(item)

    window.nodes_tree.insertTopLevelItems(0, items)
    window.nodes_tree.setCurrentItem(window.nodes_tree.topLevelItem(0).child(0))

    if node_list and params_list_changed():
        window.show()  # Показываем окно
        app.exec_()  # и запускаем приложение
