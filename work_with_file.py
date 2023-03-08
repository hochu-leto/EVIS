import datetime
import os
import pathlib
import pickle

import pandas as pd
import yaml

from EVOErrors import EvoError
from helper import NewParamsList, get_nearest_lower_value
from EVONode import EVONode
from EVOParametr import Parametr
from helper import TheBestNode

value_type_dict = {'UNSIGNED16': 0x2B,
                   'SIGNED16': 0x2B,
                   'UNSIGNED32': 0x23,
                   'SIGNED32': 0x23,
                   'UNSIGNED8': 0x2F,
                   'SIGNED8': 0x2F,
                   'FLOAT': 0x23}

need_fields = {'name', 'address', 'type'}
WORK_DIR = str(pathlib.Path.cwd())
SETTINGS_DIR = pathlib.Path(WORK_DIR, 'ECU_Settings')
DEFAULT_DIR = 'Default'
PARAMETERS_YAML_FILE = 'parameters.yaml'
USER_PARAMETERS_FILE = 'user_parameters.yaml'
PARAMETERS_PICKLE_FILE = 'parameters.pickle'
ERRORS_YAML_FILE = 'errors.yaml'
ERRORS_PICKLE_FILE = 'errors.pickle'
NODES_YAML_FILE = pathlib.Path(WORK_DIR, 'Data', 'all_nodes.yaml')
NODES_PICKLE_FILE = pathlib.Path(WORK_DIR, 'Data', 'all_nodes.pickle')


def save_diff(diff, file_name, description=''):
    now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    node_yaml_dict = dict(
        date_time=now,
        description='Разница между текущими параметрами из блока и настройками из файла перед сохранением настроек в '
                    'блок ' + description,
        difference={p.name: dict(current_value=p.value,
                                 value_from_file=p.value_compare) for p in diff})

    with open(file_name, 'w', encoding='UTF-8') as file:
        yaml.dump(node_yaml_dict, file,
                  default_flow_style=False,
                  sort_keys=False,
                  allow_unicode=True)


# ===================================== заполнение словаря для сравнения ====================================
# ============== теоретически можно несколько блоков в одном файле, но пока не используется =================
# ------------------------------------- для старых файлов из экселя -----------------------------------------

def fill_sheet_dict(file_name):
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
                        p = Parametr(param)
                        if isinstance(param['value'], str):
                            p.value_string = param['value']
                        p_list.append(p)
                node_params_dict[prev_group_name] = p_list.copy()

            del node_params_dict['']
            if node_params_dict:
                sheets_dict[sheet_name] = node_params_dict
    return sheets_dict


# ------------------------------------------- для новых файлов настроек из ямл -------------------------------------
def fill_yaml_dict(file_name):
    with open(file_name, "r", encoding="UTF-8") as stream:
        try:
            nodes_list = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
            return
    node_dict = {}

    if 'device' in nodes_list.keys():
        node = nodes_list['device']
        node_dict[node['name']] = param_dict(node['parameters'])
    elif 'devices' in nodes_list.keys():
        # а вот сюда можно запихнуть всю машину с настройками всех блоков
        for node in nodes_list['devices'].values():
            node_dict[node['name']] = param_dict(node['parameters'])
    return node_dict


def param_dict(params: dict):
    return {name_group: [Parametr(p) for p in group] for name_group, group in params.items()}


# ========== первоначальная загрузка параметров, ошибок и блоков - версия для ошибок-объектов и ямл-файлов ===========
# ------------------------------------- заполнение списка с ошибками -----------------------------------------
def fill_err_list_from_yaml(file, node):
    with open(file, "r", encoding="UTF-8") as stream:
        try:
            canopen_error = yaml.safe_load(stream) or []
        except yaml.YAMLError as exc:
            print(exc)
    node_err_list = [EvoError(e, node=node) for e in canopen_error]
    return node_err_list


# ------------------------------------- заполнения словаря с группами параметров -----------------------------
def fill_par_dict_from_yaml(file, node, user_params_file=None):
    try:
        with open(user_params_file, "r", encoding="UTF-8") as stream:
            try:
                user_params_list = yaml.safe_load(stream) or []
            except yaml.YAMLError as exc:
                print(exc)
    except FileNotFoundError:
        user_params_list = []
        print('Нет файла с пользовательскими настройками параметров, загружаю стандартные')

    with open(file, "r", encoding="UTF-8") as stream:
        try:
            canopen_params = yaml.safe_load(stream) or {}
        except yaml.YAMLError as exc:
            print(exc)

    node_params_dict = {}
    for group, group_params in canopen_params.items():
        param_list = []
        for p in group_params:
            par = p.copy()
            for user_p in user_params_list:
                print(p['name'].strip(), user_p['name'].strip(), p['name'].strip() == user_p['name'].strip())
                print(type(p), type(user_p))
                if p['name'].strip() == user_p['name'].strip():
                    par = user_p.copy()
                    user_params_list.remove(user_p)
                    break
            param_list.append(Parametr(par.copy(), node=node))
        node_params_dict[group] = param_list.copy()
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
def try_load_pickle_parameters(dir_name, node, user_file=None):
    try:
        with open(pathlib.Path(dir_name, PARAMETERS_PICKLE_FILE), 'rb') as f:
            params_dict = pickle.load(f)
    except FileNotFoundError:
        try:
            params_dict = fill_par_dict_from_yaml(pathlib.Path(dir_name, PARAMETERS_YAML_FILE), node, user_file)
            with open(pathlib.Path(dir_name, PARAMETERS_PICKLE_FILE), 'wb') as f:
                pickle.dump(params_dict, f)
        except FileNotFoundError:
            print(f'В папке {dir_name} нет списка параметров для блока ')
            return False
    return params_dict


def try_load_pickle_errors(dir_name, node):
    try:
        with open(pathlib.Path(dir_name, ERRORS_PICKLE_FILE), 'rb') as f:
            err_list = pickle.load(f)
    except FileNotFoundError:
        try:
            err_list = fill_err_list_from_yaml(pathlib.Path(dir_name, ERRORS_YAML_FILE), node)
            with open(pathlib.Path(dir_name, ERRORS_PICKLE_FILE), 'wb') as f:
                pickle.dump(err_list, f)
        except FileNotFoundError:
            print(f'В папке {dir_name} нет списка ошибок для блока ', end=' ')
            return False
    return err_list


# ------------------------------------- сборка блока по объекту -----------------------------
def fill_node(node: EVONode):
    data_dir = pathlib.Path(os.getcwd(), 'Data')
    for directory in get_immediate_subdirectories(data_dir):
        if directory in node.name:
            node_dir = pathlib.Path(data_dir, directory)
            param_dir = err_dir = DEFAULT_DIR
            t_dir = pathlib.Path(node_dir, DEFAULT_DIR)
            user_par_file = pathlib.Path(node_dir, USER_PARAMETERS_FILE)
            node.group_params_dict = try_load_pickle_parameters(t_dir, node, user_par_file)
            node.errors_list = try_load_pickle_errors(t_dir, node)
            if not node.group_params_dict or not node.errors_list:
                return False
            f_v = node.firmware_version
            if f_v:  # версия может быть строкой, типа КВУ 1.2.0
                version_list = get_immediate_subdirectories(node_dir)
                if version_list:
                    min_vers = get_nearest_lower_value(version_list, str(f_v))
                    if min_vers:
                        t_dir = pathlib.Path(node_dir, str(min_vers))
                        params_dict = try_load_pickle_parameters(t_dir, node, user_par_file)
                        if params_dict:
                            param_dir = min_vers
                            node.group_params_dict = params_dict.copy()
                        errors_list = try_load_pickle_errors(t_dir, node)
                        if errors_list:
                            err_dir = min_vers
                            node.errors_list = errors_list.copy()
                            if node.name == 'КВУ_ТТС':
                                node.warnings_list = errors_list.copy()

            for group in node.group_params_dict.values():
                for param in group:  # только это не работает для избранного
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

    node = final_nodes_dict[TheBestNode] = node_dict[TheBestNode]
    if node.group_params_dict:
        for group in node.group_params_dict.values():
            for param in group:
                node_name_from_param_name = param.name.split('#')[1]
                try:
                    n = node_dict[node_name_from_param_name]
                    param.node = n
                except KeyError:
                    print(f'Блок {node_name_from_param_name} в списке блоков не найден')
                    param.period = 1000
                    param.value_string = 'Блок не определён'
    else:
        # и если в избранном нет параметров - добавить Новый список
        node.group_params_dict[NewParamsList] = []

    return final_nodes_dict


# ============================== сохранение Избранного в ямл ===============================================
def save_p_dict_to_yaml_file(node: EVONode):
    data_dir = pathlib.Path(os.getcwd(), 'Data')
    s_num = node.serial_number if node.serial_number else DEFAULT_DIR
    file_name = pathlib.Path(data_dir, str(node.name), str(s_num), PARAMETERS_YAML_FILE)
    pickle_params_file = pathlib.Path(data_dir, str(node.name), str(s_num), PARAMETERS_PICKLE_FILE)
    try:
        with open(file_name, 'w', encoding='UTF-8') as file:
            yaml.dump(node.groups_to_dict(), file,
                      default_flow_style=False,
                      sort_keys=False,
                      allow_unicode=True)
        if os.path.isfile(NODES_PICKLE_FILE):
            os.remove(NODES_PICKLE_FILE)
        if os.path.isfile(pickle_params_file):
            os.remove(pickle_params_file)
        return True
    except PermissionError:
        return False


def fill_compare_values(node: EVONode, dict_for_compare: dict):
    all_compare_params = {}
    for group in dict_for_compare.values():
        for par in group.copy():
            all_compare_params[par.index << 8 + par.sub_index] = par
    all_current_params = []
    for group in node.group_params_dict.values():
        for p in group:
            all_current_params.append(p)

    for cur_p in all_current_params:
        adr = cur_p.index << 8 + cur_p.sub_index
        if adr in all_compare_params.keys():
            compare_par = all_compare_params[adr]
            cur_p.value_compare = compare_par.value
    node.has_compare_params = True


# ============================== добавление пользовательского параметра в ямл ========================================
def add_parametr_to_yaml_file(parametr: Parametr):
    data_dir = pathlib.Path(os.getcwd(), 'Data')
    node_name = parametr.node.name if '#' not in parametr.name else TheBestNode
    node_dir = TheBestNode
    dirs_list = get_immediate_subdirectories(data_dir)

    for node_dir in dirs_list:
        if node_dir in node_name:
            break

    file_name = pathlib.Path(data_dir, node_dir, USER_PARAMETERS_FILE)
    try:
        with open(file_name, 'r', encoding='UTF-8') as file:
            try:
                params_list = yaml.safe_load(file) or []
            except yaml.YAMLError as exc:
                print(exc)
    except FileNotFoundError:
        params_list = []

    if params_list:
        new_param_list = [param for param in params_list.copy() if param['name'] != parametr.name]
        new_param_list.append(parametr.to_dict())
    else:
        new_param_list = [parametr.to_dict()]

    with open(file_name, 'w', encoding='UTF-8') as file:
        yaml.dump(new_param_list, file,
                  default_flow_style=False,
                  sort_keys=False,
                  allow_unicode=True)

    delete_node_parameters_pickle(node_directory=pathlib.Path(data_dir, node_dir))
    return True


def delete_node_parameters_pickle(node_directory):
    result = [os.path.join(dp, f) for dp, dn, filenames in os.walk(str(node_directory))
              for f in filenames if f == PARAMETERS_PICKLE_FILE]
    for file in result:
        os.remove(file)

    if os.path.isfile(NODES_PICKLE_FILE):
        os.remove(NODES_PICKLE_FILE)
