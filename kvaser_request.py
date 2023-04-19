import os
import pathlib
import time

from Kvaser_channel import hardware_kvaser_channels, KvaserChannel

os.environ['KVDLLPATH'] = str(pathlib.Path(pathlib.Path.cwd(), 'Kvaser_Driver_and_dll'))

import canlib.canlib

from kvaser_power import Kvaser
from work_with_file import fill_nodes_dict_from_yaml, NODES_YAML_FILE, fill_par_dict_from_yaml, WORK_DIR, \
    PARAMETERS_YAML_FILE, DEFAULT_DIR

i = 0
delay = 100_000_000

# adapter = Kvaser()
# adapter = Kvaser(bit=250)
all_nodes_dict = fill_nodes_dict_from_yaml(NODES_YAML_FILE)
front_steer_params_file = pathlib.Path(WORK_DIR, 'Data', 'Рулевая', DEFAULT_DIR, PARAMETERS_YAML_FILE)
front_steer_params = fill_par_dict_from_yaml(front_steer_params_file, all_nodes_dict['Рулевая_перед_Томск'])
param_list = front_steer_params['A0.Process state']
# param_list = ['A0.Process state']


#
ttc_params_file = pathlib.Path(WORK_DIR, 'Data', 'КВУ_ТТС', DEFAULT_DIR, PARAMETERS_YAML_FILE)
ttc_params = fill_par_dict_from_yaml(ttc_params_file, all_nodes_dict['КВУ_ТТС'])
ttc_param_list = ttc_params['abs']


def r_par(itr, adapter, param_list=None):
    if param_list is None:
        param_list = param_list
    try:
        param = param_list[itr]
    except IndexError:
        itr = 0
        param = param_list[itr]
    print(param.name, end='        ')
    print(param.get_value(adapter))
    itr += 1
    return itr


def read_can(canal):
    if getattr(canal, 'ch'):
        if isinstance(canal.ch, canlib.canlib.Channel):
            frame = canal.ch.read()
            print(hex(frame.id))
        else:
            print('no Channel')
    else:
        print('no ch in canal')
        canal.ch = canal.canal_open()


channel_dict = hardware_kvaser_channels()
print(channel_dict)
adapter_dict = {}
for channel, bit in channel_dict.items():
    adapter_dict[bit] = KvaserChannel(channel=channel, bitrate=bit)

# quit()
start_time = time.perf_counter_ns()
i = 0
j = 0
while True:
    if (time.perf_counter_ns() - delay) > start_time:
        start_time = time.perf_counter_ns()
        i = r_par(i, adapter=adapter_dict[125], param_list=param_list)
        j = r_par(j, adapter=adapter_dict[250], param_list=ttc_param_list)

