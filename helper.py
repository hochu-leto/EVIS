"""
всякие вспомогательные функции
"""
import struct
import traceback

# import traceback

from PyQt6.QtCore import QTimer, Qt, pyqtSlot, pyqtSignal, QStringListModel
from PyQt6.QtGui import QFont, QColor
from PyQt6.QtWidgets import QMessageBox, QDialog, QTableWidget, QTableWidgetItem, QHeaderView, QDialogButtonBox, \
    QComboBox, QListView, QSizePolicy, QStyleFactory

import Dialog_params
import my_dialog

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
# gray_list = (54, 60, 70)
# color_EVO_white = QColor(gray_list, 80)
color_EVO_gray = QColor(98, 104, 116, 80)
color_EVO_graphite2 = QColor(54, 60, 70, 80)
color_EVO_raven = QColor(188, 125, 136, 80)


class MyComboBox(QComboBox):
    ItemSelected = pyqtSignal(list)
    isRevealed = False
    parametr = None

    def __init__(self, parent=None, parametr=None):
        super(MyComboBox, self).__init__(parent)
        self.parametr = parametr
        self.currentIndexChanged.connect(self.item_selected_handle)

    def item_selected_handle(self, index):
        lst = []
        if self.parametr is not None:
            key = list(self.parametr.value_table.keys())[index]
            lst = [self.parametr, key]
        self.ItemSelected.emit(lst)

    def showPopup(self):  # sPopup function
        self.isRevealed = True
        super(MyComboBox, self).showPopup()  # 's showPopup ()

    def hidePopup(self):
        self.isRevealed = False
        super(MyComboBox, self).hidePopup()


def buf_to_string(buf):
    if isinstance(buf, str):
        return buf
    s = ''
    for i in buf:
        s += hex(i) + ' '
    return s


def find_param(nodes_dict: dict, s: str, node_name=None):
    list_of_params = []
    s = s.upper().strip()
    if node_name is None:
        list_of_params = [param for nd in nodes_dict.values() if nd.name != TheBestNode
                          for param_list in nd.group_params_dict.values()
                          for param in param_list
                          if s in param.name.upper() or s in param.description.upper()]
    elif node_name in nodes_dict.keys():
        nd = nodes_dict[node_name]
        list_of_params = [param for param_list in nd.group_params_dict.values()
                          for param in param_list
                          if s in param.name.upper() or s in param.description.upper()]
    return list_of_params


def show_empty_params_list(list_of_params: list, show_table: QTableWidget, has_compare=False):
    items_list = []
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

        color_ = color_EVO_green if par.editable else color_EVO_white
        name_item = QTableWidgetItem(name)
        name_item.setFlags(name_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
        name_item.setBackground(color_)
        show_table.setItem(row, 0, name_item)

        desc_item = QTableWidgetItem(description)
        desc_item.setFlags(desc_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
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
    show_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
    # максимальная ширина у описания, если не хватает длины, то переносится
    show_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
    return items_list


def pass_def():
    print('изменили комбо-бокс')
    pass


def show_new_vmu_params(params_list, table, has_compare_params=False):
    items_list = []
    row = 0
    for par in params_list:
        it = table.cellWidget(row, 2)
        if isinstance(it, MyComboBox) \
                and it.isRevealed:
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
        self.text_browser.setEnabled(False)
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
