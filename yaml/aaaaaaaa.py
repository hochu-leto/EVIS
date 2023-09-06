import re
import xml.etree.ElementTree as ET
from tkinter import filedialog as fd
import yaml

"""
Принимаем файл со словарём объектов формата xml
Единицы измерения параметра отображать в описании в квадратных скобках "[  ]" 
- внутри скобок единица измерения, также внутри квадратных скобок может быть
- если у параметра есть множитель, он записывается со знаком "*", например *0.1 или *10, после множителя - пробел, десятичный разделитель - точка . если множитель = 1, его писать не надо
- если у параметра есть смещение, оно записывается со знаком "+" или "-", например -40 или +0.5, после смещения - пробел, десятичный разделитель - точка
- если параметр может измеряться в разных единицах измерения - не надо писать его в квадратных скобках, я это захардварю
- если у параметра возможны несколько значений и у этих значений есть текстовые подсказки, то в описании к таким параметрам должны быть фигурные скобки "{ }", внутри них идёт значение параметра, знак равно, текстовая подсказка, точка с запятой и следующее значение, т.е. {1=миллиметры (от -93,5 мм до 93,5 мм);2 = проценты (от -1000 0.1% до 1000 0.1%); 3 = градусы (от -5100 град до 5100 град)}
- если значение следует отобразить как шестнадцатеричное, то в описании должно быть слово "HEX" - без кавычек
- если параметр может быть отображён в битовой последовательности(например, когда каждый бит за что-то отвечает и могут быть одновременнно включены несколько битов) то в описании должно быть слово "BIN" без кавычек - также в этом случае должен быть словарь с описанием значений битов ( в фигурных скобках)
- нигде  более в описании не использовать  ни квадратные, ни фигурные скобки и слова "HEX"  и "BIN"
"""
type_dict = {
    0x01: 'BOOLEAN',
    0x02: 'SIGNED8',  # 'INTEGER8',
    0x03: 'SIGNED16',  # 'INTEGER16',
    0x04: 'SIGNED32',  # 'INTEGER32',
    0x15: 'SIGNED64',  # 'INTEGER64',
    0x05: 'UNSIGNED8',
    0x06: 'UNSIGNED16',
    0x07: 'UNSIGNED32',
    0x1B: 'UNSIGNED64',
    0x08: 'FLOAT',  # 'REAL32',
    0x11: 'FLOAT',  # 'REAL64',
    0x10: 'INTEGER24',
    0x12: 'INTEGER40',
    0x13: 'INTEGER48',
    0x14: 'INTEGER56',
    0x16: 'UNSIGNED24',
    0x18: 'UNSIGNED40',
    0x19: 'UNSIGNED48',
    0x1A: 'UNSIGNED56',
    0x09: 'VISIBLE_STRING',
    0x0A: 'OCTET_STRING',
    0x0B: 'UNICODE_STRING',
    0x0C: 'TIME_OF_DAY',
    0x0D: 'TIME_DIFFERENCE',
    0x0F: 'DOMAIN'
}
bad_magic_words = ['Highest sub-index supported', 'Number of Entries']
access_type_dict = dict(
    rw=True,
    ro=False,
    wo=None
)
LowLimitIndex = 0x1FFF
HighLimitIndex = 0x6FFF
PATTERN = r'\{.*?\}'


def split_string(base_str:str, begin:str, finish:str=None) -> (str, str):
    """
    :param base_str:  - входящая строка, в которой будем искать
    :param begin: - начальный символ
    :param finish: - конечный символ, если не задан, до конца входящей строки
    :return: кортеж 1 - то, что находится в base_str между begin и finish,
     2 - все, что осталось от base_str кроме перой части
    """
    try:
        b_index = base_str.index(begin)
    except ValueError:
        return '', base_str
    part = base_str[b_index + len(begin):]
    if finish is None:
        f_index = len(part) - 1
    else:
        try:
            f_index = part.index(finish)
        except ValueError:
            f_index = len(part) - 1
    first_part = part[:f_index]
    second_part = base_str[:b_index].rstrip() + part[(f_index + len(finish)):].rstrip()
    return first_part, second_part


def obj_to_par(g_list: list[dict], param: ET) -> list[dict]:
    name = param.get('name')
    par = dict()
    if name and name not in bad_magic_words:
        par['name'] = name
        par['index'] = int(obj.get('index'), 16)
        if LowLimitIndex < par['index'] < HighLimitIndex:
            sub_index = param.get('subIndex')
            par['sub_index'] = int(sub_index, 16) if sub_index else 0
            par['type'] = type_dict[int(param.get('dataType'), 16)]
            par['editable'] = access_type_dict[param.get('accessType')]
            par['value'] = param.get('defaultValue')
            base = 16 if 'x' in par['value'] else 10
            par['value'] = int(par['value'], base) if par['value'] and '+' not in par['value'] else 0
            descr = param.find('description').text
            if descr:
                base = 10
                if 'HEX' in descr:
                    par['widget'] = 'HEX'
                    base = 16
                if 'BIN' in descr:
                    par['widget'] = 'BIN'
                    # if par['editable']:
                    #     par['widget'] = 'MyCheckableComboBox'
                    # else:
                    #     par['widget'] = 'MyList'

                    # base = 2
                unit, descr = split_string(descr, '[', ']')
                if unit:
                    multiplier, unit = split_string(unit, '*', ' ')
                    par['multiplier'] = float(multiplier) if multiplier else None
                    offset, par['unit'] = split_string(unit, '-', ' ') if '-' in unit else split_string(unit, '+', ' ')
                    if offset:
                        try:
                            off = int(offset)
                            par['offset'] = -1*off if '-' in unit else off
                        except ValueError:
                            print(f'bad offset {offset}')

                table, descr = split_string(descr, '{', '}')
                if table:
                    par['value_table'] = {}
                    for v in table.split(';'):
                        key_value = v.split('=')
                        try:
                            key = int(key_value[0], base)
                            par['value_table'][key] = key_value[1]
                        except Exception as ex:
                            print(ex)
                par['description'] = descr.replace('\n', '')
            if par['type'] is not None:
                g_list.append(par.copy())
    return g_list


file_name = fd.askopenfilename()
root_node = ET.parse(file_name).getroot()
CANopenObjectList = root_node.find('CANopenObjectList')
object_list = CANopenObjectList.findall('CANopenObject')
param_dict = {}
watch_list = []
for obj in object_list:
    if int(obj.get('subNumber')):
        group_list = []
        for param in obj:
            group_list = obj_to_par(group_list, param)
        if group_list:
            param_dict[obj.get('name')] = group_list.copy()
    elif obj.get('objectType') == "VAR":
        watch_list = obj_to_par(watch_list, obj)
param_dict['Watch'] = watch_list
# with open(r'parameters.yaml', 'w', encoding='windows-1251') as file:
with open(r'parameters.yaml', 'w', encoding='UTF-8') as file:
    documents = yaml.dump(param_dict, file, allow_unicode=True)
