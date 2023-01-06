from pprint import pprint
from tkinter import filedialog as fd

import pandas as pd
import yaml

file_name = fd.askopenfilename()
file = pd.ExcelFile(file_name)
err_sheet = file.parse(sheet_name='errors')
err_sheet = err_sheet.dropna(how='all')
err_list = err_sheet.to_dict(orient='records')

error_dict = {}
prev_node_name = ''
e_list = []

for er in err_list:
    if isinstance(er['value_error'], str):
        if 'node' in er['value_error']:
            with open(f'errors_{prev_node_name}.yaml', 'w', encoding='UTF-8') as file:
                documents = yaml.dump(e_list, file, allow_unicode=True)
            prev_node_name = er['value_error'].replace('node ', '')
            e_list = []
        else:
            e = er.copy()
            for k, v in er.items():
                if str(v) == 'nan':
                    del e[k]
            e['critical'] = True
            e['name_error'] = er['name_error'].replace('"', '').replace("'", '').strip()
            e_list.append(e)
            pprint(e['name_error'])
with open(f'errors_{prev_node_name}.yaml', 'w', encoding='UTF-8') as file:
    documents = yaml.dump(e_list, file, allow_unicode=True)