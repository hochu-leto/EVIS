from pprint import pprint
import pandas
from tkinter import filedialog as fd
import yaml

empty_par = {'name': '',
             'address': '',
             'editable': '',
             'description': '',
             'scale': '',
             'unit': '',
             'value': '',
             'type': '',
             'degree': '',
             'period': ''}

type_dict = dict(
    UINT32='UNSIGNED32',
    UINT16='UNSIGNED16',
    ENUM='UNSIGNED16',
    INT16='SIGNED16',
    UNION='UNSIGNED16',     # 'SIGNED16',
    STR='UNSIGNED16',     # 'SIGNED16',
    STRING='VISIBLE_STRING',
    INT32='SIGNED32',
    DATE='DATE',
    FLOAT32='FLOAT'
)


def check_dict(par_dict: dict):
    final_dict = {}

    old_n = ''
    final_dict[old_n] = []

    for n, l in par_dict.items():
        if len(l) > 3:
            final_dict[n] = l
            old_n = n
        elif l:
            final_dict[f'{old_n}&{n}'] = final_dict[old_n] + l
            del final_dict[old_n]
            old_n = f'{old_n}&{n}'
    if '' in final_dict.keys():
        del final_dict['']
    return final_dict


def split_group(final_list: list[dict]) -> dict[str:list[dict]]:
    old_group = ''
    f_list = []
    param_dict = {}
    for par in final_list:
        if par['code'].count('.') == 2:
            f_list.append(par)
        elif par['code'].count('.') == 1:
            param_dict[old_group] = f_list.copy()
            f_list.clear()
            old_group = str(par['name'])
        else:
            pass
    param_dict[old_group] = f_list.copy()
    clear_dict = {k: param_dict[k].copy() for k in param_dict.keys() if param_dict[k]}

    return clear_dict


def xls_to_list(file_name: str) -> list[dict]:
    excel_data_df = pandas.read_excel(file_name)
    nodes = excel_data_df.to_dict(orient='records')
    final_list = []

    for t in nodes:
        tg = {}
        if 'Тип' in t.keys():
            v_type = t['Тип']
        elif 'type' in t.keys():
            v_type = t['type']
        else:
            print('No types ')
            break
        if v_type in type_dict.keys():
            tg['type'] = type_dict[v_type]
        else:
            tg['type'] = 'SIGNED32'

        if 'scale' in t.keys():
            tg['degree'] = t['scale']
        elif 'Коэф-т' in t.keys():
            tg['degree'] = t['Коэф-т']
        else:
            print('No scale ')
            break
        if str(tg['degree']) != 'nan':
            scale = 10 ** int(tg['degree'])
            tg['multiplier'] = 1 / scale
        del tg['degree']

        if 'name' in t.keys():
            tg['name'] = t['name']
        elif 'Название' in t.keys():
            tg['name'] = t['Название']
        else:
            print('No Название ')
            break

        if 'address' in t.keys():
            tg['address'] = t['address']
        elif 'Адрес' in t.keys():
            tg['address'] = t['Адрес']
        else:
            print('No address ')
            break

        if 'editable' in t.keys():
            tg['editable'] = t['editable']
        elif 'Запись' in t.keys():
            tg['editable'] = t['Запись']
        else:
            print('No Запись ')
            break
        tg['editable'] = True if float(tg['editable']) == 1.0 else False

        if 'description' in t.keys():
            tg['description'] = t['description']
        elif 'Описание' in t.keys():
            tg['description'] = t['Описание']
        else:
            print('No Описание ')
            break

        if 'unit' in t.keys():
            tg['unit'] = t['unit']
        elif 'Ед. изм.' in t.keys():
            tg['unit'] = t['Ед. изм.']
        else:
            tg['unit'] = 'nan'
            print('No Ед. изм. ')
            break
        if str(tg['unit']) == 'nan':
            del tg['unit']

        # if 'Размер' in t.keys():
        #     tg['size'] = t['Размер']
        # elif 'size' in t.keys():
        #     tg['size'] = t['size']
        # else:
        #     print('No size ')
        #     break

        if 'code' in t.keys():
            tg['code'] = t['code']
        elif 'Код' in t.keys():
            tg['code'] = t['Код']
        else:
            print('No code ')
            break

        if 'Мин.' in t.keys() and str(t['Мин.']) != 'nan':
            tg['min_value'] = float(t['Мин.'].replace(',', '.'))

        if 'Макс.' in t.keys() and str(t['Макс.']) != 'nan':
            tg['max_value'] = float(t['Макс.'].replace(',', '.'))

        if 'Строки' in t.keys() and str(t['Строки']) != 'nan':
            list_v = t['Строки'].split(';\n') if len(t['Строки'].split(';\r\n')) == 1 else t['Строки'].split(';\r\n')
            try:
                tg['value_table'] = {n.split('- ')[0]: n.split('- ')[1] for n in list_v if n}
            except IndexError:
                tg['value_table'] = {0: 'Таблица неверна'}

        if v_type == 'UNION':
            tg['value_table'] = {2 ** int(k) : v.strip() for k, v in tg['value_table'].items() if 'ezerv' not in v}
            tg['value_table'][0] = 'Нет значения'
            tg['widget'] = 'BIN'

        tg['period'] = 1
        if str(tg['address']) != 'nan':
            tg['index'] = int(tg['address'])
            del tg['address']
        final_list.append(tg.copy())
    return final_list


if __name__ == '__main__':
    file_name = fd.askopenfilename()
    d = xls_to_list(file_name)
    x = split_group(d)
    # x = check_dict(x)
    with open(r'parameters_burr.yaml', 'w', encoding='UTF-8') as file:  # encoding='windows-1251'
        documents = yaml.dump(x, file, allow_unicode=True)
