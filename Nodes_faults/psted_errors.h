#pragma once

#include "DSP2833x_Device.h"

/**
 * \brief Коды Ошибок в ПСТЭД производства МЭИ (ЭТТ)
 */
struct SPstedFaults {
  Uint32 low_hv            : 1;  //!< 01 Защита от снижения напряжения в ЗПТ
  Uint32 high_hv           : 1;  //!< 02 Защита от повышения напряжения в ЗПТ
  Uint32 overcurrent_phase : 1;  //!< 03 Фазный сверхток
  Uint32 overcurrent_vozb  : 1;  //!< 04 Сверхток в обмотке возбуждения
  Uint32 overcurrent_hv    : 1;  //!< 05 Сверхток в звене постоянного тока
  Uint32 hw_driver_phase   : 1;  //!< 06 Защита драйверов трёхфазного моста
  Uint32 hw_vozb           : 1;  //!< 07 Защита драйверов регулятора тока ОВ
  Uint32 temp_mosfet       : 1;  //!< 08 Температурная защита силовых ключей
  Uint32 temp_invertor    : 1;  //!< 09 Температурная защита преобразователя
  Uint32 temp_motor       : 1;  //!< 10 Температурная защита двигателя
  Uint32 temp_vozb        : 1;  //!< 11 Температурная защита обмотки возбуждения
  Uint32 can_rx           : 1;  //!< 12 Потеря соединения по CAN-шине
  Uint32 can_tx           : 1;  //!< 13 Ошибка передачи данных по CAN-шине
  Uint32 software         : 1;  //!< 14 Программная ошибка
  Uint32 hardware         : 1;  //!< 15 Аппаратная ошибка
  Uint32 cur_sensor_phase : 1;  //!< 16 Отказ датчика фазного тока
  Uint32 cur_sensor_vozb  : 1;  //!< 17 Отказ датчика тока возбуждения
  Uint32 cur_sensor_hv    : 1;  //!< 18 Отказ датчика тока звена постоянного тока
  Uint32 em_stop_cmd      : 1;  //!< 19 Аварийный останов
  Uint32 contactor_switch : 1;  //!< 20 Ошибка включения контакторов
  Uint32 unused           : 11;
  Uint32 unknown          : 1;  //!< 32 Прочие неизвестные ошибки
};

union UPstedFaults {
  SPstedFaults bit;
  struct {
    Uint16 low;
    Uint16 high;
  } u16;
  Uint32 u32;
};

/**
 * \brief Коды Ошибок в ПСТЭД производства Цикл+ (НПФ Вектор)
 * Разбиты на два регистра по 16 бит для совместимости с RTCON
 */
struct SPstedVectorFaults {
  Uint32 vmu_fault                     : 1;  //!< 01 Авария от КВУ
  Uint32 udc_high                      : 1;  //!< 02 Повышение Udc
  Uint32 sw_1khz_fault                 : 1;  //!< 03 Сбой прогр-ы 1кГц
  Uint32 sw_10khz_fault                : 1;  //!< 04 Сбой прогр-ы 10кГц
  Uint32 sw_80khz_fault                : 1;  //!< 05 Сбой прогр-ы 80кГц
  Uint32 rtcon_conn_fault              : 1;  //!< 06 Нет связи с UniCON
  Uint32 settings_load_fault           : 1;  //!< 07 Сбой настроек
  Uint32 incorrect_settings            : 1;  //!< 08 Неверные настройки
  Uint32 adc_fault                     : 1;  //!< 09 Отказ АЦП
  Uint32 low_isolation                 : 1;  //!< 10 Низкая изоляция
  Uint32 udc_low                       : 1;  //!< 11 Понижение ЗПТ
  Uint32 hv_sensor_error               : 1;  //!< 12 Авария датчиков ЗПТ
  Uint32 no_hv_charge                  : 1;  //!< 13 Нет заряда ЗПТ
  Uint32 fault14                       : 1;  //!< 14 Авария 14
  Uint32 fault15                       : 1;  //!< 15 Авария 15
  Uint32 bms_fault_general             : 1;  //!< 16 Авария БМС общая
  Uint32 phase_wire_fault              : 1;  //!< 17 Обрыв фазы
  Uint32 flux_coil_wire_fault          : 1;  //!< 18 Обрыв ОВ
  Uint32 invertor_overheat             : 1;  //!< 19 Перегрев преобразователя
  Uint32 motor_overheat                : 1;  //!< 20 Перегрев двигателя
  Uint32 invertor_hw_fault             : 1;  //!< 21 Аппаратная инвертора
  Uint32 flux_hw_fault                 : 1;  //!< 22 Аппаратная возб.
  Uint32 model_overheat                : 1;  //!< 23 Перегрев по модели
  Uint32 phase_a_overcurrent           : 1;  //!< 24 Макс. ток фазы A
  Uint32 phase_b_overcurrent           : 1;  //!< 25 Макс. ток фазы B
  Uint32 phase_c_overcurrent           : 1;  //!< 26 Макс. ток фазы C
  Uint32 overspeed                     : 1;  //!< 27 Превышение скорости
  Uint32 flux_coil_overcurrent         : 1;  //!< 28 Макс. ток ОВ
  Uint32 current_sensor_fault          : 1;  //!< 29 Отказ датчиков тока
  Uint32 angle_sensor_fault            : 1;  //!< 30 Отказ ДПР
  Uint32 invertor_start_while_charging : 1;  //!< 31 Запуск инв. при акт. ЗУ
  Uint32 invertor_bms_fault            : 1;  //!< 32 Авария БМС инверотора
};

union UPstedVectorFaults {
  SPstedVectorFaults bit;
  struct {
    Uint16 low;
    Uint16 high;
  } u16;
  Uint32 u32;
};
