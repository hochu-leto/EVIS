import ctypes
import pathlib
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
complete_dict = {0x0: 'CI_TR_COMPLETE_OK – последняя передача в сеть была успешной',
                 0x1: 'CI_TR_COMPLETE_ABORT – последняя передача в сеть была сброшена',
                 0x2: 'CI_TR_INCOMPLETE – контроллер передает кадр в сеть',
                 0x3: 'CI_TR_DELAY'}


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

    long_buffer_60 = Buffer()
    long_buffer_60.data[0] = 0x60
    long_buffer_60.len = 8

    long_buffer_70 = Buffer()
    long_buffer_70.data[0] = 0x70
    long_buffer_70.len = 8

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
        # это массив из 1 элемента - потому что читаем один канал, который мы будем отправлять в
        # функцию ожидания события от марафона 0х01 - значит ждём нового кадра
        array_cw = self.Cw * 1
        self.cw = array_cw((self.can_canal_number, 0x01, 0))
        self.lib.CiWaitEvent.argtypes = [ctypes.POINTER(array_cw), ctypes.c_int32, ctypes.c_int16]
        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        self.buffer_array = self.Buffer * 1000

    def canal_open(self):
        result = -1
        try:
            result = self.lib.CiOpen(self.can_canal_number,
                                     0x2 | 0x4)  # 0x2 | 0x4 - это приём 11bit и 29bit заголовков
        except Exception as e:
            print('CiOpen do not work')
            # logging.
            exit()
        # else:
        #     print('в CiOpen так ' + str(result))

        if result == 0:
            try:
                result = self.lib.CiSetBaud(self.can_canal_number,
                                            self.BCI_bt0, self.BCI_ALL_bt1)
            except Exception as e:
                print('CiSetBaud do not work')
                exit()
            # else:
            #     print(' в CiSetBaud так ' + str(result))

            if result == 0:
                try:
                    result = self.lib.CiStart(self.can_canal_number)
                except Exception as e:
                    print('CiStart do not work')
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
            exit()
        # else:
        #     print('      в CiStop так ' + str(result))

        try:
            result = self.lib.CiClose(self.can_canal_number)
        except Exception as e:
            print('CiClose do not work')
            
            exit()
        # else:
        #     print('       в CiClose так ' + str(result))
        self.is_canal_open = False

    '''
    довольно странная ситуация с записью параметра в устройство. Почему-то параметр записывается не с первого раза
     хотя CiTransmit возвращает 0 - успех. Функция CiTrStat - проверка текущего состояния процесса отправки кадров
    возвращает постоянно 2 но непонятно хорошо это или плохо
    define CI_TR_COMPLETE_OK    0x0
    define CI_TR_COMPLETE_ABORT 0x1
    define CI_TR_INCOMPLETE     0x2
    define CI_TR_DELAY          0x3
    Вроде как INCOMPLETE, но параметр записывается. Поэтому принято решение просто пихать CiTransmit
    max_iteration раз - тогда гарантированно залетает. Возможно, это скажется когда нужно будет запихнуть
    кучу параметров - тогда придётся как-то решать эту проблему. Причём при запросе параметра с той же CiTransmit
    ответ приходит сразу же
    и ещё проблема - при работе с другими блоками, кроме рулевой пихать в него несколько раз одинаковое сообщение
    может быть не очень гуд. Надо как-то разбираться с этой проблемой.
    здесь два варианта - или всё нормально передалось и transmit_ok == 0 или все попытки  неудачны и
    _s16 CiTrStat(_u8 chan, _u16 * trqcnt)
    Возвращает текущее состояние процесса отправки кадров канала ввода-вывода:
    ● chan - номер канала
    ● trqcnt - указатель на переменную, куда записывается количество кадров находящихся в очереди на отправку;
    '''

    def can_write(self, can_id: int, message: list):
        if not isinstance(message, list):
            return error_codes[65535 - 16]  # надо исправлять это безобразие

        if not self.is_canal_open:
            err = self.canal_open()
            if err:
                return err

        buffer = self.Buffer()
        buffer.id = ctypes.c_uint32(can_id)
        buffer.len = len(message)
        # print(f'Отправляю   {hex(buffer.id)}  {buffer.len}  ', end=' ')
        j = 0
        for i in message:
            # print(hex(i), end=' ')
            buffer.data[j] = ctypes.c_uint8(i)
            j += 1
        # print()
        if can_id > 0xFFF:
            self.lib.msg_seteff(ctypes.pointer(buffer))

        self.lib.CiTransmit.argtypes = [ctypes.c_int8, ctypes.POINTER(self.Buffer)]
        err = -1
        try:
            err = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
            err = ctypes.c_int16(err).value
        except Exception as e:
            print('CiTransmit do not work')
            self.close_canal_can()
            return 'can_write CiTransmit do not work'

            # exit()
        else:
            pass
            # print('   в CiTransmit так ' + str(err))

        if not err:
            trqcnt = ctypes.c_int16(20)
            for i in range(self.max_iteration):
                try:
                    err = self.lib.CiTrStat(self.can_canal_number, ctypes.pointer(trqcnt))
                    err = ctypes.c_int16(err).value
                except Exception as e:
                    print('CiTransmit do not work')
                    self.close_canal_can()
                    return 'can_write CiTransmit do not work'

                    # exit()
                else:
                    pass
                    # print(f'   в CiTrStat так {complete_dict[err]}, осталось кадров на передачу {trqcnt.value} ')
                if not trqcnt.value and not err:
                    return ''
            err = 65535 - 2  # надо исправлять это безобразие

        if err in error_codes.keys():
            return error_codes[err]
        else:
            return str(err)

    # возвращает список массивов int - всю дату, что есть в буфере адаптера если удалось считать и str если ошибка
    def can_read(self, ID: int):
        if not self.is_canal_open:
            err = self.canal_open()
            if err:
                return err

        array_cw = self.Cw * 1
        cw = array_cw((self.can_canal_number, 0x01, 0))
        buffer_array = self.Buffer * 1000
        buffer_a = buffer_array()
        result = 0
        try:  # 1 = в одном из каналов. timeout = 10 миллисекунд
            result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 10)
        except Exception as e:
            print('CiWaitEvent do not work')
            
            exit()
        result = ctypes.c_int16(result).value

        if result > 0:
            '''
            _s16 CiRead(_u8 chan, canmsg_t *mbuf, _s16 cnt)
            Описание:
            Вынимает cnt кадров из очереди на прием и сохраняет их в буфере mbuf. Если в приемной
            очереди кадров меньше чем cnt, сохраняет столько кадров сколько есть в очереди. Функция
            возвращает управление сразу (не ожидает приема из сети запрошенного количества кадров
            cnt). 
                    '''
            try:
                result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer_a), 1000)
            except Exception as e:
                print('CiRead do not work')
                
                exit()
            result = ctypes.c_int16(result).value
            if result >= 0:
                data_list = []
                time_data_dict = {}
                for i in range(result):
                    buff = buffer_a[i]
                    if ID == buff.id:
                        time_data_dict[ctypes.c_uint32(buff.ts).value] = buff.data
                        data_list.append(buff.data)
                if time_data_dict:
                    try:
                        self.lib.CiRcQueCancel(self.can_canal_number, ctypes.pointer(create_unicode_buffer(10)))
                    except Exception as e:
                        print('CiRcQueCancel do not work')
                        
                        exit()
                    return time_data_dict
                else:
                    return 'Нет нужного ID в буфере'  # надо исправлять это безобразие
                # return data_list if data_list else 'Нет нужного ID в буфере'
        elif result == 0:
            return 'Время вышло, кадры не получены'
        return f'В CiWaitEvent ошибка {result}'

    # возвращает массив int если удалось считать и str если ошибка
    def can_request(self, can_id_req: int, can_id_ans: int, message: list):
        if not isinstance(message, list):
            return error_codes[65535 - 16]  # надо исправлять это безобразие

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
        # print(hex(self.BCI_bt0), end='    ')
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

        for i in range(self.max_iteration):
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(buffer))
            except Exception as e:
                print('CiTransmit do not work')
                self.close_canal_can()
                return 'can_request CiTransmit do not work'

                # exit()
            # else:
            #     print('   в CiTransmit так ' + str(transmit_ok))
            if transmit_ok == 0:
                break
        # здесь два варианта - или всё нормально передалось и transmit_ok == 0 или все попытки  неудачны и
        if transmit_ok < 0:
            self.close_canal_can()
            # print(f'закрытие канала {transmit_ok=}')

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
            self.lib.msg_zero(ctypes.pointer(buffer))
        except Exception as e:
            print('msg_zero do not work')
            
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
                
                exit()
            # else:
            #     print('     в CiRcQueCancel так ' + str(result))

            try:
                result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 100)  # timeout = 100 миллисекунд
            except Exception as e:
                print('CiWaitEvent do not work')
                
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
                        # print(buffer.ts)
                        return buffer.data
                    # ВАЖНО - здесь канал не закрывается, только возвращается данные кадра
                    else:
                        err = 65535 - 15  # надо исправлять это безобразие
                else:
                    err = 'Ошибка при чтении с буфера канала ' + str(result)
            #  если время ожидания хоть какого-то сообщения в шине больше секунды,
            #  значит , нас отключили, уходим
            elif result == 0:
                err = 65535 - 14  # надо исправлять это безобразие
            else:
                err = 'Нет подключения к CAN шине '  # надо исправлять это безобразие
        #  выход из цикла попыток
        # print('закрытие канала')
        self.close_canal_can()
        if err in error_codes.keys():
            return error_codes[err]
        else:
            return str(err)

    def can_request_long(self, can_id_req: int, can_id_ans: int, l_byte):  # , message: list):
        err = ''
        frame_counter = 0
        transmit_ok = -1
        buffer_a = self.buffer_array()
        exit_list = []
        result = 0

        if not self.is_canal_open:
            err = self.canal_open()
            if err:
                return err
        req_id = ctypes.c_uint32(can_id_req)
        self.long_buffer_60.id = req_id
        self.long_buffer_70.id = req_id
        if can_id_req > 0xFFF:
            self.lib.msg_seteff(ctypes.pointer(self.long_buffer_60))
            self.lib.msg_seteff(ctypes.pointer(self.long_buffer_70))
        # длинное сообщение состоит из нескольких фрэймов , сколько их - узнаём количество значащих байт
        # из первого фрейма с ответом 0х41 и делим на 7 значащих байт в следующих фреймов + 1 про запас
        for frame_counter in range((l_byte // 7) + 1):
            bf = self.long_buffer_70 if frame_counter % 2 else self.long_buffer_60
            # print()
            # print(f'отправляю {hex(bf.id)} ', end='   ')
            # for i in bf.data:
                # print(hex(i), end=' ')
            ''' _s16 CiTransmit(_u8 chan, canmsg_t * mbuf)
                Отправляет кадр в сеть через очередь на отправку.
                Если очередь на передачу не пуста, то кадр помещается в конец очереди, возвращается код
                успеха. В противном случае, если аппаратный буфер на отправку свободен, то кадр
                загружается в регистры CAN-контроллера и выставляется запрос на передачу кадра, если
                буфер занят, кадр помещается в очередь. 
                ● chan - номер канала;
                ● mbuf - указатель на буфер в котором находится CAN-кадр;
                Возвращаемое значение:
                0 - успешное выполнение 
                < 0 - ошибка  '''
            try:
                transmit_ok = self.lib.CiTransmit(self.can_canal_number, ctypes.pointer(bf))
            except Exception as e:
                print('CiTransmit do not work')
                print(e)
                self.close_canal_can()
                return 'can_request_long CiTransmit do not work'
                # self.canal_open()

            if transmit_ok < 0:
                self.close_canal_can()
                if transmit_ok in error_codes.keys():
                    return error_codes[transmit_ok]
                else:
                    return str(transmit_ok)
            next_frame = False
            while not next_frame:
                print()
                '''
                _s16 CiWaitEvent(canwait_t * cw, int cwcount, int tout)
                Блокирует работу потока выполнения до наступления заданного события или до
                наступления тайм-аута в одном из указанных каналов ввода-вывода. Каналы ввода-вывода и
                интересующие события задаются с помощью массива структур canwait_t
                Возвращаемое значение:
                > 0 - успешное выполнение: произошло одно из указанных событий;
                = 0 - тайм-аут;
                < 0 - ошибка
                '''
                try:
                    result = self.lib.CiWaitEvent(ctypes.pointer(self.cw), 1, 500)  # timeout = 100 миллисекунд
                except Exception as e:
                    print('CiWaitEvent do not work')
                    
                    exit()
                # количество кадров в приемной очереди стало больше или равно значению порога
                if result > 0 and self.cw[0].wflags & 0x01:
                    ''' s16 CiRead(_u8 chan, canmsg_t *mbuf, _s16 cnt)
                        Вынимает cnt кадров из очереди на прием и сохраняет их в буфере mbuf. Если в приемной
                        очереди кадров меньше чем cnt, сохраняет столько кадров сколько есть в очереди. Функция
                        возвращает управление сразу (не ожидает приема из сети запрошенного количества кадров cnt). 
                        ● chan - номер канала
                        ● mbuf - указатель на буфер в который будут скопированы кадры
                        ● cnt – запрашиваемое количество CAN-кадров
                        Возвращаемое значение:
                        >= 0 - успешное выполнение, количество прочитанных кадров
                        < 0 - ошибка '''
                    try:
                        result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer_a), 100)
                    except Exception as e:
                        print('CiRead do not work')
                        
                        exit()
                    # успешное выполнение, количество прочитанных фреймов
                    if result >= 0:
                        # просматриваем все полученные фреймы в поисках нужных ИД, может быть несколько
                        print("Принял ")
                        for w in range(result):
                            buff = buffer_a[w]
                            print(hex(buff.id), end='     ')
                            if can_id_ans == buff.id:
                                next_frame = True
                                for r in range(1, 7):
                                    print(hex(buff.data[r]), end=' ')
                                    exit_list.append(buff.data[r])
                                break
                    else:
                        err = 'Ошибка при чтении с буфера канала ' + str(result)
                # если время ожидания хоть какого-то сообщения в шине больше полсекунды, значит , нас отключили, уходим
                elif result == 0:  # result = 0 - тайм-аут;
                    err = 65535 - 14  # надо исправлять это безобразие
                else:  # result < 0 - ошибка
                    err = 'Нет подключения к CAN шине '  # надо исправлять это безобразие
            # if len(exit_list) > l_byte - 1:
        print()
        print(f'Было отправлено {frame_counter} фреймов, принято {len(exit_list)} байт, возвращаю ')
        if not err:
            return exit_list

        #  выход из цикла попыток
        # print('закрытие канала')
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
                print('can_request_many CiTransmit do not work')
                
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
                    
                    exit()
                # else:
                #     print('     в CiRcQueCancel так ' + str(result))

                # теперь самое интересное - ждём события когда появится новое сообщение в очереди
                try:
                    result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 1000)  # timeout = 1000 миллисекунд
                except Exception as e:
                    print('CiWaitEvent do not work')
                    
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
                
                exit()
            # else:
            #     print('     в CiRcQueCancel так ' + str(result))

            try:
                result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 100)  # timeout = 300 миллисекунд
            except Exception as e:
                print('CiWaitEvent do not work')
                
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
                    
                    exit()
                try:
                    result = self.lib.CiWaitEvent(ctypes.pointer(cw), 1, 50)  # timeout = 30 миллисекунд
                except Exception as e:
                    print('CiWaitEvent do not work')
                    
                    exit()
                if result > 0 and cw[0].wflags & 0x01:
                    # и тогда читаем этот кадр из очереди
                    try:
                        result = self.lib.CiRead(self.can_canal_number, ctypes.pointer(buffer), 1)
                    except Exception as e:
                        print('CiRead do not work')
                        
                        exit()
                    if result >= 0:
                        print(hex(buffer.id), end='    ')
                        for e in buffer.data:
                            print(hex(e), end=' ')
                        print()
                        self.close_canal_can()
                        return name_bit
            self.close_canal_can()
        return error_codes[65535 - 8]  # надо исправлять это безобразие


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
