"""
на сегодня28.07.22:
- сделать модуль определения адаптера, если его нет, то и не включаться вовсе
- сделать максимально быстрое определение
-отключился блок(нет ответа на более 3х обязательных запросов),
-отключили шину(нет вообще никаких сообщений),
-отключили адаптер
--- нужно отваливаться

- сделать определение адаптера для виндовз
- сделать определение наличия на шине блоков
- продумать реляционную БД для параметров
- сделать возможность выбора нужных параметров для своего списка

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
import time
from pprint import pprint
import sys
import traceback

from PyQt5.QtCore import QThread, pyqtSignal, pyqtSlot, Qt, QTimer, QEventLoop
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QMessageBox, QTableWidgetItem, QApplication, QMainWindow, QTreeWidgetItem
import pathlib
import ctypes
import struct
import VMU_monitor_ui
from kvaser_power import Kvaser
from marathon_power import CANMarathon
from work_with_file import fill_vmu_list, make_vmu_error_dict, feel_req_list, fill_node_list
from sys import platform

can_adapter = None

dir_path = str(pathlib.Path.cwd())
vmu_param_file = 'table_for_params_new_VMU1.xlsx'
vmu_errors_file = 'kvu_error_codes_my.xlsx'


# Если при ошибке в слотах приложение просто падает без стека,
# есть хороший способ ловить такие ошибки:
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print(text)
    QMessageBox.critical(None, 'Error', text)
    quit()


sys.excepthook = log_uncaught_exceptions


class AThread(QThread):
    threadSignalAThread = pyqtSignal(list)
    max_iteration = 1000
    iter_count = 1

    def __init__(self):
        super().__init__()

    def run(self):
        def emitting():
            self.threadSignalAThread.emit(self.ans_list)
            self.params_counter = 0
            self.errors_counter = 0
            self.ans_list = []
            self.iter_count += 1
            if self.iter_count > self.max_iteration:
                self.iter_count = 1

        def request_node():

            if not self.iter_count == 1:
                while not self.iter_count % vmu_params_list[self.params_counter]['period'] == 0:
                    self.ans_list.append(bytearray([0, 0, 0, 0, 0, 0, 0, 0]))
                    self.params_counter += 1
                    if self.params_counter == self.len_param_list:
                        emitting()
                        return

            param = can_adapter.can_request(self.current_node.req_id, self.current_node.ans_id,
                                            req_list[self.params_counter])
            self.ans_list.append(param)
            self.params_counter += 1

            if isinstance(param, str):
                self.errors_counter += 1
                if self.errors_counter > 3:
                    self.threadSignalAThread.emit([param])
                    return
            else:
                self.errors_counter = 0

            if self.params_counter == self.len_param_list:
                emitting()

        send_delay = 10  # задержка отправки в кан сообщений
        self.len_param_list = len(req_list)
        self.current_node = evo_nodes[window.nodes_tree.currentItem().parent().text(0)]
        self.errors_counter = 0
        self.params_counter = 0
        self.ans_list = []

        timer = QTimer()
        timer.timeout.connect(request_node)
        timer.start(send_delay)
        loop = QEventLoop()
        loop.exec_()


# запросить у мэишного инвертора параметр 00000601 8 HEX   40  01  21  00
# записать в мэишный инвертор параметр    00000601 8 HEX   20  01  21  00
# есть подозрения, что последний байт - номер параметра из файла пдф

def params_list_changed():
    global vmu_params_list, req_list
    is_run = False
    param_list = window.nodes_tree.currentItem().text(0)
    if param_list in list(evo_nodes.keys()):
        return False
    else:
        if window.thread.isRunning():
            is_run = True
            window.connect_to_node()

        node = window.nodes_tree.currentItem().parent().text(0)
        # param_list = window.nodes_tree.currentItem().text(0)
        if hasattr(evo_nodes[node], 'params_list'):
            vmu_params_list = fill_vmu_list(evo_nodes[node].params_list[param_list])
            req_list = feel_req_list(evo_nodes[node].protocol, vmu_params_list)
            show_empty_params_list(vmu_params_list, 'vmu_param_table')
            if is_run and window.thread.isFinished():
                window.connect_to_node()
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
                # для реек вот так  address_ans = '0x' + int_to_hex_str(data[4]) + int_to_hex_str(data[5]) наверное
                # для реек вот так  value = (data[3] << 24) + (data[2] << 16) + (data[1] << 8) + data[0]
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
    pass


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


# поток для сохранения настроечных параметров блока в файл
# поток для ответа на апи
#  поток для опроса и записи текущих в файл параметров кву

class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow):
    record_vmu_params = False

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.setupUi(self)
        self.setWindowIcon(QIcon('icons_speed.png'))
        #  Создаю поток для опроса параметров кву
        self.thread = AThread()

    @pyqtSlot(list)
    def add_new_vmu_params(self, list_of_params: list):
        global can_adapter
        if len(list_of_params) < 2 and isinstance(list_of_params[0], str):
            err = str(list_of_params[0])
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
                QMessageBox.critical(window, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.Ok)
            self.connect_btn.setText("Подключиться")
            if can_adapter is not None:
                can_adapter.close_canal_can()
            if err == 'Адаптер не подключен':
                can_adapter = None
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

    def connect_to_node(self):
        global can_adapter
        if can_adapter is None:
            if platform == "linux" or platform == "linux2":  # linux
                can_adapter = Kvaser(0, 125)
            elif platform == "darwin":  # OS X
                print("Ошибка " + 'С таким говном не работаем' + '\n' + "Вон ОТСЮДА!!!")
            elif platform == "win32":  # Windows...
                can_adapter = Kvaser(0, 125)
                mes = can_adapter.can_request(0, 0, [0])
                if isinstance(mes, str):
                    if mes == 'Адаптер не подключен':
                        can_adapter = CANMarathon()

        if not self.thread.isRunning():
            self.thread.threadSignalAThread.connect(self.add_new_vmu_params)
            self.thread.finished.connect(self.finishedAThread)
            self.thread.iter_count = 1
            self.thread.start()
            self.connect_btn.setText("Отключиться")
            # self.nodes_tree.setEnabled(False)
        else:
            self.thread.quit()
            self.thread.wait()
            self.connect_btn.setText("Подключиться")
            can_adapter.close_canal_can()

    def finishedAThread(self):
        pass

    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Информация',
                                     "Вы уверены, что хотите закрыть приложение?",
                                     QMessageBox.Yes,
                                     QMessageBox.No)
        if reply == QMessageBox.Yes:
            if self.thread:
                self.thread.quit()
                self.thread.wait()
            del self.thread
            if can_adapter is not None:
                can_adapter.close_canal_can()
        else:
            event.ignore()


if __name__ == '__main__':
    app = QApplication([])
    window = VMUMonitorApp()
    window.setWindowTitle('Параметры всех блоков нижнего уровня EVO1')
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    window.connect_btn.clicked.connect(window.connect_to_node)

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
        window.vmu_param_table.adjustSize()
        window.nodes_tree.adjustSize()
        window.show()  # Показываем окно
        app.exec_()  # и запускаем приложение
