"""
всякие вспомогательные функции
"""
import struct
import traceback
from PyQt6.QtCore import Qt, pyqtSlot, QStringListModel
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox, \
    QComboBox, QListView, QSizePolicy

import my_dialog
from EVOWidgets import GreenLabel, MyComboBox

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
color_EVO_red = QColor(222, 73, 14)
color_EVO_green = QColor(0, 254, 0, 80)
color_EVO_red_dark = QColor(234, 76, 76, 80)
color_EVO_orange = QColor(241, 91, 34)
color_EVO_orange_shine = QColor(255, 184, 65, 80)
color_EVO_white = QColor(255, 254, 254, 80)
color_EVO_gray = QColor(98, 104, 116, 80)
color_EVO_graphite2 = QColor(54, 60, 70, 80)
color_EVO_raven = QColor(188, 125, 136, 80)


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


def show_empty_params_list(list_of_params: list, show_table: QTableWidget, has_compare=False):
    items_list = []
    show_table.setRowCount(0)
    show_table.setRowCount(len(list_of_params))
    row = 0
    headers_list = ['Параметр', 'Описание', 'Значение', 'Сравнение', 'Размерность']
    show_table.setColumnCount(len(headers_list))
    show_table.setHorizontalHeaderLabels(headers_list)

    # пока отображаю только три атрибута + само значение отображается позже
    for par in list_of_params:
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
            show_table.setCellWidget(row, 0, lb)
        else:
            name_item = QTableWidgetItem(name)
            name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            show_table.setItem(row, 0, name_item)

        desc_item = QTableWidgetItem(description)
        # desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        desc_item.setFlags(desc_item.flags() | Qt.ItemFlag.ItemIsEditable)
        show_table.setItem(row, 1, desc_item)

        value_item = QTableWidgetItem('')
        value_item.setFlags(value_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        show_table.setItem(row, 2, value_item)

        compare_item = QTableWidgetItem(compare)
        compare_item.setFlags(compare_item.flags() & ~Qt.ItemFlag.ItemIsEditable)

        show_table.setItem(row, 3, compare_item)

        unit_item = QTableWidgetItem(unit)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        show_table.setItem(row, show_table.columnCount() - 1, unit_item)

        row += 1

    show_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    show_table.setColumnHidden(show_table.columnCount() - 2, not has_compare)
    # # максимальная ширина у описания, если не хватает длины, то переносится
    show_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
    show_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    show_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
    return items_list


def show_new_vmu_params(params_list, table, has_compare_params=False):
    items_list = []
    row = 0
    for par in params_list:
        it = table.cellWidget(row, 2)
        if isinstance(it, MyComboBox) \
                and it.isInFocus:
            continue

        value_in_dict = False

        if par.value_string:
            v_name = par.value_string
        elif isinstance(par.value, str):
            v_name = par.value
        elif par.value_table:
            k = int(par.value)
            if k in par.value_table:
                value_in_dict = True
                v_name = par.value_table[k]
            else:
                v_name = f'{k} нет в словаре'
        else:
            v_name = zero_del(par.value)

        if value_in_dict and par.editable:
            if not isinstance(it, MyComboBox):
                comBox = MyComboBox()
                v_list = list(par.value_table.values())
                comBox.setModel(QStringListModel(v_list))
                # Отображатель выпадающего списка QListView
                listView = QListView()
                # Включаем перенос строк
                listView.setWordWrap(True)
                # Устанавливаем отображатель списка (popup)
                comBox.setView(listView)
                # comBox.addItems(v_list)
                comBox.parametr = par
                comBox.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToContentsOnFirstShow)
                # .AdjustToMinimumContentsLengthWithIcon + AdjustToContentsOnFirstShow + AdjustToContents)
                comBox.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)
                comBox.setMaximumSize(220, 170)
                table.setCellWidget(row, 2, comBox)
                items_list.append(comBox)
            table.cellWidget(row, 2).setCurrentText(par.value_table[int(par.value)])
        else:
            value_item = QTableWidgetItem(v_name)
            if par.editable:
                flags = (value_item.flags() | Qt.ItemFlag.ItemIsEditable)
            else:
                flags = value_item.flags() & ~Qt.ItemFlag.ItemIsEditable
            value_item.setFlags(flags)
            # подкрашиваем в голубой в зависимости от периода опроса
            color_opacity = int((150 / 1000) * abs(par.period)) + 3
            value_item.setBackground(QColor(0, 255, 255, color_opacity))
            table.setItem(row, 2, value_item)

        if has_compare_params:
            compare_name = table.item(row, 3).text()
            color_ = color_EVO_red_dark if v_name.strip() != compare_name.strip() else color_EVO_white
            table.item(row, 3).setBackground(color_)
        row += 1
    return items_list


class DialogChange(QDialog, my_dialog.Ui_value_changer_dialog):

    def __init__(self, label=None, value=None, table=None, radio_btn=None, text=None, process=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        # self.text_browser.setEnabled(False)
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
            show_empty_params_list(table, show_table=self.param_table)
        else:
            self.param_table.hide()

        if radio_btn is not None:
            self.r_btn1.setText(radio_btn[0])
            self.r_btn2.setText(radio_btn[1])
        else:
            self.r_btn1.hide()
            self.r_btn2.hide()

        if text is not None:
            self.text_browser.setText(text)
        else:
            self.text_browser.hide()

        if process is not None:
            self.process_bar.setValue(process)
        else:
            self.process_bar.hide()

        self.adjustSize()

    @pyqtSlot(list, list, int)
    def change_mess(self, st=None, list_of_params=None, progress=None):
        if st and isinstance(st, list):
            self.text_browser.append('\n'.join(st))
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


def zero_del(s):
    return f'{round(s, 5):>8}'.rstrip('0').rstrip('.') if s is not None else 'NaN'


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
