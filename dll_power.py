import ctypes
from ctypes import *

# /*
# *  Error codes
# */
# define ECIOK      0            /* success */
# define ECIGEN     1            /* generic (not specified) error */
# define ECIBUSY    2            /* device or resourse busy */
# define ECIMFAULT  3            /* memory fault */
# define ECISTATE   4            /* function can't be called for chip in current state */
# define ECIINCALL  5            /* invalid call, function can't be called for this object */
# define ECIINVAL   6            /* invalid parameter */
# define ECIACCES   7            /* can not access resource */
# define ECINOSYS   8            /* function or feature not implemented */
# define ECIIO      9            /* input/output error */
# define ECINODEV   10           /* no such device or object */
# define ECIINTR    11           /* call was interrupted by event */
# define ECINORES   12           /* no resources */
# define ECITOUT    13           /* time out occured */

error_codes = {
    -1: 'generic (not specified) error',
    -2: 'device or resourse busy',
    -3: 'memory fault',
    -4: "function can't be called for chip in current state",
    -5: "invalid call, function can't be called for this object",
    -6: 'invalid parameter',
    -7: 'can not access resource',
    -8: 'function or feature not implemented',
    -9: 'input/output error',
    -10: 'no such device or object',
    -11: 'call was interrupted by event',
    -12: 'no resources',
    -13: 'time out occured',
    65526: 'Адаптер не подключен'
}

from pprint import pprint


def trying():
    class Buffer(Structure):
        _fields_ = [
            ('id', ctypes.c_int32),
            ('data', ctypes.c_int8 * 8),
            ('len', ctypes.c_int8),
            ('flags', ctypes.c_int16),
            ('ts', ctypes.c_int32)
        ]

    class Cw(Structure):
        _fields_ = [
            ('chan', ctypes.c_int8),
            ('wflags', ctypes.c_int8),
            ('rflags', ctypes.c_int8)
        ]

    array_cw = Cw * 2
    cw = array_cw((0, 0x1 | 0x4, 0), (1, 0x1 | 0x4, 0))
    buffer = Buffer()
    lib = cdll.LoadLibrary(r"C:\Program Files (x86)\CHAI-2.14.0\x64\chai.dll")
    lib.CiInit()

    open_canal = -1
    while open_canal < 0:
        lib.CiOpen(0, 0x2 | 0x4)
        lib.CiSetBaud(0, 0x00, 0x1c)
        open_canal = lib.CiStart(0)

    ret = 0
    lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
    can_read = 0
    old_id = 0
    while can_read >= 0:
        while not ret:
            ret = lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд

        can_read = lib.CiRead(0, ctypes.pointer(buffer), 1)
        if old_id != buffer.id:
            print(hex(buffer.id), end='    ')
            for i in range(buffer.len):
                print(hex(buffer.data[i]), end=' ')
            print()
        old_id = buffer.id
        lib.msg_zero(ctypes.pointer(cw))

    lib.CiStop(0)

    lib.CiClose(0)


class CANMarathon:
    class Buffer(Structure):
        _fields_ = [
            ('id', ctypes.c_uint32),
            ('data', ctypes.c_uint8 * 8),
            ('len', ctypes.c_uint8),
            ('flags', ctypes.c_uint16),
            ('ts', ctypes.c_uint32)
        ]

    class Cw(Structure):
        _fields_ = [
            ('chan', ctypes.c_int8),
            ('wflags', ctypes.c_int8),
            ('rflags', ctypes.c_int8)
        ]

    max_iteration = 10
    is_canal_open = False

    def __init__(self):
        self.lib = cdll.LoadLibrary(r"C:\Program Files (x86)\CHAI-2.14.0\x64\chai.dll")
        self.lib.CiInit()
        self.can_canal_number = 0

    def canal_open(self):
        result = -1
        open_canal = -1
        try:
            result = self.lib.CiOpen(self.can_canal_number,
                                     0x2 | 0x4)  # 0x2 | 0x4 - это приём 11bit и 29bit заголовков
        except Exception as e:
            print('CiOpen do not work')
            pprint(e)
            exit()
        else:
            print('в CiOpen так ' + str(result))

        if result != 0:
            self.lib.CiInit()
            if result in error_codes.keys():
                return error_codes[result]
            else:
                return str(result)

        try:
            result = self.lib.CiSetBaud(self.can_canal_number, 0x03, 0x1c)  # 0x03, 0x1c это скорость CAN BCI_125K
        except Exception as e:
            print('CiSetBaud do not work')
            pprint(e)
            exit()
        else:
            print(' в CiSetBaud так ' + str(result))

        if result != 0:
            if result in error_codes.keys():
                return error_codes[result]
            else:
                return str(result)

        try:
            open_canal = self.lib.CiStart(self.can_canal_number)  # 0x00, 0x1c это скорость CAN BCI_500K
        except Exception as e:
            print('CiStart do not work')
            pprint(e)
            exit()
        else:
            print('  в CiStart так ' + str(open_canal))

        if open_canal != 0:
            self.is_canal_open = False
            if result in error_codes.keys():
                return error_codes[result]
            else:
                return str(result)

        self.is_canal_open = True
        return ''

    def check_connection(self):
        effort = self.canal_open()
        if effort:
            return effort
        self.lib.CiStop(self.can_canal_number)
        self.lib.CiClose(self.can_canal_number)
        return ''

    def can_read(self, can_id: int):
        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x1 | 0x4, 0))  # 0x1 | 0x4 - это wflags - флаги интересующих нас событий
        #  = количество кадров в приемной очереди стало больше или равно значению порога + ошибка сети
        buffer = self.Buffer()
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]

        c_open = self.canal_open()
        if c_open:
            return c_open

        for i in range(self.max_iteration):
            # ret = 0
            # while not ret:
            ret = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд

            if ret > 0:
                if cw[0].wflags & 0x01:  # количество кадров в приемной очереди стало больше
                    # или равно значению порога
                    can_read = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                    if can_read >= 0:
                        print(hex(buffer.id) + ' = ' + hex(can_id))
                        if can_id == buffer.id:  #
                            print(hex(buffer.id), end='    ')
                            for i in range(buffer.len):
                                print(hex(buffer.data[i]), end=' ')
                            print()
                            self.lib.CiStop(self.can_canal_number)
                            self.lib.CiClose(self.can_canal_number)
                            return buffer.data
                    else:
                        ret = can_read
                        print('Ошибка при чтении с буфера канала ')
                elif cw[0].wflags == 0x04:  # ошибка сети
                    print('ошибка сети EWL, BOFF, HOVR, SOVR, или WTOUT')
                    # здесь процедурой CiErrsGetClear надо вычислить что за ошибка
        self.lib.CiStop(self.can_canal_number)
        self.lib.CiClose(self.can_canal_number)
        if ret in error_codes.keys():
            return error_codes[ret]
        else:
            return str(ret)

    def can_write(self, can_id: int, message: list):

        c_open = self.canal_open()
        if c_open:
            return c_open

        buffer = self.Buffer()
        buffer.id = ctypes.c_uint32(can_id)
        j = 0
        for i in message:
            buffer.data[j] = ctypes.c_uint8(i)
            j += 1
        buffer.len = len(message)
        if can_id > 0xFFF:
            buffer.flags = 2
        else:
            buffer.flags = 0
        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]

        for i in range(self.max_iteration):
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
                # print(f'Trying to send in address {hex(buffer.id)} message {hex(buffer.data[0])} {hex(buffer.data[1])}')
            except Exception as e:
                print('CiTransmit do not work')
                pprint(e)
                exit()
            else:
                print('   в CiTransmit так ' + str(transmit_ok))
            if transmit_ok == 0:
                self.lib.CiStop(self.can_canal_number)
                self.lib.CiClose(self.can_canal_number)
                return ''

        self.lib.CiStop(self.can_canal_number)
        self.lib.CiClose(self.can_canal_number)
        if transmit_ok in error_codes.keys():
            return error_codes[transmit_ok]
        else:
            return str(transmit_ok)

    def can_write_fast(self, can_id: int, message: list):
        # перед запуском убрать коммент!!!!!!!!!!!!!!
        if not self.is_canal_open:
            c_open = self.canal_open()
            if c_open:
                return c_open

        buffer = self.Buffer()
        buffer.id = ctypes.c_uint32(can_id)
        print(hex(buffer.id), end='    ')
        j = 0
        for i in message:
            buffer.data[j] = ctypes.c_uint8(i)
            print(hex(buffer.data[j]), end=' ')
            j += 1
        print()
        buffer.len = len(message)
        if can_id > 0xFFF:
            buffer.flags = 4
        else:
            buffer.flags = 0
        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        transmit_ok = 0
        for i in range(self.max_iteration):
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
            except Exception as e:
                print('CiTransmit do not work')
                pprint(e)
                exit()

            if transmit_ok == 0:
                return ''

        if self.is_canal_open:
            self.lib.CiStop(self.can_canal_number)
            self.lib.CiClose(self.can_canal_number)
            self.is_canal_open = False

        if transmit_ok in error_codes.keys():
            return error_codes[transmit_ok]
        else:
            return str(transmit_ok)

    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x01, 0))  # 0x1 | 0x4 - это wflags - флаги интересующих нас событий
        #  = количество кадров в приемной очереди стало больше или равно значению порога + ошибка сети
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        buffer = self.Buffer()
        buffer.id = ctypes.c_uint32(can_id_req)
        j = 0
        for i in message:
            buffer.data[j] = ctypes.c_uint8(i)
            j += 1
        buffer.len = len(message)
        if can_id_req > 0xFFF:
            buffer.flags = 2
        else:
            buffer.flags = 0
        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]

        c_open = self.canal_open()
        if c_open:
            return c_open

        for i in range(self.max_iteration):
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
            except Exception as e:
                print('CiTransmit do not work')
                pprint(e)
                exit()
            else:
                print('   в CiTransmit так ' + str(transmit_ok))
            if transmit_ok == 0:
                break
        if transmit_ok < 0:
            if transmit_ok in error_codes.keys():
                return error_codes[transmit_ok]
            else:
                return str(transmit_ok)

        try:
            result = self.lib.msg_zero(ctypes.pointer(buffer))
        except Exception as e:
            print('msg_zero do not work')
            pprint(e)
            exit()
        else:
            print('    в msg_zero так ' + str(result))

        for itr_global in range(self.max_iteration):
            try:
                result = self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
            except Exception as e:
                print('CiRcQueCancel do not work')
                pprint(e)
                exit()
            else:
                print('     в CiRcQueCancel так ' + str(result))

            ret = 0
            can_read = 0
            # while ret <= 0:  # если адаптер подключен к юсб но не подключен к КАНу - здесь возникает вечный Цикл
            # for itr in range(self.max_iteration):
            try:
                ret = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд
            except Exception as e:
                print('CiWaitEvent do not work')
                pprint(e)
                exit()
            else:
                print('      в CiWaitEvent так ' + str(ret))

            # if ret > 0:
            #     break
            # if ret <= 0:
            #     print(' It seems like there is no CAN bus here')
            #     return False
            if ret > 0 and cw[0].wflags & 0x01:  # количество кадров в приемной очереди стало больше
                # или равно значению порога
                try:
                    can_read = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                except Exception as e:
                    print('CiRead do not work')
                    pprint(e)
                    exit()
                else:
                    print('       в CiRead так ' + str(can_read))
                print('Принято сообщение с ID  ' + hex(buffer.id))
                if can_read >= 0:
                    if can_id_ans == buffer.id:  # попался нужный ид
                        print('Iteration = ' + str(itr_global))
                        print(hex(buffer.id), end='    ')
                        for i in range(buffer.len):
                            print(hex(buffer.data[i]), end=' ')
                        print()

                        try:
                            result = self.lib.CiStop(self.can_canal_number)
                        except Exception as e:
                            print('CiStop do not work')
                            pprint(e)
                            exit()
                        else:
                            print('      в CiStop так ' + str(result))

                        try:
                            result = self.lib.CiClose(self.can_canal_number)
                        except Exception as e:
                            print('CiClose do not work')
                            pprint(e)
                            exit()
                        else:
                            print('       в CiClose так ' + str(result))

                        return buffer.data
                    else:
                        print(' Не тот ИД')
                else:
                    print('Ошибка при чтении с буфера канала ')
                    ret = can_read
            else:
                print(' Нет события или нет нового байта')
            # else:  # if cw[0].wflags == 0x04:  # ошибка сети
            #     print('ошибка сети EWL, BOFF, HOVR, SOVR, или WTOUT')
            # здесь процедурой CiErrsGetClear надо вычислить что за ошибка
        self.lib.CiStop(self.can_canal_number)
        self.lib.CiClose(self.can_canal_number)
        if ret in error_codes.keys():
            return error_codes[ret]
        else:
            return str(ret)

if __name__ == "__main__":
    #  trying()
    marathon = CANMarathon()
    # marathon.can_write(0x4F5, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2B,
    #                                  0x03])  # запрос у передней рулевой рейки порядок
    # print(marathon.can_read(0x4F7))
    # передачи байт многобайтных параметров, 0x00 - прямой, 0x01 - обратный
    # m = False
    # while not m:
    m = marathon.can_request(0x4F5, 0x4F7, [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2B,
                                            0x03])  # запрос у передней рулевой рейки порядок
