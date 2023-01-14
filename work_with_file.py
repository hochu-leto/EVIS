import os
import pathlib
import pickle
import time

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
par_pick_file = 'parameters.pickle'
err_file = 'errors.yaml'
err_pick_file = 'errors.pickle'
dir_path = str(pathlib.Path.cwd())
vmu_param_file = 'table_for_params_new_VMU.xlsx'
vmu_param_file = pathlib.Path(dir_path, 'Tables', vmu_param_file)
nodes_yaml_file = pathlib.Path(dir_path, 'Data', 'all_nodes.yaml')
nodes_pickle_file = pathlib.Path(dir_path, 'Data', 'all_nodes.pickle')


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


# =========================================версия для ошибок-объектов и ямл-файлов============================
# ------------------------------------- заполнение списка с ошибками----------------------------
def fill_err_list_from_yaml(file, node):
    with open(file, "r", encoding="UTF-8") as stream:
        try:
            canopen_error = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    if canopen_error is None:
        canopen_error = []
    node_err_list = [EvoError(e, node=node) for e in canopen_error]
    return node_err_list


# ------------------------------------- заполнения словаря с группами параметров -----------------------------
def fill_par_dict_from_yaml(file, node):
    with open(file, "r", encoding="UTF-8") as stream:
        try:
            canopen_params = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    if canopen_params is None:
        canopen_params = {}
    node_params_dict = {group: [Parametr(p, node=node) for p in group_params]
                        for group, group_params in canopen_params.items()}
    return node_params_dict


# ------------------------------------- заполнения словаря со всеми блоками -----------------------------
def fill_nodes_dict_from_yaml(file):
    with open(file, "r", encoding="UTF-8") as stream:
        try:
            nodes = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    node_dict = {name: EVONode(n) for name, n in nodes.items()}
    return node_dict


def get_immediate_subdirectories(a_dir):
    return [name for name in os.listdir(a_dir)
            if os.path.isdir(os.path.join(a_dir, name))]


# ------------------------------------- попытка загрузки пикл, либо сериализация ямл -------------------------------
def try_load_pickle(f, dir_name, node):
    if f == 'params':
        func = fill_par_dict_from_yaml
        file = par_file
        p_file = par_pick_file
    elif f == 'errors':
        func = fill_err_list_from_yaml
        file = err_file
        p_file = err_pick_file
    else:
        return False
    try:
        with open(pathlib.Path(dir_name, p_file), 'rb') as f:
            dict_or_list = pickle.load(f)
    except FileNotFoundError:
        try:
            dict_or_list = func(pathlib.Path(dir_name, file), node)
            with open(pathlib.Path(dir_name, p_file), 'wb') as f:
                pickle.dump(dict_or_list, f)
        except FileNotFoundError:
            print(f'В папке {dir_name} нет списка {f} для блока ', end=' ')
            return False
    return dict_or_list


# ------------------------------------- сборка блока по объекту -----------------------------
def fill_node(node: EVONode):
    data_dir = pathlib.Path(os.getcwd(), 'Data')
    for directory in get_immediate_subdirectories(data_dir):
        if directory in node.name:
            node_dir = pathlib.Path(data_dir, directory)
            param_dir = err_dir = Default
            t_dir = pathlib.Path(node_dir, Default)
            node.group_params_dict = try_load_pickle('params', t_dir, node)
            node.errors_list = try_load_pickle('errors', t_dir, node)
            if node.name == 'КВУ_ТТС':
                node.warnings_list = node.errors_list.copy()
            if not node.group_params_dict or not node.errors_list:
                return False
            f_v = node.firmware_version
            if f_v:     # версия может быть строкой, типа КВУ 1.2.0
                version_list = get_immediate_subdirectories(node_dir)
                if version_list:
                    min_vers = get_nearest_lower_value(version_list, str(f_v))
                    if min_vers:
                        t_dir = pathlib.Path(node_dir, str(min_vers))
                        params_dict = try_load_pickle('params', t_dir, node)
                        if params_dict:
                            param_dir = min_vers
                            node.group_params_dict = params_dict.copy()
                        errors_list = try_load_pickle('errors', t_dir, node)
                        if errors_list:
                            err_dir = min_vers
                            node.errors_list = errors_list.copy()
                            if node.name == 'КВУ_ТТС':
                                node.warnings_list = errors_list.copy()

            for group in node.group_params_dict.values():
                for param in group:
                    param.node = node
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
            final_nodes_dict[name] = full_node
    # надо добавить избранное, если его нет
    if TheBestNode not in final_nodes_dict.keys():
        # и если в избранном нет параметров - добавить Новый список
        if not node_dict[TheBestNode].group_params_dict:
            node_dict[TheBestNode].group_params_dict[NewParamsList] = []
        final_nodes_dict[TheBestNode] = node_dict[TheBestNode]

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


def save_p_dict_to_file(par_dict: dict):
    data_dir = pathlib.Path(os.getcwd(), 'Data')
    file_name = pathlib.Path(data_dir, TheBestNode, Default, par_pick_file)
    try:
        with open(file_name, 'wb') as f:
            pickle.dump(par_dict, f)
        if os.path.isfile(nodes_pickle_file):
            os.remove(nodes_pickle_file)
        return True
    except PermissionError:
        return False


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
