import os
import time
from datetime import datetime
from tkinter import filedialog as fd
import can
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

import can  # pip install python-can


def log_to_asc_convert(log_file: str) -> str:
    log_in = can.io.CanutilsLogReader(log_file)
    asc_file = log_file.replace('.log', '.asc')

    try:
        for msg in log_in:
            pass
        with open(asc_file, 'w') as f_out:
            log_out = can.io.ASCWriter(f_out)
            for msg in log_in:
                log_out.on_message_received(msg)
        log_out.stop()
    except ValueError:
        canwise_log_to_candump(log_file, asc_file)
    return asc_file


def canwise_log_to_candump(log_file, exit_file):
    ms_string = '0018992249'
    date_string = '31.05.2023'
    time_string = '14:23:22.903'
    temp_file = 'temp.log'
    with open(log_file, 'r') as f_in:
        with open(temp_file, 'w') as f_temp:
            for mess in f_in.readlines():
                ms = mess.split()
                if ms[0] == 'ER':
                    continue
                byte_count = int(ms[4])
                ms_string = ms[byte_count + 6]
                date_string = ms[byte_count + 7]
                time_string = ms[byte_count + 8]
                # time_stamp = datetime.strptime(ms_string, "%f")
                # time_stamp = datetime.strptime(date_string + time_string[:-4] + ms_string[4:],
                #                                "%d.%m.%Y%H:%M:%S%f")
                time_stamp = datetime.strptime(date_string + time_string,
                                               "%d.%m.%Y%H:%M:%S.%f")
                # time_stamp = datetime.strptime(ms_string[:4] + '.' + ms_string[4:], "%S.%f")
                now = str(datetime.timestamp(time_stamp)).ljust(17, '0')
                id_string = ms[3] if ms[2] == 'EFF' else ms[3][-3:]
                data_string = ''.join(ms[6:6 + byte_count])
                ch_string = 'can0'
                f_temp.write(f'({now}) {ch_string} {id_string}#{data_string}\n')

    log_in = can.io.CanutilsLogReader(temp_file)
    with open(exit_file, 'w') as f_out:
        log_out = can.io.ASCWriter(f_out)
        for msg in log_in:
            log_out.on_message_received(msg)
    log_out.stop()


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
# log_to_asc_convert(file_name)
# quit()
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
                data_list.append([stroka[18], int(stroka[3], 16),
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
        print(f'Выбраны параметры из файла {dbc_can} ')
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
    if now >= timestamp + 1000000:
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

df = pd.DataFrame(final_list, columns=cols)
if os.path.exists(new_file_name):
    ex_wr = ExcelWriter(new_file_name, mode="a", if_sheet_exists='new')
else:
    ex_wr = ExcelWriter(new_file_name, mode="w")

with ex_wr as writer:
    df.to_excel(writer, index=False)
