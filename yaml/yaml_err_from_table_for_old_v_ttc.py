import pandas as pd
import yaml

# file_name = fd.askopenfilename()
file_name = 'vmu_errors_parse.xlsx'
file = pd.ExcelFile(file_name)
new_err_sheet = file.parse(sheet_name='Sheet1')
new_err_list = new_err_sheet.to_dict(orient='records')

old_err_sheet = file.parse(sheet_name='Sheet3')
old_err_list = old_err_sheet.to_dict(orient='records')

error_dict = {}
prev_node_name = ''
e_list = []

for old_er in old_err_list:
    old_er['name_error'] = old_er['name_error'].replace("'", '').replace('"', '').strip()
    if str(old_er['description_error']) == 'nan':
        old_er['description_error'] = f'Для ошибки {old_er["name_error"]} пока нет подробного описания'

with open(f'errors_for_100.yaml', 'w', encoding='UTF8') as file:
    documents = yaml.dump(old_err_list, file, allow_unicode=True)
