import pathlib
import time
from timeit import Timer

from PyQt6.QtCore import QTimer

from kvaser_power import Kvaser
from work_with_file import fill_nodes_dict_from_yaml, NODES_YAML_FILE, fill_par_dict_from_yaml, WORK_DIR, \
    PARAMETERS_YAML_FILE, DEFAULT_DIR

adapter = Kvaser()
all_nodes_dict = fill_nodes_dict_from_yaml(NODES_YAML_FILE)
front_steer_params_file = pathlib.Path(WORK_DIR, 'Data', 'Рулевая', DEFAULT_DIR, PARAMETERS_YAML_FILE)
front_steer_params = fill_par_dict_from_yaml(front_steer_params_file, all_nodes_dict['Рулевая_перед_Томск'])
param_list = front_steer_params['A0.Process state']
i = 0
delay = 100_000_000


def r_par(i):
    try:
        param = param_list[i]
    except IndexError:
        i = 0
        param = param_list[i]
    print(param.name, end='        ')
    print(param.get_value(adapter))
    # if not param.req_list:
    #     param.get_list()
    #
    # if not adapter.can_write(param.node.request_id, param.req_list):
    #     data = adapter.can_read(param.node.answer_id)
    #     if isinstance(data, str):
    #         print(data)
    #     else:
    #         for byt in data:
    #             print(hex(byt), end=' ')
    #         print()
    # else:
    #     print('Не удалось запросить')
    i += 1
    return i


start_time = time.perf_counter_ns()

while True:
    if (time.perf_counter_ns() - delay) > start_time:
        start_time = time.perf_counter_ns()
        i = r_par(i)
