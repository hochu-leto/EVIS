"""
Всякие вспомогательные функции
"""
import struct
import traceback
from time import perf_counter

import numpy
from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox, \
    QCheckBox, QWidget, QHBoxLayout, QPushButton, QGraphicsProxyWidget, QDockWidget, QGridLayout, QMainWindow
from pyqtgraph import PlotWidget, mkPen, GraphicsLayoutWidget

import my_dialog
from EVOWidgets import GreenLabel, MyComboBox, MyEditLine, zero_del, MyColorBar, MySlider, color_EVO_red_dark, \
    color_EVO_white, GraphCheckBox

NAME_COLUMN = 0
DESCRIPTION_COLUMN = 1
GRAPH_COLUMN = 2
VALUE_COLUMN = 3
COMPARE_COLUMN = 4
UNIT_COLUMN = 5
headers_list = ['Параметр', 'Описание', 'GR', 'Значение', 'Сравнение', 'Размерность']

TheBestNode = 'Избранное'
NewParamsList = 'Новый список'
easter_egg = 'Бинго! Ты нашёл тот самый параметр после изменения которого блок рулевой рейки меняет свои ID и выходит ' \
             'из чата.(перестаёт отвечать) Ничего страшного, нужно перезагрузить программу и заново определить все ' \
             'блоки. Очень надеюсь ты понимаешь что делаешь и что в данный момент подключен только ОДИН блок рулевой ' \
             'рейки. В противном случае ты поимеешь два блока, которые отвечают по одинаковым адресам, и тогда уже ' \
             'по-любому придётся отключать один из них так что лучше сделай это заранее '
empty_par = {'name': '',
             'address': '',
             'editable': '',
             'description': '',
             'scale': '',
             'offset': '',
             'unit': '',
             'value': '',
             'type': '',
             'group': '',
             'period': '',
             # 'size': '',
             'degree': '',
             'min_value': '',
             'max_value': '',
             # 'widget': '',
             # 'value_compare': '',
             'value_table': {}}
# 'value_string': ''}
#  параметр для экспериментов
example_par = {'name': 'fghjk',
               'address': '34567',
               'editable': 1,
               'description': 'ytfjll hkvlbjkkj',
               'scale': 10,
               'scaleB': -40,
               'unit': 'A',
               'value': '23',
               'type': 'SIGNED16',
               'group': '1',
               'period': '20',
               'size': 'nan',
               'degree': 3,
               'value_table': '1: dvfvdhfh, 2:ygsksu, 5:uvcjvacj, 111:bhjbhjhj'}


def buf_to_string(buf):
    if isinstance(buf, str):
        return buf
    s = ''
    for i in buf:
        s += hex(i) + ' '
    return s


def find_param(s: str, node=None, nodes_dict=None) -> list:
    list_of_params = []
    s = s.upper().strip()
    if node is None:
        list_of_params = [param for nd in nodes_dict.values() if nd.name != TheBestNode
                          for param_list in nd.group_params_dict.values()
                          for param in param_list
                          if s in param.name.upper() or s in param.description.upper()]
    elif isinstance(node, str):
        if node in nodes_dict.keys():
            nd = nodes_dict[node]
            list_of_params = [param for param_list in nd.group_params_dict.values()
                              for param in param_list
                              if s in param.name.upper() or s in param.description.upper()]
    elif hasattr(node, 'group_params_dict'):
        list_of_params = [param for param_list in node.group_params_dict.values()
                          for param in param_list
                          if s in param.name.upper() or s in param.description.upper()]
    return list_of_params


@pyqtSlot(object)
def focus_in(item):
    print("focus in", item.isInFocus, item.text())


@pyqtSlot()
def focus_out():
    print("focus out")


def show_empty_params_list(list_of_params: list, show_table: QTableWidget, has_compare=False, par_in_graph_list=[]):
    items_list = []
    show_table.setRowCount(0)
    show_table.setRowCount(len(list_of_params))
    show_table.setColumnCount(len(headers_list))
    show_table.setHorizontalHeaderLabels(headers_list)

    for row, par in enumerate(list_of_params):
        name = par.name
        unit = par.units
        description = par.description
        v_c = par.value_compare
        if isinstance(v_c, str):
            compare = v_c
        elif par.value_table:
            k = int(v_c)
            if k in par.value_table:
                compare = par.value_table[k]
            else:
                compare = f'{k} нет в словаре'
        else:
            compare = zero_del(v_c)

        if par.editable:
            lb = GreenLabel()
            lb.setText(name)
            lb.setToolTip(description)
            show_table.setCellWidget(row, NAME_COLUMN, lb)
        else:
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            name_item.setToolTip(description)
            show_table.setItem(row, NAME_COLUMN, name_item)

        match par.widget:
            case 'MyColorBar':
                show_table.setCellWidget(row, DESCRIPTION_COLUMN, MyColorBar(parametr=par))
            case 'MySlider':
                widget = MySlider(parametr=par)
                show_table.setCellWidget(row, DESCRIPTION_COLUMN, widget)
                items_list.append(widget)
            case _:
                desc_item = QTableWidgetItem(description)
                # desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                desc_item.setFlags(desc_item.flags() | Qt.ItemFlag.ItemIsEditable)
                desc_item.setToolTip(description)
                show_table.setItem(row, DESCRIPTION_COLUMN, desc_item)

        graph_checkbox = GraphCheckBox(parametr=par)
        graph_checkbox.setChecked(par in par_in_graph_list)
        cell_widget = QWidget()
        lay_out = QHBoxLayout(cell_widget)
        lay_out.addWidget(graph_checkbox)
        lay_out.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lay_out.setContentsMargins(0, 0, 0, 0)
        cell_widget.setLayout(lay_out)
        show_table.setCellWidget(row, GRAPH_COLUMN, cell_widget)
        # show_table.setCellWidget(row, GRAPH_COLUMN, graph_checkbox)

        value_item = QTableWidgetItem('')
        value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        color_opacity = int((150 / 1000) * abs(par.period)) + 3
        value_item.setBackground(QColor(0, 255, 255, color_opacity))
        value_item.setToolTip(f'{par.min_value}...{par.max_value}')
        show_table.setItem(row, VALUE_COLUMN, value_item)

        compare_item = QTableWidgetItem(compare)
        compare_item.setFlags(compare_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        show_table.setItem(row, COMPARE_COLUMN, compare_item)

        unit_item = QTableWidgetItem(unit)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        show_table.setItem(row, show_table.columnCount() - 1, unit_item)

    show_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    # show_table.setColumnHidden(show_table.columnCount() - 2, not has_compare)
    show_table.setColumnHidden(COMPARE_COLUMN, not has_compare)
    # # максимальная ширина у описания, если не хватает длины, то переносится
    show_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    show_table.horizontalHeader().setSectionResizeMode(DESCRIPTION_COLUMN, QHeaderView.ResizeMode.Stretch)
    show_table.horizontalHeader().setSectionResizeMode(NAME_COLUMN, QHeaderView.ResizeMode.ResizeToContents)
    show_table.horizontalHeader().setSectionResizeMode(GRAPH_COLUMN, QHeaderView.ResizeMode.ResizeToContents)
    show_table.setColumnWidth(VALUE_COLUMN, 150)
    return items_list


def show_new_vmu_params(params_list, table, has_compare_params=False):
    items_list = []
    for row, par in enumerate(params_list):
        it = table.cellWidget(row, VALUE_COLUMN)
        if hasattr(it, 'isInFocus') \
                and it.isInFocus:
            continue
        value_in_dict = False
        if par.value_string:
            v_name = par.value_string
        elif isinstance(par.value, str):
            v_name = par.value
        elif par.value_table:
            if par.value is not None:
                k = int(par.value)
                if k in par.value_table:
                    value_in_dict = True
                    v_name = par.value_table[k]
                else:
                    v_name = f'{k} нет в словаре'
            else:
                v_name = f'Нет ответа'
        else:
            v_name = zero_del(par.value)

        if value_in_dict and par.editable:
            if not isinstance(it, MyComboBox):
                widget_ = MyComboBox(parametr=par)
                table.setCellWidget(row, VALUE_COLUMN, widget_)
                items_list.append(widget_)
            table.cellWidget(row, VALUE_COLUMN).set_text()
        elif par.editable:
            if not isinstance(it, MyEditLine):
                widget_ = MyEditLine(v_name, parametr=par)
                table.setCellWidget(row, VALUE_COLUMN, widget_)
                items_list.append(widget_)
            table.cellWidget(row, VALUE_COLUMN).set_text()
        else:
            table.item(row, VALUE_COLUMN).setText(v_name)

        if has_compare_params:
            compare_name = table.item(row, COMPARE_COLUMN).text()
            # здесь тоже неплохо бы делать цветную метку, но я так всё утоплю в метках
            color_ = color_EVO_red_dark if v_name.strip() != compare_name.strip() else color_EVO_white
            table.item(row, COMPARE_COLUMN).setBackground(color_)

        if par.widget != 'Text':
            table.cellWidget(row, DESCRIPTION_COLUMN).set_value()

    return items_list


class EVOGraph(QMainWindow):
    chunkSize = 100
    maxChunks = 10
    pens = [mkPen(color=(0, 255, 0)), mkPen(color=(255, 0, 0)), mkPen(color=(0, 0, 255)),
            mkPen(color=(0, 255, 255)), mkPen(color=(255, 255, 0)), mkPen(color=(255, 0, 255))]

    def __init__(self):
        super().__init__()
        self.data_y = None
        self.params_list = None
        self.data_x = numpy.zeros((self.chunkSize + 1))
        self.counter = 0
        self.curves = []
        self.startTime = perf_counter()
        self.dock_widget = QDockWidget('Dockable', self)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName("dockWidgetContents")
        self.gridLayout = QGridLayout(self.dockWidgetContents)
        self.gridLayout.setObjectName("gridLayout")
        self.start_stop_btn = QPushButton('СТАРТ', parent=self.dockWidgetContents)
        self.start_stop_btn.setObjectName("start_stop_btn")
        self.gridLayout.addWidget(self.start_stop_btn, 0, 0, 1, 1)
        self.clear_btn = QPushButton('СБРОС', parent=self.dockWidgetContents)
        self.clear_btn.setObjectName("clear_btn")
        self.clear_btn.setEnabled(False)
        self.gridLayout.addWidget(self.clear_btn, 0, 7, 1, 1)
        self.widget = PlotWidget(parent=self.dockWidgetContents)
        self.widget.showGrid(x=True, y=True)
        self.legend = self.widget.addLegend()
        self.widget.enableAutoRange('y', 0.95)
        self.widget.setXRange(- self.chunkSize / 10, 0)
        self.gridLayout.addWidget(self.widget, 1, 0, 1, 8)
        self.dock_widget.setWidget(self.dockWidgetContents)
        self.dock_widget.setFloating(False)
        self.dock_widget.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable |
                                     QDockWidget.DockWidgetFeature.DockWidgetMovable)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dock_widget)

    def update_params_list(self, new_params_list: list):
        self.params_list = new_params_list
        self.data_y = numpy.zeros((self.chunkSize + 1, len(self.params_list)))
        for i, param in enumerate(self.params_list):
            self.data_y[-1, i] = param.value

    @pyqtSlot()
    def update_plots(self):
        if not self.params_list:
            return False
        now = perf_counter()
        # пробегаемся по списку со всеми кривыми
        # и задаём им позицию х - чтоб весь график сдвинулся влево
        for curs in self.curves:
            for c in curs:
                c.setPos(-(now - self.startTime), 0)

        i = self.counter % self.chunkSize
        # я так и не понимаю зачем создаётся новый массив в 100 элементов
        # как понял, потому что 400 элементов это тяжело
        # и сохраняются в памяти только последние 100
        if i == 0:
            # когда количество кривых кратно количеству 100
            # добавляется новая пачка кривых в список
            curve = []
            self.legend.clear()
            for parametr in self.params_list:
                curve.append(self.widget.plot(name=parametr.name))
            self.curves.append(curve)
            # из старого массива достаём последний элемент
            last_x = self.data_x[-1]
            last_y = self.data_y[-1]
            # создаём новый массив причём для всех графиков
            self.data_x = numpy.zeros((self.chunkSize + 1))
            self.data_y = numpy.zeros((self.chunkSize + 1, len(self.params_list)))
            # и впихиваем в него на первую позицию последний элемент старого массива
            self.data_x[0] = last_x
            self.data_y[0] = last_y

            # если количество кусков больше 10, удаляем до 10
            while len(self.curves) > self.maxChunks:
                c = self.curves.pop(0)
                for cc in c:
                    self.widget.removeItem(cc)
        else:
            # если сейчас не 100я кривая, то берём последний
            curve = self.curves[-1]

        self.data_x[i + 1] = now - self.startTime

        for indx, par in enumerate(self.params_list):
            self.data_y[i + 1, indx] = par.value
            crv = curve[indx]
            crv.setData(x=self.data_x[:i + 2], y=self.data_y[:i + 2, indx],
                        pen=self.pens[indx])
        self.counter += 1
        return True


class DialogChange(QDialog, my_dialog.Ui_value_changer_dialog):

    def __init__(self, label=None, value=None, table=None, compare=False, radio_btn=None,
                 text=None, process=None, check_boxes=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        self.text_browser.setStyleSheet("font: bold 14px;")
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText('ОК')
        self.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText('Отмена')
        # никаких защит и проверок

        if label is not None:
            self.value_name_lbl.setText(label)
        else:
            self.value_name_lbl.hide()

        if value is not None:
            self.lineEdit.setText(value)
        else:
            self.lineEdit.hide()

        if table is not None:
            show_empty_params_list(table, show_table=self.param_table, has_compare=compare)
        else:
            self.param_table.hide()

        if radio_btn is not None:
            self.r_btn1.setText(radio_btn[0])
            self.r_btn2.setText(radio_btn[1])
        else:
            self.r_btn1.hide()
            self.r_btn2.hide()
        # надо бы его на список переделать?
        if text is not None:
            self.text_browser.setText(text)
        else:
            self.text_browser.hide()

        if process is not None:
            self.process_bar.setValue(process)
        else:
            self.process_bar.hide()

        if check_boxes is not None:
            i, self.check_box_list = 0, []
            for check in check_boxes:
                c_box = QCheckBox(self)
                c_box.setObjectName('c_box' + str(i))
                self.check_box_list.append(c_box)
                c_box.setText(str(check))
                c_box.stateChanged.connect(self.c_boxes)
                self.gridLayout.addWidget(c_box, i + 1, 0)
                i += 1
            self.gridLayout.addWidget(self.buttonBox, i + 1, 0, 1, 1)
            self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)

        self.adjustSize()

    def set_widgets(self, widgets_list: list):
        i = 0
        for widget in widgets_list:
            if isinstance(widget, QWidget):
                self.gridLayout.addWidget(widget, i + 1, 0)
            i += 1

    def c_boxes(self, state):
        for check in self.check_box_list:
            if not check.isChecked():
                self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
                return
        self.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)

    @pyqtSlot(list, list, int)
    def change_mess(self, text=None, list_of_params=None, progress=None):
        if text and isinstance(text, list):
            self.text_browser.append('\n'.join(text))
        if list_of_params and isinstance(list_of_params, list):
            show_new_vmu_params(list_of_params, self.param_table)
        if progress and isinstance(progress, int):
            self.process_bar.setValue(progress)


# Если при ошибке в слотах приложение просто падает без стека,
# есть хороший способ ловить такие ошибки:
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print(text)
    QMessageBox.critical(None, 'Error', text)
    quit()


def get_nearest_lower_value(iterable, value):
    if value in iterable:
        return value
    iterable.append(value)
    iterable.sort()
    ind = iterable.index(value)
    return iterable[ind - 1] if ind else ind


def int_to_hex_str(x: int):
    return hex(x)[2:].zfill(2).upper()


def float_to_int(f):
    return int(struct.unpack('<I', struct.pack('<f', f))[0])


def bytes_to_float(b: list):
    return struct.unpack('<f', bytearray(b))[0]


def dw2float(dw_array):
    assert (len(dw_array) == 4)
    dw = int.from_bytes(dw_array, byteorder='little', signed=False)
    s = -1 if (dw >> 31) == 1 \
        else 1  # Знак
    e = (dw >> 23) & 0xFF  # Порядок
    m = ((dw & 0x7FFFFF) | 0x800000) if e != 0 \
        else ((dw & 0x7FFFFF) << 1)  # Мантисса
    m1 = m * (2 ** (-23))  # Мантисса в float
    return s * m1 * (2 ** (e - 127))

#
# пока просто не нужный код, может, потом пригодится
#
# root = self.nodes_tree.invisibleRootItem()
# child_count = root.childCount()
# the_best = root.child(child_count - 1)
# the_best_count = the_best.childCount()
#
# for i in range(the_best_count):
#     item = the_best.child(i)
#     group_param_name = item.text(0)
#     print(group_param_name)


# def define_max_current(self, value: int):
#     result = False
#     self.move_to(value)
#     current_time = start_time = time.perf_counter()
#
#     # а дальше смотрим за текущими параметрами пока не вышло время
#     while time.perf_counter() < start_time + self.time_for_moving:
#         print(f'\rТекущее положение {self.current_position} '
#               f'ток сейчас {self.actual_current()} '
#               f'заданное положение {value} '
#               f'максимальный ток {self.max_current}', end='', flush=True)
#
#         # регулярно опрашиваем текущее положение
#         if time.perf_counter() > current_time + self.time_for_request:
#             current_time = time.perf_counter()
#             self.actual_position()
#
#         #  выходим с победой если попали в нужный диапазон
#         if value + self.parameters_get['position'].min_value < \
#                 self.current_position < value + self.parameters_get['position'].max_value:
#             result = True
#             break
#     self.set_straight()
#     # отключаем мотор и все параметры возвращаем к номинальным
#     self.stop()
#     print()
#     return result

# def current_loop(self, value: int, start_current=None, delta_current=None):
#     self.max_current = self.get_param(self.parameters_set['current'])
#     self.set_straight()
#     if delta_current is not None:
#         self.delta_current = delta_current
#     self.time_for_moving = 3
#     if start_current is None:
#         start_current = self.parameters_get['current'].min_value
#     cur = self.set_current(start_current)
#     if cur:
#         at = 0
#         while not self.define_max_current(value):
#             start_current += self.delta_current
#             cur = self.set_current(start_current)
#             if not cur or at > self.max_iteration:
#                 return 'Слишком долго'
#             at += 1
#         return start_current
#     else:
#         return f'Невозможно задать ток {start_current}'
# param_list_for_steer_current = ['FROM_STEERING_FRONT_POSITION', 'FROM_STEERING_FRONT_CURRENT',
#                                 'FROM_STEERING_REAR_POSITION', 'FROM_STEERING_REAR_CURRENT']
# n_name = 'КВУ_ТТС'
# for p_name in param_list_for_steer_current:
#     wait_thread.imp_par_set.add(
#         find_param(p_name, node=n_name,
#                    nodes_dict=window.thread.current_nodes_dict)[0])
# adapter_vmu = adapter_for_node(window.thread.adapter, 250)
# if adapter_vmu:


# else:
#     QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.StandardButton.Ok)

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

# if abs(new_delta) > abs(old_delta) + (self.parameters_get['position'].max_value * 3):
#     result = 'Рейка движется не в том направлении'
#     QMessageBox.critical(None, "Ошибка ", result,
#                          QMessageBox.StandardButton.Ok)
#     break

#  выходим с победой если попали в нужный диапазон

# print(f'\rТекущее положение {self.current_position} '
#       f'ток сейчас {self.actual_current()} '
#       f'заданное положение {value} '
#       f'максимальный ток {self.max_current}', end='', flush=True)
# регулярно опрашиваем текущее положение


# new_delta = value - self.current_position
# if abs(old_delta) - self.parameters_get['position'].max_value < \
#         abs(new_delta) \
#         <= abs(old_delta) + self.parameters_get['position'].max_value:


#
# def make_compare_params_list():
#     file_name = QFileDialog.getOpenFileName(window, 'Файл с нужными параметрами', str(settings_dir),
#                                             "Файл с настройками блока (*.yaml *.xlsx)")[0]
#     if file_name:
#         if '.xls' in file_name:
#             compare_nodes_dict = fill_sheet_dict(file_name)
#         elif '.yaml' in file_name:
#             compare_nodes_dict = fill_yaml_dict(file_name)
#         else:
#             window.log_lbl.setText('Выбран неправильный файл')
#             return False
#         comp_node_name = ''
#         if compare_nodes_dict:
#             for cur_node in window.thread.current_nodes_dict.values():
#                 # как минимум, два варианта что этот блок присутствует
#                 #  - если имя страницы, он же ключ у словаря из файла совпадает с имеющимся сейчас блоком
#                 #  - если список параметров, хотя бы частично, совпадает со списком параметров имеющегося блока
#                 if cur_node.name in compare_nodes_dict.keys():
#                     fill_compare_values(cur_node, compare_nodes_dict[cur_node.name])
#                     comp_node_name += cur_node.name + ', '
#                 else:
#                     for comp_params_dict in compare_nodes_dict.values():
#                         if set(cur_node.group_params_dict.keys()) & set(comp_params_dict.keys()):
#                             fill_compare_values(cur_node, comp_params_dict)
#                             comp_node_name += cur_node.name + ', '
#                             break
#         show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table,
#                                has_compare=window.thread.current_node.has_compare_params)
#         if comp_node_name:
#             window.log_lbl.setText(f'Загружены параметры сравнения для блока {comp_node_name}')
#         else:
#             window.log_lbl.setText(f'Не найден блок для загруженных параметров')
#     else:
#         window.log_lbl.setText('Файл не выбран')
#         return False

#
# def change_min(param):
#     print(f'Задаю минимум для параметра {param.name}')
#     dialog = DialogChange(label=f'Измени минимальное значение для {param.name}', value=str(param.min_value))
#     reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
#     dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
#     if dialog.exec() == QDialog.DialogCode.Accepted:
#         val = dialog.lineEdit.text()
#         if val:
#             val = float(val)
#             if val < type_values[param.type]['min'] or \
#                     val > param.max_value or \
#                     val > param.value:
#                 val = param.min_value
#             param.min_value = val
#
#
# def change_max(param):
#     print(f'Задаю максимум для параметра {param.name}')
#     dialog = DialogChange(label=f'Измени максимальное значение для {param.name}', value=str(param.max_value))
#     reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
#     dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
#     if dialog.exec() == QDialog.DialogCode.Accepted:
#         val = dialog.lineEdit.text()
#         if val:
#             val = float(val)
#             if val > type_values[param.type]['max'] or \
#                     val < param.min_value or \
#                     val < param.value:
#                 val = param.max_value
#             param.max_value = val
#


# def save_p_dict_to_pickle_file(node: EVONode):
#     data_dir = pathlib.Path(os.getcwd(), 'Data')
#     s_num = node.serial_number if node.serial_number else DEFAULT_DIR
#     file_name = pathlib.Path(data_dir, node.name, s_num, PARAMETERS_PICKLE_FILE)
#     try:
#         with open(file_name, 'wb') as f:
#             pickle.dump(node.group_params_dict, f)
#         if os.path.isfile(NODES_PICKLE_FILE):
#             os.remove(NODES_PICKLE_FILE)
#         return True
#     except PermissionError:
#         return False
#
#


# if is_editable:
#     dialog = DialogChange(label=current_param.name, value=c_text.strip())
#     reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
#     dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
#     if dialog.exec() == QDialog.DialogCode.Accepted:
#         val = dialog.lineEdit.text()
#         info_m, lab = set_new_value(current_param, val)
#         print(lab, lab.styleSheet())
# else:
#     info_m = f'Сейчас этот параметр нельзя изменить\n' \
#              f'Изменяемые параметры подкрашены зелёным\n' \
#              f'Также требуется подключение к ВАТС'
# info_and_widget(info_m, lab)
#
# all_compare_params = {}
#     for group in dict_for_compare.values():
#         for par in group.copy():
#             all_compare_params[par.index << 8 + par.sub_index] = par

# all_current_params = []
#     for group in node.group_params_dict.values():
#         for p in group:
#             all_current_params.append(p)
