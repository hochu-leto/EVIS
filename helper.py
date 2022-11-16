"""
всякие вспомогательные функции
"""
import struct
import traceback

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimer, Qt, QRegExp, pyqtSlot
from PyQt5.QtGui import QFont, QRegExpValidator, QColor
from PyQt5.QtWidgets import QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView

import Dialog_params
import my_dialog

NewParamsList = 'Новый список'

empty_par = {'name': '',
             'address': '',
             'editable': '',
             'description': '',
             'scale': '',
             'scaleB': '',
             'unit': '',
             'value': '',
             'type': '',
             'group': '',
             'period': '',
             'size': '',
             'degree': '',
             'min_value': '',
             'max_value': '',
             'widget': ''}
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
               'degree': 3}


def show_empty_params_list(list_of_params: list, show_table: QTableWidget, has_compare=False):
    # show_table = getattr(w, table)
    show_table.setRowCount(0)
    show_table.setRowCount(len(list_of_params))
    row = 0
    if has_compare:
        show_table.setColumnCount(5)
        show_table.setHorizontalHeaderLabels(['Параметр', 'Описание', 'Значение', 'Сравнение', 'Размерность'])
    else:
        show_table.setColumnCount(4)
        show_table.setHorizontalHeaderLabels(['Параметр', 'Описание', 'Значение', 'Размерность'])

    # пока отображаю только три атрибута + само значение отображается позже
    for par in list_of_params:
        name = par.name
        unit = par.unit
        description = par.description
        compare = par.compare_value if isinstance(par.compare_value, str) else zero_del(par.compare_value)

        if par.editable:
            color_opacity = 30
        else:
            color_opacity = 0
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemIsEditable)
        name_item.setBackground(QColor(0, 192, 0, color_opacity))
        show_table.setItem(row, 0, name_item)

        desc_item = QTableWidgetItem(description)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemIsEditable)
        # desc_item.setBackground(QColor(0, 192, 0, color_opacity))
        show_table.setItem(row, 1, desc_item)

        value_item = QTableWidgetItem('')
        value_item.setFlags(value_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, 2, value_item)

        compare_item = QTableWidgetItem(compare)
        compare_item.setFlags(compare_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, 3, compare_item)

        unit_item = QTableWidgetItem(unit)
        unit_item.setFlags(unit_item.flags() & ~Qt.ItemIsEditable)
        show_table.setItem(row, show_table.columnCount() - 1, unit_item)

        row += 1
    show_table.verticalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    show_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    # максимальная ширина у описания, если не хватает длины, то переносится
    show_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)


def show_new_vmu_params(params_list, table, has_compare_params=False):
    row = 0
    for par in params_list:
        v_name = par.value if isinstance(par.value, str) else zero_del(par.value)
        value_item = QTableWidgetItem(v_name)
        if par.editable:
            flags = (value_item.flags() | Qt.ItemIsEditable)
        else:
            flags = value_item.flags() & ~Qt.ItemIsEditable
        value_item.setFlags(flags)
        # подкрашиваем в голубой в зависимости от периода опроса
        color_opacity = int((150 / 1000) * par.period) + 3
        value_item.setBackground(QColor(0, 255, 255, color_opacity))
        table.setItem(row, 2, value_item)
        if has_compare_params:
            compare_name = table.item(row, 3).text()
            if v_name.strip() != compare_name.strip():
                color = QColor(255, 0, 0, 50)
            else:
                color = QColor(255, 255, 255, 0)
            table.item(row, 3).setBackground(color)
        row += 1


class InfoMessage(QDialog, Dialog_params.Ui_Dialog_params):

    def __init__(self, info: str):
        super().__init__()
        self.setupUi(self)
        self.info_lbl.setText(info)
        self.info_lbl.setFont(QFont('MS Shell Dlg 2', 10))
        self.setWindowFlag(Qt.FramelessWindowHint)
        QTimer.singleShot(1700, self.close)


class DialogChange(QDialog, my_dialog.Ui_value_changer_dialog):

    def __init__(self, label=None, value=None, table=None, radio_btn=None, text=None, process=None):
        super().__init__()
        self.setupUi(self)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
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

        if text is not None:
            self.text_browser.setText(value)
        else:
            self.text_browser.hide()

        if process is not None:
            self.process_bar.setValue(process)
        else:
            self.process_bar.hide()

        self.adjustSize()

    @pyqtSlot(str, list)
    def change_mess(self, st: str, list_of_params=None):
        if st:
            self.text_browser.append(st)
        if list_of_params is not None and isinstance(list_of_params, list):
            show_new_vmu_params(list_of_params, self.params_table)


# Если при ошибке в слотах приложение просто падает без стека,
# есть хороший способ ловить такие ошибки:
def log_uncaught_exceptions(ex_cls, ex, tb):
    text = '{}: {}:\n'.format(ex_cls.__name__, ex)
    text += ''.join(traceback.format_tb(tb))

    print(text)
    QMessageBox.critical(None, 'Error', text)
    quit()


def zero_del(s):
    return f'{round(s, 5):>8}'.rstrip('0').rstrip('.')


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
