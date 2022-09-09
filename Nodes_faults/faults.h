/*!
 \file faults.h
 \brief Software module for calculate faults

 \author Aleksey
 \version 1.0
 \date 05.09.2020
 \defgroup
 */

#pragma once

#include "DSP.h"
#include "IQmathLib.h"
#include "Bits_to_enum_numbers.h"

#ifdef __cplusplus
extern "C" {
#endif
enum eFaults1Bits
{
  FAULT1_PSTED      = BIT0,  //!< Критическая ошибка ПСТЭД
  FAULT1_SERVO_STR1 = BIT1,  //!< Критическая ошибка передней рулевой рейки
  FAULT1_SERVO_STR2 = BIT2,  //!< Критическая ошибка задней рулевой рейки
  FAULT1_SERVO_BRK1 = BIT3,  //!< Критическая ошибка сервопривода 1 тормозной системы
  FAULT1_SERVO_BRK2 = BIT4,  //!< Критическая ошибка сервопривода 2 тормозной системы
  FAULT1_FAULT_EMER_STOP       = BIT5,  //!< Сработала кнеопка аварийной остановки
  FAULT1_NO_RUN_PSTED          = BIT6,
  FAULT1_U_DC_SENSOR           = BIT7,
  FAULT1_U_DC_SENSOR_LOW       = BIT8,
  FAULT1_U_DC_SENSOR_HIGH      = BIT9,
  FAULT1_NO_CONNECT_PSTED      = BIT10,  //!< Нет связи с ПСТЭД
  FAULT1_NO_CONNECT_SERVO_RUL1 = BIT11,  //!< Нет связи с передней рулевой рейкой
  FAULT1_NO_CONNECT_SERVO_RUL2 = BIT12,  //!< Нет связи с задней рулевой рейкой
  FAULT1_NO_CONNECT_BKU        = BIT13,  //!< Нет связи с БКУ
  FAULT1_NO_CONNECT_SERVO_BRK1 = BIT14,  //!< Нет связи с сервоприводом 1 тормозной системы
  FAULT1_NO_CONNECT_BMS = BIT15,  //!< Нет связи с сервоприводом 2 тормозной системы
};
// 16
// bit_fault2 - устанавливает общую аварию устройства, а что за авариЯ берём с устройства
// 17
enum eFaults2Bits
{
  FAULT2_CAN_RESTORATION_ERROR = BIT0,  //!< Ошибка загрузки сохраненных параметров из EEPROM
  FAULT2_PROGRAM_BACKGROUND = BIT1,  //!< Фоновый цикл вызывается слишком редко
  FAULT2_PROGRAM_80K        = BIT2,  //!< Прерывание 80кГц выходит за пределы своего бюджета времени
  FAULT2_PROGRAM_10K        = BIT3,  //!< Прерывание 10кГц выходит за пределы своего бюджета времени
  FAULT2_PROGRAM_1K = BIT4,  //!< Прерывание 1кГц выходит за пределы своего бюджета времени
  FAULT2_PPM_1         = BIT5,   //!< Ошибка входа 1 PPM (Управление по радиоканалу)
  FAULT2_PPM_2         = BIT6,   //!< Ошибка входа 2 PPM (Управление по радиоканалу)
  FAULT2_PPM_3         = BIT7,   //!< Ошибка входа 3 PPM (Управление по радиоканалу)
  FAULT2_PPM_4         = BIT8,   //!< Ошибка входа 4 PPM (Управление по радиоканалу)
  FAULT2_PULT_PPM      = BIT9,   //!< Ошибка управления по радиоканалу
  FAULT2_CHARGER_FAULT = BIT10,  //!< Ошибка бортового зарядного устройства
  FAULT2_CHARGER_NO_CONNECT = BIT11,  //!< Нет свзи с бортовым зарядным устройством
  FAULT2_BRAKE_FLUID_LEVEL = BIT12,  //!< Сработал датчик уровня тормозной жидкости
  FAULT2_COOLING_FLUID_LEVEL = BIT13,  //!< Сработал датчик уровня охлаждающей жидкости
  FAULT2_BMS_FAULT           = BIT14,  //!< BMS Fault
  // FAULT2                     = BIT15,
  // 32
};

enum eFaultsState
{
  FAULTS_OFF,
  FAULTS_ON_OK,
  FAULTS_FAIL,
  FAULTS_UNDEFINED,
};

struct SPstedLister {
  // регистры ошибок ПСТЭД для отображения текстом в RTCON
  Uint16          fault_reg1;
  Uint16          fault_reg2;
  SBitsToEnumNums lister;
  Uint16          lister_ctr;
};

typedef volatile struct SPstedLister TPstedLister;

#define DEFAULTS_PSTED_LISTER                                                                                          \
  {                                                                                                                    \
    .lister = BITS_TO_ENUM_NUMS_DEFAULTS, .lister_ctr = 0, .fault_reg1 = 0, .fault_reg2 = 0                            \
  }

struct Sfaults {
  Uint16 fault_code;  //!< листающийся код аварии

  Uint32 bit_faults_mix;

  Uint16 bit_faults1;  //!< Слово аварий
  Uint16 bit_faults2;  //!< Слово аварий

  Uint16 bit_faults1PrevEvent;  //!< Слово аварий для отслеживания фронтов ивентов
  Uint16 bit_faults2PrevEvent;  //!< Слово аварий для отслеживания фронтов ивентов

  Uint16 bit_faultsNoAutoReset1;  //!< Слово аварий, не сбрасывается автоматически при пропаже аварии
  Uint16 bit_faultsNoAutoReset2;  //!< Слово аварий, не сбрасывается автоматически при пропаже аварии

  Uint16 bit_faults_for_stop_1;  //!< Слово аварий, по которым производится аварийный останов
  Uint16 bit_faults_for_stop_2;  //!< Слово аварий, по которым производится аварийный останов

  Uint16 masked_bit_faults1;  //!<Слово аварий после маскированиЯ
  Uint16 masked_bit_faults2;  //!<Слово аварий после маскированиЯ

  Uint16 mask_bit_faults1;  //!< Слово маскированиЯ аварий
  Uint16 mask_bit_faults2;  //!< Слово маскированиЯ аварий

  Uint16 mask_for_stop_faults1;  //!< Слово маскированиЯ аварий, которые приводят к останову
  Uint16 mask_for_stop_faults2;  //!< Слово маскированиЯ аварий, которые приводят к останову

  Uint16 mask_from_apv_ignor_faults1;  //!< Слово маскирования для игнорирования аварий от АПВ
  Uint16 mask_from_apv_ignor_faults2;  //!< Слово маскирования для игнорирования аварий от АПВ

  Uint16 bit_faults_written1;  //!<Бит записи аварии в лог
  Uint16 bit_faults_written2;  //!<Бит записи аварии в лог
  // Параметры аварий
  Uint16 error_reset_flag;
  Uint16 reset_in_progress;
  Uint16 reset_cntr;
  Uint16 reset_timeout;
  bool   reset_psted_in_progress;

  Uint16 WriteCounter;

  // ДА
  Uint16       enable;
  eFaultsState state;
  eFaultsState state_prev;

  SPstedLister psted_lister;

  Uint16 powered_okCounter;
  Uint32 HiDwordFaultMaskForBIUS;
  Uint16 KAU_enabledSignal_prev;
  Uint16 NetworkOnTimeout_ok;
  Uint16 GlobalFaultEmergencyStop;
  Uint16 faultsDevET_buf_iterator;
  Uint32 BackgroundDropCounter;
  Uint16 NumberTDonFault;

  // Уставки для защит
  _iq UdcMin;
  _iq UdcMax;
  _iq UdcDeltaForSensors;
  _iq T_Udc;
  _iq Imax_protect;
  _iq Umax_protect;
  _iq TemprInvert_protect;
  _iq TemprDrive_protect;
  _iq speed_max;
  _iq Uakb_low;  // Минимально-допустимое напрЯжение АКБ

  //!< Удобный интерфейс для маскирования аварий
  //!< Общие аварии
  Uint16 NumOfRWFault;  //часть интерпретатора редактированиЯ аварий
  Uint16 RWFaultState;  //часть интерпретатора редактированиЯ аварий
  Uint16 NumOfRWFaultPrev;
  Uint16 RWFaultStatePrev;
  //!< Аварии для останова
  Uint16 NumOfRWFaultStop;  //часть интерпретатора редактированиЯ аварий
  Uint16 RWFaultStateStop;  //часть интерпретатора редактированиЯ аварий
  Uint16 NumOfRWFaultPrevStop;
  Uint16 RWFaultStatePrevStop;

  void (*calc_init)(volatile struct Sfaults*); /* Pointer to the init funcion           */
  void (*calc_BG)(volatile struct Sfaults*);   /* Pointer to the calc funtion           */
  void (*calc_1k)(volatile struct Sfaults*);   /* Pointer to the calc funtion           */
};
typedef volatile struct Sfaults Tfaults;

#define DEFAULTS_FAULTS                                                                                                \
  {                                                                                                                    \
    .state = FAULTS_OFF, .state_prev = FAULTS_UNDEFINED, .calc_init = Faults_calc_init, .calc_BG = Faults_calc_BG,     \
    .calc_1k = Faults_calc_1k, .mask_for_stop_faults1 = 0xFFFF, .mask_for_stop_faults2 = 0xFFFF,                       \
    .mask_bit_faults1 = 0xFFFF, .mask_bit_faults2 = 0xFFFF, .bit_faults1 = 0, .bit_faults2 = 0, .reset_timeout = 200,  \
    .psted_lister = DEFAULTS_PSTED_LISTER, .reset_psted_in_progress = false                                            \
  }

// Прототипы функций
void Faults_calc_init(Tfaults*);
void Faults_calc_BG(Tfaults*);
void Faults_calc_1k(Tfaults*);

void Faults_resetOtherDeviceErrors(Tfaults* p);

extern Tfaults faults;  //!< ДА защит

#ifdef __cplusplus
}
#endif
