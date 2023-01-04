import yaml
from helper import int_to_hex_str
from tkinter import filedialog as fd
from parse_yaml_for_burr import check_dict

convert_types = dict(uint8='UNSIGNED8', int8='SIGNED8', uint16='UNSIGNED16', int16='SIGNED16', uint32='UNSIGNED32',
                     int32='SIGNED32', float='FLOAT', string='VISIBLE_STRING')
file = "canopen_parameters.yml"
# file = "C:\\workspace\\PycharmProjects\\VMU_monitor\\Data\\all_nodes.yaml"

if __name__ == '__main__':
    file_name = 'iolib_errors.yml'
    with open(file_name, "r", encoding="UTF8") as stream:
        try:
            vmu_ttc_ioe = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)
    iolib_errors_dict = vmu_ttc_ioe['iolib_errors']

    file_name = fd.askopenfilename()

    with open(file_name, "r", encoding="UTF8") as stream:
        try:
            canopen_vmu_ttc = yaml.safe_load(stream)
        except yaml.YAMLError as exc:
            print(exc)

    parse_dict = {}
    for group, group_list in canopen_vmu_ttc['canopen_parameters'].items():
        for par in group_list:
            par['address'] = hex(par['index']) + int_to_hex_str(par['subindex'])
            del par['index']
            del par['subindex']
            par['type'] = convert_types[par['type']]
            par['description'] = par['description'].strip().replace('\n', '')
            par['editable'] = True if 'w' in par['access'] else False
            del par['access']
            if 'units' in par.keys():
                par['unit'] = par['units']
                del par['units']
            if 'mult' in par.keys():
                par['scale'] = (1 / par['mult'])
                del par['mult']
            if 'offset' in par.keys():
                par['scaleB'] = par['offset']
                del par['offset']
            if 'iolib_errors' in par['description']:
                par['values_table'] = iolib_errors_dict.copy()
        parse_dict[group] = group_list
    with open(r'parameters.yaml', 'w', encoding='UTF-8') as file:
        documents = yaml.dump(check_dict(parse_dict), file, allow_unicode=True)
