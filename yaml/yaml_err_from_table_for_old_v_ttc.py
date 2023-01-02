from pprint import pprint
from tkinter import filedialog as fd

import pandas as pd
import yaml

# file_name = fd.askopenfilename()
file_name = 'vmu_errors_parse.xlsx'
file = pd.ExcelFile(file_name)
new_err_sheet = file.parse(sheet_name='Sheet1')
new_err_list = new_err_sheet.to_dict(orient='records')

old_err_sheet = file.parse(sheet_name='Sheet2')
old_err_list = old_err_sheet.to_dict(orient='records')

error_dict = {}
prev_node_name = ''
e_list = []

# for er in new_err_list:
#     name_error = er['name'].upper().replace('_', ' ').strip()
#     for old_er in old_err_list:
#         if name_error in old_er['name_error'].upper().strip():
#             er['important_parametr'] = old_er['important_parametr']

for old_er in old_err_list:
    old_er['name_error'] = old_er['name_error'].replace('"', '').replace("'", '')
    name_error = old_er['name_error'].upper().strip()
    for er in new_err_list:
        if er['name'].upper().replace('_', ' ').strip() in name_error:
            old_er['critical'] = er['critical']
            old_er['description_error'] = er['description_error']

with open(f'errors_for_120.yaml', 'w', encoding='UTF8') as file:
    documents = yaml.dump(new_err_list, file, allow_unicode=True)

with open(f'errors_for_130.yaml', 'w', encoding='UTF8') as file:
    documents2 = yaml.dump(old_err_list, file, allow_unicode=True)
