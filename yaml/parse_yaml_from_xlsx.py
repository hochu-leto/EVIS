import yaml
import pandas
from tkinter import filedialog as fd


file_name = fd.askopenfilename()
# excel_data_df = pandas.read_excel(file_name)
# nodes = excel_data_df.to_dict(orient='records')
# final_list = []
#
#
# err_sheet = file_name.parse(sheet_name='errors')
# err_list = err_sheet.to_dict(orient='records')  # парим лист "errors"
# error_dict = {}
# prev_node_name = ''
# e_list = []
# for er in err_list:
#     if isinstance(er['value_error'], str):
#         if 'node' in er['value_error']:
#             prev_node_name = er['value_error'].replace('node ', '')
#             with open(f'errors_{prev_node_name}.yaml', 'w', encoding='windows-1251') as file:
#                 documents = yaml.dump(e_list, file, allow_unicode=True)
#             e_list = []
#         else:
#             e_list.append(er)
#
    # err['name_error'] = err['name_ru']
    # if err['description']:
    #     err['description_error'] = err['description'].strip()
    # err['value_error'] = err['code']
    # if err['code']:
    #     print(err['code'], bin(err['code']), err['code'] & (1 << 5), err['code'] & (1 << 6), err['code'] & (1 << 7))
    # err['critical'] = True if err['code'] & (1 << 5) else False
    # del err['description']
    # del err['name_ru']
    # del err['hardware_id']
    # parse_list.append(err)


