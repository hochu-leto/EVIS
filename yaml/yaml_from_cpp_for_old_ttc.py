import yaml

from helper import int_to_hex_str
from parse_yaml_for_burr import check_dict
from parse_yml_params import convert_types

# file_name = 'iolib_errors.yml'
# with open(file_name, "r", encoding="UTF8") as stream:
#     try:
#         vmu_ttc_ioe = yaml.safe_load(stream)
#     except yaml.YAMLError as exc:
#         print(exc)
#     except UnicodeDecodeError as exc:
#         print(' iolib_errors', exc)
# iolib_errors_dict = vmu_ttc_ioe['iolib_errors']
iolib_errors_dict = {0: 'OK',
                     2: 'BUSY',
                     3: 'UNKNOWN',
                     5: 'DRV_SAFETY_CONF_NOT_CONFIG',
                     6: 'INVALID_SAFETY_CONFIG',
                     7: 'DRV_SAFETY_CYCLE_RUNNING',
                     10: 'OPEN_LOAD',
                     11: 'SHORT_GND',
                     12: 'SHORT_BAT',
                     13: 'OPEN_LOAD_OR_SHORT_BAT',
                     14: 'INVALID_VOLTAGE',
                     15: 'NO_DIAG',
                     16: 'STARTUP',
                     17: 'SAFE_STATE',
                     18: 'REFERENCE',
                     19: 'SAFETY_SWITCH_DISABLED',
                     20: 'FET_PROT_ACTIVE',
                     21: 'FET_PROT_PERMANENT',
                     22: 'FET_PROT_REENABLE',
                     23: 'FET_PROT_WAIT',
                     24: 'FET_PROT_NOT_ACTIVE',
                     25: 'RESOLVING',
                     26: 'RESOLVING_FAILED',
                     30: 'NULL_POINTER',
                     31: 'INVALID_PARAMETER',
                     32: 'CHANNEL_BUSY',
                     33: 'CHANNEL_NOT_CONFIGURED',
                     34: 'INVALID_CHANNEL_ID',
                     35: 'INVALID_LIMITS',
                     36: 'PERIODIC_NOT_CONFIGURED',
                     37: 'CH_CAPABILITY',
                     38: 'DRIVER_NOT_INITIALIZED',
                     39: 'INVALID_OPERATION',
                     40: 'CAN_OVERFLOW',
                     41: 'CAN_WRONG_HANDLE',
                     42: 'CAN_MAX_MO_REACHED',
                     43: 'CAN_MAX_HANDLES_REACHED',
                     44: 'CAN_FIFO_FULL',
                     45: 'CAN_OLD_DATA',
                     46: 'CAN_ERROR_PASSIVE',
                     47: 'CAN_BUS_OFF',
                     48: 'CAN_ERROR_WARNING',
                     49: 'CAN_TIMEOUT',
                     60: 'EEPROM_RANGE',
                     70: 'UART_BUFFER_FULL',
                     71: 'UART_BUFFER_EMPTY',
                     72: 'UART_OVERFLOW',
                     73: 'UART_PARITY',
                     74: 'UART_FRAMING',
                     101: 'PWD_NOT_FINISHED',
                     102: 'PWD_OVERFLOW',
                     104: 'PWD_CURRENT_THRESH_HIGH',
                     105: 'PWD_CURRENT_THRESH_LOW',
                     146: 'CM_CALIBRATION',
                     200: 'FPGA_NOT_INITIALIZED',
                     201: 'FPGA_TIMEOUT',
                     202: 'FPGA_CRC_ERROR',
                     203: 'FPGA_VERSION',
                     240: 'WD_RANGE',
                     241: 'WD_INITIALIZATION',
                     242: 'WD_PRECISION',
                     243: 'WD_ACTIVATION',
                     244: 'WD_TRIGGER',
                     245: 'WD_SAFE_LOCK',
                     246: 'WD_DEBUGGING_PREPARED',
                     247: 'WD_SELF_MONITORING',
                     248: 'WD_VICE_VERSA_MONITORING',
                     249: 'WD_STATUS_INVALID',
                     250: 'RTC_CLOCK_INTEGRITY_FAILED',
                     260: 'LIN_BIT',
                     261: 'LIN_PHYSICAL_BUS',
                     262: 'LIN_CHECKSUM',
                     263: 'LIN_INCONSISTENT_SYNCH_FIELD',
                     264: 'LIN_NO_RESPONSE',
                     265: 'LIN_FRAMING',
                     266: 'LIN_OVERRUN',
                     267: 'LIN_PARITY',
                     268: 'LIN_TIMEOUT',
                     269: 'FLASH_WRONG_DEVICE_ID',
                     270: 'FLASH_BLANK_CHECK_FAILED',
                     271: 'FLASH_OP_FAILED',
                     272: 'FLASH_OP_TIMEOUT',
                     282: 'INVALID_VARIANT',
                     283: 'INVALID_PROD_DATA',
                     284: 'INVALID_PIN_CONFIG',
                     285: 'INVALID_SERIAL_NUMBER',
                     286: 'CORE_TEST_FAILED',
                     287: 'ERROR_PIN_TEST_TIMEOUT',
                     288: 'ERROR_PIN_TEST_FAILED',
                     289: 'INTERNAL_MEM_FAILED',
                     290: 'INVALID_ESM_INIT_STATUS',
                     292: 'INTERNAL_CSM',
                     300: 'ETH_INIT_FAIL',
                     301: 'ETH_INIT_TIMEOUT',
                     302: 'ETH_DEINIT_TIMEOUT',
                     303: 'ETH_MAC_INVALID',
                     304: 'ETH_READ_FAIL',
                     305: 'ETH_WRITE_FAIL',
                     306: 'ETH_NO_LINK',
                     307: 'ETH_MDIO_TIMEOUT',
                     308: 'ETH_MDIO_READ',
                     310: 'DOWNLOAD_NO_REQ',
                     311: 'DOWNLOAD_TIMEOUT',
                     312: 'DOWNLOAD_HANDSHAKE',
                     320: 'SHM_INTEGRITY',
                     330: 'MPU_REGION_ENABLED',
                     331: 'MPU_REGION_DISABLED',
                     340: 'OPTION_NOT_SUPPORTED',
                     440: 'UDP_NOMORESOCKETS',
                     442: 'UDP_OVERFLOW',
                     443: 'UDP_WRONG_HANDLE',
                     444: 'SOCKET_NOT_INITIALIZED',
                     445: 'WRONG_ADDRESS',
                     446: 'UDP_INVALID_BUFFER',
                     447: 'UDP_WRONG_PORT',
                     449: 'UDP_ARP_RECEIVED',
                     }

file_name = 'canopen_parameters.yml'
with open(file_name, "r", encoding="UTF8") as stream:
    try:
        canopen_vmu_ttc = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)
    except UnicodeDecodeError as exc:
        print(' canopen_parameters', exc)

parse_dict = {}
for group, group_list in canopen_vmu_ttc['canopen_parameters'].items():
    for par in group_list:
        parse_dict[par['name'].upper().strip()] = par

file_name = 'co_dictionary_old_ttc.cpp'  # fd.askopenfilename()
with open(file_name, "r") as file:
    try:
        nodes = file.readlines()
    except UnicodeDecodeError as exc:
        print(exc)
coun = 0
final_list = []
group_par_dict = {}
prev_name = ''
for tag in nodes:
    tg = {}
    if ' // ' in tag or ' /* ' in tag:
        group_par_dict[prev_name] = final_list.copy()
        final_list.clear()
        prev_name = tag.strip()[3:].replace('-', '')
    elif 'static_cast' in tag:
        t = tag.split(',')
        tg['address'] = t[0].strip()[8:] + (hex(int(t[1].strip()))[2:].zfill(2)).upper()
        tg['type'] = t[2].strip()[3:-16].strip()
        tg['editable'] = True if 'RW' in t[2] else False
        tg['name'] = t[4].strip()[30:-1]
        name_par = tg['name'].upper().strip()
        if name_par in parse_dict.keys():
            coun += 1
            print('Совпадение', name_par, coun)
            parametr = parse_dict[name_par]
            tg['description'] = parametr['description'].strip().replace('\n', '')
            if 'units' in parametr.keys():
                tg['unit'] = parametr['units']
            if 'value' in parametr.keys():
                tg['value'] = parametr['value']
            if 'mult' in parametr.keys():
                tg['scale'] = 1 / parametr['mult']
            if 'offset' in parametr.keys():
                tg['scaleB'] = parametr['offset']
            if 'value_table' in parametr.keys():
                tg['value_table'] = parametr['value_table']

            if 'iolib_errors' in parametr['description']:
                tg['value_table'] = iolib_errors_dict.copy()
    if tg:
        final_list.append(tg.copy())
del group_par_dict['']
with open(r'../Data/КВУ_ТТС/1.4.0/parameters.yaml', 'w', encoding='UTF8') as file:
    documents = yaml.dump(check_dict(group_par_dict), file, allow_unicode=True)
