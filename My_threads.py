import datetime

import pandas as pd
from PyQt5.QtCore import QThread, pyqtSignal, QTimer, QEventLoop
import CANAdater
from EVONode import EVONode
from Parametr import Parametr, empty_par


class SaveToFileThread(QThread):
    SignalOfReady = pyqtSignal(int, str, bool)
    err_thread_signal = pyqtSignal(str)
    max_iteration = 1000
    iter_count = 1
    current_params_list = []
    ready_persent = 0

    def __init__(self):
        super().__init__()
        self.max_errors = 30
        self.adapter = CANAdater
        self.node_to_save = EVONode
        self.finished.connect(self.finished_tread)
        self.adapter_is_busy = False

    def finished_tread(self):
        self.killTimer(self.num_timer)

    def run(self):
        self.errors_counter = 0
        self.params_counter = 0

        def request_param():
            # print('saving request')
            param = all_params_list[self.params_counter]
            while param.value:
                self.params_counter += 1
                param = all_params_list[self.params_counter]
                # print(f' уже был {param.name} = {param.value}')
            if param.address and int(param.address, 16) > 0:
                param = all_params_list[self.params_counter].get_value(self.adapter)
                # all_params_list[self.params_counter].value = param
                # print(f' запросил {all_params_list[self.params_counter].name} = '
                #       f'{all_params_list[self.params_counter].value}')

                while isinstance(param, str):
                    self.errors_counter += 1
                    param = all_params_list[self.params_counter].get_value(self.adapter)
                    if self.errors_counter >= self.max_errors:
                        self.errors_counter = 0
                        self.params_counter = 0
                        self.SignalOfReady.emit(self.ready_persent,
                                                f'{param} \n'
                                                f' параметр {all_params_list[self.params_counter].name}', False)
                        timer.stop()
                        print(' ng ', param)
                        return

            self.errors_counter = 0
            self.params_counter += 1
            self.ready_persent = int(90 * self.params_counter / len_param_list)
            self.SignalOfReady.emit(self.ready_persent, '', False)
            if self.params_counter >= len_param_list:
                timer.stop()
                self.save_file(all_params_list)

        send_delay = 3  # задержка отправки в кан сообщений
        all_params_list = []
        for group_name, param_list in self.node_to_save.group_params_dict.items():
            e_par = Parametr()
            e_par.name = f'group {group_name}'
            all_params_list.append(e_par)
            for param in param_list:
                all_params_list.append(param)
        len_param_list = len(all_params_list)

        timer = QTimer()
        timer.timeout.connect(request_param)
        self.num_timer = timer.start(send_delay)

        loop = QEventLoop()
        loop.exec_()

    def save_file(self, all_params_list):
        self.errors_counter = 0
        self.params_counter = 0
        save_list = []
        l = 10 / len(all_params_list)
        for p in all_params_list:
            if 'group' in p.name:
                par = empty_par.copy()
                par['name'] = p.name
            else:
                par = p.to_dict().copy()
            self.ready_persent += l
            self.SignalOfReady.emit(self.ready_persent, '', False)

            save_list.append(par.copy())

        now = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_name = f'ECU_Settings/{self.node_to_save.name}_{self.node_to_save.serial_number}_{now}.xlsx'
        df = pd.DataFrame(save_list, columns=p.to_dict().keys())
        df.to_excel(file_name, index=False)
        self.SignalOfReady.emit(100, file_name, True)
