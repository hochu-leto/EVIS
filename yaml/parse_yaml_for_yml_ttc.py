import yaml
from helper import int_to_hex_str
from tkinter import filedialog as fd
from parse_yaml_for_burr import check_dict

convert_types = dict(uint8='UNSIGNED8', int8='SIGNED8', uint16='UNSIGNED16', int16='SIGNED16', uint32='UNSIGNED32',
                     int32='SIGNED32', float='FLOAT', string='VISIBLE_STRING')
# file = "canopen_parameters.yml"
# file = "C:\\workspace\\PycharmProjects\\VMU_monitor\\Data\\all_nodes.yaml"
'''
  required_fields:
    name:           name:
    index:          index:
    sub_index:      subindex: !!!!!!!!
    type:           type: !!!!!!!
  optional_fields:
    editable:       access: !!!!!!!!!!
    description:    description:
    offset:         offset:
    multiplier:     mult: !!!!!!!!!!
    eeprom:         eeprom:
    value:          value:
    units:          units:          
    value_table:    values_table: !!!!!!!
    period:
    min_value:
    max_value: 
    widget: 
    
from 'canopen_parameters.yml'
    name: Содержит имя параметра
    index: Определяет адрес параметра в словаре Canopen устройства
    subindex: Определяет адрес параметра в словаре Canopen устройства
    access: 'Определяет доступ к параметру, возможные значения: ro, rw'
    type: 'Определяет тип данных параметра, возможные значения: uint8, int8, uint16, int16, uint32, int32, string'
    description: Содержит подробное описание параметра

  Опциональные поля: 
    offset: > 
      Смещение для перевода полученного integer-значения в дробное по формуле value = (raw_value * mult) - offset. 
      Указывается только для физических величин, которые нуждаются в конвертации. Если значение 0, то может не 
      указываться.
    mult: > 
      Множитель для перевода полученного integer-значения в дробное по формуле value = (raw_value * mult) - offset. 
      Указывается только для физических величин, которые нуждаются в конвертации. Если значение 1, то может не 
      указываться.
    eeprom: > 
      Наличие поля показывает, что этот параметр сохраняется в энергонезависимую память. Запись и чтение осуществляются 
      по запросам со стороны пользователя. При включении КВУ чтение параметров из EEPROM происходит автоматически.
    value: >  
      Предназначено для сохранения актуального значения параметра при выгрузке конфигурации из КВУ в файл и обратно. 
      Может быть указано и для ro-параметра (для анализа конфигурации), и для rw-параметра (для быстрой загрузки 
      типовой конфигурации в устройство)
    units: Единицы измерения либо диапазон значений, если величина безразмерная
    values_table: Расшифровка возможных значений в пол    
  
  example  
    - name: ABS_WHEEL_TICKS
      index: 8544
      sub_index: 1
      description: Количество зубцов на измерительном колесе, которое считывает энкодер(датчик скорости!!!!!!!!)
      type: UNSIGNED8
      value: 48.0
      editable: true
      min_value: 0
      max_value: 255
      eeprom: true  
'''

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
            par['type'] = convert_types[par['type']]
            par['description'] = par['description'].strip().replace('\n', '')
            par['editable'] = True if 'w' in par['access'] else False
            del par['access']
            par['sub_index'] = par['subindex']
            del par['subindex']

            if 'units' in par.keys():
                if '[' in par['units']:
                    par['min_value'] = float(par['units'].split('..')[0].replace('[', ''))
                    par['max_value'] = float(par['units'].split('..')[1].replace(']', ''))

            if 'mult' in par.keys():
                par['multiplier'] = par['mult']
                del par['mult']

            if 'values_table' in par.keys():
                par['value_table'] = par['values_table']
                del par['values_table']

            if 'eeprom' in par.keys():
                par['eeprom'] = True

            if 'value' in par.keys():
                if par['value'] and not '[' in par['value']:
                    par['value'] = float(par['value'])
                else:
                    del par['value']

            if 'iolib_errors' in par['description']:
                par['value_table'] = iolib_errors_dict.copy()
        parse_dict[group] = group_list
    with open(r'parameters.yaml', 'w', encoding='UTF-8') as file:
        documents = yaml.dump(check_dict(parse_dict), file, allow_unicode=True)
