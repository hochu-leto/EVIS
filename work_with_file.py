import os
import pathlib
from pprint import pprint

import pandas as pd
import yaml
from PyQt5.QtWidgets import QMessageBox
from pandas import ExcelWriter

from EVOErrors import EvoError
from helper import NewParamsList, get_nearest_lower_value
from EVONode import EVONode
from Parametr import Parametr
from helper import empty_par, TheBestNode

value_type_dict = {'UNSIGNED16': 0x2B,
                   'SIGNED16': 0x2B,
                   'UNSIGNED32': 0x23,
                   'SIGNED32': 0x23,
                   'UNSIGNED8': 0x2F,
                   'SIGNED8': 0x2F,
                   'FLOAT': 0x23}

need_fields = {'name', 'address', 'type'}
Default = 'Default'
par_file = 'parameters.yaml'
err_file = 'errors.yaml'


# ------------------------------------- заполнение словаря для сравнения----------------------------
# можно несколько блоков в одном файле
def fill_sheet_dict(file_name):
    #  пока принимает только эксель
    file = pd.ExcelFile(file_name)
    sheets_dict = {}

    for sheet_name in file.sheet_names:
        sheet = file.parse(sheet_name=sheet_name)
        headers = list(sheet.columns.values)
        node_params_dict = {}
        if set(need_fields).issubset(headers):
            sheet_params_dict = sheet.to_dict(orient='records')
            prev_group_name = ''
            p_list = []

            for param in sheet_params_dict:
                if str(param['name']) != 'nan':
                    if 'group ' in param['name']:
                        node_params_dict[prev_group_name] = p_list.copy()
                        p_list.clear()
                        prev_group_name = param['name'].replace('group ', '')
                    else:
                        #  делает словарь только с имя-значение. скорее нужно делать полный параметр
                        p_list.append(Parametr(param))
                node_params_dict[prev_group_name] = p_list.copy()

            del node_params_dict['']
            if node_params_dict:
                sheets_dict[sheet_name] = node_params_dict
    return sheets_dict


# ------------------------------------- заполнение основного словаря из файла----------------------------
# работающая сейчас версия с экселем
def full_node_list(file_name):
    file = pd.ExcelFile(file_name)

    def fill_er_list(sheets_name: str):
        err_sheet = file.parse(sheet_name=sheets_name)
        err_list = err_sheet.to_dict(orient='records')  # парим лист "errors"
        error_dict = {}
        prev_node_name = ''
        e_list = []
        for er in err_list:
            if isinstance(er['value_error'], str) and 'node' in er['value_error']:
                error_dict[prev_node_name] = e_list.copy()
                e_list = []
                prev_node_name = er['value_error'].replace('node ', '')
            else:
                e_list.append(er)
        error_dict[prev_node_name] = e_list.copy()
        del error_dict['']
        return error_dict

    bookmark_dict = {}
    if not {'node', 'errors'}.issubset(file.sheet_names):
        QMessageBox.critical(None, "Ошибка ", 'Корявый файл с параметрами', QMessageBox.Ok)
        return
    # sheet "nodes" is founded
    for sheet_name in file.sheet_names:  # пробегаюсь по всем листам документа
        sheet = file.parse(sheet_name=sheet_name)
        headers = list(sheet.columns.values)
        if set(need_fields).issubset(headers):  # если в заголовках есть все нужные поля
            sheet_params_list = sheet.to_dict(orient='records')  # то запихиваю весь этот лист со всеми
            bookmark_dict[sheet_name] = sheet_params_list  # строками в словарь,где ключ - название страницы
    # здесь я имею словарь ключ - имя блока , значение - словарь с параметрами ( не по группам)

    err_dict = fill_er_list('errors')
    # здесь я имею словарь с ошибками где ключ - имя блока, значение - словарь с ошибками

    wr_dict = fill_er_list('warnings')
    # здесь я имею словарь с ошибками где ключ - имя блока, значение - словарь с предупреждениями

    node_sheet = file.parse(sheet_name='node')
    node_list = node_sheet.to_dict(orient='records')  # парсим лист "node"
    node_dict = {}
    for node in node_list:
        er_d = []
        wr_d = []
        if node['name'] in err_dict.keys():
            er_d = err_dict[node['name']].copy()

        if node['name'] in wr_dict.keys():
            wr_d = wr_dict[node['name']].copy()

        ev_node = EVONode(node, er_d, wr_d)
        node_dict[node['name']] = ev_node
    # не совсем вдуплил, но здесь у меня есть словарь, где ключи - названия блоков, а значения - объекты блоков

    # ну и финалочка - раскидываю по блокам словари, где ключи - названия групп параметров,
    # а значения - списки объектов параметров
    nodes_list = []
    for node_name, ev_node in node_dict.items():
        node_params_dict = {}
        for params_list in bookmark_dict.keys():  # бегу по словарю со списками параметров
            prev_group_name = ''
            p_list = []
            if node_name in params_list:
                for param in bookmark_dict[params_list]:
                    if str(param['name']) != 'nan':
                        if 'group ' in param['name']:
                            node_params_dict[prev_group_name] = p_list.copy()
                            p_list = []
                            prev_group_name = param['name'].replace('group ', '')
                        else:
                            if '#' in param['name']:
                                # это для Избранного, где названия параметров через # -
                                # там нужно узнать с какого блока этот параметр возможно, в будущем,
                                # я перейду на постгрес и там будет ещё одна промежуточная таблица,
                                # чтоб не заморачиваться с названиями
                                nod_name = param['name'].split('#')[1]
                                p = Parametr(param, node_dict[nod_name])
                            else:
                                p = Parametr(param, ev_node)
                            p_list.append(p)
                node_params_dict[prev_group_name] = p_list.copy()
                del node_params_dict['']

        ev_node.group_params_dict = node_params_dict.copy() if node_params_dict else {NewParamsList: []}
        nodes_list.append(ev_node)

    return nodes_list


# =========================================версия для ошибок-объектов============================
# ------------------------------------- заполнение словаря с ошибками----------------------------
def fill_error_dict(file, sheet_name: str, critical=True):
    err_sheet = file.parse(sheet_name=sheet_name)
    err_list = err_sheet.to_dict(orient='records')  # парсим лист "errors"
    err_dict = {}
    prev_node_name = ''
    e_list = []
    for er in err_list:
        if isinstance(er['value_error'], str) and 'node' in er['value_error']:
            err_dict[prev_node_name] = e_list.copy()
            e_list = []
            prev_node_name = er['value_error'].replace('node ', '')
        else:
            e = EvoError(er)
            e.critical = critical
            e_list.append(e)
    err_dict[prev_node_name] = e_list.copy()
    del err_dict['']
    return err_dict


# ------------------------------------- заполнения словаря с параметрами -----------------------------
def fill_par_dict(file):
    bookmark_dict = {}
    node_params_dict = {}
    for sheet_name in file.sheet_names:  # пробегаюсь по всем листам документа
        sheet = file.parse(sheet_name=sheet_name)
        headers = list(sheet.columns.values)
        if set(need_fields).issubset(headers):  # если в заголовках есть все нужные поля
            sheet_params_list = sheet.to_dict(orient='records')  # то запихиваю весь этот лист со всеми
            bookmark_dict[sheet_name.split()[0]] = sheet_params_list  # строками в словарь,где ключ - название страницы
            prev_group_name = ''
            p_list = []
            for param in sheet_params_list:
                if 'group ' in param['name']:
                    node_params_dict[prev_group_name] = p_list.copy()
                    p_list = []
                    prev_group_name = param['name'].replace('group ', '')
                else:
                    p = Parametr(param)
                    p_list.append(p)
            node_params_dict[prev_group_name] = p_list.copy()
            del node_params_dict['']
    return node_params_dict


# ------------------------------------- финальное заполнения словаря с блоками -----------------------------
def make_node_list(file_name):
    file = pd.ExcelFile(file_name)
    # начинаю с проверки что есть лист с ошибками и лист с блоками
    if not {'node', 'errors'}.issubset(file.sheet_names):
        QMessageBox.critical(None, "Ошибка ", 'Корявый файл с параметрами', QMessageBox.Ok)
        return
    # парсим лист "node"
    node_sheet = file.parse(sheet_name='node')
    node_list = node_sheet.to_dict(orient='records')
    ev_node_list = []
    node_dict = {}
    for node in node_list:
        ev_node_list.append(EVONode(node))
        node_dict[node['name']] = EVONode(node)
    # здесь я имею словарь ключ - имя блока , значение - словарь с параметрами ( не по группам)

    # with open(r'Data/all_nodes.yaml', 'w', encoding='windows-1251') as file:
    #     documents = yaml.dump({n['name']: n for n in node_list}, file, allow_unicode=True, encoding="UTF8")

    err_dict = fill_error_dict(file, 'errors')
    # здесь я имею словарь с ошибками где ключ - имя блока, значение - словарь с ошибками

    wr_dict = fill_error_dict(file, 'warnings', False)
    # здесь я имею словарь с ошибками где ключ - имя блока, значение - словарь с предупреждениями
    par_dict = fill_par_dict(file)
    # ну и финалочка - раскидываю по блокам словари, где ключи - названия групп параметров,
    # а значения - списки объектов параметров
    nodes_list = []
    for node_name, ev_node in node_dict.items():
        node_params_dict = {}
        if node_name in err_dict.keys():
            ev_node.errors_list = err_dict[node_name]

        if node_name in wr_dict.keys():
            ev_node.errors_list = wr_dict[node_name]

        if node_name in par_dict.keys():
            for group in par_dict[node_name].values():
                for param in group:
                    if node_name == TheBestNode:    # Избранное надо раскидывать - параметры м/б из разных блоков
                        param.check_node(node_dict)
                    else:
                        param.node = ev_node
            ev_node.group_params_dict = par_dict[node_name]

    return node_dict
# =================================================================================================================


# =========================================версия для ошибок-объектов и ямл-файлов============================
# ------------------------------------- заполнение списка с ошибками----------------------------
def fill_err_list_from_yaml(file):
    with open(file, "r", encoding="windows-1251") as stream:
        try:
            canopen_error = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    node_err_list = [EvoError(e) for e in canopen_error]
    return node_err_list


# ------------------------------------- заполнения словаря с группами параметров -----------------------------
def fill_par_dict_from_yaml(file):
    with open(file, "r", encoding="windows-1251") as stream:
        try:
            canopen_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    node_params_dict = {group: [Parametr(p) for p in group_params]
                        for group, group_params in canopen_params.items()}
    return node_params_dict


# ------------------------------------- заполнения словаря со всеми блоками -----------------------------
def fill_nodes_dict_from_yaml(file):
    with open(file, "r", encoding="windows-1251") as stream:
        try:
            nodes = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    node_dict = {name: EVONode(n) for name, n in nodes.items()}
    return node_dict


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


# ------------------------------------- сборка блока по объекту -----------------------------
def fill_node(node: EVONode):
    data_dir = pathlib.Path(os.getcwd(), 'Data')
    for directory in get_immediate_subdirectories(data_dir):
        if directory in node.name:

            node_dir = pathlib.Path(data_dir, directory)
            param_dir = err_dir = Default
            try:
                group_params_dict = fill_par_dict_from_yaml(pathlib.Path(node_dir, param_dir, par_file))
            except FileNotFoundError:
                print(f'В папке {Default} нет списка параметров для блока {node.name}. Нужны параметры по-умолчанию')
                return False

            try:
                node.errors_list = fill_err_list_from_yaml(pathlib.Path(node_dir, err_dir, err_file))
            except FileNotFoundError:
                print(f'В папке {Default} нет списка ошибок для блока {node.name}. Нужны ошибки по-умолчанию')
                return False

            f_v = node.firmware_version

            if f_v and f_v != '---':
                version_list = [int(v) for v in get_immediate_subdirectories(node_dir) if v.isdigit()]
                if version_list:
                    min_vers = get_nearest_lower_value(version_list, f_v)
                    if min_vers:
                        try:
                            group_params_dict = fill_par_dict_from_yaml(pathlib.Path(node_dir, str(min_vers), par_file))
                            param_dir = min_vers
                        except FileNotFoundError:
                            print(f'В папке {min_vers} нет списка параметров для блока {node.name}')

                        try:
                            node.errors_list = fill_err_list_from_yaml(pathlib.Path(node_dir, str(min_vers), err_file))
                            err_dir = min_vers
                        except FileNotFoundError:
                            print(f'В папке {min_vers} нет списка ошибок для блока {node.name}.')

            for group in group_params_dict.values():
                for param in group:
                    param.node = node
            node.group_params_dict = group_params_dict
            print(f'для блока {node.name} с версией ПО {node.firmware_version} '
                  f'применяю параметры из папки {param_dir} и ошибки из папки {err_dir}')
            return node
    print(f'для блока {node.name} нет папки с параметрами')
    return False


# ------------------------------------- финальное заполнения словаря с блоками -----------------------------
def make_nodes_dict(node_dict):

    final_nodes_dict = {}
    for name, node in node_dict.items():
        full_node = fill_node(node)
        if full_node:
            if name == TheBestNode:
                full_node.group_params_dict = {group_name: [param.check_node(node_dict) for param in group_params]
                                               for group_name, group_params in full_node.group_params_dict.items()}
            final_nodes_dict[name] = full_node
    return final_nodes_dict

# =============================================================================================================


def save_params_dict_to_file(param_d: dict, file_name: str, sheet_name=None):
    if sheet_name is None:
        sheet_name = TheBestNode
    all_params_list = []
    param_dict = param_d.copy()
    for group_name, param_list in param_dict.items():
        par = empty_par.copy()
        par['name'] = f'group {group_name}'
        all_params_list.append(par)
        for param in param_list:
            all_params_list.append(param.to_dict().copy())

    df = pd.DataFrame(all_params_list, columns=empty_par.keys())
    if os.path.exists(file_name):
        try:
            ex_wr = ExcelWriter(file_name, mode="a", if_sheet_exists='overlay')
        except PermissionError:
            return False
    else:
        ex_wr = ExcelWriter(file_name, mode="w")

    with ex_wr as writer:
        df.to_excel(writer, index=False, sheet_name=sheet_name)
    return True


def fill_compare_values(node: EVONode, dict_for_compare: dict):
    all_compare_params = {}
    for group in dict_for_compare.values():
        for par in group.copy():
            all_compare_params[par.address] = par
    all_current_params = []
    for group in node.group_params_dict.values():
        for p in group:
            all_current_params.append(p)

    for cur_p in all_current_params:
        if cur_p.address in all_compare_params.keys():
            compare_par = all_compare_params[cur_p.address]
            cur_p.value_compare = compare_par.value_string if compare_par.value_string else float(compare_par.value)
            # del all_compare_params[cur_p.address]
    node.has_compare_params = True
