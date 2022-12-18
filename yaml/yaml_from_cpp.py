from operator import itemgetter
from tkinter import filedialog as fd
import yaml
from parse_yaml_for_burr import type_dict, check_dict

empty_par = {'name': '',
             'address': '',
             'editable': False,
             'description': '',
             'unit': '',
             'type': '',
             'group': ''}

if __name__ == '__main__':

    file_name = fd.askopenfilename()
    with open(file_name, "r") as file:
        nodes = file.readlines()

    final_list = []

    for tag in nodes:
        tg = empty_par.copy()
        if 'OD_' in tag:
            t = tag.split(',')
            tg['name'] = t[4].strip()[1:-1]
            tg['group'] = t[3].strip()[1:-1]
            tg['address'] = t[0].strip()[2:] + t[1].strip()[2:-1]
            v_type = t[6].strip()[3:]
            tg['type'] = type_dict[v_type] if v_type in type_dict.keys() else 'SIGNED32'
            if t[5] != '""':
                tg['unit'] = t[5].strip()[1:-1]
            print(tg['name'], t[8])
            tg['editable'] = True if 'true' in t[8] else False
            if v_type != 'FUNC':
                final_list.append(tg.copy())

    final_list = sorted(final_list, key=itemgetter('group'))

    old_par = empty_par
    final_dict = {}
    old_group = ''
    f_list = []
    for par in final_list:
        if par['group'] != old_group:
            final_dict[old_group] = f_list.copy()
            old_group = par['group']
            f_list.clear()
        f_list.append(par)
    final_dict[old_group] = f_list.copy()
    del final_dict['']
    with open(r'parameters_inverter.yaml', 'w', encoding='windows-1251') as file:
        documents = yaml.dump(check_dict(final_dict), file, allow_unicode=True)
