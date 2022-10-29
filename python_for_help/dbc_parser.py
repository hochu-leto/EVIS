import time
from tkinter import filedialog as fd

import can_decoder
import pandas as pd

# dbc_can1 = 'dbc/N1_CAN1.dbc'
# dbc_can2 = 'dbc/VMU_BKU_v2.dbc'
dbc_can2 = fd.askopenfilename()
db = can_decoder.load_dbc(dbc_can2)
df_decoder = can_decoder.DataFrameDecoder(db)

file_name = fd.askopenfilename()
with open(file_name, "r") as file:
    nodes = file.readlines()
col_pn = ['TimeStamp', 'ID', 'IDE', 'DataBytes']
data_dict = {}
data_list = []
for tag in nodes:
    stroka = tag.split()
    if stroka[0] != 'ER':
        try:  # + 2147483648
            if int(stroka[4]) > 7:
                data_list.append([stroka[14], int(stroka[3], 16),
                                  False if stroka[2] == 'SFF' else True,
                                  [int(i, 16) for i in stroka[6:14]]])
        except IndexError:
            pass
            # print(tag)
df2 = pd.DataFrame(data_list, columns=col_pn)
ln_log = len(data_list)
print(f'В логе {ln_log} строк')
timest = df2.to_dict()['TimeStamp']
df_phys_1 = df_decoder.decode_frame(df2, columns_to_drop=["CAN ID", "Raw Value", "PGN", "Source Address"])
if df_phys_1.empty:
    print(f'Нет совпадений из лога и файла {dbc_can2}')
else:
    df_phys_t = df_phys_1.transpose()
    cols = sorted(list(set(df_phys_t.values[0])))
    print(f'В dbc файле найдено {len(cols)} параметров')
    cols.insert(0, 'Time')
    prev_dict = dict.fromkeys(cols, 0)
    final_list = []
    timestamp = 0

    # delta_time = time.perf_counter()
    # j = 0
    for v in df_phys_t:
        i = 0
        now = int(timest[v])
        if now >= timestamp + 20000:
            timestamp = now
            print(now)
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
    df.to_excel(file_name.split('.')[0] + '.xlsx', index=False)

