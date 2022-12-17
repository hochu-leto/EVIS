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

type_dict = dict(UINT32='UNSIGNED32',
                 UINT16='UNSIGNED16',
                 INT16='SIGNED16',
                 UNION='SIGNED16',
                 STR='VISIBLE_STRING',
                 INT32='SIGNED32',
                 DATE='SIGNED32')

file_name = fd.askopenfilename()
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
        print('No Ед. изм. ')
        break

    if 'Размер' in t.keys():
        tg['size'] = t['Размер']
    elif 'size' in t.keys():
        tg['size'] = t['size']
    else:
        print('No size ')
        break

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
        list_v = t['Строки'].split(';\r\n')
        if len(list_v) == 1:
            list_v = t['Строки'].split(';\n')
        print(len(list_v))
        pprint(list_v)
        tg['values_table'] = {}
        for n in list_v:
            if n:
                v = n.split('- ')[0]
            # try:
                k = n.split('- ')[1]
                print(tg['name'], v, k)
                tg['values_table'][int(v)] = k
            # except IndexError:
            #     print(tg['name'], t['Строки'], n)

        # tg['values_table'] = {n.split('- ')[0]: n.split('- ')[1] for n in t['Строки'].split(' ;\r\n') if n}
    tg['period'] = 1
    if str(tg['address']) != 'nan':
        tg['address'] = '0x' + hex(int(tg['address']))[2::].zfill(4)

    final_list.append(tg.copy())

old_group = ''
f_list = []
final_dict = {}
for par in final_list:
    if par['code'].count('.') == 2:
        f_list.append(par)
    elif par['code'].count('.') == 1:
        final_dict[old_group] = f_list.copy()
        f_list.clear()
        old_group = str(par['name'])
    else:
        pass
final_dict[old_group] = f_list.copy()
del final_dict['']

with open(r'parameters.yaml', 'w', encoding='windows-1251') as file:
    documents = yaml.dump(final_dict, file, allow_unicode=True)
