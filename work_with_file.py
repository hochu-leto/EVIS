import datetime
import struct
from pprint import pprint

import pandas
from PyQt5.QtWidgets import QMessageBox

from helper import NewParamsList
from EVONode import EVONode
from Parametr import Parametr

value_type_dict = {'UNSIGNED16': 0x2B,
                   'SIGNED16': 0x2B,
                   'UNSIGNED32': 0x23,
                   'SIGNED32': 0x23,
                   'UNSIGNED8': 0x2F,
                   'SIGNED8': 0x2F,
                   'FLOAT': 0x23}


def fill_bookmarks_list(file_name):
    need_fields = {'name', 'address', 'type'}
    file = pandas.ExcelFile(file_name)
    bookmark_dict = {}

    for sheet_name in file.sheet_names:
        sheet = file.parse(sheet_name=sheet_name)
        headers = list(sheet.columns.values)
        if set(need_fields).issubset(headers):
            sheet_params_list = sheet.to_dict(orient='records')
            bookmark_dict[sheet_name] = sheet_params_list

    return bookmark_dict


def fill_node_list(file_name):
    need_fields = {'name', 'address', 'type'}
    file = pandas.ExcelFile(file_name)
    bookmark_dict = {}
    if 'nodes' not in file.sheet_names:
        QMessageBox.critical(None, "Ошибка ", 'Корявый файл с параметрами', QMessageBox.Ok)
        return
    # sheet "nodes" is founded
    for sheet_name in file.sheet_names:  # пробегаюсь по всем листам документа
        sheet = file.parse(sheet_name=sheet_name)
        headers = list(sheet.columns.values)
        if set(need_fields).issubset(headers):  # если в заголовках есть все нужные поля
            sheet_params_list = sheet.to_dict(orient='records')  # то запихиваю весь этот лист со всеми
            bookmark_dict[sheet_name] = sheet_params_list  # строками в словарь,где ключ - название страницы

    node_sheet = file.parse(sheet_name='nodes')
    node_list = node_sheet.to_dict(orient='records')  # парсим лист "nodes"
    for node in node_list:
        node_name = node['name']
        node_params_list = {}
        for params_list in bookmark_dict.keys():  # бегу по словарю со списками параметров
            prev_group_name = ''
            p_list = []
            if node_name in params_list:
                for param in bookmark_dict[params_list]:
                    if str(param['type']) != 'nan':
                        param['type'] = param['type'].strip()
                    if str(param['name']) != 'nan':
                        if 'group ' in param['name']:
                            node_params_list[prev_group_name] = p_list.copy()
                            p_list = []
                            prev_group_name = param['name'].replace('group ', '')
                        else:
                            #  получается, что здесь я не проверяю наличие нужных поле у параметра
                            #  это происходит только при заполнении списка vmu_params_list
                            #  здесь нужно в список добавлять объект Параметр с полями и методами
                            p_list.append(param)
                node_params_list[prev_group_name] = p_list.copy()
                del node_params_list['']
        if node_params_list:
            node['params_list'] = node_params_list.copy()
        node['req_id'] = check_id(node['req_id'])
        node['ans_id'] = check_id(node['ans_id'])

    return node_list


def full_node_list(file_name):
    need_fields = {'name', 'address', 'type'}
    file = pandas.ExcelFile(file_name)
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

    err_sheet = file.parse(sheet_name='errors')
    err_list = err_sheet.to_dict(orient='records')  # парсим лист "errors"
    err_dict = {}
    prev_node_name = ''
    e_list = []
    for er in err_list:
        if 'node' in er['value_error']:
            err_dict[prev_node_name] = e_list.copy()
            e_list = []
            prev_node_name = er['value_error'].replace('node ', '')
        else:
            e_list.append(er)
    err_dict[prev_node_name] = e_list.copy()
    del err_dict['']
    # здесь я имею словарь с ошибками где ключ - имя блока, значение - словарь с ошибками
    nodes_list = []
    node_sheet = file.parse(sheet_name='node')
    node_list = node_sheet.to_dict(orient='records')  # парсим лист "node"
    for node in node_list:
        node_name = node['name']
        node_params_list = {}
        ev_node = EVONode(node, err_dict[node['name']]) if node['name'] in err_dict.keys() else EVONode(node)
        for params_list in bookmark_dict.keys():  # бегу по словарю со списками параметров
            prev_group_name = ''
            p_list = []
            if node_name in params_list:
                for param in bookmark_dict[params_list]:
                    if str(param['type']) != 'nan':
                        param['type'] = param['type'].strip()
                    if str(param['name']) != 'nan':
                        if 'group ' in param['name']:
                            node_params_list[prev_group_name] = p_list.copy()
                            p_list = []
                            prev_group_name = param['name'].replace('group ', '')
                        else:
                            p = Parametr(param, ev_node)
                            p_list.append(p)
                node_params_list[prev_group_name] = p_list.copy()
                del node_params_list['']

        ev_node.group_params_dict = node_params_list.copy() if node_params_list else {NewParamsList: []}
        nodes_list.append(ev_node)

    return nodes_list


def check_id(string: str):
    if str(string) == 'nan':
        return 'nan'
    if '0x' in string:
        return int(string.replace('0x', ''), 16)
    elif '0b' in string:
        return int(string.replace('0b', ''), 2)
    else:
        return int(string)


def fill_vmu_list(vmu_params_list):
    exit_list = []
    for par in vmu_params_list:
        if str(par['name']) != 'nan':
            if str(par['address']) != 'nan':
                if isinstance(par['address'], str):
                    if '0x' in par['address']:
                        par['address'] = par['address'].rsplit('x')[1]
                        par['address'] = int(par['address'], 16)
                    elif '0b' in par['address']:
                        par['address'] = par['address'].rsplit('b')[1]
                        par['address'] = int(par['address'], 2)
                    else:
                        par['address'] = int(par['address'])
                if str(par['scale']) == 'nan' or par['scale'] == 0:
                    par['scale'] = 1
                if 'scaleB' not in par.keys() or str(par['scaleB']) == 'nan':
                    par['scaleB'] = 0

                if 'period' not in par.keys() or str(par['period']) == 'nan' or par['period'] <= 0:
                    par['period'] = 1
                elif par['period'] > 1000:
                    par['period'] = 1000

                exit_list.append(par)
    return exit_list


def make_vmu_error_dict(file_name):
    excel_data_df = pandas.read_excel(file_name)
    vmu_er_list = excel_data_df.to_dict(orient='records')
    ex_dict = {}
    for par in vmu_er_list:
        if str(par['Code']) != 'nan':
            ex_dict[par['Code']] = par['Description']
    return ex_dict


def feel_req_list(protocol: str, p_list: list):
    req_list = []
    for par in p_list:
        if par['type'] in value_type_dict.keys():
            value_type = value_type_dict[par['type']]
        else:
            value_type = 0x2B
        address = int(par['address'])
        # print('address =   ', address)
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        if protocol == 'CANOpen':
            data = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
        elif protocol == 'MODBUS':
            data = [0, 0, 0, 0, sub_index, LSB, value_type, 0x03]
        else:
            data = bytearray([0, 0, 0, 0, 0, 0, 0, 0])
        # pprint(data)
        req_list.append(data)
    return req_list


def adding_to_csv_file(name_or_value: str, vmu_params_list: list, recording_file_name: str):
    if not recording_file_name:
        return
    data = []
    data_string = []
    for par in vmu_params_list:
        data_string.append(par[name_or_value])
    dt = datetime.datetime.now()
    dt = dt.strftime("%H:%M:%S.%f")
    if name_or_value == 'name':
        dt = 'time'
    data_string.append(dt)
    data.append(data_string)
    df = pandas.DataFrame(data)
    # df.to_csv(recording_file_name,
    #           mode='a',
    #           header=False,
    #           index=False,
    #           encoding='windows-1251')

