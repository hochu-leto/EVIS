from pprint import pprint

import canopen
from tkinter import filedialog as fd

import yaml

from helper import int_to_hex_str
from parse_yaml_for_burr import check_dict

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


def convert_variable_to_evo_param(param_list: list, var: canopen.objectdictionary.Variable):
    if var.name != 'Number of Entries' and var.index > 0xFF:
        parametr = dict(
            name=var.name.replace('g_', ''),
            editable=var.writable,
            type=type_dict[var.data_type],
            value=var.default,
            # address=hex(var.index) + int_to_hex_str(var.subindex)
            index=var.index,
            sub_index=var.subindex
        )
        param_list.append(parametr)
    return param_list


if __name__ == '__main__':

    network = canopen.Network()
    file_name = fd.askopenfilename()
    final_dict = {}
    watch_list = []
    node = network.add_node(0x620, file_name)
    for name, param in node.object_dictionary.names.items():
        if 'Transmit ' not in name and 'Receive' not in name:
            if type(param) is canopen.objectdictionary.Variable:
                watch_list = convert_variable_to_evo_param(watch_list, param)
            else:
                group_name = name.replace('g_', '')
                par_list = []
                for nam, par in param.names.items():
                    # print(name, nam, type(par))
                    par_list = convert_variable_to_evo_param(par_list, par)
                final_dict[group_name] = par_list
    final_dict['watch'] = watch_list

    with open(r'parameters_tab.yaml', 'w', encoding='UTF-8') as file:
        documents = yaml.dump(check_dict(final_dict), file, allow_unicode=True)
