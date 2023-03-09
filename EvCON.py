"""
Сейчас программа умеет
    - определить ОС
    - определить подключенный адаптер
    - определить какие кан-шины подключены
    - подключиться к ВАТС по двойному щелчку на блоке или группе параметров блока или по кнопке Подключиться
    - запросить серийник и версию ПО блока, если серийник есть, то блок считается подключенным,
        серийник может быть текстовым
    - запросить и удалить ошибки подключенных блоков
    - запросить параметр и изменить параметр
    - сохранение нужного значения параметров в ЕЕПРОМ
    - сохранять все параметры текущего блока в эксель файл - можно параллельно с основным потоком, но лучше отключаться
    - возможность выбрать параметры из разных блоков и сохранить их в отдельный список и
        хранить пользовательский список параметров в файле - Избранное - Новый список
    - сравнение всех параметров из файла с текущими из блоков
    - поиск по имени и описанию параметра
    - возможность записи лога текущих параметров из открытого списка и сохранять запись в эксель файл - лог
    - хранение профилей блока в отдельном файле с названием_блока_версия_ПО в папках с Название_блока
            в файле список параметров и ошибки. Это позволит оставить пользовательский список Избранное
    - добавить в параметр поле со словарём значений -
            если считано подходящее - подставлять значение из словаря (как сохранять??)
    - сделать ошибки объектами с описанием, ссылками и выводом нужных параметров


следующие шаги
- графики выбранных текущих параметров
- виджеты по управлению параметром
- всплывающее меню при правом щелчке по параметру - Добавить в Избранное и Изменить период
- автоматическое определение нужного периода опроса параметра и сохранение этого периода в свойства параметра в файл
- работа в линуксе
- работа с квайзером
- в новом параметре КВУ формировать ВИН номер машины+номера_блоков -
        сделать автоматический опрос номеров и сравнение с тем, что в памяти
- сделать процесс подключения видимым

НА ПОДУМАТЬ
- может ли приёмник джойстика отвечать по SDO например, положения кнопок?
- может ли БКУ отвечать по SDO хотя бы серийник?
- продумать реляционную БД для параметров
- на отдельном листе управление для этого блока с виджетами типами - слайдеры, кнопки, чекбоксы - по каким адресам,
  название и так далее.
выводить в соседнем окошке список определённых для этого блока виджетов (слайдеры, кнопки) + количество этих окошек с
виджетами для каждого блока задаёт пользователь, т.е. он может создать свои нужные виджеты и сохранить их в профиль к
этому блоки, а при загрузке это должно подгрузится - и стандартные и выбранные для того блока пользователем -
полагаю отдельный лист Экселя с выбранными параметрами - виджетами
- ещё кнопка - загрузка параметров из файла - здесь должна быть жёсткая защита - не все редактируемые параметры
 из одного блока можно напрямую заливать в другой. Или их ограничить до минимума или предлагать делать изменение вручную

"""
import datetime
import pickle
import sys
import time

import pandas as pd
import qrainbowstyle
from PyQt6.QtCore import pyqtSlot, Qt, QRegularExpression
from PyQt6.QtGui import QIcon, QPixmap, QBrush, QRegularExpressionValidator
from PyQt6.QtWidgets import QMessageBox, QApplication, QMainWindow, QTreeWidgetItem, QDialog, \
    QSplashScreen, QFileDialog, QDialogButtonBox, QStyleFactory, QLabel, QMenu, QTableWidgetItem, QTableWidget, \
    QLineEdit
import pathlib

from pyqtgraph import PlotWidget
from qt_material import apply_stylesheet, list_themes, QtStyleTools

import VMU_monitor_ui
from CANAdater import CANAdapter
from EVOErrors import EvoError
from EVONode import EVONode
from EVOWidgets import GreenLabel, RedLabel, zero_del, color_EVO_red_dark, color_EVO_white, color_EVO_orange_shine
from EVOThreads import SaveToFileThread, MainThread, WaitCanAnswerThread
from EVOParametr import Parametr, type_values
from command_buttons import suspension_to_zero, mpei_invert, mpei_calibrate, mpei_power_on, mpei_power_off, \
    mpei_reset_device, mpei_reset_params, joystick_bind, load_from_eeprom, save_to_eeprom, let_moment_mpei, rb_toggled, \
    check_steering_current, multyvibrator
from work_with_file import fill_sheet_dict, fill_compare_values, fill_nodes_dict_from_yaml, make_nodes_dict, WORK_DIR, \
    NODES_PICKLE_FILE, NODES_YAML_FILE, save_p_dict_to_yaml_file, \
    fill_yaml_dict, SETTINGS_DIR, save_diff, add_parametr_to_yaml_file
from helper import NewParamsList, log_uncaught_exceptions, DialogChange, show_empty_params_list, \
    show_new_vmu_params, find_param, TheBestNode, easter_egg

can_adapter = CANAdapter()
sys.excepthook = log_uncaught_exceptions
wait_thread = WaitCanAnswerThread()
extra = {  # Density Scale
    'density_scale': '-2', }

@pyqtSlot(object)
def set_focus(param):
    row = window.thread.current_params_list.index(param)
    widget = window.vmu_param_table.cellWidget(row, 2)
    if widget:
        widget.isInFocus = True


@pyqtSlot(object)
def show_value(param):
    row = window.thread.current_params_list.index(param)
    widget = window.vmu_param_table.cellWidget(row, 2)
    if widget:
        widget.set_text()
    else:
        window.vmu_param_table.item(row, 2).setText(zero_del(param.value))


def wrapper_show_empty(params_list: list, param_table: QTableWidget, has_compare=False):
    slider_list = show_empty_params_list(params_list, show_table=param_table,
                                         has_compare=has_compare)
    for slider in slider_list:
        slider.ValueChanged.connect(show_value)
        slider.SliderHold.connect(set_focus)
        slider.ValueSelected.connect(change_value)


def search_param():
    def line_edit_change(s):
        len_s = len(s)
        if len_s >= 4:
            dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(True)
            dialog.lineEdit.setStyleSheet("color: black;")
        else:
            dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
            dialog.lineEdit.setStyleSheet("color: red;")

    dialog = DialogChange(label='Не менее 4 букв из имени или описания параметра, которого нужно найти', value='')
    dialog.lineEdit.setText('')
    dialog.setWindowTitle('Поиск параметра')
    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setEnabled(False)
    dialog.lineEdit.textChanged.connect(line_edit_change)
    if dialog.exec() == QDialog.DialogCode.Accepted:
        search_text = dialog.lineEdit.text()
        was_run = False
        if window.thread.isRunning():
            was_run = True
            window.connect_to_node()
        par_list = find_param(search_text, nodes_dict=window.thread.current_nodes_dict).copy()
        if par_list:
            p_list = []
            for par in par_list:
                if '#' not in par.name:
                    new_par = par.copy()
                    new_par.name += '#' + new_par.node.name
                    p_list.append(new_par)
            window.thread.current_nodes_dict[TheBestNode].group_params_dict[search_text] = p_list.copy()
            rowcount = window.nodes_tree.topLevelItemCount() - 1
            best_node_item = window.nodes_tree.topLevelItem(rowcount)
            item = QTreeWidgetItem()
            item.setText(0, search_text)
            best_node_item.addChild(item)
            window.nodes_tree.setCurrentItem(item)
        else:
            QMessageBox.critical(window, "Проблема", f'Ни одного параметра с "{search_text}"\n'
                                                     f' в текущих блоках найти не удалось ',
                                 QMessageBox.StandardButton.Ok)
        # search_bar.close()
        if was_run and window.thread.isFinished():
            window.connect_to_node()


def record_log():
    state = window.thread.is_recording
    window.nodes_tree.setEnabled(state)
    window.vmu_param_table.setEnabled(state)
    window.compare_btn.setEnabled(state)
    window.save_eeprom_btn.setEnabled(state)
    window.save_to_file_btn.setEnabled(state)
    window.reset_faults.setEnabled(state)
    window.management_tab.setEnabled(state)
    window.connect_btn.setEnabled(state)
    if not state:  # начинаю запись
        window.thread.is_recording = True
        window.log_record_btn.setText('Остановить запись')
    else:
        window.thread.is_recording = False
        window.log_record_btn.setText('Запись текущих параметров')
        if window.thread.record_dict:
            file_name = window.nodes_tree.currentItem().text(0).replace('.', '_')
            now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_name = pathlib.Path(WORK_DIR, 'ECU_Records', f'{file_name}_{now}.xlsx')
            df = pd.DataFrame(window.thread.record_dict)
            df_t = df.transpose()
            window.thread.record_dict.clear()
            ex_wr = pd.ExcelWriter(file_name, mode="w")
            with ex_wr as writer:
                df_t.to_excel(writer)
            QMessageBox.information(window, "Успешный успех!", f'Лог сохранён в файл {file_name}',
                                    QMessageBox.StandardButton.Ok)


def make_compare():
    file_name = QFileDialog.getOpenFileName(window, 'Файл с нужными параметрами', str(SETTINGS_DIR),
                                            "Файл с настройками блока (*.yaml *.xlsx)")[0]
    if file_name:
        if '.xls' in file_name:
            compare_nodes_dict = fill_sheet_dict(file_name)
        elif '.yaml' in file_name:
            compare_nodes_dict = fill_yaml_dict(file_name)
        else:
            QMessageBox.information(window, 'Ошибка', 'Выбран неправильный файл'
                                                      'настройки могут быть в *.yaml или в *.xlsx файлах',
                                    QMessageBox.StandardButton.Ok)
            window.log_lbl.setText('Выбран неправильный файл')
            return False
        if compare_nodes_dict:
            node = None
            # как минимум, два варианта, что этот блок присутствует
            #  - если имя блока, он же ключ у словаря из файла совпадает с имеющимся сейчас блоком
            for node_name in compare_nodes_dict.keys():
                if node_name in window.thread.current_nodes_dict.keys():
                    node = window.thread.current_nodes_dict[node_name]
                    fill_compare_values(node, compare_nodes_dict[node_name])
                    break
            #  - если список параметров, хотя бы частично, совпадает со списком параметров имеющегося блока
            if node is None:
                for node_ in window.thread.current_nodes_dict.values():
                    for comp_params_dict in compare_nodes_dict.values():
                        # если есть пересечение списков
                        if set(node_.group_params_dict.keys()) & set(comp_params_dict.keys()):
                            node = node_
                            fill_compare_values(node, comp_params_dict)
                            break
            if node is not None:
                if window.thread.isRunning():
                    window.connect_to_node()
                window.tr.adapter = can_adapter
                window.tr.node_to_save = node
                window.tr.SignalOfReady.disconnect()
                window.tr.SignalOfReady.connect(window.progress_bar_silent)
                # запускаем параллельный поток сохранения
                window.tr.start()
            else:
                QMessageBox.information(window, 'Нет совпадений', 'В выбранном файле нет совпадений параметров'
                                                                  ' ни с одним из подключенных блоков',
                                        QMessageBox.StandardButton.Ok)
                window.log_lbl.setText('Нет совпадений с текущими блоками')
                return False
        wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table,
                           has_compare=window.thread.current_node.has_compare_params)
    else:
        window.log_lbl.setText('Файл не выбран')
        return False


@pyqtSlot(list)
def change_value(lst):
    # принимает список из двух элементов, первый - Parametr(), второй - новое значение для него
    # пора бы переделать под object, new_value

    info_m, lab = 'От виджета пришёл пустой список', None
    if lst:
        parametr = lst[0]
        new_value = lst[1]
        if not window.vmu_param_table.currentItem():
            row = window.thread.current_params_list.index(parametr)
            window.vmu_param_table.setCurrentCell(row, 2)
        info_m, lab = set_new_value(parametr, new_value)
    info_and_widget(info_m, lab)


def set_new_value(param: Parametr, val):
    info_m = ''
    my_label = None
    if 'WheelTypeSet' in param.name:
        if QMessageBox.information(window, "Пасхалка", easter_egg,
                                   QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel) \
                != QMessageBox.StandardButton.Ok:
            return "Пердумал", my_label
    try:
        float(val)
        if window.thread.isRunning():
            # отключаем поток, если он был включен
            window.connect_to_node()
            # отправляю параметр, полученный из диалогового окна
            param.set_value(can_adapter, float(val))
            # и сразу же проверяю записался ли он в блок
            value_data = param.get_value(can_adapter)  # !!!если параметр строковый, будет None!!--
            if isinstance(value_data, str):
                new_val = ''
            else:
                new_val = zero_del(value_data).strip()
            # и сравниваю их - соседняя ячейка становится зеленоватой, если ОК и красноватой если не ОК
            my_label = QLabel()
            if zero_del(val).strip() == new_val:
                my_label = GreenLabel()
                if param.node.save_to_eeprom:
                    param.node.param_was_changed = True
                    # В Избранном кнопку не активируем, может быть несколько блоков.
                    # Возможно, я когда-то смогу
                    if window.thread.current_node.name != TheBestNode:
                        window.save_eeprom_btn.setEnabled(True)
                        if window.thread.current_node.name == 'Инвертор_МЭИ':
                            info_m = f'Параметр будет работать, \nтолько после сохранения в ЕЕПРОМ'
                        elif window.thread.current_node.name == 'КВУ_ТТС':
                            param.node.param_was_changed = param.eeprom
                            window.save_eeprom_btn.setEnabled(param.eeprom)
            else:
                my_label = RedLabel()
                # если поток был запущен до изменения, то запускаем его снова
            if window.thread.isFinished():
                # и запускаю поток
                window.connect_to_node()
        else:
            info_m = f'Подключение прервано, \nДля изменения параметра\nтребуется подключение к ВАТС'
    except ValueError:
        info_m = 'Параметр должен быть числом'
    row = window.thread.current_params_list.index(param)
    widget = window.vmu_param_table.cellWidget(row, 2)
    if widget:
        widget.isInFocus = False
    return info_m, my_label


def info_and_widget(info_m='', my_lab=None):
    if info_m:
        QMessageBox.information(window, "Информация", info_m, QMessageBox.StandardButton.Ok)
    if window.vmu_param_table.currentItem() and my_lab:
        try:
            c_row = window.vmu_param_table.currentItem().row()
            c_next_col = window.vmu_param_table.columnCount() - 1
            c_next_text = window.vmu_param_table.item(c_row, c_next_col).text()
            window.vmu_param_table.item(c_row, c_next_col).setText('')
            my_lab.setText(c_next_text)
            window.vmu_param_table.setCellWidget(c_row, c_next_col, my_lab)
        except AttributeError:
            print('Поставить метку  НЕ УДАЛОСЬ')


def want_to_value_change(c_row, c_col):
    cell = window.vmu_param_table.item(c_row, c_col)
    current_cell = cell if cell else window.vmu_param_table.cellWidget(c_row, c_col)
    c_text = current_cell.text()
    col_name = window.vmu_param_table.horizontalHeaderItem(c_col).text().strip().upper()
    current_param = window.thread.current_params_list[c_row]
    # меняем значение параметра
    if col_name == 'ЗНАЧЕНИЕ':
        c_flags = current_cell.flags()
        is_editable = True if Qt.ItemFlag.ItemIsEditable & c_flags else False
        info_m, lab = '', None
        if is_editable:
            dialog = DialogChange(label=current_param.name, value=c_text.strip())
            reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
            dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
            if dialog.exec() == QDialog.DialogCode.Accepted:
                val = dialog.lineEdit.text()
                info_m, lab = set_new_value(current_param, val)
                print(lab, lab.styleSheet())
        else:
            info_m = f'Сейчас этот параметр нельзя изменить\n' \
                     f'Изменяемые параметры подкрашены зелёным\n' \
                     f'Также требуется подключение к ВАТС'
        info_and_widget(info_m, lab)
        # сбрасываю фокус с текущей ячейки, чтоб выйти красиво, при запуске потока и
        # обновлении значения она снова станет редактируемой, пользователь не замечает изменений
        window.vmu_param_table.item(c_row, c_col).setFlags(c_flags & ~Qt.ItemFlag.ItemIsEditable)
    # добавляю параметр в Избранное/Новый список
    # пока редактирование старых списков не предусмотрено
    elif col_name == 'ПАРАМЕТР':
        add_param_to_the_best_node(current_param)
    return


def add_param_to_the_best_node(current_param):
    # достаю список Избранное
    user_node = window.thread.current_nodes_dict[TheBestNode]
    # из текущего параметра делаю новый с новым именем через #
    new_param = current_param.copy()
    if window.thread.current_node != user_node and '#' not in new_param.name:
        new_param.name = f'{new_param.name}#{new_param.node.name}'
    text = f'добавлен в блок {TheBestNode}'
    # если Новый список есть в Избранном
    rowcount = window.nodes_tree.topLevelItemCount() - 1
    best_node_item = window.nodes_tree.topLevelItem(rowcount)  # это очень плохо
    result = True
    if NewParamsList in user_node.group_params_dict.keys():
        if remove_param_from_the_best_node(new_param):
            text = f'удалён из блока {TheBestNode}'
            result = False
        # если нового параметра нет в Новом списке, добавляю его туда
        else:
            if not user_node.group_params_dict[NewParamsList]:
                item = best_node_item.child(best_node_item.childCount() - 1)
                best_node_item.setExpanded(True)
                item.setBackground(0, color_EVO_red_dark)
                index = window.nodes_tree.indexFromItem(item, 0)
                window.nodes_tree.scrollTo(index)
            user_node.group_params_dict[NewParamsList].append(new_param)
    # если Нового списка нет в Избранном, надо его создать и добавить в него новый параметр
    else:
        user_node.group_params_dict[NewParamsList] = [new_param]
        item = QTreeWidgetItem()
        item.setText(0, NewParamsList)
        best_node_item.addChild(item)
        # и немного красоты - раскрываем, спускаем и подкрашиваем
        best_node_item.setExpanded(True)
        item.setBackground(0, color_EVO_red_dark)
        index = window.nodes_tree.indexFromItem(item, 0)
        window.nodes_tree.scrollTo(index)
    window.log_lbl.setText(f'Параметр {current_param.name} {text}')
    if result:
        paint_cells(current_param, color_EVO_red_dark)
    else:
        paint_cells(current_param, color_EVO_white)
    return result


def change_limit(param):
    print(f'Задаю пределы для параметра {param.name}')
    value_changer_dialog = DialogChange()

    reg_ex = QRegularExpression("[+-]?([0-9]*[.])?[0-9]+")
    max_lbl = QLabel(value_changer_dialog)
    max_lbl.setText('Задай максимальное значение параметра')
    value_changer_dialog.max_line_edit = QLineEdit(value_changer_dialog)
    value_changer_dialog.max_line_edit.setText(str(param.max_value))
    value_changer_dialog.max_line_edit.setValidator(QRegularExpressionValidator(reg_ex))

    min_lbl = QLabel(value_changer_dialog)
    min_lbl.setText('Задай минимальное значение параметра')
    value_changer_dialog.min_line_edit = QLineEdit(value_changer_dialog)
    value_changer_dialog.min_line_edit.setText(str(param.min_value))
    value_changer_dialog.min_line_edit.setValidator(QRegularExpressionValidator(reg_ex))

    value_changer_dialog.set_widgets(widgets_list=[max_lbl, value_changer_dialog.max_line_edit,
                                                   min_lbl, value_changer_dialog.min_line_edit])

    if value_changer_dialog.exec() == QDialog.DialogCode.Accepted:
        min_val = value_changer_dialog.min_line_edit.text()
        if min_val:
            val = float(min_val)
            if val < type_values[param.type]['min'] or \
                    val > param.max_value or \
                    val > param.value:
                val = param.min_value
            param.min_value = val
        max_val = value_changer_dialog.max_line_edit.text()
        if max_val:
            val = float(max_val)
            if val > type_values[param.type]['max'] or \
                    val < param.min_value or \
                    val < param.value:
                val = param.max_value
            param.max_value = val
        add_parametr_to_yaml_file(parametr=param)
        wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table)


def change_period(param):
    print(f'Меняю период параметра {param.name}')
    dialog = DialogChange(label=f'Измени период опроса для параметра {param.name} (1-1000)', value=str(param.period))
    reg_ex = QRegularExpression("^([1-9][0-9]{0,2}|1000)$")
    dialog.lineEdit.setValidator(QRegularExpressionValidator(reg_ex))
    if dialog.exec() == QDialog.DialogCode.Accepted:
        val = dialog.lineEdit.text()
        if val:
            param.period = int(val)
        add_parametr_to_yaml_file(parametr=param)


def set_bar(param):
    if param.widget != 'MyColorBar':
        if float(param.min_value) == float(type_values[param.type]['min']) \
                and float(param.max_value) == float(type_values[param.type]['max']):
            change_limit(param)
        param.widget = 'MyColorBar'
        add_parametr_to_yaml_file(parametr=param)
        wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table)
    else:
        set_text_description(param)


def set_slider(param):
    if param.widget != 'MySlider':
        if float(param.min_value) == float(type_values[param.type]['min']) \
                and float(param.max_value) == float(type_values[param.type]['max']):
            change_limit(param)
        param.widget = 'MySlider'
        add_parametr_to_yaml_file(parametr=param)
        wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table)
    else:
        set_text_description(param)


def set_text_description(param):
    param.widget = 'Text'
    add_parametr_to_yaml_file(parametr=param)
    wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table)


def paint_cells(parametr, color):
    if window.thread.current_params_list == \
            window.thread.current_nodes_dict[TheBestNode].group_params_dict[NewParamsList]:
        return
    try:
        c_row = window.thread.current_params_list.index(parametr)
    except ValueError:
        print('Параметр отсутствует')
        return
    for i in range(1, window.vmu_param_table.columnCount()):
        c_item = window.vmu_param_table.item(c_row, i)
        try:
            c_item.setBackground(color)
            # здесь можно вставить виджет редлейбл чтоб в других темах было видно
        except AttributeError:
            print('Ячейка отсутствует', i)


def remove_param_from_the_best_node(parametr):
    result = False
    user_node = window.thread.current_nodes_dict[TheBestNode]
    par = check_param_in_the_best_node(parametr)
    if par:
        result = True
        was_run = False
        # останавливаю поток и удаляю параметр из Нового списка
        if window.thread.isRunning():
            window.connect_to_node()
            was_run = True
        user_node.group_params_dict[NewParamsList].remove(par)
        # если юзер сейчас в Новом списке, обновляю вид таблицы
        if window.thread.current_node == user_node:
            wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table)
        if window.thread.isFinished() and was_run:
            window.connect_to_node()
    return result


def check_param_in_the_best_node(parametr: Parametr):
    user_node = window.thread.current_nodes_dict[TheBestNode]
    if NewParamsList not in user_node.group_params_dict.keys():
        return False
    if window.thread.current_node != user_node and '#' not in parametr.name:
        p_name = f'{parametr.name}#{parametr.node.name}'
    else:
        p_name = parametr.name
    # Проверяю есть ли уже новый параметр в Новом списке
    for par in user_node.group_params_dict[NewParamsList]:
        if par.name in p_name:
            return par
    return False


def show_error(item, column):
    current_err_name = ''
    current_err = EvoError()
    # имя блока - до скобки - какой же это колхоз, пора переходить на MKV
    try:
        current_node_text = item.parent().text(0).split('(')[0]
        current_err_name = item.text(0)
    except AttributeError:
        current_node_text = item.text(0).split('(')[0]
    # нужно определить на какую ошибку щёлкнул юзер
    # если он щёлкнул на блок, выводить первую ошибку этого блока
    if current_err_name:
        for current_err in window.thread.err_dict[current_node_text]:
            if current_err.name == current_err_name:
                break
    else:
        current_err = window.thread.err_dict[current_node_text][0]
    err_links_list = '\n'.join([f'<br><a href="{li}">Проверка здесь</a></br>' for li in current_err.check_link]) \
        if current_err.check_link else ''
    window.errors_browser.setHtml(current_err.description + '\n' + err_links_list)
    window.errors_browser.setOpenExternalLinks(True)
    if current_err.important_parameters:
        err_param_list = set()
        for par in current_err.important_parameters:
            er_par = find_param(par, current_err.node.name, window.thread.current_nodes_dict)
            if er_par:
                err_param_list.add(er_par[0])
        user_node = window.thread.current_nodes_dict[TheBestNode]
        #  если текущей ошибки ещё нет в блоке Избранное, надо добавить туда новый список параметров
        if current_err.name not in user_node.group_params_dict.keys():
            user_node.group_params_dict[current_err.name] = list(err_param_list)

            item = QTreeWidgetItem()
            item.setText(0, current_err.name)
            rowcount = window.nodes_tree.topLevelItemCount() - 1
            window.nodes_tree.topLevelItem(rowcount).addChild(item)
            current_err.err_tree_item = item

            if window.thread.current_node == user_node:
                wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table)
            window.nodes_tree.setCurrentItem(item)
        else:
            # кажется, это не работает, нужно проверить, да ЭТО НЕ РАБОТАЕТ
            window.nodes_tree.setCurrentItem(current_err.err_tree_item)


def params_list_changed(item=None, column=None):  # если в левом окошке выбираем разные блоки или группы параметров
    is_run = False
    current_group_params = ''
    if window.nodes_tree.currentItem() is None:
        return
    try:
        current_node_text = window.nodes_tree.currentItem().parent().text(0)
        current_group_params = window.nodes_tree.currentItem().text(0)
    except AttributeError:
        current_node_text = window.nodes_tree.currentItem().text(0)
    # определяю что за блок выбран
    nod = window.thread.current_nodes_dict[current_node_text]
    window.thread.current_node = nod
    # если не выбрана какая-то конкретная, то выбираю первую группу блока
    if current_group_params:
        window.thread.current_params_list = nod.group_params_dict[current_group_params]
    else:
        window.thread.current_params_list = nod.group_params_dict[list(nod.group_params_dict.keys())[0]]
    # тормозим поток
    if window.thread.isRunning():
        is_run = True
        window.connect_to_node()
    # отображаем имя блока, серийник и всё такое и обновляю список параметров в окошке справа
    window.show_node_name(window.thread.current_node)
    wrapper_show_empty(window.thread.current_params_list, window.vmu_param_table,
                       has_compare=window.thread.current_node.has_compare_params)
    if is_run and window.thread.isFinished():
        window.connect_to_node()
    return True


def check_node_online(all_node_dict: dict):
    exit_dict = {}
    has_invertor = False
    # из всех возможных блоков выбираем те, которые отвечают на запрос серийника
    for nd in all_node_dict.values():
        if nd.request_serial_number:
            print(nd.name, 'serial=  ', end=' ')
            nd.serial_number = nd.get_data(can_adapter, nd.request_serial_number)
        if nd.serial_number != '':
            if nd.request_firmware_version:
                print(nd.name, 'firmware=  ', end=' ')
                nd.firmware_version = nd.get_data(can_adapter, nd.request_firmware_version)
            # тут выясняется, что на старых машинах, где Инвертор_Цикл+ кто-то отвечает по ID Инвертор_МЭИ,
            # может и китайские рейки, нет особого желания разбираться. Вообщем это костыль, чтоб он не вылазил
            if 'Инвертор_Цикл+' in nd.name:
                has_invertor = True
            elif 'Инвертор_МЭИ' in nd.name:
                window.invertor_mpei_box.setEnabled(True)
            elif 'КВУ_ТТС' in nd.name:
                window.joy_bind_btn.setEnabled(True)
                window.susp_zero_btn.setEnabled(True)
                window.load_from_eeprom_btn.setEnabled(True)
                window.light_box.setEnabled(True)
            elif 'Рулевая_зад_Томск' in nd.name:
                window.rear_steer_rbtn.setEnabled(True)
                window.rear_steer_rbtn.setChecked(True)
                window.curr_measure_btn.setEnabled(True)
            elif 'Рулевая_перед_Томск' in nd.name:
                window.front_steer_rbtn.setEnabled(True)
                window.curr_measure_btn.setEnabled(True)
            exit_dict[nd.name] = nd
    if has_invertor:
        if 'Инвертор_МЭИ' in exit_dict.keys():
            del exit_dict['Инвертор_МЭИ']
            window.invertor_mpei_box.setEnabled(False)
    # на случай если только избранное найдено - значит ни один блок не ответил
    if not exit_dict:
        window.front_steer_rbtn.setEnabled(True)
        return all_node_dict.copy(), False
    exit_dict[TheBestNode] = all_node_dict[TheBestNode]
    exit_dict = make_nodes_dict(exit_dict)

    window.nodes_tree.currentItemChanged.disconnect()
    window.show_nodes_tree(list(exit_dict.values()))
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    return exit_dict, True


def erase_errors():
    is_run = False
    # останавливаем поток
    if window.thread.isRunning():
        is_run = True
        window.connect_to_node()
    # и трём все ошибки
    for nod in window.thread.current_nodes_dict.values():
        nod.erase_errors(can_adapter)
    window.add_new_errors({})
    window.errors_browser.clear()
    # запускаем поток снова, если был остановлен
    if is_run and window.thread.isFinished():
        window.connect_to_node()


def save_to_file_pressed():  # если нужно записать текущий блок в файл
    # останавливаем поток
    if window.thread.isRunning():
        window.connect_to_node()
    window.connect_btn.setEnabled(False)
    window.save_to_file_btn.setEnabled(False)
    window.tr.adapter = can_adapter
    window.tr.node_to_save = window.thread.current_node
    window.save_to_file_btn.setText(f'Сохраняются настройки блока:\n {window.tr.node_to_save.name}')
    # запускаем параллельный поток сохранения
    window.tr.start()


class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow, QtStyleTools):
    record_vmu_params = False
    node_list_defined = False
    err_str = ''
    themes_list = list_themes() + QStyleFactory.keys() + \
                  list([sty_s.lower() for sty_s in qrainbowstyle.getAvailableStyles()])
    current_theme = ''

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.all_params_dict = {}
        self.setupUi(self)
        self.setWindowIcon(QIcon('pictures/icons_speed.png'))
        #  Создаю поток для опроса параметров кву
        self.thread = MainThread(self)
        self.thread.threadSignalAThread.connect(self.add_new_vmu_params)
        self.thread.err_thread_signal.connect(self.add_new_errors)
        self.thread.adapter = can_adapter
        #  И для сохранения
        self.tr = SaveToFileThread()
        self.tr.adapter = can_adapter
        self.tr.SignalOfReady.connect(self.progress_bar_fulling)
        self.errors_tree.setColumnCount(1)
        self.errors_tree.header().close()
        self.nodes_tree.setColumnCount(1)
        self.nodes_tree.header().close()
        self.default_style_sheet = self.styleSheet()

    @pyqtSlot(list)
    def add_new_vmu_params(self, list_of_params: list):
        # выясняем что вернул опрос параметров.
        # Если параметр один и он текст - это ошибка подключения
        # Если функция опроса испустила сигнал, и при этом ничего не вернула,
        # нужно просто отобразить текущий список параметров, их значения уже обновлены
        # Если функция вернула строку, значит проблемы с подключением,
        # останавливаем поток
        # Также можно будет в дальнейшем использовать случай, если в списке есть ещё что-то
        if list_of_params and isinstance(list_of_params[0], str):
            err = str(list_of_params[0])
            if self.thread.isRunning():
                # останавливаем запись лога
                if self.thread.is_recording:
                    record_log()
                # останавливаем поток
                self.thread.quit()
                self.thread.wait()
                # выкидываем ошибку
                QMessageBox.critical(self, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.StandardButton.Ok)
            self.connect_btn.setText("Подключиться")
            if can_adapter.isDefined:
                can_adapter.close_canal_can()
            if err == 'Адаптер не подключен':
                can_adapter.isDefined = False
        elif not list_of_params and self.thread.current_params_list:  # ошибок нет - всё хорошо
            # показываем свежие обновлённые параметры
            widgets_list = show_new_vmu_params(params_list=self.thread.current_params_list,
                                               table=self.vmu_param_table,
                                               has_compare_params=self.thread.current_node.has_compare_params)
            # если есть виджеты, подвязываю изменение их значения к изменению параметра
            for i in widgets_list:
                i.ValueSelected.connect(change_value)
        else:
            print('непредвиденная ситуация в списке что то есть, длина списка = ', len(list_of_params))

    @pyqtSlot(dict)  # добавляем ошибки в окошко
    def add_new_errors(self, nds: dict):
        cur_item = ''
        # запоминаю где сейчас курсор - тупо по тексту
        try:
            old_item_name = window.errors_tree.currentItem().text(0)
        except AttributeError:
            old_item_name = ''

        self.errors_tree.clear()
        items = []
        for nod, nod_err in nds.items():
            if nod_err:
                # создаю основные вкладки - названия блоков
                item = QTreeWidgetItem()
                item_name = f'{nod}({len(nod_err)})'
                item.setText(0, item_name)
                if old_item_name == item_name:
                    # если если ранее выбранный блок среди имеющихся, запоминаю его
                    cur_item = item
                for err in nod_err:
                    # подвкладки - ошибки
                    child_item = QTreeWidgetItem()
                    child_item.setText(0, err.name)
                    if err.critical:
                        child_item.setBackground(0, QBrush(color_EVO_red_dark))  # setForeground
                    else:
                        child_item.setBackground(0, QBrush(color_EVO_orange_shine))
                    item.addChild(child_item)
                    # если ранее курсор стоял на группе, запоминаю ее
                    if old_item_name == err.name:  # не работает для рулевых - нужно запоминать и имя блока тоже
                        cur_item = child_item

                items.append(item)

        if not items:
            item = QTreeWidgetItem()
            item.setText(0, 'Ошибок нет')
            items.append(item)
        self.errors_tree.insertTopLevelItems(0, items)
        # если курсор стоял на блоке, который отсутствует в нынешнем списке, то курсор на самый первый блок...
        if not cur_item:
            cur_item = self.errors_tree.topLevelItem(0)
        if cur_item.childCount():
            self.errors_tree.setCurrentItem(cur_item)

    @pyqtSlot(int, str, bool)
    def progress_bar_silent(self, percent: int, err: str, is_finished: bool):
        # рисуем змейку прогресса
        self.node_nsme_pbar.setValue(percent)
        # выходим из потока если есть строка ошибки или файл сохранён
        if is_finished or err:
            self.tr.quit()
            self.tr.wait()
            if is_finished:
                node = self.tr.node_to_save
                ex_word_list = ['System']
                diff_ = [p for group in node.group_params_dict.values() for p in group
                         if p.editable and p.value != p.value_compare]
                diff_list = [p for p in diff_ for ex in ex_word_list
                             if ex not in p.name and ex not in p.description]
                if diff_list:
                    dialog = DialogChange(text='Нужно чётко понимать, что автоматическая загрузка параметров из файла'
                                               ' НИКАК не проверяет, что эти параметры верные и '
                                               'загрузит ВСЕ различающиеся значения.\n'
                                               ' Только при полной уверенности, что ничего не сломается'
                                               ' можно нажимать кнопку "Принять ВСЕ настройки из файла" '
                                               'В противном случае лучше нажать "Поменяю настройки сам" и изменить'
                                               ' только нужные параметры', table=diff_list,
                                          compare=True)
                    dialog.setWindowTitle(f'Разные значения параметров блока {node.name}')
                    dialog.setMinimumWidth(int(window.width() * 0.8))
                    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setText('Поменяю настройки сам')
                    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText(
                        'Принять ВСЕ настройки из файла')
                    dialog.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).setDefault(True)
                    dialog.change_mess(list_of_params=diff_list)
                    if dialog.exec():
                        # пересохранение файла с настройками
                        settings = pathlib.Path(err)
                        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                        old_dir = pathlib.Path(SETTINGS_DIR, f'{node.name}_{now}')
                        old_dir.mkdir()
                        old_set = pathlib.Path(old_dir, 'old_settings.yaml')
                        settings.rename(old_set)
                        # сохранение дифференса
                        diff_file = pathlib.Path(old_dir, 'difference.yaml')
                        save_diff(diff_list, diff_file)
                        # заливка всех настроек из файла
                        err_param_dict = {}
                        for par in diff_list:
                            try:
                                float(par.value_compare)
                                attempt = par.set_value(self.tr.adapter, par.value_compare)
                                if attempt:
                                    err_param_dict[par] = f'Не удалось установить значение {par.value_compare} ' \
                                                          f'для параметра {par.name} ошибка - {attempt}'
                            except ValueError:
                                err_param_dict[par] = f'Несоответствие типа параметра {par.name},' \
                                                      f'значение {par.value_compare} его тип {type(par.value_compare)}'
                        for par in diff_list:
                            par.get_value(self.tr.adapter)
                            if par.value != par.value_compare:
                                err_param_dict[par] = f'Не удалось установить параметр {par.name} ' \
                                                      f'Задавали значение {par.value_compare} ' \
                                                      f'По факту значение {par.value}'
                        if err_param_dict:
                            # сохранение файла несохранённых параметров
                            err_file = pathlib.Path(old_dir, 'wrong_set.yaml')
                            save_diff(list(err_param_dict.keys()), err_file,
                                      description='Это параметры, которые не удалось загрузить в блок')
                            # лучше дать ссылки на файлы
                            dialog1 = DialogChange(text='Не все параметры удалось записать. \nНа всякий случай '
                                                        f'старые настройки блока в файле \n{old_set} \n'
                                                        f' различия в файле  \n{diff_file} \n'
                                                        f' параметры, которые не удалось загрузить в блок, в файле  \n'
                                                        f'{err_file} \nчтоб новые настройки сохранились'
                                                        f' нужно нажать \n "Сохранить в ЕЕПРОМ"',
                                                   table=list(err_param_dict.keys()), compare=True)
                            dialog1.setWindowTitle('Есть проблемки')
                            dialog1.setMinimumWidth(int(window.width() * 0.8))
                            dialog1.buttonBox.button(QDialogButtonBox.StandardButton.Cancel).hide()
                            dialog1.buttonBox.button(QDialogButtonBox.StandardButton.Ok).setText('Печально')
                            dialog1.change_mess(list_of_params=list(err_param_dict.keys()),
                                                text=list(err_param_dict.values()))
                            dialog1.exec()
                        # предупреждение, что старые настройки в файле ерр,
                        # дифференс в файле дифф
                        # надо нажать сохранить в еепром
                        else:
                            QMessageBox.information(window, "Готово",
                                                    f'Поздравляю, <b>старые настройки</b> блока в файле  \n{old_set} \n'
                                                    f' <b>различия</b> в файле  \n{diff_file} \n'
                                                    f'чтоб новые настройки сохранились'
                                                    f' нужно нажать <b>"Сохранить в ЕЕПРОМ"</b>',
                                                    QMessageBox.StandardButton.Ok)
            self.node_nsme_pbar.setValue(0)
            self.connect_to_node()
            self.tr.SignalOfReady.disconnect()
            self.tr.SignalOfReady.connect(self.progress_bar_fulling)

    @pyqtSlot(int, str, bool)
    def progress_bar_fulling(self, percent: int, err: str, is_finished: bool):
        # рисуем змейку прогресса
        self.node_nsme_pbar.setValue(percent)
        # выходим из потока если есть строка ошибки или файл сохранён
        if is_finished or err:
            self.tr.quit()
            self.tr.wait()

            if is_finished:
                QMessageBox.information(self, "Успешный успех!", 'Файл сохранён ' + '\n' + err,
                                        QMessageBox.StandardButton.Ok)
                self.log_lbl.setText('Сохранён файл с настройками ' + err.replace('\n', ''))
            elif err:
                QMessageBox.critical(self, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.StandardButton.Ok)
                self.log_lbl.setText('Файл не сохранён, ошибка ' + err.replace('\n', ''))
            self.node_nsme_pbar.setValue(0)

            self.connect_btn.setEnabled(True)
            self.save_to_file_btn.setEnabled(True)
            self.save_to_file_btn.setText(f'Сохранить настройки блока: \n {self.thread.current_node.name} в файл')
            self.connect_to_node()

    def double_click(self):  # можно подключиться по двойному щелчку по группе параметров
        # для Нового списка даю возможность изменить его название
        if self.nodes_tree.currentItem().text(0) == NewParamsList:
            self.save_list_to_file(self.thread.current_params_list,
                                   'Можно изменить название списка')
            # для всех остальных - просто подключаемся
        if not self.thread.isRunning():
            self.connect_to_node()

    def save_list_to_file(self, p_list, lab: str):
        state = False
        if p_list:
            dialog = DialogChange(label=lab, value=NewParamsList)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                val = dialog.lineEdit.text()
                if val and val != NewParamsList:
                    # берём последний в списке блоков блок - Это Избранное
                    user_node = self.thread.current_nodes_dict[TheBestNode]
                    # создаём в его словаре параметров ещё одну пару - копию нового списка
                    user_node.group_params_dict[val] = user_node.group_params_dict[NewParamsList].copy()
                    # а Новый список удаляем
                    del user_node.group_params_dict[NewParamsList]
                    # проверяю удалось ли сохранить список
                    # if save_params_dict_to_file(self.thread.current_node.group_params_dict, vmu_param_file):
                    # if save_p_dict_to_pickle_file(user_node):
                    if save_p_dict_to_yaml_file(user_node):
                        err_mess = f'{val} успешно сохранён в {TheBestNode}'
                        state = True
                        # создаём новый итем для дерева
                        child_item = QTreeWidgetItem()
                        child_item.setText(0, val)
                        best_node_item = self.nodes_tree.topLevelItem(self.nodes_tree.topLevelItemCount() - 1)
                        best_node_item.addChild(child_item)
                        # а старый итем стираем
                        # может, это и неправильно и надо использовать модель-виев, но я пока не дорос
                        for it in range(best_node_item.childCount()):
                            best_child = best_node_item.child(it)
                            if best_child.text(0) == NewParamsList:
                                best_node_item.removeChild(best_child)
                                break
                    else:  # если сохранить не удалось возвращаю Новый список
                        user_node.group_params_dict[NewParamsList] = user_node.group_params_dict[val].copy()
                        # а  список изменённый удаляем
                        del user_node.group_params_dict[val]
                        err_mess = f'Сохранить не удалось\n файл открыт в другой программе'
                else:
                    err_mess = 'Некорректное имя списка'
            else:
                err_mess = f'Отказ пользователя.\n{NewParamsList} не будет сохранён'
                state = True
        else:
            err_mess = 'Список пуст'
        QMessageBox.information(self, "Информация", err_mess, QMessageBox.StandardButton.Ok)
        self.log_lbl.setText(err_mess.replace('\n', ''))
        return state

    def show_nodes_tree(self, nds: list):
        cur_item = ''
        # запоминаю где сейчас курсор - тупо по тексту
        try:
            old_item_name = window.nodes_tree.currentItem().text(0)
        except AttributeError:
            old_item_name = ''

        self.nodes_tree.clear()
        items = []

        for nd in nds:
            # создаю основные вкладки - названия блоков
            item = QTreeWidgetItem()
            item.setText(0, nd.name)
            if old_item_name == nd.name:
                # если если ранее выбранный блок среди имеющихся, запоминаю его
                cur_item = item
            for param_list in nd.group_params_dict.keys():
                # подвкладки - названия групп параметров
                child_item = QTreeWidgetItem()
                child_item.setText(0, str(param_list))
                item.addChild(child_item)
                # если ранее курсор стоял на группе, запоминаю ее
                if old_item_name == str(param_list):  # не работает для рулевых - нужно запоминать и имя блока тоже
                    cur_item = child_item
            items.append(item)

        self.nodes_tree.insertTopLevelItems(0, items)
        # если курсор стоял на блоке, который отсутствует в нынешнем списке, то курсор на самый первый блок...
        if not cur_item:
            cur_item = self.nodes_tree.topLevelItem(0)
        self.nodes_tree.setCurrentItem(cur_item)
        # ... и текущий блок,соответственно, самый первый
        if self.thread.current_node not in nds:
            self.thread.current_node = nds[0]
        self.show_node_name(self.thread.current_node)

    def show_node_name(self, nd: EVONode):
        # чтоб юзер понимал в каком блоке он находится
        self.node_name_lab.setText(nd.name)
        self.node_s_n_lab.setText(f'Серийный номер: {nd.serial_number}')
        self.node_fm_lab.setText(f'Версия ПО: {nd.cut_firmware()}')
        if self.save_to_file_btn.isEnabled():
            self.save_to_file_btn.setText(f'Сохранить настройки блока:\n {nd.name} в файл')
        return

    def connect_to_node(self):
        # такое бывает при первом подключении или если вырвали адаптер - надо заново его определить
        if not can_adapter.isDefined:
            self.log_lbl.setText('Определяется подключенный адаптер...')
            if not can_adapter.find_adapters():
                self.log_lbl.setText('Адаптер не подключен')
                return
        # если у нас вообще нет адаптеров, надо выходить
        # наверное, это можно объединить, если вырвали адаптер, список тоже нужно обновлять,\
        # хотя когда теряем кан-шину также есть смысл обновить список подключенных блоков
        # надо это добавить!
        if not self.node_list_defined:
            self.log_lbl.setText('Определяются имеющиеся на шине CAN блоки...')
            self.thread.current_nodes_dict, check = check_node_online(self.thread.current_nodes_dict)
            params_list_changed()
            self.reset_faults.setEnabled(check)
            self.save_to_file_btn.setEnabled(check)
            self.node_list_defined = check
            self.log_lbl.setText(f'Обнаружено {check * len(self.thread.current_nodes_dict)} блоков')

        check = not self.thread.isRunning()
        self.log_record_btn.setEnabled(check)

        if check:
            self.thread.iter_count = 1
            self.thread.start()
            self.connect_btn.setText("Отключиться")
        else:
            self.thread.quit()
            self.thread.wait()
            self.connect_btn.setText("Подключиться")
            can_adapter.close_canal_can()

    def closeEvent(self, event):
        # может, есть смысл сделать из этого функцию, дабы не повторять дважды

        for node in self.thread.current_nodes_dict.values():
            if node.param_was_changed:
                msg = QMessageBox(self)
                msg.setWindowTitle("Параметры не сохранены")
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText(f"В блоке {node.name} были изменены параметры,\n"
                            f" но они не сохранены в EEPROM,\n"
                            f" нужно ли их сохранить в память?")

                buttonAccept = msg.addButton("Сохранить", QMessageBox.ButtonRole.YesRole)
                msg.addButton("Не сохранять", QMessageBox.ButtonRole.RejectRole)
                msg.setDefaultButton(buttonAccept)
                msg.exec()
                if msg.clickedButton() == buttonAccept:
                    save_to_eeprom(self, node)

        if TheBestNode in self.thread.current_nodes_dict.keys():
            user_node_dict = self.thread.current_nodes_dict[TheBestNode].group_params_dict
            if NewParamsList in user_node_dict.keys() and user_node_dict[NewParamsList]:
                if not self.save_list_to_file(user_node_dict[NewParamsList],
                                              f'В {NewParamsList} добавлены параметры \n'
                                              f' нужно сохранить этот список?'):
                    event.ignore()

        msg = QMessageBox(self)
        msg.setWindowTitle("Выход")
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setText("Вы уверены, что хотите закрыть приложение?")

        buttonAccept = msg.addButton("Да", QMessageBox.ButtonRole.YesRole)
        msg.addButton("Отменить", QMessageBox.ButtonRole.RejectRole)
        msg.setDefaultButton(buttonAccept)
        msg.exec()

        if msg.clickedButton() == buttonAccept:
            with open(stylesheet_file, 'w+') as f:
                f.write(self.current_theme)
            if self.thread.isRunning():
                self.thread.quit()
                self.thread.wait()
                del self.thread
            if can_adapter.isDefined:
                can_adapter.close_canal_can()
        else:
            event.ignore()

    def change_tab(self):
        if self.main_tab.currentWidget() == self.management_tab:
            if self.thread.isRunning():
                self.connect_to_node()
                print('Поток остановлен')
            print('Вкладка управление')
        elif self.main_tab.currentWidget() == self.params_tab:
            self.connect_to_node()
            print('Вкладка параметры, поток запущен')
        # elif self.main_tab.currentWidget() == self.grafics_tab:
        #     print('Графики не готовы')
        else:
            print('Неизвестное состояние')

    def generate_menu(self, pos):
        c_row = window.vmu_param_table.currentRow()
        if c_row < 0:
            print('Нет ячейки')
            return
        parametr = window.thread.current_params_list[c_row]
        menu = QMenu()
        all_items_menu_dict = dict([
            ('Добавить в Избранное', add_param_to_the_best_node),
            ('Удалить из Избранного', add_param_to_the_best_node),
            ('Задать период опроса', change_period),
            ('Установить пределы', change_limit),
            # ('Установить максимум', change_max),
            # ('Установить минимум', change_min)
        ])

        if check_param_in_the_best_node(parametr):
            del all_items_menu_dict['Добавить в Избранное']
        else:
            del all_items_menu_dict['Удалить из Избранного']

        match parametr.widget:
            case 'Text':
                if not parametr.value_table:
                    all_items_menu_dict['Линейный индикатор'] = set_bar
                    if parametr.editable:
                        all_items_menu_dict['Слайдер'] = set_slider
            case 'MyColorBar':
                all_items_menu_dict['Описание'] = set_text_description
                if parametr.editable:
                    all_items_menu_dict['Слайдер'] = set_slider
            case 'MySlider':
                all_items_menu_dict['Линейный индикатор'] = set_bar
                all_items_menu_dict['Описание'] = set_text_description

        items = {menu.addAction(u'' + item): value for item, value in all_items_menu_dict.items()}

        action = menu.exec(self.vmu_param_table.mapToGlobal(pos))
        # Display the data text of the selected row
        if action:
            res = items[action](parametr)


def change_theme():
    if window.current_theme:
        theme_count = window.themes_list.index(window.current_theme)
        if theme_count == len(window.themes_list) - 1:
            window.current_theme = window.themes_list[0]
        else:
            window.current_theme = window.themes_list[theme_count + 1]
    else:
        window.current_theme = window.themes_list[0]
    set_theme(window.current_theme)


def set_theme(theme_str=''):
    if theme_str in QStyleFactory.keys():
        app.setStyleSheet('')
        app.setStyle(theme_str)
    elif theme_str in list_themes():
        apply_stylesheet(app, theme_str, extra=extra)
        stapp = app.styleSheet()
        pr_c_index = stapp.find('QPushButton {')
        primary_color = stapp[pr_c_index + 23:pr_c_index + 30]
        c_f_index = stapp.find('*{')
        c_f_index_end = stapp.find('*:focus')
        cur_font = stapp[c_f_index + 2:c_f_index_end]
        b_f_index = stapp.find('/*  QPushButton  */')
        b_f_index_end = stapp.find('QPushButton:checked,')
        butt_font = stapp[b_f_index + 34:b_f_index_end]
        my_style = f'QLabel {{color: {primary_color};\n' \
                   f'{butt_font}\n' \
                   f'GreenLabel, RedLabel {{\n' \
                   f'{cur_font} '
        app.setStyleSheet(stapp + my_style)
    elif theme_str in [sty_s.lower() for sty_s in qrainbowstyle.getAvailableStyles()]:
        app.setStyleSheet(qrainbowstyle.load_stylesheet(style=theme_str))
    else:
        app.setStyleSheet('')
    c_style_sheet = app.styleSheet()
    app.setStyleSheet(c_style_sheet + 'GreenLabel {background-color: rgba(0, 200, 0, 50);} '
                                      'RedLabel {background-color: rgba(200, 0, 0, 50);} ')


if __name__ == '__main__':
    start_time = time.perf_counter()
    app = QApplication(sys.argv)
    splash = QSplashScreen()
    # splash.setPixmap(QPixmap('pictures/EVO-EVIS_l.jpg'))
    splash.setPixmap(QPixmap('pictures/EVO-EvCON.jpg'))
    splash.show()
    window = VMUMonitorApp()
    window.label.setPixmap(QPixmap('pictures/grafic.png'))
    # window.setWindowTitle('Electric Vehicle Information System')
    window.setWindowTitle('Electrical vehicle CONtrol')
    stylesheet_file = pathlib.Path(WORK_DIR, 'Data', 'EVOStyleSheet.txt')

    window.main_tab.currentChanged.connect(window.change_tab)
    # ============================== подключаю сигналы нажатия на окошки============
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    window.errors_tree.itemPressed.connect(show_error)
    window.nodes_tree.doubleClicked.connect(window.double_click)
    window.vmu_param_table.cellDoubleClicked.connect(want_to_value_change)
    window.errors_browser.setStyleSheet("font: bold 14px;")
    window.vmu_param_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
    window.vmu_param_table.customContextMenuRequested.connect(window.generate_menu)
    # ============================== и сигналы нажатия на кнопки=====================
    # -----------------Инвертор---------------------------
    window.invert_btn.clicked.connect(lambda: mpei_invert(window))
    window.calibrate_btn.clicked.connect(lambda: mpei_calibrate(window))
    window.power_on_btn.clicked.connect(lambda: mpei_power_on(window))
    window.power_off_btn.clicked.connect(lambda: mpei_power_off(window))
    window.reset_device_btn.clicked.connect(lambda: mpei_reset_device(window))
    window.reset_param_btn.clicked.connect(lambda: mpei_reset_params(window))
    window.let_moment_btn.clicked.connect(lambda: let_moment_mpei(window))
    window.invertor_mpei_box.setEnabled(False)
    # ------------------Кнопки вспомогательные----------------
    window.joy_bind_btn.clicked.connect(lambda: joystick_bind(window))
    window.susp_zero_btn.clicked.connect(lambda: suspension_to_zero(window))
    window.load_from_eeprom_btn.clicked.connect(lambda: load_from_eeprom(window))
    window.curr_measure_btn.clicked.connect(lambda: check_steering_current(window))
    window.susp_zero_btn.setEnabled(False)
    window.load_from_eeprom_btn.setEnabled(False)
    window.joy_bind_btn.setEnabled(False)
    window.change_theme_btn.clicked.connect(change_theme)
    window.front_steer_rbtn.setEnabled(False)
    window.rear_steer_rbtn.setEnabled(False)
    window.curr_measure_btn.setEnabled(False)
    # ------------------Главные кнопки-------------------------
    window.connect_btn.clicked.connect(window.connect_to_node)
    window.save_eeprom_btn.clicked.connect(lambda: save_to_eeprom(window))
    window.reset_faults.clicked.connect(erase_errors)
    # window.compare_btn.clicked.connect(make_compare_params_list)
    window.compare_btn.clicked.connect(make_compare)
    window.save_to_file_btn.clicked.connect(save_to_file_pressed)
    window.log_record_btn.clicked.connect(record_log)
    window.search_btn.clicked.connect(search_param)
    window.save_to_file_btn.setEnabled(False)
    # ----------------------------- сигналы от радио кнопок
    window.off_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.left_side_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.right_side_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.stop_light_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.rear_light_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.low_beam_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.high_beam_rbtn.clicked.connect(lambda: rb_toggled(window))
    window.flash_light_checkBox.clicked.connect(lambda: multyvibrator(window))
    window.light_box.setEnabled(False)
    # ----------------------------------- подготовка под графики ------------------------------------------------
    window.label.deleteLater()
    window.graphWidget = PlotWidget()
    window.gridLayout_5.addWidget(window.graphWidget, 0, 0, 1, 1)


    # заполняю первый список блоков из файла - максимальное количество всего, что может быть на нижнем уровне
    try:
        with open(NODES_PICKLE_FILE, 'rb') as f:
            node_dict = pickle.load(f)
    except FileNotFoundError:
        node_dict = make_nodes_dict(fill_nodes_dict_from_yaml(NODES_YAML_FILE))
        with open(NODES_PICKLE_FILE, 'wb') as f:
            pickle.dump(node_dict, f)

    try:
        with open(stylesheet_file) as f:
            window.current_theme = f.read()
    except FileNotFoundError:
        print('Файл со стилем не найден, Оставляем стиль по умолчанию')
    finally:
        set_theme(window.current_theme)

    window.thread.current_nodes_dict = node_dict.copy()
    # показываю дерево с блоками и что ошибок нет
    window.show_nodes_tree(list(node_dict.values()))
    # если со списком блоков всё ок, показываем его в левом окошке и запускаем приложение
    if node_dict and params_list_changed():
        if can_adapter.find_adapters():
            window.connect_to_node()
        else:
            window.log_lbl.setText('Адаптер не подключен')

        window.show()  # Показываем окно
        splash.finish(window)  # Убираем заставку
        sys.exit(app.exec())  # и запускаем приложение

# реальный номер 11650178014310 считывает 56118710341001 наоборот - Антон решает
# не обновляется все значения параметров если фокус в одном из виджетов
# кнопка сохранить всё в гит
# сохранение настроек параметра в ямл файл(и удаление пикл)
# при обновлении проги должны добавляться только новые папки, старые параметры не трогаем
# вывести окно сравнения различающихся параметров, которые можно менять при заливке других настроек
# виджеты с частыми параметрами в окно управление
# цветомузыка
# научиться парсить текстовые настройки ТАБ
# научиться парсить настройки старого КВУ
# когда сохраняется файл, давать не него ссылку
# делаем графики
