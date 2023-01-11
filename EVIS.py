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

следующие шаги
- поиск по имени и описанию параметра
- возможность записи лога текущих параметров из открытого списка и сохранять запись в эксель файл - лог
- графики выбранных текущих параметров
- виджеты по управлению параметром
- хранение профилей блока в отдельном файле эксель с названием_блока_версия_ПО в папках с Название_блока
        в файле список параметров и ошибки. Это позволит оставить пользовательский список Избранное
- добавить в параметр поле со словарём значений -
        если считано подходящее - подставлять значение из словаря (как сохранять??)
- всплывающее меню при правом щелчке по параметру - Добавить в Избранное и Изменить период
- автоматическое определение нужного периода опроса параметра и сохранение этого периода в свойства параметра в файл
- работа в линуксе
- работа с квайзером
- в новом параметре КВУ формировать ВИН номер машины+номера_блоков -
        сделать автоматический опрос номеров и сравнение с тем, что в памяти
- сохранение и парсинг параметров в yaml
- при изменении параметра в инверторе мэи напоминать, что он не действует без сохранения в еепром
- если не подключен к ВАТС, изменение параметров пачкой и при подключении их заброс в блок
- если нет опроса, но изменён параметр, не запускать опрос после изменения
- прерывать опрос только при отправке нового параметра, после сразу запускать
- добавить в кву кнопку считать с ЕЕПРОМ
- покрасить критические ошибки в красный с приставкой - критическая!
- добавить вкладку ПНР, на ней несколько подвкладок со страницами процесса пнр с нужными параметрами
- добавить возможность ОТМЕНы при нажатии любой кнопки управления
- добавить напоминание выключить высокое при калибровке инвертора
- выдавать какую ошибку схватил инвертор, если время кончилось, а положительного ответа от инвертора не поступило
- сделать процесс подключения видимым
- подкрашивать параметры, которые в новый список улетают, чтоб было заметно
- сделать видимым процесс привязки джойстика и установки подвески
- сделать ошибки объектами с описанием, ссылками и выводом нужных параметров

НА ПОДУМАТЬ
- может ли приёмник джойстика отвечать по SDO например, положения кнопок?
- может ли БКУ отвечать по SDO хотя бы серийник?
- продумать реляционную БД для параметров
- на отдельном листе управление для этого блока с виджетами типами - слайдеры, кнопки, чекбоксы - по каким адресам,
  название и так далее.
- добавлять блок в список имеющихся и
выводить в соседнем окошке список определённых для этого блока виджетов (слайдеры, кнопки) + количество этих окошек с
виджетами для каждого блока задаёт пользователь, т.е. он может создать свои нужные виджеты и сохранить их в профиль к
этому блоки, а при загрузке это должно подгрузится - и стандартные и выбранные для того блока пользователем -
полагаю отдельный лист Экселя с выбранными параметрами - виджетами
- ещё кнопка - загрузка параметров из файла - здесь должна быть жёсткая защита - не все редактируемые параметры
 из одного блока можно напрямую заливать в другой. Или их ограничить до минимума или предлагать делать изменение вручную

"""
import copy
import datetime
import pickle
import sys
import time
from pprint import pprint

import pandas as pd
from PyQt5.QtCore import pyqtSlot, Qt, QRegExp, pyqtSignal
from PyQt5.QtGui import QIcon, QColor, QPixmap, QRegExpValidator, QBrush
from PyQt5.QtWidgets import QMessageBox, QApplication, QMainWindow, QTreeWidgetItem, QDialog, \
    QSplashScreen, QFileDialog, QDialogButtonBox
import pathlib
from pandas import ExcelWriter
import VMU_monitor_ui
from CANAdater import CANAdapter
from EVOErrors import EvoError
from EVONode import EVONode
from My_threads import SaveToFileThread, MainThread, WaitCanAnswerThread, SleepThread
from Parametr import Parametr
from work_with_file import fill_sheet_dict, fill_compare_values, fill_nodes_dict_from_yaml, make_nodes_dict, dir_path, \
    vmu_param_file, nodes_pickle_file, nodes_yaml_file, save_p_dict_to_file
from helper import zero_del, NewParamsList, log_uncaught_exceptions, DialogChange, show_empty_params_list, \
    show_new_vmu_params, find_param, TheBestNode, easter_egg

can_adapter = CANAdapter()
sys.excepthook = log_uncaught_exceptions
wait_thread = WaitCanAnswerThread()
sleep_thread = SleepThread(3)


def search_param():
    def line_edit_change(s):
        len_s = len(s)
        if len_s >= 4:
            dialog.buttonBox.button(QDialogButtonBox.Ok).setEnabled(True)
            dialog.lineEdit.setStyleSheet("color: black;")
        else:
            dialog.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
            dialog.lineEdit.setStyleSheet("color: red;")

    dialog = DialogChange(label='Не менее 4 букв из имени или описания параметра, которого нужно найти', value='')
    dialog.lineEdit.setText('')
    dialog.setWindowTitle('Поиск параметра')
    dialog.buttonBox.button(QDialogButtonBox.Ok).setEnabled(False)
    dialog.lineEdit.textChanged.connect(line_edit_change)
    if dialog.exec_() == QDialog.Accepted:
        search_text = dialog.lineEdit.text()
        was_run = False
        if window.thread.isRunning():
            was_run = True
            window.connect_to_node()
        # search_bar = DialogChange(label=f'Ищем параметр с {search_text}', process=0)
        # search_bar.exec_()
        # SearchProcess = pyqtSignal(int)
        # SearchProcess.connect(search_bar.change_mess)
        par_list = find_param(window.thread.current_nodes_dict, search_text).copy()
        if par_list:
            p_list = []
            for par in par_list:
                # search_bar.change_mess(progress=50)
                if '#' not in par.name:
                    new_par = copy.copy(par)
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
                                                     f' в текущих блоках найти не удалось ', QMessageBox.Ok)
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
            file_name = pathlib.Path(dir_path, 'ECU_Records', f'{file_name}_{now}.xlsx')
            df = pd.DataFrame(window.thread.record_dict)
            df_t = df.transpose()
            window.thread.record_dict.clear()
            ex_wr = ExcelWriter(file_name, mode="w")
            with ex_wr as writer:
                df_t.to_excel(writer)
            QMessageBox.information(window, "Успешный успех!", f'Лог сохранён в файл {file_name}', QMessageBox.Ok)


def make_compare_params_list():
    file_name = QFileDialog.getOpenFileName(window, 'Файл с нужными параметрами', dir_path,
                                            "Excel tables (*.xlsx)")[0]
    if file_name and ('.xls' in file_name):
        compare_nodes_dict = fill_sheet_dict(file_name)
        comp_node_name = ''
        if compare_nodes_dict:
            for cur_node in window.thread.current_nodes_dict.values():
                # как минимум, два варианта что этот блок присутствует
                #  - если имя страницы, он же ключ у словаря из файла совпадает с имеющимся сейчас блоком
                #  - если список параметров, хотя бы частично, совпадает со списком параметров имеющегося блока
                if cur_node.name in compare_nodes_dict.keys():
                    fill_compare_values(cur_node, compare_nodes_dict[cur_node.name])
                    comp_node_name += cur_node.name + ', '
                else:
                    for comp_params_dict in compare_nodes_dict.values():
                        if set(cur_node.group_params_dict.keys()) & set(comp_params_dict.keys()):
                            fill_compare_values(cur_node, comp_params_dict)
                            comp_node_name += cur_node.name + ', '
                            break
        show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table,
                               has_compare=window.thread.current_node.has_compare_params)
        if comp_node_name:
            window.log_lbl.setText(f'Загружены параметры сравнения для блока {comp_node_name}')
        else:
            window.log_lbl.setText(f'Не найден блок для загруженных параметров')
    else:
        window.log_lbl.setText('Файл не выбран')
        return False


def save_to_eeprom(node=None):
    if not node:
        node = window.thread.current_node

    if node.save_to_eeprom:
        if window.thread.isRunning():
            window.connect_to_node()
            isRun = True
        else:
            isRun = False

        if node.name == 'Инвертор_МЭИ':
            voltage = find_param(window.thread.current_nodes_dict, 'DC_VOLTAGE', 'Инвертор_МЭИ')[0]
            err = voltage.get_value(can_adapter.adapters_dict[125])  # ---!!!если параметр строковый, будет None!!---
            if not isinstance(err, str):
                # Сохраняем в ЕЕПРОМ Инвертора МЭИ только если выключено высокое - напряжение ниже 30В
                if err < 30:
                    err = node.send_val(node.save_to_eeprom, can_adapter.adapters_dict[125])
                    sleep_thread.start()
                else:
                    err = 'Высокое напряжение не выключено\nВыключи высокое напряжение и повтори сохранение'
            else:
                err = f'Некорректный ответ от инвертора\n{err}'
        else:
            err = node.send_val(node.save_to_eeprom, can_adapter, value=1)

        if err:
            QMessageBox.critical(window, "Ошибка ", f'Настройки сохранить не удалось\n{err}', QMessageBox.Ok)
            window.log_lbl.setText('Настройки в память НЕ сохранены, ошибка ' + err)
        else:
            QMessageBox.information(window, "Успешный успех!", 'Текущие настройки сохраняются в EEPROM', QMessageBox.Ok)
            window.log_lbl.setText('Настройки сохранены в EEPROM')
            node.param_was_changed = False
            erase_errors()
            window.save_eeprom_btn.setEnabled(False)

        if window.thread.isFinished() and isRun:
            window.connect_to_node()
    else:
        QMessageBox.information(window, "Информация", f'В {node.name} параметры сохранять не нужно', QMessageBox.Ok)
        window.save_eeprom_btn.setEnabled(False)


@pyqtSlot(list)
def change_value(lst):
    next_cell = window.vmu_param_table.item(window.vmu_param_table.currentItem().row(),
                                            window.vmu_param_table.currentItem().column() + 1)
    info_m = 'От комбо-бокса пришёл пустой список'
    if lst:
        parametr = lst[0]
        new_value = lst[1]
        info_m = set_new_value(next_cell, parametr, new_value)

    if info_m:
        QMessageBox.information(window, "Информация", info_m, QMessageBox.Ok)


def set_new_value(next_cell, param: Parametr, val):
    info_m = ''
    if 'WheelTypeSet' in param.name:
        if QMessageBox.information(window, "Пасхалка", easter_egg, QMessageBox.Ok | QMessageBox.Cancel) != QMessageBox.Ok:
            return "Пердумал"
    try:
        float(val)
        if window.thread.isRunning():  # отключаем поток, если он был включен
            window.connect_to_node()
            # отправляю параметр, полученный из диалогового окна
            param.set_val(can_adapter, float(val))
            # и сразу же проверяю записался ли он в блок
            value_data = param.get_value(can_adapter)  # !!!если параметр строковый, будет None!!--
            if isinstance(value_data, str):
                new_val = ''
            else:
                new_val = zero_del(value_data).strip()
            # и сравниваю их - соседняя ячейка становится зеленоватой, если ОК и красноватой если не ОК
            if str(val) == new_val:
                next_cell.setBackground(QColor(0, 254, 0, 30))
                if param.node.save_to_eeprom:
                    param.node.param_was_changed = True
                    # В Избранном кнопку не активируем, может быть несколько блоков.
                    # Возможно, я когда-то смогу
                    if window.thread.current_node.name != TheBestNode:
                        window.save_eeprom_btn.setEnabled(True)
                        if window.thread.current_node.name == 'Инвертор_МЭИ':
                            info_m = f'Параметр будет работать, \nтолько после сохранения в ЕЕПРОМ'
            else:
                next_cell.setBackground(QColor(254, 0, 0, 30))
            # если поток был запущен до изменения, то запускаем его снова
            if window.thread.isFinished():
                # и запускаю поток
                window.connect_to_node()
        else:
            info_m = f'Подключение прервано, \nДля изменения параметра\nтребуется подключение к ВАТС'
    except ValueError:
        info_m = 'Параметр должен быть числом'
    return info_m


def want_to_value_change():
    #  над разбивать, как минимум, на две функции
    current_cell = window.vmu_param_table.currentItem()
    c_row = current_cell.row()
    c_col = current_cell.column()
    c_text = current_cell.text()
    # возможно, лучше сразу флаги дёрнуть, потом их изменять
    c_flags = current_cell.flags()
    col_name = window.vmu_param_table.horizontalHeaderItem(c_col).text().strip().upper()
    current_param = window.thread.current_params_list[c_row]
    next_cell = window.vmu_param_table.item(c_row, c_col + 1)

    # меняем значение параметра
    if col_name == 'ЗНАЧЕНИЕ':
        is_editable = True if Qt.ItemIsEditable & current_cell.flags() else False
        info_m = ''
        if is_editable:
            dialog = DialogChange(label=current_param.name, value=c_text.strip())
            reg_ex = QRegExp("[+-]?([0-9]*[.])?[0-9]+")
            dialog.lineEdit.setValidator(QRegExpValidator(reg_ex))

            if dialog.exec_() == QDialog.Accepted:
                val = dialog.lineEdit.text()
                info_m = set_new_value(next_cell, current_param, val)
        else:
            info_m = f'Сейчас этот параметр нельзя изменить\n' \
                     f'Изменяемые параметры подкрашены зелёным\n' \
                     f'Также требуется подключение к ВАТС'
        if info_m:
            QMessageBox.information(window, "Информация", info_m, QMessageBox.Ok)
        # сбрасываю фокус с текущей ячейки, чтоб выйти красиво, при запуске потока и
        # обновлении значения она снова станет редактируемой, пользователь не замечает изменений
        window.vmu_param_table.item(c_row, c_col).setFlags(c_flags & ~Qt.ItemIsEditable)
    # добавляю параметр в Избранное/Новый список
    # пока редактирование старых списков не предусмотрено
    elif col_name == 'ПАРАМЕТР':
        # достаю список Избранное
        user_node = window.thread.current_nodes_dict[TheBestNode]
        # из текущего параметра делаю новый с новым именем через #
        new_param = current_param.copy()
        if window.thread.current_node != user_node:
            new_param.name = f'{new_param.name}#{new_param.node.name}'
        text = f'добавлен в блок {TheBestNode}'
        next_cell.setBackground(QColor(254, 0, 0, 30))
        # если Новый список есть в Избранном
        rowcount = window.nodes_tree.topLevelItemCount() - 1
        best_node_item = window.nodes_tree.topLevelItem(rowcount)

        if NewParamsList in user_node.group_params_dict.keys():
            # Проверяю есть ли уже новый параметр в Новом списке
            p = None
            for par in user_node.group_params_dict[NewParamsList]:
                if par.name in new_param.name:
                    p = par
            # если есть, то удаляю его (как-то тупо определяю, надо переделать)
            if p:
                text = f'удалён из блока {TheBestNode}'
                window.vmu_param_table.item(c_row, c_col + 1).setBackground(QColor(254, 254, 254, 30))
                was_run = False
                # останавливаю поток и удаляю параметр из Нового списка
                if window.thread.isRunning():
                    window.connect_to_node()
                    was_run = True

                user_node.group_params_dict[NewParamsList].remove(p)

                # если юзер сейчас в Новом списке, обновляю вид таблицы
                if window.thread.current_node == user_node:
                    show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table)

                if window.thread.isFinished() and was_run:
                    window.connect_to_node()
            # если нового параметра нет в Новом списке, добавляю его туда
            else:
                if not user_node.group_params_dict[NewParamsList]:
                    item = best_node_item.child(best_node_item.childCount() - 1)
                    best_node_item.setExpanded(True)
                    item.setBackground(0, QColor(254, 0, 0, 30))
                    # window.nodes_tree.show()
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
            item.setBackground(0, QColor(254, 0, 0, 30))
            # window.nodes_tree.show()
            index = window.nodes_tree.indexFromItem(item, 0)
            window.nodes_tree.scrollTo(index)

        window.log_lbl.setText(f'Параметр {current_param.name} {text}')
    return


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
    err_links_list = '\n'.join([f'<a href="{li}">Link</a>' for li in current_err.check_link])\
        if current_err.check_link else ''
    window.errors_browser.setText(current_err.description + '\n' + err_links_list)
    window.errors_browser.setOpenExternalLinks(True)
    if current_err.important_parameters:
        err_param_list = set()
        for par in current_err.important_parameters:
            er_par = find_param(window.thread.current_nodes_dict, par, current_err.node.name)
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
                show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table)
            window.nodes_tree.setCurrentItem(item)
        else:
            # кажется, это не работает, нужно проверить, да ЭТО НЕ РАБОТАЕТ
            window.nodes_tree.setCurrentItem(current_err.err_tree_item)


def params_list_changed(item=None, column=None):  # если в левом окошке выбираем разные блоки или группы параметров
    # pprint(inspect.stack()[1][3])
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
    # отображаем имя блока, ерийник и всё такое и обновляю список параметров в окошке справа
    window.show_node_name(window.thread.current_node)
    show_empty_params_list(window.thread.current_params_list, show_table=window.vmu_param_table,  # combo_list =
                           has_compare=window.thread.current_node.has_compare_params)
    # for com in combo_list:
    #     com.clicked.connect(some_def)
    # и запускаю поток, если он был запущен
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
            exit_dict[nd.name] = nd
    if has_invertor:
        if 'Инвертор_МЭИ' in exit_dict.keys():
            del exit_dict['Инвертор_МЭИ']
            window.invertor_mpei_box.setEnabled(False)
    # на случай если только избранное найдено - значит ни один блок не ответил
    if not exit_dict:
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
    # запускаем поток снова, если был остановлен
    if is_run and window.thread.isFinished():
        window.connect_to_node()


def some_def():
    print(f' выбран комбобокс ')


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
    window.tr.run()


class VMUMonitorApp(QMainWindow, VMU_monitor_ui.Ui_MainWindow):
    record_vmu_params = False
    node_list_defined = False
    err_str = ''

    def __init__(self):
        super().__init__()
        # Это нужно для инициализации нашего дизайна
        self.all_params_dict = {}
        self.setupUi(self)
        self.setWindowIcon(QIcon('pictures/icons_speed.png'))
        #  Создаю поток для опроса параметров кву
        self.thread = MainThread()
        self.thread.threadSignalAThread.connect(self.add_new_vmu_params)
        self.thread.err_thread_signal.connect(self.add_new_errors)
        self.thread.adapter = can_adapter
        #  И для сохранения
        self.tr = SaveToFileThread()
        self.tr.adapter = can_adapter
        self.tr.SignalOfReady.connect(self.progress_bar_fulling)
        # проверить это
        self.errors_tree.setColumnCount(1)
        self.errors_tree.header().close()
        self.nodes_tree.setColumnCount(1)
        self.nodes_tree.header().close()

    @pyqtSlot(list)
    def add_new_vmu_params(self, list_of_params: list):
        # global can_adapter
        # выясняем что вернул опрос параметров. Если параметр один и он текст - это ошибка подключения
        if len(list_of_params) < 2 and isinstance(list_of_params[0], str):
            err = str(list_of_params[0])
            if self.thread.isRunning():
                if self.thread.is_recording:
                    record_log()
                self.thread.quit()
                self.thread.wait()
                QMessageBox.critical(self, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.Ok)
            self.connect_btn.setText("Подключиться")
            if can_adapter.isDefined:
                can_adapter.close_canal_can()
            if err == 'Адаптер не подключен':
                can_adapter.isDefined = False
        else:
            combo_boxes = show_new_vmu_params(params_list=self.thread.current_params_list,
                                              table=self.vmu_param_table,
                                              has_compare_params=self.thread.current_node.has_compare_params)
            for i in combo_boxes:
                i.ItemSelected.connect(change_value)  # activated

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
                        child_item.setForeground(0, QBrush(QColor(254, 0, 0)))
                    else:
                        child_item.setForeground(0, QBrush(QColor(247, 242, 26)))
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
        # self.errors_tree.currentItemChanged.connect(show_error)
        # если курсор стоял на блоке, который отсутствует в нынешнем списке, то курсор на самый первый блок...
        if not cur_item:
            cur_item = self.errors_tree.topLevelItem(0)
        if cur_item.childCount():
            self.errors_tree.setCurrentItem(cur_item)

    @pyqtSlot(int, str, bool)
    def progress_bar_fulling(self, percent: int, err: str, is_finished: bool):
        # рисуем змейку прогресса
        self.node_nsme_pbar.setValue(percent)
        # выходим из потока если есть строка ошибки или файл сохранён
        if is_finished or err:
            self.tr.quit()
            self.tr.wait()

            if is_finished:
                QMessageBox.information(self, "Успешный успех!", 'Файл сохранён ' + '\n' + err, QMessageBox.Ok)
                self.log_lbl.setText('Сохранён файл с настройками ' + err.replace('\n', ''))
            elif err:
                QMessageBox.critical(self, "Ошибка ", 'Нет подключения' + '\n' + err, QMessageBox.Ok)
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
            if dialog.exec_() == QDialog.Accepted:
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
                    if save_p_dict_to_file(self.thread.current_node.group_params_dict):
                        err_mess = f'{val} успешно сохранён в {TheBestNode}'
                        state = True
                        # создаём новый итем для дерева
                        child_item = QTreeWidgetItem()
                        child_item.setText(0, val)
                        self.nodes_tree.currentItem().parent().addChild(child_item)
                        # а старый итем стираем
                        # может, это и неправильно и надо использовать модель-виев, но я пока не дорос
                        self.nodes_tree.currentItem().parent().removeChild(self.nodes_tree.currentItem())
                    else:  # если сохранить не удалось возвращаю Новый список
                        user_node.group_params_dict[NewParamsList] = user_node.group_params_dict[val].copy()
                        # а  список изменённый удаляем
                        del user_node.group_params_dict[val]
                        err_mess = f'Сохранить не удалось\n {vmu_param_file.name} открыт в другой программе'
                else:
                    err_mess = 'Некорректное имя списка'
            else:
                err_mess = f'Отказ пользователя.\n{NewParamsList} не будет сохранён'
                state = True
        else:
            err_mess = 'Список пуст'
        QMessageBox.information(self, "Информация", err_mess, QMessageBox.Ok)
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
                msg.setIcon(QMessageBox.Information)
                msg.setText(f"В блоке {node.name} были изменены параметры,\n"
                            f" но они не сохранены в EEPROM,\n"
                            f" нужно ли их сохранить в память?")

                buttonAceptar = msg.addButton("Сохранить", QMessageBox.YesRole)
                msg.addButton("Не сохранять", QMessageBox.RejectRole)
                msg.setDefaultButton(buttonAceptar)
                msg.exec_()
                if msg.clickedButton() == buttonAceptar:
                    save_to_eeprom(node)

        if TheBestNode in self.thread.current_nodes_dict.keys():
            user_node_dict = self.thread.current_nodes_dict[TheBestNode].group_params_dict
            if NewParamsList in user_node_dict.keys() and user_node_dict[NewParamsList]:
                if not self.save_list_to_file(user_node_dict[NewParamsList],
                                              f'В {NewParamsList} добавлены параметры \n'
                                              f' нужно сохранить этот список?'):
                    event.ignore()

        msg = QMessageBox(self)
        msg.setWindowTitle("Выход")
        msg.setIcon(QMessageBox.Question)
        msg.setText("Вы уверены, что хотите закрыть приложение?")

        buttonAceptar = msg.addButton("Да", QMessageBox.YesRole)
        msg.addButton("Отменить", QMessageBox.RejectRole)  # buttonCancelar =
        msg.setDefaultButton(buttonAceptar)
        msg.exec_()

        if msg.clickedButton() == buttonAceptar:
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
        elif self.main_tab.currentWidget() == self.grafics_tab:
            print('Графики не готовы')
        else:
            print('Неизвестное состояние')


# --------------------------------------------------- кнопки управления ----------------------------------------------
def load_from_eeprom():
    node = window.thread.current_nodes_dict['КВУ_ТТС']
    if node.request_id in window.thread.adapter.id_nodes_dict.keys():
        adapter_can2 = window.thread.adapter.id_nodes_dict[node.request_id]
        print('Отправляю команду на запрос из еепром')
        answer = node.send_val(0x210201, adapter_can2, value=0x01)  # это адрес вытащить из еепром для кву ттс
        if answer:
            answer = 'Команду выполнить не удалось\n' + answer
        else:
            QMessageBox.information(window, "Успешный успех!", 'Параметры загружены из ЕЕПРОМ', QMessageBox.Ok)
            node.param_was_changed = False
            return
    else:
        answer = 'В списке адаптеров канал 250 не найден'

    QMessageBox.critical(window, "Ошибка", answer, QMessageBox.Ok)


def mpei_invert():
    m = window.thread.invertor_command('INVERT_ROTATION')
    window.log_lbl.setText(m)


def mpei_power_on():
    m = window.thread.invertor_command('POWER_ON')
    window.log_lbl.setText(m)


def mpei_power_off():
    m = window.thread.invertor_command('POWER_OFF')
    window.log_lbl.setText(m)


def mpei_reset_device():
    m = window.thread.invertor_command('RESET_DEVICE')
    window.log_lbl.setText(m)


def mpei_reset_params():
    m = window.thread.invertor_command('RESET_PARAMETERS')
    window.log_lbl.setText(m.replace('\n', ''))


# ---------------------------------------------- кнопки с диалогом ----------------------------------------------------
def mpei_calibrate():
    param_list_for_calibrate = ['FAULTS', 'DC_VOLTAGE', 'SPEED_RPM', 'FIELD_CURRENT',
                                'PHA_CURRENT', 'PHB_CURRENT', 'PHC_CURRENT']  # 'STATOR_CURRENT', 'TORQUE',
    for p_name in param_list_for_calibrate:
        wait_thread.imp_par_list.append(
            find_param(window.thread.current_nodes_dict, p_name, node_name='Инвертор_МЭИ')[0])

    wait_thread.req_delay = 50
    wait_thread.adapter = can_adapter.adapters_dict[125]
    wait_thread.id_for_read = 0x381
    wait_thread.answer_byte = 4
    wait_thread.answer_dict = {0x0A: 'Калибровка прошла успешно!',
                               0x0B: 'Калибровка не удалась',
                               0x0C: 'Настройки сохранены в ЕЕПРОМ'}

    dialog = DialogChange(label='Процесс калибровки',
                          text='Команда на калибровку отправлена',
                          table=wait_thread.imp_par_list)
    dialog.setWindowTitle('Калибровка Инвертора МЭИ')

    @pyqtSlot(list, list)
    def check_dialog_mess(st, list_of_params):
        if wait_thread.isRunning():
            dialog.change_mess(st, list_of_params)
        else:
            print('Поток калибровки остановлен')
            node = window.thread.current_nodes_dict['Инвертор_МЭИ']
            # передавать надо исключительно в первый кан
            if node.request_id in window.thread.adapter.id_nodes_dict.keys():
                adapter_can1 = window.thread.adapter.id_nodes_dict[node.request_id]
                faults = list(node.check_errors(adapter=adapter_can1))
                if not faults:
                    st.append('Ошибок во время калибровки не появилось')
                else:
                    faults.insert(0, 'Во время калибровки возникли ошибки: ')
                    st += faults
                dialog.change_mess(st)

    wait_thread.SignalOfProcess.connect(check_dialog_mess)

    s = window.thread.invertor_command('BEGIN_POSITION_SENSOR_CALIBRATION', wait_thread)
    if not s:
        wait_thread.start()
        if dialog.exec_():
            wait_thread.quit()
            wait_thread.wait()
            print('Поток калибровки остановлен')


def joystick_bind():
    if not can_adapter.isDefined:
        if not can_adapter.find_adapters():
            return
    if 250 in can_adapter.adapters_dict:
        QMessageBox.information(window, "Информация", 'Перед привязкой проверь:\n'
                                                      ' - что джойстик ВЫКЛЮЧЕН\n'
                                                      ' - высокое напряжение ВКЛЮЧЕНО',
                                QMessageBox.Ok)
        adapter = can_adapter.adapters_dict[250]

        dialog = DialogChange(text='Команда на привязку отправлена')
        dialog.setWindowTitle('Привязка джойстика')

        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.wait_time = 20  # время в секундах для включения и прописки джойстика
        wait_thread.req_delay = 250  # время в миллисекундах на опрос параметров
        wait_thread.max_err = 80  # потому что приёмник джойстика не отвечает постоянно, а только трижды
        wait_thread.adapter = adapter
        wait_thread.id_for_read = 0x18FF87A7
        wait_thread.answer_dict = {
            0: 'принята команда привязки',
            1: 'приемник переведен в режим привязки, ожидание включения пульта ДУ',
            2: 'привязка завершена',
            254: 'ошибка',
            255: 'команда недоступна'}

        bind_command = adapter.can_write(0x18FF86A5, [0] * 8)

        if not bind_command:
            wait_thread.start()
            if dialog.exec_():
                wait_thread.quit()
                wait_thread.wait()
                print('Поток остановлен')
        else:
            QMessageBox.critical(window, "Ошибка ", 'Команда привязки не отправлена\n' + bind_command, QMessageBox.Ok)
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.Ok)


def suspension_to_zero():
    param_list_for_suspension = ['SUSPENSION_HEIGHT_CUR_1', 'SUSPENSION_PRESSURE_CUR_1',
                                 'SUSPENSION_HEIGHT_CUR_2', 'SUSPENSION_PRESSURE_CUR_2',
                                 'SUSPENSION_HEIGHT_CUR_3', 'SUSPENSION_PRESSURE_CUR_3',
                                 'SUSPENSION_HEIGHT_CUR_4', 'SUSPENSION_PRESSURE_CUR_4', ]
    for p_name in param_list_for_suspension:
        wait_thread.imp_par_list.append(find_param(window.thread.current_nodes_dict, p_name)[0])

    if not can_adapter.isDefined:
        if not can_adapter.find_adapters():
            return
    if 250 in can_adapter.adapters_dict:
        QMessageBox.information(window, "Информация", 'Перед выравниванием проверь что:\n'
                                                      ' - тумблер режима подвески в положении АВТО КВУ\n'
                                                      ' - остальные тумблеры в нейтральном положении',
                                QMessageBox.Ok)
        adapter = can_adapter.adapters_dict[250]
        dialog = DialogChange(text='Команда на установку отправлена',
                              table=wait_thread.imp_par_list)
        dialog.setWindowTitle('Установка подвески v ноль')

        wait_thread.SignalOfProcess.connect(dialog.change_mess)
        wait_thread.wait_time = 20  # время в секундах для установки подвески
        wait_thread.req_delay = 50  # время в миллисекундах на опрос параметров
        wait_thread.adapter = adapter

        command_zero_suspension = adapter.can_write(0x18FF83A5, [1, 0x7D, 0x7D, 0x7D, 0x7D])
        if not command_zero_suspension:  # если передача прошла успешно
            wait_thread.start()
            if dialog.exec_():
                wait_thread.quit()
                wait_thread.wait()
                print('Поток остановлен')

        else:
            QMessageBox.critical(window, "Ошибка ", f'Команда не отправлена\n{command_zero_suspension}', QMessageBox.Ok)
            window.log_lbl.setText(command_zero_suspension.replace('\n', ''))
    else:
        QMessageBox.critical(window, "Ошибка ", 'Нет адаптера на шине 250', QMessageBox.Ok)


@pyqtSlot(str)
def set_log_lbl(s: str):
    window.log_lbl.setText(s.replace('\n', ''))


if __name__ == '__main__':
    start_time = time.perf_counter()
    app = QApplication([])
    splash = QSplashScreen()
    splash.setPixmap(QPixmap('pictures/EVO-EVIS_l.jpg'))
    splash.show()
    window = VMUMonitorApp()
    window.setWindowTitle('Electric Vehicle Information System')
    sleep_thread.SignalOfProcess.connect(window.progress_bar_fulling)

    #
    window.main_tab.currentChanged.connect(window.change_tab)
    # подключаю сигналы нажатия на окошки
    window.nodes_tree.currentItemChanged.connect(params_list_changed)
    window.errors_tree.itemPressed.connect(show_error)
    window.nodes_tree.doubleClicked.connect(window.double_click)
    window.vmu_param_table.cellDoubleClicked.connect(want_to_value_change)
    # и сигналы нажатия на кнопки
    # -----------------Инвертор---------------------------
    window.invert_btn.clicked.connect(mpei_invert)
    window.calibrate_btn.clicked.connect(mpei_calibrate)
    window.power_on_btn.clicked.connect(mpei_power_on)
    window.power_off_btn.clicked.connect(mpei_power_off)
    window.reset_device_btn.clicked.connect(mpei_reset_device)
    window.reset_param_btn.clicked.connect(mpei_reset_params)
    window.invertor_mpei_box.setEnabled(False)
    # ------------------Кнопки вспомогательные----------------
    window.joy_bind_btn.clicked.connect(joystick_bind)
    window.susp_zero_btn.clicked.connect(suspension_to_zero)
    window.load_from_eeprom_btn.clicked.connect(load_from_eeprom)
    window.susp_zero_btn.setEnabled(False)
    window.load_from_eeprom_btn.setEnabled(False)
    window.joy_bind_btn.setEnabled(False)
    # ------------------Главные кнопки-------------------------
    window.connect_btn.clicked.connect(window.connect_to_node)
    window.save_eeprom_btn.clicked.connect(save_to_eeprom)
    window.reset_faults.clicked.connect(erase_errors)
    window.compare_btn.clicked.connect(make_compare_params_list)
    window.save_to_file_btn.clicked.connect(save_to_file_pressed)
    window.log_record_btn.clicked.connect(record_log)
    window.search_btn.clicked.connect(search_param)
    # window.search_btn.hide()
    window.save_to_file_btn.setEnabled(False)
    # заполняю первый список блоков из файла - максимальное количество всего, что может быть на нижнем уровне
    try:
        with open(nodes_pickle_file, 'rb') as f:
            node_dict = pickle.load(f)
    except FileNotFoundError:
        node_dict = make_nodes_dict(fill_nodes_dict_from_yaml(nodes_yaml_file))
        with open(nodes_pickle_file, 'wb') as f:
            pickle.dump(node_dict, f)
    window.thread.current_nodes_dict = node_dict.copy()
    # показываю дерево с блоками и что ошибок нет
    # window.add_new_errors({})
    window.show_nodes_tree(list(node_dict.values()))  # ---------!!!!!!!!!! проверить, исправить на словарь!!!-----
    # если со списком блоков всё ок, показываем его в левом окошке и запускаем приложение
    if node_dict and params_list_changed():
        if can_adapter.find_adapters():
            window.connect_to_node()
        else:
            window.log_lbl.setText('Адаптер не подключен')
        window.show()  # Показываем окно
        splash.finish(window)  # Убираем заставку
        print(time.perf_counter() - start_time)
        app.exec_()  # и запускаем приложение

# реальный номер 11650178014310 считывает 56118710341001 наоборот - Антон решает
# не считывает варнинги КВУ - другой адрес
# при удалении ошибок очищать и описание их
# кнопку Сохранения в еепром-наверх
# скукоживается блок названия блока после поиска
