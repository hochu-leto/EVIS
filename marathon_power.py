import ctypes
import pathlib
import time
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
from datetime import datetime

from AdapterCAN import AdapterCAN

error_codes = {

    65535 - 0: 'Адаптер не подключен',
    65535 - 1: 'generic (not specified) error',
    65535 - 2: 'device or recourse busy',
    65535 - 3: 'memory fault',
    65535 - 4: "function can't be called for chip in current state",
    65535 - 5: "invalid call, function can't be called for this object",
    65535 - 6: 'invalid parameter - номер канала, переданный в качестве параметра, выходит за '
               'пределы поддерживаемого числа каналов, либо канал не был открыт;',
    65535 - 7: 'can not access resource',
    65535 - 8: 'function or feature not implemented - скорость шины не определена',
    65535 - 9: 'Адаптер не подключен',  # input/output error
    65535 - 10: 'no such device or object',
    65535 - 11: 'call was interrupted by event',
    65535 - 12: 'no resources',
    65535 - 13: 'time out occured',
    65535 - 14: 'Нет CAN шины больше секунды ',
    65535 - 15: 'Нет ответа от блока управления',
    65535 - 16: 'Неправильные данные для передачи. Нужен список',
}

from pprint import pprint


class CANMarathon(AdapterCAN):
    BCI_125K_bt0 = 0x03
    BCI_250K_bt0 = 0x01
    BCI_500K_bt0 = 0x00
    BCI_ALL_bt1 = 0x1c
    can_bitrate = {
        125: BCI_125K_bt0,
        250: BCI_250K_bt0,
        500: BCI_500K_bt0
    }

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

    class Request(Structure):
        _fields_ = [
            ('id_req', ctypes.c_uint32),
            ('id_ans', ctypes.c_uint32),
            ('data', ctypes.c_uint8 * 8)
        ]

    def __init__(self, channel=0, bit=125):
        self.lib = cdll.LoadLibrary(str(pathlib.Path(pathlib.Path.cwd(), 'Marathon_Driver_and_dll', 'chai.dll')))
        self.lib.CiInit()
        self.can_canal_number = channel  # по умолчанию нулевой канал
        if bit in self.can_bitrate.keys():
            self.BCI_bt0 = self.can_bitrate[bit]
        else:
            self.BCI_bt0 = self.BCI_125K_bt0  # и скорость 125
        self.is_busy = False

        self.max_iteration = 15
        self.is_canal_open = False
        self.log_file = pathlib.Path(pathlib.Path.cwd(),
                                     'Marathon_logs',
                                     'log_marathon_' +
                                     datetime.now().strftime("%Y-%m-%d_%H-%M") +
                                     '.txt')

    def canal_open(self):
        result = -1
        try:
            result = self.lib.CiOpen(self.can_canal_number,
                                     0x2 | 0x4)  # 0x2 | 0x4 - это приём 11bit и 29bit заголовков
        except Exception as e:
            print('CiOpen do not work')
            # logging.
            pprint(e)
            exit()
        # else:
        #     print('в CiOpen так ' + str(result))

        if result == 0:
            try:
                result = self.lib.CiSetBaud(self.can_canal_number,
                                            self.BCI_bt0, self.BCI_ALL_bt1)
            except Exception as e:
                print('CiSetBaud do not work')
                pprint(e)
                exit()
            # else:
            #     print(' в CiSetBaud так ' + str(result))

            if result == 0:
                try:
                    result = self.lib.CiStart(self.can_canal_number)
                except Exception as e:
                    print('CiStart do not work')
                    pprint(e)
                    exit()
                # else:
                #     print('  в CiStart так ' + str(result))

                if result == 0:
                    self.is_canal_open = True
                    return ''
        self.lib.CiInit()
        self.is_canal_open = False
        if result in error_codes.keys():
            return error_codes[result]
        else:
            return str(result)

    def close_canal_can(self):
        # закрываю канал и останавливаю Марафон
        try:
            result = self.lib.CiStop(self.can_canal_number)
        except Exception as e:
            print('CiStop do not work')
            pprint(e)
            exit()
        # else:
        #     print('      в CiStop так ' + str(result))

        try:
            result = self.lib.CiClose(self.can_canal_number)
        except Exception as e:
            print('CiClose do not work')
            pprint(e)
            exit()
        # else:
        #     print('       в CiClose так ' + str(result))
        self.is_canal_open = False

    def can_write(self, can_id: int, message: list):
        if not isinstance(message, list):
            return error_codes[65535 - 16]

        if not self.is_canal_open:
            err = self.canal_open()
            if err:
                return err

        buffer = self.Buffer()
        buffer.id = ctypes.c_uint32(can_id)
        buffer.len = len(message)
        j = 0
        for i in message:
            buffer.data[j] = ctypes.c_uint8(i)
            j += 1

        if can_id > 0xFFF:
            self.lib.msg_seteff(ctypes.pointer(buffer))

        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        err = -1

        # временно
        # for i in range(self.max_iteration):

        try:
            err = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
        except Exception as e:
            print('CiTransmit do not work')
            pprint(e)
            exit()
            # else:
            #     print('   в CiTransmit так ' + str(err))
        # довольно странная ситуация с записью параметра в устройство. Почему-то параметр записывается не с первого раза
        #  хотя CiTransmit возвращает 0 - успех. Функция CiTrStat - проверка текущего состояния процесса отправки кадров
        # возвращает постоянно 2 но непонятно хорошо это или плохо
        # define CI_TR_COMPLETE_OK    0x0
        # define CI_TR_COMPLETE_ABORT 0x1
        # define CI_TR_INCOMPLETE     0x2
        # define CI_TR_DELAY          0x3
        # Вроде как INCOMPLETE, но параметр записывается. Поэтому принято решение просто пихать CiTransmit
        # max_iteration раз - тогда гарантированно залетает. Возможно, это скажется когда нужно будет запихнуть
        # кучу параметров - тогда придётся как-то решать эту проблему. Причём при запросе параметра с той же CiTransmit
        # ответ приходит сразу же
        # и ещё проблема - при работе с другими блоками, кроме рулевой пихать в него несколько раз одинаковое сообщение
        # может быть не очень гуд. Надо как-то разбираться с этой проблемой.
        # здесь два варианта - или всё нормально передалось и transmit_ok == 0 или все попытки  неудачны и

        # self.close_canal_can()
        if err < 0:
            if err in error_codes.keys():
                return error_codes[err]
            else:
                return str(err)
        return ''

    def can_read(self, ID: int):
        start_time = time.perf_counter()

        if not self.is_canal_open:
            err = self.canal_open()
            # print('Время на открытие канала', time.perf_counter() - start_time)
            if err:
                return err

        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x01, 0))
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        buffer = self.Buffer()
        buffer.id = ctypes.c_uint32(ID)
        buffer.len = 8

        if ID > 0xFFF:
            self.lib.msg_seteff(ctypes.pointer(buffer))

        try:
            self.lib.msg_zero(ctypes.pointer(buffer))
        except Exception as e:
            print('msg_zero do not work')
            pprint(e)
            exit()
        # else:
        #     print('    в msg_zero так ' + str(result))
        # и несколько попыток на считывание ответа
        # print('Время перед циклом', time.perf_counter() - start_time)
        # start_time_с = time.perf_counter()

        for itr_global in range(self.max_iteration):
            # CiRcQueCancel Принудительно очищает (стирает) содержимое приемной очереди канала.
            # наверное, надо почистить очередь перед опросом. но это неточно. совсем неточно
            result = 0
            try:
                result = self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
            except Exception as e:
                print('CiRcQueCancel do not work')
                pprint(e)
                exit()
            # else:
            #     print('     в CiRcQueCancel так ' + str(result))

            try:
                result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 150 миллисекунд
            except Exception as e:
                print('CiWaitEvent do not work')
                pprint(e)
                exit()
            # else:
            #     print('      в CiWaitEvent так ' + str(result))

            # и когда количество кадров в приемной очереди стало больше
            # или равно значению порога - 1
            if result > 0 and cw[0].wflags & 0x01:
                # print('Время когда поймали кадр ', time.perf_counter() - start_time_с)

                # и тогда читаем этот кадр из очереди
                try:
                    result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                except Exception as e:
                    print('CiRead do not work')
                    pprint(e)
                    exit()
                # else:
                #     print('       в CiRead так ' + str(result))
                # если удалось прочитать
                if result >= 0:
                    # print('Время когда прочитали кадр', time.perf_counter() - start_time_с)

                    # print(hex(buffer.id), end='    ')
                    # for e in buffer.data:
                    #     print(hex(e), end=' ')
                    # print()
                    # попался нужный ид
                    if ID == buffer.id:
                        # print('Время когда пришёл нужный айди ', time.perf_counter() - start_time_с)

                        # print(hex(buffer.id), end='    ')
                        # for i in buffer.data:
                        #     print(hex(i), end=' ')
                        # print()
                        return buffer.data
                    # ВАЖНО - здесь канал не закрывается, только возвращается данные кадра
                    else:
                        err = 65535 - 15
                else:
                    err = 'Ошибка при чтении с буфера канала ' + str(result)
            #  если время ожидания хоть какого-то сообщения в шине больше секунды,
            #  значит , нас отключили, уходим
            elif result == 0:
                err = 65535 - 14
            else:
                err = 'Нет подключения к CAN шине '
        #  выход из цикла попыток
        self.close_canal_can()
        if err in error_codes.keys():
            return error_codes[err]
        else:
            return str(err)

    # возвращает массив int если удалось считать и str если ошибка
    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        if not isinstance(message, list):
            return error_codes[65535 - 16]

        # если канал закрыт, его нда открыть
        err = ''
        if not self.is_canal_open:
            err = self.canal_open()
            if err:
                return err

        transmit_ok = 0
        # это массив из 1 элемента - потому что читаем один канал, который мы будем отправлять в
        # функцию ожидания события от марафона 0х01 - значит ждём нового кадра
        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x01, 0))
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        buffer = self.Buffer()

        buffer.id = ctypes.c_uint32(can_id_req)
        # print(hex(buffer.id), end='    ')
        j = 0
        for i in message:
            buffer.data[j] = ctypes.c_uint8(i)
            # print(hex(buffer.data[j]), end=' ')
            j += 1
        # print()
        buffer.len = len(message)
        #  от длины iD устанавливаем протокол расширенный
        if can_id_req > 0xFFF:
            self.lib.msg_seteff(ctypes.pointer(buffer))

        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        # несколько попыток, чтоб передать
        for i in range(self.max_iteration):
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
            except Exception as e:
                print('CiTransmit do not work')
                pprint(e)
                exit()
            # else:
            #     print('   в CiTransmit так ' + str(transmit_ok))
            if transmit_ok == 0:
                break
        # здесь два варианта - или всё нормально передалось и transmit_ok == 0 или все попытки  неудачны и
        if transmit_ok < 0:
            self.close_canal_can()
            if transmit_ok in error_codes.keys():
                return error_codes[transmit_ok]
            else:
                return str(transmit_ok)
        # void msg_zero (canmsg_t *msg) - обнуляет кадр msg; после вызова msg
        # представляет собой кадр стандартного формата (SFF - standart frame format,
        # идентификатор - 11 бит), длина поля данных - ноль, данные и все остальные поля
        # равны нулю;
        # не совсем понимаю зачем это нужно, но на всякий случай пока оставлю
        try:
            result = self.lib.msg_zero(ctypes.pointer(buffer))
        except Exception as e:
            print('msg_zero do not work')
            pprint(e)
            exit()
        # else:
        #     print('    в msg_zero так ' + str(result))
        # и несколько попыток на считывание ответа
        for itr_global in range(self.max_iteration):
            # CiRcQueCancel Принудительно очищает (стирает) содержимое приемной очереди канала.
            # наверное, надо почистить очередь перед опросом. но это неточно. совсем неточно
            result = 0
            try:
                result = self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
            except Exception as e:
                print('CiRcQueCancel do not work')
                pprint(e)
                exit()
            # else:
            #     print('     в CiRcQueCancel так ' + str(result))

            try:
                result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 100)  # timeout = 150 миллисекунд
            except Exception as e:
                print('CiWaitEvent do not work')
                pprint(e)
                exit()
            # else:
            #     print('      в CiWaitEvent так ' + str(result))

            # и когда количество кадров в приемной очереди стало больше
            # или равно значению порога - 1
            if result > 0 and cw[0].wflags & 0x01:
                # и тогда читаем этот кадр из очереди
                try:
                    result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                except Exception as e:
                    print('CiRead do not work')
                    pprint(e)
                    exit()
                # else:
                #     print('       в CiRead так ' + str(result))
                # если удалось прочитать
                if result >= 0:
                    # print(hex(buffer.id), end='    ')
                    # for e in buffer.data:
                    #     print(hex(e), end=' ')
                    # print()
                    # попался нужный ид
                    if can_id_ans == buffer.id:
                        # print(hex(buffer.id), end='    ')
                        # for i in buffer.data:
                        #     print(hex(i), end=' ')
                        # print()
                        return buffer.data
                    # ВАЖНО - здесь канал не закрывается, только возвращается данные кадра
                    else:
                        err = 65535 - 15
                else:
                    err = 'Ошибка при чтении с буфера канала ' + str(result)
            #  если время ожидания хоть какого-то сообщения в шине больше секунды,
            #  значит , нас отключили, уходим
            elif result == 0:
                err = 65535 - 14
            else:
                err = 'Нет подключения к CAN шине '
        #  выход из цикла попыток
        self.close_canal_can()
        if err in error_codes.keys():
            return error_codes[err]
        else:
            return str(err)

    def can_request_many(self, can_id_req: int, can_id_ans: int, messages: list):
        # проверяю что канал Марафона открывается
        c_open = self.canal_open()
        if c_open:
            return c_open
        # ответный список
        answer_list = []
        # буфер данных для запроса - задаю ID для запроса
        buffer = self.Buffer()
        # массив из одного члена для определения события, по которому сработает CiWaitEvent
        # 0x01 это wflags - флаг интересующих нас событий
        #  = количество кадров в приемной очереди стало больше или равно значению порога + ошибка сети
        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x01, 0))
        # определяю переменные, которые отправляются в CiWaitEvent
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        # и в CiTransmit
        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        errors_counter = 0
        len_req_list = len(messages)
        # предполагается, что в messages будут список сообщений по 8 байт для запроса по ID can_id_req
        # поэтому нужно пройти по списку
        for message in messages:
            # если ошибочных сообщений больше трети, что-то здесь не так
            if errors_counter > len_req_list / 3:
                self.close_canal_can()
                return err
            err = ''
            # из-за того, что буфер каждый раз обнуляю, надо заново записывать в него ИД и флаг сообщения
            buffer.id = ctypes.c_uint32(can_id_req)
            # если ID длинный, значит это Extended протокол
            if can_id_req > 0xFFF:
                buffer.flags = 2
                self.lib.msg_seteff(ctypes.pointer(buffer))
            else:
                buffer.flags = 0
            # записываю данные
            j = 0
            for i in message:
                buffer.data[j] = ctypes.c_uint8(i)
                j += 1
            buffer.len = len(message)
            # отправляю запрос. В идеальном мире это должно получиться с первого раза
            # если не будет стабильно получаться, оставлю этот цикл
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
            except Exception as e:
                print('CiTransmit do not work')
                pprint(e)
                exit()
            # else:
            #     print('   в CiTransmit ' + str(transmit_ok))

            # если передача не удалась, запрашиваю следующий параметр
            # при этом в ответный список добавляю строковое сообщение об ошибке
            if transmit_ok < 0:
                if transmit_ok in error_codes.keys():
                    answer_list.append(error_codes[transmit_ok])
                else:
                    answer_list.append('Не удалось передать запрос ' + str(transmit_ok))
                break

            # void msg_zero (canmsg_t *msg) - обнуляет кадр msg; после вызова msg
            # представляет собой кадр стандартного формата (SFF - standart frame format,
            # идентификатор - 11 бит), длина поля данных - ноль, данные и все остальные поля
            # равны нулю;
            # не совсем понимаю зачем это нужно, но на всякий случай пока оставлю
            # если будет и без нее работать, то удалю эту функцию
            try:
                result = self.lib.msg_zero(ctypes.pointer(buffer))
            except Exception as e:
                print('msg_zero do not work')
                pprint(e)
                exit()
            # else:
            #     print('    в msg_zero так ' + str(result))

            # кажется, цикл здесь нужен, если между запросом и ответом влезет сообщение с чужого ID
            # поэтому цикл пусть остается
            for itr_global in range(self.max_iteration):
                result = 0

                # CiRcQueCancel(_u8 chan, _u16 * rcqcnt)
                # Принудительно очищает (стирает) содержимое приемной очереди канала.
                # наверное, надо почистить очередь перед опросом. но это неточно
                try:
                    result = self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
                except Exception as e:
                    print('CiRcQueCancel do not work')
                    pprint(e)
                    exit()
                # else:
                #     print('     в CiRcQueCancel так ' + str(result))

                # теперь самое интересное - ждём события когда появится новое сообщение в очереди
                try:
                    result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд
                except Exception as e:
                    print('CiWaitEvent do not work')
                    pprint(e)
                    exit()
                # else:
                #     print('      в CiWaitEvent так ' + str(result))

                # и когда количество кадров в приемной очереди стало больше
                # или равно значению порога - 1
                if result > 0 and cw[0].wflags & 0x01:
                    # и тогда читаем этот кадр из очереди
                    try:
                        result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                    except Exception as e:
                        print('CiRead do not work')
                        pprint(e)
                        exit()
                    # else:
                    #     print('       в CiRead так ' + str(result))

                    # если удалось прочитать
                    if result >= 0:
                        # попался нужный ид
                        if can_id_ans == buffer.id:
                            # добавляю в список новую строку и прехожу к следующей итерации
                            byte_list = []
                            for i in range(buffer.len):
                                byte_list.append(buffer.data[i])
                            answer_list.append(byte_list)
                            err = ''
                            break
                        else:
                            err = 'Нет ответа от блока управления'
                    else:
                        err = 'Ошибка при чтении с буфера канала ' + str(result)
                #  если время ожидания хоть какого-то сообщения в шине больше секунды,
                #  значит , нас отключили, уходим
                elif result == 0:
                    err = 'Нет CAN шины больше секунды '
                    self.close_canal_can()
                    return err
                else:
                    err = 'Нет подключения к CAN шине '
            if err:
                answer_list.append(err)
                errors_counter += 1
        self.close_canal_can()
        return answer_list

    # возвращает массив int если удалось считать и str если ошибка
    def can_read_all(self):
        # если канал закрыт, его нда открыть
        err = ''
        if not self.is_canal_open:
            err = self.canal_open()
            if err:
                return err

        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x01, 0))
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        buffer = self.Buffer()

        for itr_global in range(self.max_iteration):
            # CiRcQueCancel Принудительно очищает (стирает) содержимое приемной очереди канала.
            # наверное, надо почистить очередь перед опросом. но это неточно. совсем неточно
            result = 0
            try:
                result = self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
            except Exception as e:
                print('CiRcQueCancel do not work')
                pprint(e)
                exit()
            # else:
            #     print('     в CiRcQueCancel так ' + str(result))

            try:
                result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 100)  # timeout = 300 миллисекунд
            except Exception as e:
                print('CiWaitEvent do not work')
                pprint(e)
                exit()
            # else:
            #     print('      в CiWaitEvent так ' + str(result))

            # и когда количество кадров в приемной очереди стало больше
            # или равно значению порога - 1
            if result > 0 and cw[0].wflags & 0x01:
                # и тогда читаем этот кадр из очереди
                try:
                    result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                except Exception as e:
                    print('CiRead do not work')
                    pprint(e)
                    exit()
                # else:
                #     print('       в CiRead так ' + str(result))
                # если удалось прочитать
                if result >= 0:
                    # print(hex(buffer.id), end='    ')
                    # for e in buffer.data:
                    #     print(hex(e), end=' ')
                    # print()
                    return [hex(buffer.id), buffer.len, buffer.flags, buffer.data, buffer.ts]
                    # ВАЖНО - здесь канал не закрывается, только возвращается данные кадра
                else:
                    err = 'Ошибка при чтении с буфера канала ' + str(result)
            #  если время ожидания хоть какого-то сообщения в шине больше секунды,
            #  значит , нас отключили, уходим
            elif result == 0:
                err = 'Нет CAN шины больше секунды '
            else:
                err = 'Нет подключения к CAN шине '
        #  выход из цикла попыток
        self.close_canal_can()
        return err

    def check_bitrate(self):
        # если канал закрыт, его нда открыть
        for name_bit, bit in self.can_bitrate.items():
            print(f'Проверяю битрейт {name_bit}')
            self.BCI_bt0 = bit
            err = self.canal_open()
            if err:
                return err
            array_cw = self.Cw * 1
            cw = array_cw((self.can_canal_number, 0x01, 0))
            self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
            buffer = self.Buffer()
            for itr_global in range(self.max_iteration):
                # CiRcQueCancel Принудительно очищает (стирает) содержимое приемной очереди канала.
                # наверное, надо почистить очередь перед опросом. но это неточно. совсем неточно
                result = 0
                try:
                    result = self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
                except Exception as e:
                    print('CiRcQueCancel do not work')
                    pprint(e)
                    exit()
                try:
                    result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 50)  # timeout = 30 миллисекунд
                except Exception as e:
                    print('CiWaitEvent do not work')
                    pprint(e)
                    exit()
                if result > 0 and cw[0].wflags & 0x01:
                    # и тогда читаем этот кадр из очереди
                    try:
                        result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                    except Exception as e:
                        print('CiRead do not work')
                        pprint(e)
                        exit()
                    if result >= 0:
                        print(hex(buffer.id), end='    ')
                        for e in buffer.data:
                            print(hex(e), end=' ')
                        print()
                        self.close_canal_can()
                        return name_bit
                        # ВАЖНО - здесь канал не закрывается, только возвращается данные кадра
            self.close_canal_can()
        return error_codes[65535 - 8]


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
