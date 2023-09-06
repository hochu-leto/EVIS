from pprint import pprint

import canopen
from tkinter import filedialog as fd

import yaml

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


def check_dict(par_dict: dict):
    final_dict = {}
    old_n = ''
    final_dict[old_n] = []

    for n, l in par_dict.items():
        if len(l) > 3:
            final_dict[n] = l
            old_n = n
        else:
            final_dict[f'{old_n}&{n}'] = final_dict[old_n] + l
            del final_dict[old_n]
            old_n = f'{old_n}&{n}'
    if '' in final_dict.keys():
        del final_dict['']
    return final_dict


def convert_variable_to_evo_param(param_list: list, var: canopen.objectdictionary.Variable):
    if var.name not in bad_magic_words  and var.index > 0xFF:
        parametr = dict(
            name=var.name.replace('g_', ''),
            editable=var.writable,
            type=type_dict[var.data_type],
            value=var.default,
            index=var.index,
            sub_index=var.subindex,
            description=var.description
        )
        param_list.append(parametr)
    return param_list


def add_line(l: list[str], first_part: str, second_part: str = None) -> list[str]:
    if first_part in l:
        ind = l.index(first_part)
        l[ind] = first_part[:-1] + second_part
    return l


eds_temp = 'temp.eds'
VendorName = 'MMZ\n'
eds_dict = {
    'CreatedBy=\n': VendorName,
    'ModifiedBy=\n': VendorName,
    'VendorName=\n': VendorName,
    'VendorNumber=\n': '0x000000C2\n',
    'ProductNumber=\n': '0x00000190\n'
}


def eds_to_dict(file_name: str) -> dict[list[dict]]:
    network = canopen.Network()
    final_dict = {}
    watch_list = []
    try:
        node = network.add_node(0x620, file_name)
    except ValueError:
        with open(file_name) as f:
            lines = f.readlines()
        for f, s in eds_dict.items():
            lines = add_line(lines, f, s)
        with open(eds_temp, 'w', encoding='windows-1251') as f:
            f.writelines(lines)
        node = network.add_node(0x620, eds_temp)
    for name, param in node.object_dictionary.names.items():
        if 'Transmit ' not in name and 'Receive' not in name:
            if type(param) is canopen.objectdictionary.Variable:
                watch_list = convert_variable_to_evo_param(watch_list, param)
            else:
                group_name = name.replace('g_', '')
                par_list = []
                for nam, par in param.names.items():
                    par_list = convert_variable_to_evo_param(par_list, par)
                final_dict[group_name] = par_list
    final_dict['watch'] = watch_list
    return final_dict


if __name__ == '__main__':

    final_dict = eds_to_dict(fd.askopenfilename())
    with open(r'parameters_eds.yaml', 'w', encoding='UTF-8') as file:
        documents = yaml.dump(check_dict(final_dict), file, allow_unicode=True)
