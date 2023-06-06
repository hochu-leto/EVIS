from datetime import datetime
from tkinter import filedialog

import can


def log_to_asc_convert(log_file: str) -> str:
    with open(log_file, 'r') as f_in:
        first_line = f_in.readline()
    if 'can' in first_line and '#' in first_line:
        print('Лог от верхнего уровня')
        lg_file = log_file
    elif 'HEX' in first_line and first_line.count(':') == 2:
        print('Лог от канвайза')
        lg_file = canwise_log_to_candump(log_file)
    else:
        print('Неизвестный Лог')
        return ''
    log_in = can.io.CanutilsLogReader(lg_file)
    asc_file = log_file.replace('.log', '.asc')
    ln = sum(1 for line in open(lg_file, 'r'))
    print(f'Всего в файле {ln} записей. Преобразую в лог asc')
    i = 0
    with open(asc_file, 'w') as f_out:
        log_out = can.io.ASCWriter(f_out)
        for msg in log_in:
            print(f'\rОсталось преобразовать {ln - i - 1} записей', end='', flush=True)
            log_out.on_message_received(msg)
            i += 1
    log_out.stop()
    print()
    print('Готово!')
    return asc_file


def canwise_log_to_candump(log_file: str) -> str:
    ms_string = '0018992249'
    date_string = '31.05.2023'
    time_string = '14:23:22.903'
    temp_file = 'temp.log'
    with open(log_file, 'r') as f_in:
        lines = f_in.readlines()
    ln = len(lines)
    print(f'Всего в файле {ln} записей. Преобразую во временный лог candump')
    with open(temp_file, 'w') as f_temp:
        for i, mess in enumerate(lines):
            print(f'\rОсталось преобразовать {ln - i - 1} записей', end='', flush=True)
            ms = mess.split()
            if ms[0] == 'ER':
                continue
            byte_count = int(ms[4])
            ms_string = ms[byte_count + 6]
            date_string = ms[byte_count + 7]
            time_string = ms[byte_count + 8]
            # time_stamp = datetime.strptime(date_string + time_string[:-4] + ms_string[4:],
            #                                "%d.%m.%Y%H:%M:%S%f")
            time_stamp = datetime.strptime(date_string + time_string,
                                           "%d.%m.%Y%H:%M:%S.%f")
            now = str(datetime.timestamp(time_stamp)).ljust(17, '0')
            id_string = ms[3] if ms[2] == 'EFF' else ms[3][-3:]
            data_string = ''.join(ms[6:6 + byte_count])
            ch_string = 'can0'
            f_temp.write(f'({now}) {ch_string} {id_string}#{data_string}\n')
    print()
    return temp_file


if __name__ == '__main__':
    file_name = filedialog.askopenfilename()
    if not file_name:
        print('Файл не выбран')
        quit()
    elif '.log' not in file_name:
        print('Нужно выбрать файл лога КАН шины *.log')
        quit()
    log_to_asc_convert(file_name)
