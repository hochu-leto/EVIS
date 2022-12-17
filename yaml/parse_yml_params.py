import yaml
from helper import int_to_hex_str

convert_types = dict(uint8='UNSIGNED8', int8='SIGNED8', uint16='UNSIGNED16', int16='SIGNED16', uint32='UNSIGNED32',
                     int32='SIGNED32', float='FLOAT', string='VISIBLE_STRING')
file = "canopen_parameters.yml"
# file = "C:\\workspace\\PycharmProjects\\VMU_monitor\\Data\\all_nodes.yaml"

with open(file, "r", encoding="UTF8") as stream:
    try:
        canopen_vmu_ttc = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)

parse_dict = {}
for group, group_list in canopen_vmu_ttc['canopen_parameters'].items():
    for par in group_list:
        par['address'] = hex(par['index']) + int_to_hex_str(par['subindex'])
        par['type'] = convert_types[par['type']]
        par['editable'] = True if 'w' in par['access'] else False

        par['scale'] = (1 / par['mult']) if 'mult' in par.keys() else 1
        par['scaleB'] = par['offset'] if 'offset' in par.keys() else 0
    parse_dict[group] = group_list

with open(r'../Data/КВУ_ТТС/Default/parameters.yaml', 'w', encoding='windows-1251') as file:
    documents = yaml.dump(parse_dict, file, allow_unicode=True)

