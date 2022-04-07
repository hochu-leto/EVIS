import datetime
from pprint import pprint

import pandas
from PyQt5.QtWidgets import QMessageBox


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
    node_sheet = file.parse(sheet_name='nodes')
    node_list = node_sheet.to_dict(orient='records')
    for sheet_name in file.sheet_names:
        sheet = file.parse(sheet_name=sheet_name)
        headers = list(sheet.columns.values)
        if set(need_fields).issubset(headers):
            sheet_params_list = sheet.to_dict(orient='records')
            bookmark_dict[sheet_name] = sheet_params_list

    for node in node_list:
        node_name = node['name']
        node_params_list = {}
        for params_list in bookmark_dict.keys():
            if node_name in params_list:
                node_params_list[params_list.replace(node_name + ' ', '')] = bookmark_dict[params_list]
        if node_params_list:
            node['params_list'] = node_params_list
        node['req_id'] = check_id(node['req_id'])
        node['ans_id'] = check_id(node['ans_id'])

    return node_list


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
                if str(par['scale']) == 'nan':
                    par['scale'] = 1
                if str(par['scaleB']) == 'nan':
                    par['scaleB'] = 0
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


def feel_req_list(p_list: list):
    req_list = []
    for par in p_list:
        address = par['address']
        MSB = ((address & 0xFF0000) >> 16)
        LSB = ((address & 0xFF00) >> 8)
        sub_index = address & 0xFF
        data = [0x40, LSB, MSB, sub_index, 0, 0, 0, 0]
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
    df.to_csv(recording_file_name,
              mode='a',
              header=False,
              index=False,
              encoding='windows-1251')


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
