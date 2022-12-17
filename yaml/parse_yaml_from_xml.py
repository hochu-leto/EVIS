import xml.etree.ElementTree as ET
from operator import itemgetter
from pprint import pprint

from tkinter import filedialog as fd

import yaml

excepted_scale_format = ['6144', '12288']
empty_par = {'name': '',
             'address': '',
             'description': '',
             'scale': 0,
             'unit': '',
             'editable': False,
             'value': 0.0,
             'type': '',
             'group': 0}

type_dict = dict(U32='UNSIGNED32',
                 UINT32='UNSIGNED32',
                 DATE='SIGNED32',
                 INT32='SIGNED32',
                 I32='SIGNED32',
                 UINT16='UNSIGNED16',
                 INT16='SIGNED16',
                 U16='UNSIGNED16',
                 I16vparam='SIGNED16',
                 UNION='SIGNED16',
                 U8='UNSIGNED8',
                 перечисление='UNSIGNED8',
                 десятерич='UNSIGNED8',
                 двоич='UNSIGNED8',
                 STR='VISIBLE_STRING',
                 )

file_name = fd.askopenfilename()
root_node = ET.parse(file_name).getroot()
nodes = root_node.findall('param')
final_list = []


for tag in nodes:
    tg = empty_par.copy()
    t = tag.attrib

    v_type = t['tdim']
    if v_type in type_dict.keys():
        v_type = type_dict[v_type]
    else:
        v_type = 'SIGNED32'

    scale = int(t['scale_value'])
    if scale:
        # scale = 16777216 / int(scale)
        scale = 0x100000 / scale

    if t['scale_format'] in excepted_scale_format:
        v_type = 'SIGNED16'
        scale = 0

    tg['description'] = t['FullText']
    tg['name'] = t['EngText'] if t['EngText'] else tg['description']
    tg['value'] = float(t['value'])
    tg['address'] = hex(int(t['co_index'])) + hex(int(t['co_subindex']))[2:].zfill(2)
    tg['editable'] = True if int(t['checked']) else False
    tg['scale'] = scale
    tg['unit'] = t['tdim']
    tg['type'] = v_type
    tg['group'] = int(t['group_num'])
    final_list.append(tg.copy())
final_list = sorted(final_list, key=itemgetter('group'))

old_par = empty_par
old_group = ''
f_list = []
final_dict = {}
prev_group_name = ''
for par in final_list:
    if len(f_list) > 2 and par['group'] != old_group:
        old_group = par['group']
        final_dict[prev_group_name] = f_list.copy()
        prev_group_name = str(par['description'])
        f_list.clear()
    else:
        if par['unit'] != 'корень':
            f_list.append(par)
del final_dict['']

with open(r'parameters_vector.yaml', 'w', encoding='windows-1251') as file:
    documents = yaml.dump(final_dict, file, allow_unicode=True)
