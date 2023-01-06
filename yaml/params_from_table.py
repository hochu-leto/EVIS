import pandas as pd
import yaml

from parse_yaml_for_burr import check_dict

file_name = 'table_for_params_new_VMU.xlsx'
file = pd.ExcelFile(file_name)
kvu_sheet = file.parse(sheet_name='КВУ_ТТС', encodings='windows-1251')
kvu_list = kvu_sheet.to_dict(orient='records')

final_dict = {}
prev_name = ''
par_list = []
for par in kvu_list:
    if 'group ' in par['name']:
        final_dict[prev_name] = par_list.copy()
        prev_name = par['name'].replace('group ', '').strip()
        par_list.clear()
    else:
        par['editable'] = True if par['editable'] == 1 else False
        p = par.copy()
        for k, v in par.items():
            if str(v) == 'nan' or not v:
                del p[k]
        p['type'] = p['type'].strip()
        par_list.append(p)

del final_dict['']

with open(r'parameters_ttc_120.yaml', 'w', encoding='UTF8') as file:
    documents = yaml.dump(check_dict(final_dict), file, allow_unicode=True)
