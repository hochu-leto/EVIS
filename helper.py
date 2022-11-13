"""
всякие вспомогательные функции
"""
import struct
import traceback

from PyQt5.QtCore import QTimer, Qt, QRegExp, pyqtSlot
from PyQt5.QtGui import QFont, QRegExpValidator
from PyQt5.QtWidgets import QMessageBox, QDialog, QTableWidget

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


class InfoMessage(QDialog, Dialog_params.Ui_Dialog_params):

    def __init__(self, info: str):
        super().__init__()
        self.setupUi(self)
        self.info_lbl.setText(info)
        self.info_lbl.setFont(QFont('MS Shell Dlg 2', 10))
        self.setWindowFlag(Qt.FramelessWindowHint)
        QTimer.singleShot(1700, self.close)


class DialogChange(QDialog, my_dialog.Ui_value_changer_dialog):

    def __init__(self, value_name: str, value):
        super().__init__()
        self.setupUi(self)
        self.value_name_lbl.setText(value_name)
        self.lineEdit.setText(value)
        # self.setIcon(QMessageBox.Information)
        # self.setWindowIcon(QMessageBox.Information)
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)

    @pyqtSlot(str)
    def change_mess(self, st: str):
        self.lineEdit.setText(st)


def set_table_width(table: QTableWidget, col_w_stretch=None):
    col = table.columnCount()
    table_w = table.width()
    if col_w_stretch is None:
        col_w_stretch = [1 for _ in range(col)]
    if len(col_w_stretch) < col:
        col_w_stretch += [1 for _ in range(col - len(col_w_stretch))]
    byt = table_w / sum(col_w_stretch)
    for i in range(col):
        wid = byt * col_w_stretch[i]
        table.setColumnWidth(i, wid)


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
