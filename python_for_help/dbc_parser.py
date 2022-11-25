import os
import time
from tkinter import filedialog as fd

import can_decoder
import pandas as pd
import glob
from os import listdir
from os.path import isfile, join
from os import walk

from pandas import ExcelWriter

mypath = 'dbc/'
#
# f = []
# for (dirpath, dirnames, dbc_files_list) in walk(mypath):
#     f.extend(dbc_files_list)
#     break
#
# dbc_files_list1 = next(walk(mypath), (None, None, []))[2]  # [] if no file
# dbc_files_list2 = [f for f in listdir(mypath) if isfile(join(mypath, f))]
dbc_files_list = glob.glob(mypath + "*.dbc")
if not dbc_files_list:
    print(f'*.dbc Файлы в папке {mypath} не найдены')
    quit()

# dbc_can1 = 'dbc/N1_CAN1.dbc'
# dbc_can2 = 'dbc/VMU_BKU_v2.dbc'

file_name = fd.askopenfilename()
if not file_name:
    print('Файл не выбран')
    quit()
f = str(file_name)
new_file_name = f[:f.rfind('.')] + '.xlsx'
with open(file_name, "r") as file:
    nodes = file.readlines()
col_pn = ['TimeStamp', 'ID', 'IDE', 'DataBytes']
data_dict = {}
data_list = []
for tag in nodes:
    stroka = tag.split()
    if stroka[0] != 'ER':
        try:
            if int(stroka[4]) > 7:
                data_list.append([stroka[14], int(stroka[3], 16),
                                  False if stroka[2] == 'SFF' else True,
                                  [int(i, 16) for i in stroka[6:14]]])
        except IndexError:
            print(f'Пропускаю строку {tag}')
        except ValueError:
            print(f'Неправильный лог. Не могу парсить строку:\n {tag}')
            quit()
df2 = pd.DataFrame(data_list, columns=col_pn)
ln_log = len(data_list)
print(f'В логе {ln_log} строк')
timest = df2.to_dict()['TimeStamp']
df_phys_t = None
for dbc_can in dbc_files_list:
    db = can_decoder.load_dbc(dbc_can)
    df_decoder = can_decoder.DataFrameDecoder(db)
    df_phys = df_decoder.decode_frame(df2, columns_to_drop=["CAN ID", "Raw Value", "PGN", "Source Address"])

    if df_phys.empty:
        print(f'Нет совпадений из лога и файла {dbc_can}')
    else:
        df_phys_t = df_phys.transpose()
        ln_log = df_phys_t.shape[1]
        print(f'В датафрейме {ln_log} записей')
        break

if df_phys_t is None:
    print('Для этого лога нет совпадений из файлов dbc')
    quit()

cols = sorted(list(set(df_phys_t.values[0])))
print(f'В dbc файле найдено {len(cols)} параметров')
cols.insert(0, 'Time')
prev_dict = dict.fromkeys(cols, 0)
final_list = []
timestamp = 0

for v in df_phys_t:
    i = 0
    now = int(timest[v])
    ln_log -= 1
    print(f'\rОсталось обработать {ln_log} записей', end='', flush=True)
    if now >= timestamp + 20000:
        timestamp = now
        # print(now)
        prev_dict['Time'] = timestamp
        final_list.append(prev_dict.copy())
    for par in df_phys_t[v].values[0]:
        try:
            prev_dict[par] = df_phys_t[v].values[1][i]
        except TypeError:
            continue
        else:
            i += 1
    # delta_time = time.perf_counter() - delta_time
    # print(f'Примерно осталось {delta_time * (ln_log - j)} секунд')
    # j += 1
    # delta_time = time.perf_counter()

df = pd.DataFrame(final_list, columns=cols)
# df.to_excel(new_file_name, index=False)
if os.path.exists(new_file_name):
    ex_wr = ExcelWriter(new_file_name, mode="a", if_sheet_exists='new')
else:
    ex_wr = ExcelWriter(new_file_name, mode="w")

with ex_wr as writer:
    df.to_excel(writer, index=False)

